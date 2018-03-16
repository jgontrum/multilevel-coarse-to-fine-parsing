import json
import logging
from time import time

from prettytable import PrettyTable

from ctf_parser.grammar.pcfg import PCFG
from ctf_parser.parser.tokenizer import PennTreebankTokenizer


class CKYParser:

    def __init__(self, pcfg):
        self.pcfg = pcfg
        self.tokenizer = PennTreebankTokenizer()
        self.logger = logging.getLogger('CtF Parser')

    def parse_best(self, sentence):
        words = self.tokenizer.tokenize(sentence)
        norm_words = []

        for word in words:
            norm_words.append((self.pcfg.norm_word(word), word))
        chart = self.cky(norm_words)

        tree = self.backtrace(chart[0][-1][self.pcfg.start_symbol], chart)

        tree[0] = tree[0].split("|")[0]

        return tree, chart

    def parse(self, sentence):
        words = self.tokenizer.tokenize(sentence)
        norm_words = []

        for word in words:
            norm_words.append((self.pcfg.norm_word(word), word))

        return self.cky(norm_words)

    def backtrace(self, item, chart):
        if item.terminal:
            assert item.backpointers is None
            return [
                self.pcfg.get_word_for_id(item.symbol),
                item.terminal
            ]

        rhs_1, rhs_2 = item.backpointers

        return [
            pcfg.get_word_for_id(item.symbol),
            self.backtrace(
                chart[rhs_1.i][rhs_1.j][rhs_1.symbol],
                chart
            ),
            self.backtrace(
                chart[rhs_2.i][rhs_2.j][rhs_2.symbol],
                chart
            )
        ]

    def cky(self, norm_words):
        t0 = time()

        # Initialize your charts (for scores and backpointers)
        size = len(norm_words)
        chart = [[{} for _ in range(size)] for _ in range(size)]

        # Code for adding the words to the chart
        for i, (norm, word) in enumerate(norm_words):
            id_ = self.pcfg.get_id_for_word(norm)
            for lhs, rhs, prob in self.pcfg.get_lhs_for_terminal_rule(id_):
                item = CKYParser.ChartItem(lhs, prob, rule=(lhs, rhs, prob),
                                           terminal=word,
                                           pcfg=self.pcfg)
                existing_item = chart[i][i].get(lhs)
                if not existing_item or \
                        existing_item.probability < item.probability:
                    chart[i][i][lhs] = item

        # Implementation is based upon J&M
        for j in range(size):
            for i in range(j, -1, -1):
                for k in range(i, j):
                    first_nts = chart[i][k]
                    second_nts = chart[k + 1][j]

                    lookup = self.__loop_based_lookup

                    for entry in lookup(first_nts, second_nts):
                        lhs, rhs_1, rhs_2, probability = entry
                        existing_item = chart[i][j].get(lhs)
                        if not existing_item \
                                or existing_item.probability < probability:
                            item = CKYParser.ChartItem(lhs, probability,
                                                       (i, k, rhs_1),
                                                       (k + 1, j, rhs_2),
                                                       rule=entry,
                                                       pcfg=self.pcfg)
                            chart[i][j][lhs] = item

        stats = {
            "time": time() - t0,
            "length": len(norm_words)
        }

        self.logger.info(json.dumps(stats))
        return chart

    def __loop_based_lookup(self, first_nts, second_nts):
        second_symbols = second_nts.keys()
        first_symbols = self.pcfg.first_rhs_symbols

        possible_rhs1 = first_symbols.intersection(first_nts)

        for rhs_1_symbol in possible_rhs1:
            rhs_1 = first_nts[rhs_1_symbol]

            possible_rhs2 = \
                self.pcfg.first_rhs_to_second_rhs[
                    rhs_1_symbol].intersection(
                    second_symbols)

            for rhs_2_symbol in possible_rhs2:
                rhs_2 = second_nts[rhs_2_symbol]

                for lhs, _, _, prob in self.pcfg.get_lhs(rhs_1.symbol,
                                                         rhs_2.symbol):
                    probability = rhs_1.probability
                    probability += rhs_2.probability
                    probability += prob

                    yield lhs, rhs_1.symbol, rhs_2.symbol, probability

    def print_table(self, chart):
        table = PrettyTable([""] + list(range(len(chart))))
        for i, row in enumerate(chart):
            r = [i]
            for cell in row:
                r.append(
                    {self.pcfg.get_word_for_id(k): v for k, v in cell.items()})
            table.add_row(r)
        print(table)

    class ChartItem(object):
        class Backpointer(object):
            def __init__(self, i, j, symbol):
                self.i = i
                self.j = j
                self.symbol = symbol

        def __init__(self, symbol, probability, bp_1=None, bp_2=None,
                     terminal=None, rule=None, pcfg=None):
            self.symbol = symbol
            self.probability = probability
            self.pcfg = pcfg
            self.rule = rule

            self.backpointers = (
                CKYParser.ChartItem.Backpointer(bp_1[0], bp_1[1], bp_1[2]),
                CKYParser.ChartItem.Backpointer(bp_2[0], bp_2[1], bp_2[2])
            ) if bp_1 else None

            self.terminal = terminal

        def __repr__(self):
            if self.pcfg:
                symbol = self.pcfg.get_word_for_id(self.symbol)
            else:
                symbol = self.symbol
            return f"[{symbol},{self.probability:0.4f}]"


if __name__ == '__main__':
    pcfg = PCFG(start_symbol="P")
    pcfg.load_model([json.loads(l) for l in open("grammar_0.pcfg")])

    parser = CKYParser(pcfg)

    print(parser.parse("This is a test."))
