import os
import stormpy
#from pycarl.gmp.gmp import Rational
from relreach.utility import common

import itertools

class Model:
    def __init__(self, model_path):
        self.list_of_states = []
        self.dict_of_acts = {}
        self.dict_of_acts_tran = {}
        self.has_rewards = False
        self.model_path = model_path
        self.parsed_model = None

    def parseModel(self, exact, options):
        try:
            assert os.path.exists(self.model_path), "Model file does not exist!"

            initial_prism_program = stormpy.parse_prism_program(self.model_path)
            if exact:
                initial_model_sparse = stormpy.build_sparse_exact_model_with_options(initial_prism_program, options)
            else:
                initial_model_sparse = stormpy.build_sparse_model_with_options(initial_prism_program, options)
            #common.colourinfo("Model created from " + self.model_path + " with options")
            return initial_model_sparse

        except IOError as e:
            common.colourerror("I/O error({0}): {1}".format(e.errno, e.strerror))
        except Exception as err:  # handle other exceptions such as attribute errors
            common.colourerror("Unexpected error in file {0} is {1}".format(self.model_path, err))

    def getListOfStates(self):
        return self.list_of_states

    def getDictOfActionsWithTransition(self):
        return self.dict_of_acts_tran

    def getDictOfActions(self):
        return self.dict_of_acts

    def getNumberOfActions(self):
        return len(set(itertools.chain.from_iterable(self.dict_of_acts.values())))

    def hasRewards(self):
        return self.has_rewards
