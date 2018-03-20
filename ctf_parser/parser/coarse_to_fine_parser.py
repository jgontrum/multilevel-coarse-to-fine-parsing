import json
import logging
import time

import yaml

from ctf_parser.grammar.pcfg import PCFG
from ctf_parser.grammar.transform import transform_to_new_grammar, \
    replace_symbols
from ctf_parser.parser.cky_parser import CKYParser, NoParseFoundException
from ctf_parser.parser.ctf_mapper import CtfMapper
from ctf_parser.parser.inside_outside_calculator import InsideOutsideCalculator


class CoarseToFineParser:

    def __init__(self, pcfg, mapping, prefix="grammar", threshold=0.0001):
        self.THRESHOLD = threshold
        self.logger = logging.getLogger('CtF Parser')
        self.mapping = mapping
        self.grammars = [pcfg]

        current_pcfg = pcfg
        for i in range(mapping.levels, -1, -1):
            self.logger.info(f"Transform {i}")
            current_pcfg = transform_to_new_grammar(current_pcfg, mapping, i,
                                                    save=True, read=True,
                                                    prefix=prefix)

            # TODO make this generic
            if i == 2:
                current_pcfg.start_symbol = current_pcfg.get_id_for_word("S_")
            if i == 1:
                current_pcfg.start_symbol = current_pcfg.get_id_for_word("HP")
            if i == 0:
                current_pcfg.start_symbol = current_pcfg.get_id_for_word("P")

            self.grammars.append(current_pcfg)

        self.logger.info(f"Prepared {len(self.grammars)} grammars...")

        self.grammars.reverse()

    def parse_best(self, sentence):
        """
        Returns the tree of the best parse for the sentence.
        :param sentence: String
        :return: Tree
        """
        chart = self.parse(sentence)
        parser = CKYParser(self.grammars[-1])
        return parser.get_best_from_chart(chart)

    def create_evaluation_function(self, fine_pcfg, coarse_pcfg,
                                   inside_outside_calculator, fine_to_coarse,
                                   sentence_probability):
        """
        Defines the evaluation function used to decide if an item will be
        pruned or not.

        I created this function to streamline the main coarse-to-fine code.
        :param fine_pcfg: PCFG of the current level
        :param coarse_pcfg: PCFG of the previous level
        :param inside_outside_calculator: IO Calculator of the previous level
        :param fine_to_coarse: Mapping to get coarse symbols for fine ones.
        :param sentence_probability: Probability of the previous sentence.
        :return:
        """
        symbol_cache = {}

        def evaluate(item):
            """
            Takes a symbol and its position and evaluate if it should
            be entered into the chart or not.

            This function has to be defined here, as it needs the local
            variables like inside_outside_calculator, fine- and coarse pcfgs
            or the threshold.
            :param item: Tuple of (symbol, start, end)
            :return: True or False
            """
            if inside_outside_calculator is None:
                # In level 0, there are no previous scores to use,
                # so we accept all symbols into the chart.
                return True

            fine_symbol, start, end = item

            # Lazily create the coarse version of a symbol for a given fine one
            coarse_symbol = symbol_cache.get(fine_symbol)
            if coarse_symbol is None:
                coarse_symbol_as_string = replace_symbols(
                    fine_pcfg.get_word_for_id(fine_symbol), fine_to_coarse)

                coarse_symbol = coarse_pcfg.get_id_for_word(
                    coarse_symbol_as_string)
                symbol_cache[fine_symbol] = coarse_symbol

            if coarse_symbol is None:
                self.logger.warning(f"No coarse symbol found for "
                                    f"{pcfg.get_word_for_id(fine_symbol)}")
                return True

            # Calculate inside and outside scores for the coarse symbol
            # in the previous chart.

            inside = inside_outside_calculator.inside(
                coarse_symbol, start, end)
            outside = inside_outside_calculator.outside(
                coarse_symbol, start, end)

            score = inside * outside / sentence_probability

            return score > self.THRESHOLD

        return evaluate

    def parse(self, sentence):
        """
        Parses the input and returns the chart.
        :param sentence: String
        :return: Chart
        """
        t0 = time.time()
        overall_statistics = {"threshold": self.THRESHOLD,
                              "input": sentence, "items_pruned": 0,
                              "items_entered": 0, "type": "summary",
                              "timestamp": t0}

        fine_pcfg = None
        fine_chart = None
        inside_outside_calculator = None
        sentence_probability = None
        parser = None

        # Iterate from coarse to fine grammars and parse the sentence.
        for i in range(0, len(self.grammars)):
            t1 = time.time()
            fine_to_coarse = self.mapping.fine_to_coarse[i - 1]

            coarse_pcfg = fine_pcfg
            fine_pcfg = self.grammars[i]

            # Create the evaluation function that decides over pruning.
            # If this is the first, level 0 grammar, the function will accept
            # every item to be entered into the chart.
            evaluate = self.create_evaluation_function(
                fine_pcfg, coarse_pcfg, inside_outside_calculator,
                fine_to_coarse, sentence_probability)

            parser = CKYParser(fine_pcfg, evaluation_function=evaluate)

            # Parse the sentence with the current grammar.
            log_statistics = {"level": i, "threshold": self.THRESHOLD,
                              "input": sentence, "type": "level",
                              "timestamp": t1}
            fine_chart = parser.parse(sentence, log_dict=log_statistics)

            overall_statistics['length'] = log_statistics['length']
            overall_statistics['items_pruned'] += log_statistics['items_pruned']
            overall_statistics['items_entered'] += log_statistics[
                'items_entered']

            if i < len(self.grammars) - 1:
                # Set up the inside-outside calculator that will be used to
                # parse with the next finer grammar. These steps are only
                # necessary if there is a next level.

                inside_outside_calculator = InsideOutsideCalculator(
                    fine_chart, fine_pcfg)

                # Also pre-compute the sentence probability.
                sentence_probability = inside_outside_calculator.inside(
                    fine_pcfg.start_symbol, 0, len(fine_chart) - 1)

                log_statistics['sentence_probability'] = sentence_probability
                if sentence_probability == 0.0:
                    raise NoParseFoundException(
                        f"No parse found after parsing at level {i}. Aborting.")

                log_statistics['overall_time'] = time.time() - t1

            self.logger.info(json.dumps(log_statistics, sort_keys=True))

        overall_statistics['time'] = time.time() - t0
        self.logger.info(json.dumps(overall_statistics, sort_keys=True))

        return fine_chart
