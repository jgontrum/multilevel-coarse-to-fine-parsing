# distutils: language=c++
import logging

from libcpp.unordered_map cimport unordered_map
from libcpp.vector cimport vector
from libcpp.pair cimport pair

from ctf_parser.grammar.pcfg import PCFG
from ctf_parser.parser.cky_parser import CKYParser
from cython.operator cimport dereference as deref


ctypedef unsigned long long CacheContainer_t
ctypedef int Symbol_t
ctypedef short Position_t
ctypedef float Score_t

cdef struct Rule:
    Symbol_t lhs
    Symbol_t rhs_1
    Symbol_t rhs_2
    float probability

cdef CacheContainer_t bitshift(Symbol_t symbol, Position_t start, Position_t end):
    cdef CacheContainer_t item
    cdef symbol_large = <CacheContainer_t> symbol
    item = (symbol_large << 32) ^ (start << 16) ^ end
    return item

cdef Score_t outside(Symbol_t symbol, Position_t start, Position_t end,
                     short input_length, Symbol_t start_symbol,
                     unordered_map[CacheContainer_t, Score_t]& cache, pcfg):
    """
    Calculate the outside score of the symbol for the given span and save
    the result in a cache.
    :param symbol: j
    :param start: p
    :param end: q
    :return:
    """

    # Convert the symbol, start and end variables to one 64bit integer
    bit_item = bitshift(symbol, start, end)

    # Lookup in cache
    cdef unordered_map[CacheContainer_t, Score_t].iterator cache_end = \
        cache.end()
    cdef unordered_map[CacheContainer_t, Score_t].iterator cache_it = \
        cache.begin()
    cdef pair[CacheContainer_t, Score_t] map_entry

    if cache_it != cache_end:
        return deref(cache_it).second

    # Base case
    if start == 0 and end == input_length - 1:
        if symbol == start_symbol:
            score = 1.0
        else:
            score = 0.0

        # Write to cache
        map_entry.first = bit_item
        map_entry.second = score
        cache.insert(map_entry)
        return score

    # Inductive case
    score = 0.0

    cdef unsigned int lhs
    cdef unsigned int rhs_1
    cdef unsigned int rhs_2
    cdef float rule_prob
    cdef float outside
    cdef float inside

    cdef size_t e

    # Right
    for e in range(end + 1, input_length):
        for rule in pcfg.rhs1_to_rule.get(symbol, []):
            lhs = rule[0]
            rhs_2 = rule[2]

            rule_prob = rule[3]

            outside = outside(lhs, start, e)
            inside = inside(rhs_2, end + 1, e)
            score += rule_prob * outside * inside

    # Left
    for e in range(0, start):
        for rule in pcfg.rhs2_to_rule.get(symbol, []):
            lhs = rule[0]
            rhs_1 = rule[1]

            rule_prob = rule[3]

            outside = outside(lhs, e, end)
            inside = inside(rhs_1, e, start - 1)
            score += rule_prob * outside * inside

    # Write to cache
    map_entry.first = bit_item
    map_entry.second = score
    cache.insert(map_entry)

    return score

cdef class InsideOutsideCalculator:
    """
    Implementation from Manning & Schütze: Foundations of Statistical
    Natural Language Processing, p. 392 - 396
    """
    cdef unordered_map[CacheContainer_t, Score_t] inside_cache
    cdef unordered_map[CacheContainer_t, Score_t] outside_cache

    cdef unordered_map[Symbol_t, vector[Rule]] rule_for_lhs
    cdef unordered_map[Symbol_t, vector[Rule]] rule_for_rhs1
    cdef unordered_map[Symbol_t, vector[Rule]] rule_for_rhs2

    cdef Symbol_t start_symbol
    cdef short input_length

    def __init__(self, chart, pcfg):
        self.start_symbol = pcfg.start_symbol
        self.input_length = <short> len(chart)

        cdef Symbol_t symbol
        cdef Rule r
        cdef pair[Symbol_t, vector[Rule]] map_entry
        cdef vector[Rule] v

        for symbol, rules in pcfg.lhs_to_rhs.items():
            for rule in rules:
                r.rhs_1 = <Symbol_t> rule[1]
                r.rhs_2 = <Symbol_t> rule[2]
                r.probability = rule[3]
                v.push_back(r)

            map_entry.first = <Symbol_t> symbol
            map_entry.second = v

            self.rule_for_lhs.insert(map_entry)


        self.logger = logging.getLogger('CtF Parser')

    def precompute(self):
        self.inside(self.start_symbol, 0, self.input_length - 1)






    def inside(self, unsigned int symbol, size_t start,
               size_t end):
        """
        Calculate the inside score of the symbol for the given span.
        :param symbol: j
        :param start: p
        :param end: q
        :return:
        """

        # Convert the symbol, start and end variables to one 64bit integer
        bit_item = self.bitshift(symbol, start, end)

        # Lookup in cache
        cdef unordered_map[CacheContainer_t, Score_t].iterator cache_end = \
            self.outside_cache.end()
        cdef unordered_map[CacheContainer_t, Score_t].iterator cache_it = \
            self.outside_cache.begin()
        cdef pair[CacheContainer_t, Score_t] map_entry

        if cache_it != cache_end:
            return deref(cache_it).second

        # Base case
        if start == end:
            cell = self.chart[start][end]
            entry = cell.get(symbol)
            score = entry.rule[-1] if entry else 0.0

            # Write to cache
            map_entry.first = bit_item
            map_entry.second = score
            self.inside_cache.insert(map_entry)

            return score

        # Induction
        # cdef float score <- This breaks the code for whatever reason.
        cdef unsigned int rhs_1
        cdef unsigned int rhs_2
        cdef float prob
        cdef size_t d

        score = 0.0

        for d in range(start, end):
            for rule in self.pcfg.lhs_to_rhs.get(symbol, []):
                rhs_1 = rule[1]
                rhs_2 = rule[2]
                prob = rule[3]

                score += prob * self.inside(rhs_1, start, d) * self.inside(
                    rhs_2, d + 1, end)

        # Write to cache
        map_entry.first = bit_item
        map_entry.second = score
        self.inside_cache.insert(map_entry)

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
