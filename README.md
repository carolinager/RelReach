# RelReach

Currently we expect
- an MDP where exactly one state is labeled "init1" and exactly one state is labeled "init2"
- target: a target label

We want to check whether there exists some scheduler such that the probability of reaching target from the first initial state is equivalent to the probability of reaching target from the second initial state, i.e., a (2\sigma2s) property with the same target for both state variables.

We do so by transforming the problem to a (1\sigma1s) problem, i.e., transforming the MDP.
