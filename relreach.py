from relreach.inputparser import parseArguments
from relreach.utility import common
from relreach.modelparser import Model
from relreach.modelchecker import ModelChecker

def main():
    try:
        input_args = parseArguments()

        model = Model(input_args.modelPath)
        targets = input_args.targets # (input_args.target1, input_args.target2)

        if input_args.checkModel:
            model.parseModel(False, targets)
        else:
            # todo can we do this more efficiently?
            ## i.e., can we build the mdp once and make the targets absorbing only *afterwards*?
            for target in targets:
                model.parseModel(True, target)

                modelchecker = ModelChecker(model, target)
                res = modelchecker.modelCheck()
                if res != 1:
                    break
        print("\n")

    except Exception as err:
        common.colourerror("Unexpected error encountered: " + str(err))


if __name__ == "__main__":
    main()
