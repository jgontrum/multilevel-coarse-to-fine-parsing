import argparse
import hashlib
import json
import logging
import time
from sys import stdin, stderr

import yaml

from ctf_parser.grammar.pcfg import PCFG
from ctf_parser.parser.cky_parser import NoParseFoundException, CKYParser
from ctf_parser.parser.coarse_to_fine_parser import CoarseToFineParser
from ctf_parser.parser.ctf_mapper import CtfMapper


def ctf():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--grammar", help="Path to the grammar to be used.",
                        type=str, required=False, default="data/grammar.pcfg")
    parser.add_argument("--ctfmapping",
                        help="Path to the coarse-to-fine symbol mapping file.",
                        type=str, required=False,
                        default="data/ctf_mapping.yml")
    parser.add_argument("--threshold",
                        help="Threshold for coarse-to-fine parsing.",
                        type=float, required=False, default=0.0001)

    parser.add_argument("--enable_logs",
                        help="Enable logging to stdout and file.",
                        dest='enable_logs', action='store_true',
                        required=False, default=False)

    args = parser.parse_args()

    if not args.enable_logs:
        logger = logging.getLogger('CtF Parser')
        logger.setLevel(logging.ERROR)

    print("Preparing parser... This can take a few seconds...", file=stderr)

    pcfg = PCFG()
    pcfg.load_model([json.loads(l) for l in open(args.grammar)])
    mapping = CtfMapper(yaml.load(open(args.ctfmapping)))

    # Create a hash from the file name so that a transformed grammar can be
    # saved / read with that prefix. (e.g. tmp_ctf_grammar_11268463_0.pcfg
    # for a grammar at level 0).
    filename_hash = int(hashlib.sha1(args.grammar.encode()).hexdigest(), 16
                        ) % (10 ** 8)
    ctf = CoarseToFineParser(pcfg, mapping,
                             prefix=f"tmp_ctf_grammar_{filename_hash}",
                             threshold=args.threshold)

    print("Done! Please enter a sentence.\n", file=stderr)
    for line in stdin:
        try:
            print(ctf.parse_best(line.strip()))
        except NoParseFoundException:
            print("[]")


def cky():
    parser = argparse.ArgumentParser(
        "ckyparser", description="CKY Parser to compare the performance to the "
                                 "coarse-to-fine parser.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--grammar", help="Path to the grammar to be used.",
                        type=str, required=False, default="data/grammar.pcfg")

    parser.add_argument("--enable_logs",
                        help="Enable logging to stdout and file.",
                        dest='enable_logs', action='store_true',
                        required=False, default=False)

    args = parser.parse_args()
    logger = logging.getLogger('CtF Parser')

    if not args.enable_logs:
        logger.setLevel(logging.ERROR)

    print("Preparing parser...", file=stderr)

    pcfg = PCFG()
    pcfg.load_model([json.loads(l) for l in open(args.grammar)])

    parser = CKYParser(pcfg)

    print("Done! Please enter a sentence.\n", file=stderr)
    for line in stdin:
        try:
            log = {"sentence": line.strip(), "timestamp": time.time()}
            tree = parser.parse_best(line.strip(), log)
            print(tree)
            logger.info(json.dumps(log, sort_keys=True))
        except NoParseFoundException:
            print("[]")
