from relreach.inputparser import parseArguments
from relreach.utility import common
from relreach.modelparser import Model
from relreach.modelchecker import ModelChecker
import stormpy

import os
import time
import datetime

def main():
    try:
        start_time = time.perf_counter()
        input_args = parseArguments()

        model = Model(input_args.modelPath)
        numScheds = input_args.numScheds # n
        numInit = input_args.numInit # m
        schedList = input_args.schedList # family of indices k_1 ... k_m
        targets = input_args.targets
        coeff = input_args.coefficient # q_1, ..., q_{m+1}
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
            common.colourerror("At least one scheduler is lonely: Number of initial state labels < number of schedulers. Will assume numScheds := numInit.")
            numScheds = numInit

        assert len(targets) == numInit, "Number of target labels does not match number of initial state labels."
        assert len(coeff) == (numInit+1), "Number of coefficients does not match number of initial state labels + 1."
        assert len(schedList) == numInit, "Size of scheduler list does not match number of initial state labels."
        assert set(schedList) == set(range(1,numScheds+1)), "List of schedulers does not cover the range {1,...,numScheds} or exceeds it."

        # prepare for storing witness schedulers+
        log_dir = None
        if witness:
            cur_time = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
            model_id = os.path.basename(input_args.modelPath)
            log_dir = f"logs/{cur_time}_{model_id}"

        # Parse + build MDP
        options = stormpy.BuilderOptions()
        options.set_build_state_valuations()
        options.set_build_all_labels()

        common.colourinfo(f"{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")}: Parsing + building model...")
        model.parseModel(exact, options)
        parsing_time = time.perf_counter()
        common.colourinfo("Number of states: {0}".format(model.parsed_model.nr_states), False)
        common.colourinfo("Number of transitions: {0}".format(model.parsed_model.nr_transitions), False)
        common.colourinfo("Building the model took: " + str(round(parsing_time - start_time, 2)) + " seconds", False)

        # assert each init label labels exactly one state, create state-sched-combinations and store which indices are associated with which initial state
        state_sched_comb = set()
        ind_dict = {}
        for i in range(1,numInit+1):
            states_i = list(model.parsed_model.labeling.get_states(f"init{i}"))
            assert len(states_i) == 1, f"No or more than a single state is labeled with init{i}"
            comb = (states_i[0], schedList[i-1])
            state_sched_comb.add(comb)
            if comb in ind_dict.keys():
                ind_dict[comb].append(i)
            else:
                ind_dict[comb] = [i]
        common.colourinfo("State-scheduler combinations and associated initial state label indices: " + str(ind_dict))

        # Model-checking
        if not input_args.checkModel:
            modelchecker = ModelChecker(model.parsed_model, ind_dict, targets, compOp, coeff, exact, epsilon, witness, log_dir)
            modelchecker.modelCheck()

        # Output statistics
        end_time = time.perf_counter()
        common.colourinfo(f"{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")}: Finished. Statistics:")
        common.colourinfo("Solving took: " + str(round(end_time - parsing_time, 2)) + " seconds", False)
        common.colourinfo("Total time: " + str(round(end_time - start_time, 2)) + " seconds", False)

    except Exception as err:
        common.colourerror("Unexpected error encountered: " + str(err))


if __name__ == "__main__":
    main()
