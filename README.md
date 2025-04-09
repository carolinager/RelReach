# RelReach

Tool for checking universally quantified relational reachability properties
like "Does it hold for all schedulers that the probability of reaching states labeled a is the same as the probability of reaching states labeled b?",
working on top of storm.

## Usage
### Arguments:
#### Required Arguments:
- ```--modelPath```: path to MDP model file
- ```--numScheds```: number of schedulers to quantify over ($n$)
- ```--numInit```: number of initial state labels ($m$)
- ```--schedList```: list of scheduler indices (corresponding to the family of indices $k_1, ..., k_m$).
  Expected to be a string of integers, separated by spaces, of length ```numInit```, covering all indices from 1 to ```numScheds```
- ```--targets```: list of target labels $T_1, ..., T_m$ (one per initial state).
  Expected to be a string of labels, separated by spaces, of length ```numInit```
- ```--coefficient```: list of coefficients $q_1, ..., q_{m+1}$.
  Expected to be a string of rational numbers, separated by spaces of length ```numInit+1```

#### Optional Arguments for the Property:
- ```--comparisonOperator```: '=', '<', '>', '<=', '>=', '!='. Default is '='
- ```--epsilon```: rational number for approximate comparison. Default is 0. Only allowed to be non-zero if ```comparisonOperator``` is '=' or '!='

#### Optional Arguments for the Computation:
- ```--checkModel```: if flag is set: check if model file can be parsed (property is not being checked)
- ```--exact```: if flag is set: do exact computation with Rationals in storm
- ```--witness```: if flag is set: output witness scheduler(s) if the property does not hold


### Assumptions on the Model File
We assume the model has exactly one state labeled "init{i}" for each i=1, ..., ```numInit```.
E.g., if numInit=2 we expect there to be exactly one state labeled "init1" and exactly one state labeled "init2".
Note that this includes models where there is a single state labeled both "init1" and "init2".


## Sample Commands
### Sample commands for ```numScheds```=2, ```numInit```=2:
We want to check whether for all pairs of schedulers,
the weighted sum of the probability of reaching "target1" from the first initial state under the first scheduler
plus the probability of reaching "target2" from the second initial state under the second scheduler
relates to the bound $q_{m+1} (i.e., the last element of ```coefficients```) as specified by the comparison operator (if applicable, wrt epsilon).

#### Single state labeled both "init1" and "init2"
- RT: ```--modelPath ./benchmark/RT/janitor_10.nm --numInit 2 --numScheds 2 --schedList 1 2 --targets target target --coefficient 1 -1 0```
  - Returns "Unknown" instantly, also with epsilon 0.000001 (too small)
  - with ```--exact``` this returns "Yes"
- RT: ```--modelPath ./benchmark/RT/janitor_10.nm --numInit 2 --numScheds 2 --schedList 1 2 --targets target target --coefficient 1 -1 0 --epsilon 0.00001```
  - Returns "Yes" instantly
- RT_w: ```--modelPath ./benchmark/RT/janitor_w_10.nm --numInit 2 --numScheds 2 --schedList 1 2 --targets target target --coefficient 1 -1 0 --epsilon 0.00001```
  - Returns "No" instantly

#### Different states labeled "init1" and "init2"
- TA, m=8: ```--modelPath ./benchmark/TL/tl_8.nm --numInit 2 --numScheds 2 --schedList 1 2 --targets j0 j0 --coefficient 1 -1 0``` and same for ```j1``` and ```j2```
  - Returns "No" instantly, already for target j0 alone
  - Analogously for the other variants (m=4,6,8) and all initial-state-combinations
- TS ```--modelPath ./benchmark/TS/th0_1.nm --numInit 2 --numScheds 2 --schedList 1 2 --targets terml1 terml1 --coefficient 1 -1 0``` and same for ```terml2```
  - Returns "No" instantly
  - Analogously for the other variants
- PW ```--modelPath ./benchmark/PW/password_leakage_1.nm --numInit 2 --numScheds 2 --schedList 1 2 --targets counter0 counter0 --coefficient 1 -1 0``` and same for the other values for counter
  - Returns "No" instantly, also if init1:s=0, init2:s=2 (pwd is s=1)

### Sample commands for ```numScheds```=1, ```numInit```=2:
We want to check whether for all schedulers,
the weighted sum of the probability of reaching "target1" from the first initial state
plus the probability of reaching "target2" from the second initial state
relates to the bound $q_{m+1} (i.e., the last element of ```coefficients```) as specified by the comparison operator (if applicable, wrt epsilon).

#### Single state labeled both "init1" and "init2"
- VN.1: ```--modelPath ./benchmark/VN/vn-gen_1.nm --numInit 2 --numScheds 1 --schedList 1 1 --targets res_is_0 res_is_1 --coefficient 1 -1 0 --epsilon 0.1```
  - Returns "Yes" instantly
- VN.2: ```--modelPath ./benchmark/VN/vn-gen_1.nm --numInit 2 --numScheds 1 --schedList 1 1 --targets res_is_0 res_is_1 --coefficient 1 -1 0 --comparisonOperator =```
  - Returns "No" instantly

#### Different states labeled "init1" and "init2"
- SD: ```--modelPath ./benchmark/SD/simple/sketch.templ --numInit 2 --numScheds 1 --schedList 1 1 --targets target target --coefficient 1 -1 0 -cop '>'```
  - Returns "No" instantly for all models, also for ```- cop >=```
  - Analogously for the other maze variants
- TL: ```--modelPath ./benchmark/TL/tl_8.nm --numInit 2 --numScheds 1 --schedList 1 1 --targets j0 j0 --coefficient 1 -1 0``` and same for ```j1``` and ```j2```
  - Returns "No" instantly, already for target j0 alone (this property is equiv to TL with ```--numScheds 2```)


## Tested with:
- storm=1.9.0 master branch
- carl-storm 14.28
- stormpy fork, relreach-full branch: https://github.com/carolinager/stormpy/tree/relreach-full
  - Note: ensure correct storm version is used when building stormpy!
- pycarl 2.3.0

Note: We use assertions for verifying the format of the input arguments. Disable at your own risk
