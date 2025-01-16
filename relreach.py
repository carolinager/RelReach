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

        # 2 probability operators / summands / init labels expected. this is NOT the same as the number of distinct initial states present in the model

        start_time = time.perf_counter()

        make_copies = False
        x = numInit == 1 and numScheds == 1
        if not (numInit == 1 and numScheds == 1):
            # if we do not have 1 scheduler and 1 initial state, then we make 2 copies of the MDP
            make_copies = True

        if make_copies: # then we look for the first target in the first copy and for the second one in the second copy
            target_a = targets[0] + "_1"
            target_b = targets[1] + "_2"
        else:
            target_a = targets[0]
            target_b = targets[1]

        if compOp in ['=', '<=', '<', '!=']:
            formula_a_minus_b = "multi(Pmax=?  [F \"" + target_a + "\"], Pmax=?  [F \"" + target_b + "\"])"
            properties = stormpy.parse_properties(formula_a_minus_b)
        if compOp in ['=', '>=', '>']:
            formula_b_minus_a = "multi(Pmax=?  [F \"" + target_b + "\"], Pmax=?  [F \"" + target_a + "\"])"
            properties = stormpy.parse_properties(formula_b_minus_a)

        help = [p.raw_formula for p in properties]
        options = stormpy.BuilderOptions([p.raw_formula for p in properties])
        options.set_build_state_valuations()
        options.set_build_all_labels()

        if input_args.checkModel:
            model.parseModel(False, numInit, targets, exact, make_copies, options)
        else:
            model.parseModel(True, numInit, targets, exact, make_copies, options)

            modelchecker = ModelChecker(model, make_copies, targets, properties, compOp, coeff, exact)
            res = modelchecker.modelCheck()
        print("\n")
        end_time = time.perf_counter()
        common.colourinfo("Total time: " + str(round(end_time - start_time, 2)) + " seconds", False)

    except Exception as err:
        common.colourerror("Unexpected error encountered: " + str(err))


if __name__ == "__main__":
    main()
