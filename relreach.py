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
        if compOp in ['=']:
            epsilon = input_args.epsilon
        else:
            if not (input_args.epsilon == 0):
                common.colourerror("Approximate comparison is only supported for =. Will treat epsilon as 0.")
            epsilon = 0


        # 2 probability operators / summands / init labels expected. this is NOT the same as the number of distinct initial states present in the model

        start_time = time.perf_counter()



        make_copies = False
        x = numInit == 1 and numScheds == 1
        if not (numInit == 1 and numScheds == 1):
            # if we do not have 1 scheduler and 1 initial state, then we make 2 copies of the MDP
            make_copies = True

        if make_copies: # then we look for the first target in the first copy and for the second one in the second copy
            target_a = targets[0] # + "_1"
            target_b = targets[1] # + "_2"

            if compOp in ['=', '<=', '<', '!=']: # calc max for a and min for b
                formula_a = "Pmax=? [F \"" + target_a + "\"]"
                formula_b = "Pmin=? [F \"" + target_b + "\"]"
            if compOp in ['=', '>=', '>', '!=']: # calc min for a and max for b
                formula_a = "Pmin=? [F \"" + target_a + "\"]"
                formula_b = "Pmax=? [F \"" + target_b + "\"]"

            properties_a = stormpy.parse_properties(formula_a)
            properties_b = stormpy.parse_properties(formula_b)

            options_a = stormpy.BuilderOptions([p.raw_formula for p in properties_a])
            options_a.set_build_state_valuations()
            options_a.set_build_all_labels()

            options_b = stormpy.BuilderOptions([p.raw_formula for p in properties_b])
            options_b.set_build_state_valuations()
            options_b.set_build_all_labels()

            common.colourinfo("Parsing model...")
            parsed_model = model.parseModel(exact, options_a)
            # todo: Clean this up, parsing wrt to one of the formulas but with all labels isnt very clean
            #todo: only init1 state should be initial state
            # parsed_model_a = model.parseModel(exact, options_a)
            #todo only init2 state should be initial state
            # parsed_model_b = model.parseModel(exact, options_b)
            parsing_time = time.perf_counter()
            common.colourinfo("Number of states: {0}".format(parsed_model.nr_states))
            common.colourinfo("Number of transitions: {0}".format(parsed_model.nr_transitions))
            common.colourinfo("Parsing took: " + str(round(parsing_time - start_time, 2)) + " seconds", False)

            if not input_args.checkModel:
                modelchecker = ModelChecker([parsed_model, parsed_model], make_copies, targets, [properties_a, properties_b], compOp, coeff, exact, epsilon)
                res = modelchecker.modelCheck()

        else:
            target_a = targets[0]
            target_b = targets[1]

            if compOp in ['=', '<=', '<', '!=']:
                formula_a_minus_b = "multi(Pmax=?  [F \"" + target_a + "\"], Pmax=?  [F \"" + target_b + "\"])"
                properties = stormpy.parse_properties(formula_a_minus_b)
            if compOp in ['=', '>=', '>']: # todo include != or exclude =
                formula_b_minus_a = "multi(Pmax=?  [F \"" + target_b + "\"], Pmax=?  [F \"" + target_a + "\"])"
                properties = stormpy.parse_properties(formula_b_minus_a)

            options = stormpy.BuilderOptions([p.raw_formula for p in properties])
            options.set_build_state_valuations()
            options.set_build_all_labels()

            # todo do I need to build the model twice, for both prop?
            common.colourinfo("Parsing model...")
            parsed_model = model.parseModel(exact, options)
            parsing_time = time.perf_counter()
            common.colourinfo("Number of states: {0}".format(parsed_model.nr_states), False)
            common.colourinfo("Number of transitions: {0}".format(parsed_model.nr_transitions), False)
            common.colourinfo("Parsing took: " + str(round(parsing_time - start_time, 2)) + " seconds", False)

            if not input_args.checkModel:
                modelchecker = ModelChecker([parsed_model], make_copies, targets, [properties], compOp, coeff, exact, epsilon)
                res = modelchecker.modelCheck()

        end_time = time.perf_counter()
        common.colourinfo("Solving took: " + str(round(end_time - parsing_time, 2)) + " seconds", True)
        common.colourinfo("Total time: " + str(round(end_time - start_time, 2)) + " seconds", False)

    except Exception as err:
        common.colourerror("Unexpected error encountered: " + str(err))


if __name__ == "__main__":
    main()
