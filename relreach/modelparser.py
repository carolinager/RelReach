import os
import stormpy
from relreach.utility import common

class Model:
    def __init__(self, model_path):
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
            self.parsed_model = initial_model_sparse

        except IOError as e:
            common.colourerror("I/O error({0}): {1}".format(e.errno, e.strerror))
        except Exception as err:  # handle other exceptions such as attribute errors
            common.colourerror("Unexpected error in file {0} is {1}".format(self.model_path, err))