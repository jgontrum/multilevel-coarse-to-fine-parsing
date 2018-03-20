from collections import defaultdict


class CtfMapper(object):

    def __init__(self, mapping):
        # Map coarse symbol to fine symbol for each level
        self.coarse_to_fine = defaultdict(dict)

        # Also map fine symbol to coarse symbol
        self.fine_to_coarse = defaultdict(dict)

        self._add_level(mapping, 0)

        self.levels = max(self.coarse_to_fine.keys())

    def _add_level(self, mapping, level):
        for key, values in mapping.items():
            if type(values) != str:
                for value in values:
                    self.fine_to_coarse[level][value] = key
                    self.coarse_to_fine[level].setdefault(key, []).append(value)

            if type(values) == dict:
                self._add_level(values, level + 1)
