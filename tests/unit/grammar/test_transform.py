import yaml
from ctf_parser.grammar.pcfg import PCFG
from ctf_parser.grammar.transform import transform, transform_to_new_grammar
from ctf_parser.parser.ctf_mapper import CtfMapper

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

MAPPING = """
P:
  HP:
    S_:
      - S
      - VP
  MP:
    N_:
      - NP
"""


def test_transform_once():
    pcfg = PCFG()
    pcfg.load_model(GRAMMAR)

    mapping = CtfMapper(yaml.load(MAPPING))
    new_grammar = transform(pcfg, mapping, level=2)

    assert new_grammar == [['Q1', 'V', 'Peter', 1.0],
                           ['Q1', 'Det', 'sees', 1.0], ['Q1', 'N', 'a', 1.0],
                           ['Q1', 'Peter', 'squirrel', 1.0],
                           ['Q2', 'S_', 'N_', 'S_', 0.6666666666666666],
                           ['Q2', 'S_', 'Det', 'N', 0.3333333333333333],
                           ['Q2', 'N_', 'V', 'N_', 1.0],
                           ['WORDS', ['Peter', 'a', 'sees', 'squirrel']]]


def test_dummy_grammar_creation():
    pcfg = PCFG()
    pcfg.load_model(GRAMMAR)

    mapping = CtfMapper(yaml.load(MAPPING))
    new_grammar = transform_to_new_grammar(pcfg, mapping, level=2)
    assert type(new_grammar) == PCFG
