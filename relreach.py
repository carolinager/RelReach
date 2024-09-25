from relreach.inputparser import parseArguments
from relreach.utility import common
# from relreach.propertyparser import Property
from relreach.modelparser import Model
# from relreach.modelchecker import ModelChecker


def main():
    try:
        input_args = parseArguments()
        # if input_args.checkProperty:
        #     hyperproperty = Property(input_args.hyperString)
        #     hyperproperty.parseProperty(True)
        if input_args.checkModel:
            model = Model(input_args.modelPath)
            model.parseModel(False)
        else:
            model = Model(input_args.modelPath)
            model.parseModel(True)
        # if not input_args.checkModel and not input_args.checkProperty:
        #     hyperproperty = Property(input_args.hyperString)
        #     hyperproperty.parseProperty(False)
        #     model = Model(input_args.modelPath)
        #     if input_args.stutterLength:
        #         stutterLength = int(input_args.stutterLength)
        #     else:
        #         stutterLength = 1
        #     model.parseModel(True)
        #     if input_args.maxSchedProb:
        #         maxSchedProb = float(input_args.maxSchedProb)
        #     else:
        #         maxSchedProb = 0.99
        #     modelchecker = ModelChecker(model, hyperproperty, stutterLength, maxSchedProb)
        #     modelchecker.modelCheck()
        # print("\n")
    except Exception as err:
        common.colourerror("Unexpected error encountered: " + str(err))

    print(model)


if __name__ == "__main__":
    main()
