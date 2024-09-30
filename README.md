# RelReach

Currently we expect
- ```--modelPath```: an MDP where exactly one state is labeled "init1" and exactly one state is labeled "init2"
- ```--targets```: target labels

Optional:
- ```--comparisonOperator```: '=', '<', '>', '<=', '>='. Default is '='

We want to check whether for all pairs of schedulers, and all specified targets, the relation of the probability of reaching target from the first initial state under the first scheduler to the probability of reaching target from the second initial state under the second scheduler is according to the specified comparison operator.
I.e., we check a conjunction (2\sigma2s) properties with the same target for both state variables.

We do so by transforming the problem to a (1\sigma1s) problem.

### Sample commands:
- TL: ```python3 relreach.py --modelPath ./benchmark/TL/tl.nm --targets j0 j1 j2```
  - Returns "No" instantly, already for target j0 alone
- SD: ```python3 relreach.py --modelPath ./benchmark/SD/simple/sketch.templ --targets target -cop >```
  - Returns "No" instantly for all models, also for ```- cop >=```


## Tested with:
- storm 1.9.0, master branch
- carl-storm 14.28
- pycarl 2.3.0
- stormpy fork, relreach branch: https://github.com/sjunges/stormpy/tree/relreach (ensure it uses the correct storm version)

## TODO
- [ ] Test other benchmarks (adjust labels?)
- [ ] Can we handle conjunction of P(F a_{s1}) = P(F a_{s2}) more efficiently? I.e., can we build MDP once and make states absorbing afterwards?
- [x] Allow strict inequality (not "P(F a_{s1}) = P(F a_{s2}) && P(F b_{s1}) > P(F b_{s2})" though since none of the case studies need it)
- [ ] Handling of more than 2 initial states? (E.g. for TA with more than 1 bit for b?). Need to build MDP for each pair of initial states.
- [ ] return witness (scheduler) in case the universal property does not hold?
- [ ] benchmark which for which the result is "True"?
