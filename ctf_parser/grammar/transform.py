import math
from collections import defaultdict

from pcfg_parser.parser.pcfg import PCFG


def transform(pcfg, mapping, level=2):
    fine_to_coarse = mapping.fine_to_coarse[level]
    symbol = pcfg.get_word_for_id

    """
    Replace Symbols:
    
    Iterate over rules in the given grammar and replace the symbols according
    to the coarse-to-find mapping.
    """
    transformed_rules = defaultdict(list)

    for i, rules in enumerate(pcfg.id_to_lhs):
        lhs_t = fine_to_coarse.get(symbol(i), symbol(i))

        for rule in rules:
            if len(rule) == 4:
                lhs, rhs1, rhs2, prob = rule

                rhs1_t = fine_to_coarse.get(symbol(rhs1), symbol(rhs1))
                rhs2_t = fine_to_coarse.get(symbol(rhs2), symbol(rhs2))
                prob_t = math.pow(math.e, prob)

                transformed_rules[lhs_t].append((lhs_t, rhs1_t, rhs2_t, prob_t))

                # print(
                #     f"{symbol(lhs)} => {symbol(rhs1)} {symbol(rhs2)} [{prob}]")
                # print(f"{lhs_t} => {rhs1_t} {rhs2_t} [{prob_t}]")

            elif len(rule) == 2:
                rhs1, prob = rule

                rhs1_t = fine_to_coarse.get(symbol(rhs1), symbol(rhs1))
                prob_t = math.pow(math.e, prob)

                transformed_rules[lhs_t].append((lhs_t, rhs1_t, prob_t))

    """
    Normalize rules:
    
    Since there are probably more rules for each left-hand side symbol, their
    probability will not add up to 1 any more. We will now normalize them by
    dividing each probability by the summed up probability.
    """
    final_rules = []
    words = set()
    for lhs, rules in transformed_rules.items():
        # Sum up rules with the same rhs:
        rhs_to_prob = defaultdict(float)

        for rule in rules:
            if len(rule) == 4:
                rhs = (rule[1], rule[2])
            elif len(rule) == 3:
                rhs = (rule[1],)
            else:
                raise ValueError("Bad rule.")

            prob = rule[-1]
            rhs_to_prob[rhs] = prob

        probability_mass = sum(rhs_to_prob.values())
        for rhs, prob in rhs_to_prob.items():
            if len(rhs) == 2:
                final_rules.append(
                    ["Q2", lhs, rhs[0], rhs[1], prob / probability_mass])
            else:
                final_rules.append(
                    ["Q1", lhs, rhs[0], prob / probability_mass])
                words.add(rhs[0])

    """
    Sort rules:
    
    Finally, sort rules according to their arity and write the vocabulary 
    as the latest.
    """
    final_rules = sorted(final_rules, key=lambda x: x[0])
    final_rules.append(["WORDS", list(words)])

    return final_rules


def transform_to_new_grammar(pcfg, mapping, level=2):
    new_pcfg = PCFG()
    new_pcfg.load_model(transform(pcfg, mapping, level))
    return new_pcfg
