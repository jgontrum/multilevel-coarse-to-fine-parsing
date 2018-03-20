# Multilevel Coarse-to-fine Parsing
## A pruning algorithm for PCFGs
Implementation of Charniak et al.'s 'Multilevel Coarse-to-fine PCFG Parsing'
for the Syntactic Parsing class at Uppsala University.

### Requirements

- Python 3.6
    - If you have Anaconda installed, please set the environment variable 
    `PYTHON3` to the original python3.6 executable on your system.
- make
- A PCFG in CNF (or use the one in `data/grammar.pcfg`)

### Installation

Execute `make`.

### Usage

Execute `env/bin/ctfparser`. It reads from stdin and writes the best tree
for each input to stdout.

```bash
usage: ctfparser [-h] [--grammar GRAMMAR] [--ctfmapping CTFMAPPING]
                 [--threshold THRESHOLD] [--enable_logs]

optional arguments:
  -h, --help            show this help message and exit
  --grammar GRAMMAR     Path to the grammar to be used. (default:
                        data/grammar.pcfg)
  --ctfmapping CTFMAPPING
                        Path to the coarse-to-fine symbol mapping file.
                        (default: data/ctf_mapping.yml)
  --threshold THRESHOLD
                        Threshold for coarse-to-fine parsing. (default:
                        0.0001)
  --enable_logs         Enable logging to stdout and file. (default: False)
```