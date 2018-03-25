# Project: Multilevel Coarse-to-Fine Parsing for PCFGs

In my project, I successfully implemented the algorithm introduced in XXX with the exception of their binarization strategy. Unfortunately, I could not reproduce the reported
10x speed improvement. In fact, the overhead introduced by calculating the inside and outside probabilities slow the parsing several orders of magnitude down compared to a CKY implementation without pruning.

## Implementation

### Coarse-to-fine mapping
The mapping of coarse to fine symbols is defined in `data/ctf_mapping.yml`. It is processed by the `CtfMapper` class in `ctf_parser/parser/ctf_mapper.py` which creates a dictionary for each level to map coarse to fine symbols and another one to reverse it.

### PCFG
I used the PCFG class I implemented for the first assignment with only a few adjustments (`ctf_parser/grammar/pcfg.py`): I introduced additional dictionaries to map the left-hand-sides to rules, as well as the first symbol of a rule and the second one. These data structures are important as they are needed to quickly lookup rules to calculate inside and outside scores later on.

### Grammar transformation
A grammar has to be created for every level of granularity. While XXX suggest their own binarization strategy, I decided to use a grammar that is already in CNF and transform its rules by replacing every fine symbol by a coarse one. As the pre binarized grammar may contain symbols like `S_PP_:`, I also replace each symbol in the string. I used the grammar generated for the first assignment as the foundation, with the only difference that I replaced the separation symbols for binarizing and removing chain rules by more unique symbols.

The code can be found in `ctf_parser/grammar/transform.py`.

### CKY parser
I adapted an optimized version of the CKY parser I wrote for assignment 1 in `ctf_parser/parser/cky_parser.py`. The most noticeable difference is that the class now has an *evaluation function*. Whenever an item has been found that should be entered into the chart, the function is called with the symbol, the span it covers and the used rule. If the function returns true, it is written to the chart, otherwise, it is discarded.

In my implementation the function is passed as a function object. If none is defined, a function is used that always returns true:


```python
if evaluation_function is None:
    self.evaluation_function = lambda _: True
else:
    self.evaluation_function = evaluation_function
```

### Calculating inside and outside scores
My implementation of the inside and outside score calculation is based on the algorithm in XXX. I tried to implement it as straightforward as possible in `ctf_parser/parser/inside_outside_calculator.py`. The main difference is that I use a cache to save already calculated results. In my approach, the inside cache is populated before the actual parsing, as the coarse-to-fine algorithm requires the probability of the sentence, which I assume to be the inside score of the whole sentence under the start symbol. The outside probabilities are calculated lazily.

### CtF parser
In `ctf_parser/parser/inside_outside_calculator.py` all the previously introduced classes come together: When the parser is initialized, it creates multiple coarse versions of the given grammar and saves them if needed. It then parses the input with the coarsest grammar, calculates the inside and outside scores and creates an evaluation function. Then the input is parsed again with the next finer grammar by passing the evaluation function to the CKY parser. 

## Performance
When using a smaller grammar or a short sentence, I could see that my implementation is actually working. In all cases, the vast majority of items were pruned (90-98%) and still, the best parse was returned.

Unfortunately, the calculation of the inside and outside probabilities introduces such a big overhead that it makes parsing long sentences basically impossible. For example, a sentence of length 5 takes 60ms to parse with the standard CKY algorithm. The pruning algorithm, however, increases the time to over 2 seconds. I also believe that this is not only a phenomenon of short sentences, as the calculation time of the inside/outside scores increases cubically with the sentence length.

In fact, I investigated the source if the bad performance using a profiler and discovered that the dictionary lookup for the cache is the bottleneck. Since dictionaries are already highly optimized and implemented in C, I did not find better ways to improve it. I experimented with just-in-time compilation for the inside and outside calculation, functions using *numba* without noticeable
effect. The biggest improvement I saw was by rewriting parts of the functions in Cython and compiling it to C++ code. It decreased the parse time by about 25%, which was sadly still worse than the time using CKY alone.
