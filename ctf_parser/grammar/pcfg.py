import math
from collections import defaultdict
from json import loads

import numpy as np
from scipy.sparse import dok_matrix

"""
Optimized PCFG class that stores binary rules in a numpy matrix and prepares
datastructures to intersect the first and second symbols of the rules.

A detailed investigation of this procedure can be found here:
https://github.com/jgontrum/cky-parser-optimization
"""

class PCFG():

    def __init__(self, start_symbol="S"):
        # '0' is reserved for the sparse matrix.
        self.word_to_id = {"DUMMY": 0}
        self.id_to_word = ["DUMMY"]

        self.well_known_words = {}
        self.start_symbol = self.__add_to_signature(start_symbol)

    def norm_word(self, word):
        return word if word in self.well_known_words else "_RARE_"

    def get_lhs(self, rhs_1, rhs_2):
        lhs_id = self.rhs_to_lhs_id[rhs_1, rhs_2]
        return self.id_to_lhs[lhs_id]

    def get_lhs_for_terminal_rule(self, rhs_1):
        lhs_id = self.terminal_rule_to_lhs_id[rhs_1]
        return self.id_to_lhs[lhs_id]

    def get_id_for_word(self, word):
        return self.word_to_id.get(word)

    def get_word_for_id(self, id_):
        return self.id_to_word[id_]

    def __build_caches(self):
        size = max(self.non_terminals) + 1
        self.rhs_to_lhs_id = dok_matrix((size, size), dtype=np.int32)
        self.terminal_rule_to_lhs_id = {}
        self.first_rhs_to_second_rhs = defaultdict(set)

        for i, (lhs, rhs, prob) in enumerate(self.rule_cache):
            rhs_1 = rhs[0]

            lhs_id = self.rhs_to_lhs_cache[tuple(rhs)]
            if len(rhs) == 1:
                # terminal rules
                self.terminal_rule_to_lhs_id[rhs_1] = lhs_id
            else:
                # non terminals
                rhs_2 = rhs[1]
                self.rhs_to_lhs_id[rhs_1, rhs_2] = lhs_id
                self.first_rhs_to_second_rhs[rhs_1].add(rhs_2)

        self.rhs_to_lhs_id = self.rhs_to_lhs_id.toarray()
        self.id_to_lhs = np.asarray(self.id_to_lhs, dtype=object)

        self.first_rhs_symbols = set(self.first_rhs_to_second_rhs.keys())

        self.rule_cache.clear()
        self.terminals.clear()
        self.non_terminals.clear()

    def __add_to_signature(self, word):
        if word in self.word_to_id:
            return self.word_to_id.get(word)

        new_id = len(self.id_to_word)
        self.id_to_word.append(word)
        self.word_to_id[word] = new_id
        return new_id

    def load_model(self, model):
        self.rule_cache = []
        self.id_to_lhs = [[]]
        self.rhs_to_lhs_cache = {}

        self.non_terminals = set()
        self.terminals = set()

        non_binary_rules_cache = []

        # Binary rules that contain only non terminals must be handled
        # before any terminals, so that the range of their ids starts at 0
        # and is continous.
        # This is important for an efficient matrix construction.
        for line in model:
            data = loads(line)

            if data[0] != "Q2":
                non_binary_rules_cache.append(data)
                continue

            lhs_raw = data[1]
            rhs_raw = data[2:-1]
            prob = data[-1]

            lhs = self.__add_to_signature(lhs_raw)
            rhs = [self.__add_to_signature(sym) for sym in rhs_raw]

            self.non_terminals.add(rhs[0])
            self.non_terminals.add(rhs[1])
            item = (lhs, rhs[0], rhs[1], math.log(prob))

            lhs_id = self.rhs_to_lhs_cache.get(tuple(rhs))
            if lhs_id is None:
                lhs_id = len(self.id_to_lhs)
                self.id_to_lhs.append([item])
                self.rhs_to_lhs_cache[tuple(rhs)] = lhs_id
            else:
                self.id_to_lhs[lhs_id].append(item)

            self.rule_cache.append((lhs, rhs, prob))

        # Now handle all other rules
        for data in non_binary_rules_cache:
            if data[0] == 'WORDS':
                self.well_known_words = data[1]
                for word in self.well_known_words:
                    self.__add_to_signature(word)
                continue

            lhs_raw = data[1]
            rhs_raw = data[2:-1]
            prob = data[-1]

            lhs = self.__add_to_signature(lhs_raw)
            rhs = [self.__add_to_signature(sym) for sym in rhs_raw]

            self.terminals.add(rhs[0])
            item = (lhs, math.log(prob))

            lhs_id = self.rhs_to_lhs_cache.get(tuple(rhs))
            if lhs_id is None:
                lhs_id = len(self.id_to_lhs)
                self.id_to_lhs.append([item])
                self.rhs_to_lhs_cache[tuple(rhs)] = lhs_id
            else:
                self.id_to_lhs[lhs_id].append(item)

            self.rule_cache.append((lhs, rhs, prob))

        self.__add_to_signature("_RARE_")

        self.__build_caches()
