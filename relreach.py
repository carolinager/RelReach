from relreach.inputparser import parseArguments
from relreach.utility import common
from relreach.modelparser import Model
from relreach.modelchecker import ModelChecker

def main():
    try:
        input_args = parseArguments()

        model = Model(input_args.modelPath)
        targets = input_args.target # (input_args.target1, input_args.target2)

        if input_args.checkModel:
            model.parseModel(False, targets)
        else:
            model.parseModel(True, targets)

            modelchecker = ModelChecker(model, targets)
            modelchecker.modelCheck()
        print("\n")

    except Exception as err:
        common.colourerror("Unexpected error encountered: " + str(err))

    print(model)


if __name__ == "__main__":
    main()
