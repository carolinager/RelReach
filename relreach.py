from relreach.inputparser import parseArguments
from relreach.utility import common
from relreach.modelparser import Model
from relreach.modelchecker import ModelChecker
import stormpy

import time

def main():
    try:
        input_args = parseArguments()

        model = Model(input_args.modelPath)
        numScheds = input_args.numScheds
        numInit = input_args.numInit
        targets = input_args.targets
        coeff = input_args.coefficient
        compOp = input_args.comparisonOperator
        exact = input_args.exact
        if compOp in ['=', '!=']:
            epsilon = input_args.epsilon
        else:
            if not (input_args.epsilon == 0):
                common.colourerror("Approximate comparison is only supported for = and !=. Will treat epsilon as 0.")
            epsilon = 0

        start_time = time.perf_counter()

        make_copies = False
        x = numInit == 1 and numScheds == 1
        if not (numInit == 1 and numScheds == 1):
            # if we do not have 1 scheduler and 1 initial state, then we make 2 copies of the MDP
            make_copies = True

        options = stormpy.BuilderOptions()
        options.set_build_state_valuations()
        options.set_build_all_labels()

        common.colourinfo("Parsing + building model...")
        parsed_model = model.parseModel(exact, options)
        parsing_time = time.perf_counter()
        common.colourinfo("Number of states: {0}".format(parsed_model.nr_states))
        common.colourinfo("Number of transitions: {0}".format(parsed_model.nr_transitions))
        common.colourinfo("Parsing took: " + str(round(parsing_time - start_time, 2)) + " seconds", False)

        if not input_args.checkModel:
            if make_copies:
                modelchecker = ModelChecker(parsed_model, make_copies, targets, compOp, coeff, exact, epsilon)
                res = modelchecker.modelCheck()

            else:
                modelchecker = ModelChecker(parsed_model, make_copies, targets, compOp, coeff, exact, epsilon)
                res = modelchecker.modelCheck()

        end_time = time.perf_counter()
        common.colourinfo("Solving took: " + str(round(end_time - parsing_time, 2)) + " seconds", True)
        common.colourinfo("Total time: " + str(round(end_time - start_time, 2)) + " seconds", False)

    except Exception as err:
        common.colourerror("Unexpected error encountered: " + str(err))


if __name__ == "__main__":
    main()
