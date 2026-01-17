from stormpy import EndComponentEliminatorReturnTypeDouble, BitVector

from relreach.inputparser import parseArguments
from relreach.utility import common
from relreach.modelparser import Model
from relreach.modelchecker import ModelChecker
import stormpy

import os
import time
import datetime

from itertools import chain, combinations


def buechi_processing(model, ind_dict, numInit, targets, targets_by_comb):
    common.colourinfo(f"{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")}: Constructing the MEC quotient...")
    quotient_construction_start_time = time.perf_counter()
    # construct MEC quotient
    ones_states = stormpy.storage.BitVector(model.parsed_model.nr_states, True)
    ones_rows = stormpy.storage.BitVector(model.parsed_model.transition_matrix.nr_rows, True)
    quotient = stormpy.eliminate_ECs(model.parsed_model.transition_matrix, ones_states, ones_rows, ones_states, True)

    # add sink for every MEC and every subset of target-comb-sets that we can ensure to visit infinitely often
    sinks = []
    sinks_by_MEC = {}
    MECs = stormpy.get_maximal_end_components(model.parsed_model)
    for MEC in MECs:
        states_MEC = set([s for (s, _) in MEC])
        for comb in ind_dict.keys():
            targets_comb = targets_by_comb[comb]
            powerset = [set(x) for x in
                        chain.from_iterable(combinations(targets_comb, r) for r in range(len(targets_comb) + 1))]

            for subset in powerset:
                # check there exists a state in the MEC for each target label in the subset
                states_subset_MEC = set()
                for target in subset:
                    target_states_MEC = set(model.parsed_model.labeling.get_states(target)).intersection(states_MEC)
                    if len(list(target_states_MEC)) > 0:
                        states_subset_MEC = states_subset_MEC.union(target_states_MEC)
                    else:
                        states_subset_MEC = set()
                        break

                if states_subset_MEC != set():
                    # collect the states labeled with a target not in the subset
                    not_subset = targets_comb - subset
                    if not_subset == set():
                        states_not_subset = set()
                    else:
                        states_not_subset = set.union(
                            *[set(model.parsed_model.labeling.get_states(x)) for x in not_subset])
                    # set of states in the MEC NOT labeled with a target not in the subset
                    states_MEC_wo_not_subset = states_MEC - states_not_subset

                    # check: does the MEC without the states from not_X still contain an EC?
                    ones_MEC_wo_not_subset= stormpy.storage.BitVector(model.parsed_model.nr_states,
                                                                      list(states_MEC_wo_not_subset))
                    quot_not_subset = stormpy.eliminate_ECs(model.parsed_model.transition_matrix,
                                                            ones_MEC_wo_not_subset, ones_rows, ones_states)

                    #rows_MEC_wo_not_subset = set.union(*[set(model.parsed_model.transition_matrix.get_rows_for_group(state)) for state in states_MEC_wo_not_subset])
                    #ones_MEC_wo_not_subset_rows = stormpy.storage.BitVector(model.parsed_model.transition_matrix.nr_rows,
                    #                                                        list(rows_MEC_wo_not_subset))
                    #MEC_matrix = model.parsed_model.transition_matrix.submatrix(ones_MEC_wo_not_subset_rows, ones_MEC_wo_not_subset)

                    # todo: I think this check does not work to check that there was an MEC
                    # if quot_not_subset.sink_rows.number_of_set_bits() > 0:
                    # check: Does one of the collapsed states of quot_not_subset correspond to an MEC that contains states for all targets in subset?
                    list_mapped_target_states = []
                    for target in subset:
                        target_states = set(model.parsed_model.labeling.get_states(target))
                        list_mapped_target_states.append({quot_not_subset.old_to_new_state_mapping[state] for state in
                                                   target_states.intersection(states_MEC)})
                    mapped_target_states_in_MEC = set.intersection(*list_mapped_target_states)
                    mapped_target_states_in_MEC_wo_nil = list(mapped_target_states_in_MEC.difference({18446744073709551615}))

                    # states not in the subsystem are mapped to 18446744073709551615 by old_to_new_state_mapping
                    if len(mapped_target_states_in_MEC_wo_nil) == 1:
                        # check: is singleton, and does not only contain 18446744073709551615, and is actually an MEC (not just a single state)
                        # check: the unique mapped state is a sink row of quot_not_subset (if it was one before it is an MEC anyways)
                        mapped_state = mapped_target_states_in_MEC_wo_nil[0]
                        if quot_not_subset.sink_rows.get(mapped_state):
                            # store that we should add a sink state simulating staying in MEC and seeing subset infinitely often, avoiding not_subset
                            collapsed_state = quotient.old_to_new_state_mapping[list(states_MEC)[0]]
                            sinks.append(subset)
                            if collapsed_state in sinks_by_MEC.keys():
                                sinks_by_MEC[collapsed_state].append(subset)
                            else:
                                sinks_by_MEC[collapsed_state] = [subset]

    # rebuild quotient.matrix and add sinks
    builder = stormpy.SparseMatrixBuilder(rows=0, columns=0, entries=0, force_dimensions=False,
                                          has_custom_row_grouping=True, row_groups=0)
    cur_row = 0
    cur_group = 0
    for state in range(0,quotient.matrix.nr_columns):
        builder.new_row_group(cur_row)
        rows = quotient.matrix.get_rows_for_group(state)
        for row in rows:
            row_iter = quotient.matrix.row_iter(row, row)
            flag = False
            for entry in row_iter:
                assert entry.value() != 0, "Something went wrong: An entry of the SparseMatrix quotient is 0"
                # transition in MEC quotient is a self-floop, do not copy
                # todo this doesnt work yet
                if entry.column != cur_group:
                    builder.add_next_value(cur_row, entry.column, entry.value())
                    flag = True
            if flag:
                cur_row += 1
            if cur_group in sinks_by_MEC.keys():
                # todo there is some indexing error here
                for subset in sinks_by_MEC[cur_group]:
                    builder.add_next_value(cur_row, quotient.matrix.nr_columns + sinks.index(subset), 1)
                    cur_row += 1
        cur_group = cur_group + 1
    for subset in sinks:
        builder.new_row_group(cur_row)
        builder.add_next_value(cur_row, quotient.matrix.nr_columns + sinks.index(subset), 1)
        cur_group = cur_group +1
    processed_nr_states = cur_group

    processed_matrix = builder.build()

    # update ind_dict
    processed_ind_dict = {}
    for (state, sched) in ind_dict.keys():
        mapped_state = quotient.old_to_new_state_mapping[state]
        processed_ind_dict[(mapped_state, sched)] = ind_dict[(state, sched)]

    # create state labeling
    state_labeling = stormpy.storage.StateLabeling(processed_nr_states)

    # reinstate init{i} labels
    state_labeling.add_label("init")
    for i in range(1, numInit + 1):
        [s_i] = list(model.parsed_model.labeling.get_states(f"init{i}"))
        new_s_i = quotient.old_to_new_state_mapping[s_i]
        state_labeling.add_label(f"init{i}")
        state_labeling.add_label_to_state(f"init{i}", new_s_i)
        state_labeling.add_label_to_state("init", new_s_i)

    # create new target labels on the success sets
    new_targets = [f"Ut{i}" for i in range(1, numInit + 1)]
    for target in new_targets:
        state_labeling.add_label(target)
    for subset in sinks:
        for i in range(1, numInit+1):
            if targets[i-1] in subset:
                state_labeling.add_label_to_state(new_targets[i-1], quotient.matrix.nr_columns + sinks.index(subset))

    components = stormpy.SparseModelComponents(transition_matrix=processed_matrix, state_labeling=state_labeling)
    processed_model = stormpy.storage.SparseMdp(components)
    assert processed_nr_states == processed_model.nr_states, "Something went wrong: Processed model does not have expected no of states"

    quotient_construction_end_time = time.perf_counter()
    common.colourinfo("Number of states of MEC quotient: {0}".format(processed_model.nr_states), False)
    common.colourinfo("Number of transitions of MEC quotient: {0}".format(processed_model.nr_transitions), False)
    common.colourinfo("Constructing the MEC quotient took: " + str(round(quotient_construction_end_time - quotient_construction_start_time, 2)) + " seconds", False)

    return processed_model, processed_ind_dict, new_targets

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
        buechi = input_args.buechi

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
        if buechi:
            targets_by_comb = {}
        for i in range(1,numInit+1):
            states_i = list(model.parsed_model.labeling.get_states(f"init{i}"))
            assert len(states_i) == 1, f"No or more than a single state is labeled with init{i}"
            comb = (states_i[0], schedList[i-1])
            state_sched_comb.add(comb)
            if comb in ind_dict.keys():
                ind_dict[comb].append(i)
            else:
                ind_dict[comb] = [i]
            if buechi:
                if comb in targets_by_comb.keys():
                    targets_by_comb[comb].add(targets[i-1])
                else:
                    targets_by_comb[comb] = {targets[i-1]}
        common.colourinfo("State-scheduler combinations and associated initial state label indices: " + str(ind_dict))


        processed_model = model.parsed_model
        processed_ind_dict = ind_dict
        processed_targets = targets
        if buechi:
            processed_model, processed_ind_dict, processed_targets = buechi_processing(model, ind_dict, numInit, targets, targets_by_comb)
            assert len(targets) == len(processed_targets), "Number of new targets does not match number of original targets."

        # Model-checking
        if not input_args.checkModel:
            modelchecker = ModelChecker(processed_model, processed_ind_dict, processed_targets,
                                        compOp, coeff, exact, epsilon, witness, log_dir)
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
