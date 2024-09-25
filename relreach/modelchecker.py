# import copy
# import time
# import itertools

from relreach.utility import common

class ModelChecker:
    def __init__(self, model, targets):
        self.model = model
        self.targets = targets  # object of property class


    def modelCheck(self):
        # create multi-objective properties, where target_1 = target label + "_1", etc
        # (1) check: max { P(F a) - P (F b)} >= 0
        ## multi(Pmax=? [ F target_1 ], Pmin=? [ F target_2 ])
        # (2) check: min { P(F a) - P (F b)} <= 0   iff    max { P(F b) - P(F a)} >=0
        ## multi(Pmax=? [ F target_2 ], Pmin=? [ F target_1 ])
        pass
