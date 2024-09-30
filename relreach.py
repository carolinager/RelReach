from relreach.inputparser import parseArguments
from relreach.utility import common
from relreach.modelparser import Model
from relreach.modelchecker import ModelChecker

import time

def main():
    try:
        input_args = parseArguments()

        model = Model(input_args.modelPath)
        targets = input_args.targets # (input_args.target1, input_args.target2)
        compOp = input_args.comparisonOperator

        start_time = time.perf_counter()
        if input_args.checkModel:
            model.parseModel(False, targets)
        else:
            # todo can we do this more efficiently?
            ## i.e., can we build the mdp once and make the targets absorbing only *afterwards*?
            for target in targets:
                model.parseModel(True, target)

                modelchecker = ModelChecker(model, target, compOp)
                res = modelchecker.modelCheck()
                if res != 1:
                    break
        print("\n")
        end_time = time.perf_counter()
        common.colourinfo("Total time: " + str(round(end_time - start_time, 2)) + " seconds", False)

    except Exception as err:
        common.colourerror("Unexpected error encountered: " + str(err))


if __name__ == "__main__":
    main()
