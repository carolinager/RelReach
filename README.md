# RelReach

Currently we expect
- ```--modelPath```: an MDP where exactly one state is labeled "init1" and exactly one state is labeled "init2"
- ```--numScheds```: number of schedulers to quantify over
- ```--targets```: list of target labels (one per initial state)

Optional:
- ```--comparisonOperator```: '=', '<', '>', '<=', '>='. Default is '='
- ```--coefficient```: Rational number
- ```--checkModel```: Check if model file can be parsed (property is not being checked)

(1) If numScheds=2:
We want to check whether for all pairs of schedulers, the probability of reaching target1 from the first initial state under the first scheduler relates to the probability of reaching target2 from the second initial state under the second scheduler as specified by the comparison operator.
I.e., we check a (2\sigma2s) or a (2\sigma1s) property.

(2) If numScheds=1:
We want to check whether for all schedulers, the probability of reaching target1 from the first initial state relates to the probability of reaching target2 from the second initial state as specified by the comparison operator.
I.e., we check a (1\sigma2s) or a (1\sigma1s) property.


### Sample commands for (2\sigma2s) properties:
- TL: ```python3 relreach.py --modelPath ./benchmark/TL/tl.nm --numScheds 2 --targets j0 j0``` and same for ```j1``` and ```j2```
  - Returns "No" instantly, already for target j0 alone
- SD: ```python3 relreach.py --modelPath ./benchmark/SD/simple/sketch.templ --targets target -cop >```
  - Returns "No" instantly for all models, also for ```- cop >=```

### Sample commands for (1\sigma1s) properties:
- VN.1: ```python3 relreach.py --modelPath ./benchmark/VN/vn-bias.nm --numScheds 1 --targets 01 10 --comparisonOperator <= --coefficient 0.2``` 
  - todo
- VN.2 ```python3 relreach.py --modelPath ./benchmark/VN/vn-bias.nm --numScheds 1 --targets 01 10 --comparisonOperator >= --coefficient -0.2```
  - todo

### sample commands for testing
- (2sched2s) --modelPath ./benchmark/TL/tl.nm --numScheds 2 --targets j0 j0
- (1sched2s) --modelPath ./benchmark/TL/tl.nm --numScheds 1 --targets j0 j0
- (1sched1s) --modelPath ./benchmark/TL/tl_single-init.nm --numScheds 1 --targets j0 j0

## Tested with:
- storm 1.9.0, master branch
- carl-storm 14.28
- pycarl 2.3.0
- stormpy fork, relreach branch: https://github.com/sjunges/stormpy/tree/relreach (ensure it uses the correct storm version)

## TODO
- [ ] Test other benchmarks
- [ ] Add coefficients for probability operators?
- [ ] approximate equality and disequality? 

## Possible Extensions
- [ ] benchmark for which the result is "True"?
- [ ] return witness (scheduler) in case the universal property does not hold?
- [ ] Add conjunction of constraints?(Efficiently? I.e., can we build MDP once and make states absorbing afterwards? Add python binding for SparseMatrix::makeRowGroupsAbsorbing ?)
- [ ] Handling of more than 2 initial states? (E.g. for TA with more than 1 bit for b?). Need to build MDP for each pair of initial states.

