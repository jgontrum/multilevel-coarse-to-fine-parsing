import logging
import math

from ctf_parser.grammar.pcfg import PCFG
from ctf_parser.parser.cky_parser import CKYParser


class InsideOutsideCalculator:
    """
    Implementation from Manning & Schütze: Foundations of Statistical
    Natural Language Processing, p. 392 - 396
    """

    def __init__(self, chart, pcfg):
        self.inside_cache = {}
        self.outside_cache = {}

        self.pcfg = pcfg
        self.chart = chart
        self.input_length = len(chart)
        self.logger = logging.getLogger('CtF Parser')

    def outside(self, symbol, start, end):
        """
        Calculate the outside score of the symbol for the given span.
        :param symbol: j
        :param start: p
        :param end: q
        :return:
        """

        # Try to read from cache
        cache = self.outside_cache.get((symbol, start, end))
        if cache is not None:
            return cache

        # Base case
        if start == 0 and end == self.input_length - 1:
            if symbol == self.pcfg.start_symbol:
                score = 1
            else:
                score = 0
            self.outside_cache[(symbol, start, end)] = score
            return score

        # Inductive case
        score = 0.0

        # Right
        for e in range(end + 1, self.input_length):
            for rule in self.pcfg.rhs1_to_rule.get(symbol, []):
                lhs = rule[0]
                rhs_2 = rule[2]

                rule_prob = rule[3]

                outside = self.outside(lhs, start, e)
                inside = self.inside(rhs_2, end + 1, e)
                score += rule_prob * outside * inside

        # Left
        for e in range(0, start):
            for rule in self.pcfg.rhs2_to_rule.get(symbol, []):
                lhs = rule[0]
                rhs_1 = rule[1]

                rule_prob = rule[3]

                outside = self.outside(lhs, e, end)
                inside = self.inside(rhs_1, e, start - 1)
                score += rule_prob * outside * inside

        self.outside_cache[(symbol, start, end)] = score

        return score

    def inside(self, symbol, start, end):
        """
        Calculate the inside score of the symbol for the given span.
        :param symbol: j
        :param start: p
        :param end: q
        :return:
        """

        # Try to read from cache
        cache = self.inside_cache.get((symbol, start, end))
        if cache is not None:
            return cache

        # Base case
        if start == end:
            cell = self.chart[start][end]
            entry = cell.get(symbol)
            score = entry.rule[-1] if entry else 0.0
            self.inside_cache[(symbol, start, end)] = score

            return score

        # Induction
        score = 0.0
        for d in range(start, end):
            for rule in self.pcfg.lhs_to_rhs.get(symbol, []):
                rhs_1 = rule[1]
                rhs_2 = rule[2]
                prob = rule[3]

                score += prob * self.inside(rhs_1, start, d) * self.inside(
                    rhs_2, d + 1, end)

        self.inside_cache[(symbol, start, end)] = score

        return score


if __name__ == '__main__':
    GRAMMAR = [
        ["Q1", "NP", "Peter", 0.5],
        ["Q1", "V", "sees", 1.0],
        ["Q1", "Det", "a", 1.0],
        ["Q1", "N", "squirrel", 1.0],
        ["Q2", "S", "NP", "VP", 1.0],
        ["Q2", "VP", "V", "NP", 1.0],
        ["Q2", "NP", "Det", "N", 0.5],
        ["WORDS", ["Peter", "a", "sees", "squirrel"]]
    ]

    pcfg = PCFG()
    pcfg.load_model(GRAMMAR)

    parser = CKYParser(pcfg)

    chart = parser.parse("Peter sees a squirrel")

    parser.print_table(chart)

    io = InsideOutsideCalculator(chart, pcfg)

    print(io.outside(pcfg.get_id_for_word("NP"), 2, 3))
