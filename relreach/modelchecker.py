# import copy
# import time
# import itertools

from relreach.utility import common

class ModelChecker:
    def __init__(self, model, targets):
        self.model = model
        self.targets = targets  # object of property class


    def modelCheck(self):
        # create property
        ## max { P(F a) - P (F b)} >= 0
        ## multi(Pmax=? [ F targets[0] ], Pmin=? [ F targets[1]" ])
        # min { P(F a) - P (F b)} <= 0   iff    max { P(F b) - P(F a)} >=0
        ## multi(Pmax=? [ F targets[1] ], Pmin=? [ F targets[0] ])
        pass
