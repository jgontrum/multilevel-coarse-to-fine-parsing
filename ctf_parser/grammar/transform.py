import json
from collections import defaultdict

from ctf_parser import logger
from ctf_parser.grammar.pcfg import PCFG


def replace_symbols(text, fine_to_coarse, unary_symbol="‡", binary_symbol="†"):
    """
    Splits a symbol and replaces all occurences with their coarse counterpart.
    This is needed because through binarization, many symbols consist of a
    sequence of other symbols.
    :param text: The symbol string
    :param fine_to_coarse: Maps fine symbols to a coarse symbol
    :param unary_symbol: Character used to separate symbols froma unary chain rule
    :param binary_symbol: Character used to separate symbols from rules with an arity > 2
    :return:
    """
    unary_split = text.split(unary_symbol)
    unaries_replaced = []
    for unary in unary_split:
        binarize_split = unary.split(binary_symbol)
        binaries_replaced = []
        for binary in binarize_split:
            binaries_replaced.append(fine_to_coarse.get(binary, binary))
        unaries_replaced.append(binary_symbol.join(binaries_replaced))
    ret = unary_symbol.join(unaries_replaced)
    return ret


def transform(pcfg, mapping, level=2):
    """
    Transforms all symbols in all rules in the given PCFG to coarse ones.
    :param pcfg: The fine grammar.
    :param mapping: Coarse-to-Fine symbol mapping
    :param level: The current level
    :return: A raw coarse grammar
    """
    fine_to_coarse = mapping.fine_to_coarse[level]
    symbol = pcfg.get_word_for_id

    """
    Replace Symbols:
    
    Iterate over rules in the given grammar and replace the symbols according
    to the coarse-to-find mapping.
    """
    transformed_rules = defaultdict(list)

    for lhs, rules in enumerate(pcfg.id_to_lhs):

        for rule in rules:
            if len(rule) == 4:
                lhs, rhs1, rhs2, prob = rule

                lhs_t = replace_symbols(symbol(lhs), fine_to_coarse)

                rhs1_t = replace_symbols(symbol(rhs1), fine_to_coarse)
                rhs2_t = replace_symbols(symbol(rhs2), fine_to_coarse)
                prob_t = prob

                transformed_rules[lhs_t].append((lhs_t, rhs1_t, rhs2_t, prob_t))

            elif len(rule) == 3:
                lhs, rhs1, prob = rule

                lhs_t = replace_symbols(symbol(lhs), fine_to_coarse)
                rhs1_t = replace_symbols(symbol(rhs1), fine_to_coarse)
                prob_t = prob

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
    final_rules.append(["WORDS", list(sorted(words))])

    return final_rules


def transform_to_new_grammar(pcfg, mapping, level=2, save=True, read=False,
                             prefix="grammar"):
    """
    Wrapper for the transform() function. Transforms a grammar and returns
    a PCFG object. Can also read/write the resulting grammar to file for speedup.
    :param pcfg: The fine grammar
    :param mapping: Coarse to fine mapping object
    :param level: The desired level of granularity
    :param save: Should the output grammar saved to a file?
    :param read: Read the grammar from file instead if it exists
    :param prefix: Prefix for the file to read/write from or to
    :return:
    """
    new_pcfg = PCFG()
    path = f"{prefix}_{level}.pcfg"

    if read:
        try:
            new_pcfg.load_model(
                [json.loads(l) for l in open(path)])
            logger.info(f"Read grammar from file (\"{path}\")"
                        f" (level {level})...")

            return new_pcfg
        except FileNotFoundError:
            pass

    new_grammar = transform(pcfg, mapping, level)
    new_pcfg.load_model(new_grammar)

    if save:
        with open(path, "w") as f:
            logger.info(f"Write to file (\"{path}\") (level {level})...")
            for l in new_grammar:
                f.write(json.dumps(l) + "\n")

    return new_pcfg
