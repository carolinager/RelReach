from relreach.inputparser import parseArguments
from relreach.utility import common
from relreach.modelparser import Model
from relreach.modelchecker import ModelChecker
import stormpy

import os
import time

def main():
    try:
        start_time = time.perf_counter()

        input_args = parseArguments()

        model = Model(input_args.modelPath)
        numScheds = input_args.numScheds # n
        numInit = input_args.numInit # m
        schedList = input_args.schedList
        targets = input_args.targets
        coeff = input_args.coefficient
        compOp = input_args.comparisonOperator
        exact = input_args.exact
        witness = input_args.witness

        # correctness checks
        if compOp in ['=', '!=']:
            epsilon = input_args.epsilon
        else:
            if not (input_args.epsilon == 0):
                common.colourerror("Approximate comparison is only supported for = and !=. Will treat epsilon as 0.")
            epsilon = 0

        if numInit < numScheds:
            common.colourerror("At least one scheduler is lonely: Number of initial states < number of schedulers. Will assume numScheds := numInit.")
            numScheds = numInit

        assert len(targets) == numInit, "Number of target labels does not match number of initial states."
        assert len(coeff) == (numInit+1), "Number of coefficients does not match number of initial states + 1."
        assert len(schedList) == numInit, "Size of scheduler list does not match number of initial state labels."
        assert set(schedList) == set(range(1,numScheds+1)), "List of schedulers does not cover the range {1,...,numScheds} or exceeds it."

        if witness:
            # create folder for storing witness schedulers
            if not os.path.exists('logs'):
                os.makedirs('logs')
                # todo clean folder or make a separate folder for each run

        # Parse + build MDP
        options = stormpy.BuilderOptions()
        options.set_build_state_valuations()
        options.set_build_all_labels()

        # Model-checking
        common.colourinfo("Parsing + building model...")
        parsed_model = model.parseModel(exact, options)
        parsing_time = time.perf_counter()
        common.colourinfo("Number of states: {0}".format(parsed_model.nr_states))
        common.colourinfo("Number of transitions: {0}".format(parsed_model.nr_transitions))
        common.colourinfo("Parsing took: " + str(round(parsing_time - start_time, 2)) + " seconds", False)

        # assert each init label labels exactly one state, create state-sched-combinations and store which indices are associated with which initial state
        state_sched_comb = set()
        ind_dict = {}
        for i in range(1,numInit+1):
            states_i = list(parsed_model.labeling.get_states(f"init{i}"))
            assert len(states_i) == 1, f"More than a single state is labeled with init{i}"
            comb = (states_i[0], schedList[i-1])
            state_sched_comb.add(comb)
            if comb in ind_dict.keys():
                ind_dict[comb].append(i)
            else:
                ind_dict[comb] = [i]

        print(ind_dict)
        # todo remove hardcoding
        make_copies = False
        if len(state_sched_comb) > 1:
            # if we do not have 1 scheduler and 1 initial state, then we make 2 copies of the MDP
            make_copies = True

        if not input_args.checkModel:
            modelchecker = ModelChecker(parsed_model, make_copies, state_sched_comb, ind_dict, targets, compOp, coeff, exact, epsilon, witness)
            res = modelchecker.modelCheck()
            # todo if witness and not make_copies:
            #    common.colourinfo("Note that output witness schedulers are defined on the goal unfolding not the original MDP")

        end_time = time.perf_counter()
        common.colourinfo("Solving took: " + str(round(end_time - parsing_time, 2)) + " seconds", True)
        common.colourinfo("Total time: " + str(round(end_time - start_time, 2)) + " seconds", False)

    except Exception as err:
        common.colourerror("Unexpected error encountered: " + str(err))


if __name__ == "__main__":
    main()
