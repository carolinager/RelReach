# RelReach

Currently we expect
- ```--modelPath```: an MDP where exactly one state is labeled "init1" and exactly one state is labeled "init2"
- ```--numScheds```: number of schedulers to quantify over
- ```--numScheds```: number of initial states
- ```--targets```: list of target labels (one per initial state)

Optional:
- ```--comparisonOperator```: '=', '<', '>', '<=', '>=', '!='. Default is '='
- ```--coefficient```: rational number
- ```--checkModel```: if flag is set: check if model file can be parsed (property is not being checked)
- ```--exact```: if flag is set: do exact computation with Rationals in storm

If numInit=1 we assume the model has exactly one state labeled "init1". 
If numInit=2, we assume the model has exactly one state labeled "init1" and exactly one state labeled "init2".

(1) If numScheds=2:
We want to check whether for all pairs of schedulers, 
the probability of reaching target1 from the first initial state under the first scheduler 
relates to the probability of reaching target2 from the second initial state under the second scheduler + coefficient
as specified by the comparison operator.
I.e., we check a (2\sigma2s) or a (2\sigma1s) property.

(2) If numScheds=1:
We want to check whether for all schedulers, 
the probability of reaching target1 from the first initial state 
relates to the probability of reaching target2 from the second initial state + coefficient
as specified by the comparison operator.
I.e., we check a (1\sigma2s) or a (1\sigma1s) property.


### Sample commands for (2\sigma2s) properties:
- TA, m=8: ```--modelPath ./benchmark/TL/tl_8.nm --numInit 2 --numScheds 2 --targets j0 j0``` and same for ```j1``` and ```j2```
  - Returns "No" instantly, already for target j0 alone
  - Analogously for the other variants (m=4,6,8) and all initial-state-combinations
- SD: ```--modelPath ./benchmark/SD/simple/sketch.templ --numInit 2 --numScheds 1 --targets target target -cop >```
  - Returns "No" instantly for all models, also for ```- cop >=```
  - Analogously for the other maze variants
- TS ```--modelPath ./benchmark/TS/th0_1.nm --numInit 2 --numScheds 2 --targets terml1 terml1``` and same for ```terml2```
  - Returns "No" instantly
  - Analogously for the other variants
- PW ```--modelPath ./benchmark/PW/password_leakage_1.nm --numInit 2 --numScheds 2 --targets counter0 counter0``` and same for the other values for counter
  - Returns "No" instantly, also if init1:s=0, init2:s=2 (pwd is s=1)

### Sample commands for (2\sigma1s) properties:
- RT: ```--modelPath ./benchmark/RT/janitor_10.nm --numInit 1 --numScheds 2 --targets target target```
  - Returns "Unknown" instantly, also with epsilon 0.000001
- RT: ```--modelPath ./benchmark/RT/janitor_10.nm --numInit 1 --numScheds 2 --targets target target --epsilon 0.00001```
  - Returns "Yes" instantly
- RT_w: ```--modelPath ./benchmark/RT/janitor_w_10.nm --numInit 1 --numScheds 2 --targets target target --epsilon 0.00001```
  - Returns "No" instantly

### Sample commands for (1\sigma2s) properties:
- TL: ```--modelPath ./benchmark/TL/tl_2.nm --numInit 2 --numScheds 1 --targets j0 j0``` and same for ```j1``` and ```j2```
  - Returns "No" instantly, already for target j0 alone (this property is equiv to TL with ```--numScheds 2```)

### Sample commands for (1\sigma1s) properties:
- VN.1: ```--modelPath ./benchmark/VN/vn-gen_1.nm --numInit 1 --numScheds 1 --targets res_is_0 res_is_1 --epsilon 0.05``` 
  - Returns "Yes" instantly
- VN.2: ```--modelPath ./benchmark/VN/vn-gen_1.nm --numInit 1 --numScheds 1 --targets res_is_0 res_is_1 --comparisonOperator =``` 
  - Returns "No" instantly

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

