import yaml
from ctf_parser.parser.ctf_mapper import CtfMapper

MAPPING = """
S1:
  S1:
    S1:
      - S1
P:
  HP:
    S_:
      - S
      - VP
      - UCP
      - SQ
      - SBAR
      - SBARQ
      - SINV
    N_:
      - NP
      - NAC
      - NX
      - LST
      - X
      - UCP
      - FRAG
  MP:
    A_:
      - ADJP
      - QP
      - CONJP
      - ADVP
      - INTJ
      - PRN
      - PRT
    P_:
      - PP
      - PRT
      - RRC
      - WHADJP
      - WHADVP
      - WHNP
      - WHPP
"""


def test_ctf_mapping():
    mapping = yaml.load(MAPPING)

    ctf_mapper = CtfMapper(mapping)
    assert ctf_mapper.coarse_to_fine == {0: {'S1': ['S1'], 'P': ['HP', 'MP']},
                                         1: {'S1': ['S1'], 'HP': ['S_', 'N_'],
                                             'MP': ['A_', 'P_']},
                                         2: {'S1': ['S1'],
                                             'S_': ['S', 'VP', 'UCP', 'SQ',
                                                    'SBAR', 'SBARQ', 'SINV'],
                                             'N_': ['NP', 'NAC', 'NX', 'LST',
                                                    'X', 'UCP', 'FRAG'],
                                             'A_': ['ADJP', 'QP', 'CONJP',
                                                    'ADVP', 'INTJ', 'PRN',
                                                    'PRT'],
                                             'P_': ['PP', 'PRT', 'RRC',
                                                    'WHADJP', 'WHADVP', 'WHNP',
                                                    'WHPP']}}
    assert ctf_mapper.fine_to_coarse == {0: {'S1': 'S1', 'HP': 'P', 'MP': 'P'},
                                         1: {'S1': 'S1', 'S_': 'HP', 'N_': 'HP',
                                             'A_': 'MP', 'P_': 'MP'},
                                         2: {'S1': 'S1', 'S': 'S_', 'VP': 'S_',
                                             'UCP': 'N_', 'SQ': 'S_',
                                             'SBAR': 'S_', 'SBARQ': 'S_',
                                             'SINV': 'S_', 'NP': 'N_',
                                             'NAC': 'N_', 'NX': 'N_',
                                             'LST': 'N_', 'X': 'N_',
                                             'FRAG': 'N_', 'ADJP': 'A_',
                                             'QP': 'A_', 'CONJP': 'A_',
                                             'ADVP': 'A_', 'INTJ': 'A_',
                                             'PRN': 'A_', 'PRT': 'P_',
                                             'PP': 'P_', 'RRC': 'P_',
                                             'WHADJP': 'P_', 'WHADVP': 'P_',
                                             'WHNP': 'P_', 'WHPP': 'P_'}}
