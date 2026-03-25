from relprop.inputparser import parseArguments
from relprop.utility import common
from relprop.modelparser import Model
from relprop.modelchecker import ModelChecker
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
                # if transition in MEC quotient is not a self-floop: copy
                if entry.column != cur_group:
                    builder.add_next_value(cur_row, entry.column, entry.value())
                    flag = True
            if flag:
                cur_row += 1
            if cur_group in sinks_by_MEC.keys():
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

def cast_to_reach(processed_model, equivClass):
    ones_states = stormpy.storage.BitVector(processed_model.nr_states, True)
    ones_rows = stormpy.storage.BitVector(processed_model.transition_matrix.nr_rows, True)
    quotient = stormpy.eliminate_ECs(processed_model.transition_matrix, ones_states, ones_rows,
                                     ones_states, True)
    # copy reward models
    quotient_reward_models = {}
    new_to_old_state_mapping = {new_s: [i for i, x in enumerate(quotient.old_to_new_state_mapping) if x == new_s] for
                                new_s in range(quotient.matrix.nr_columns)}
    for pred in equivClass:
        reward_label = f"R{pred}"
        old_rew_matrix = processed_model.reward_models[reward_label].transition_rewards
        # for each target collect all coefficients for this target in this predicate
        transRewMatrixbuilder = stormpy.SparseMatrixBuilder(rows=0, columns=0, entries=0,
                                                            force_dimensions=False,
                                                            has_custom_row_grouping=False)
        for new_s in range(quotient.matrix.nr_columns):
            old_states = new_to_old_state_mapping[new_s]
            for old_s in old_states:
                rows = old_rew_matrix.get_rows_for_group(old_s)
                for row in rows:
                    row_iter = old_rew_matrix.row_iter(row, row)
                    for entry in row_iter:
                        new_column = quotient.old_to_new_state_mapping[entry.column]
                        transRewMatrixbuilder.add_next_value(new_s, new_column, entry.value())

        new_reward_matrix = transRewMatrixbuilder.build()
        quotient_reward_models[reward_label] = stormpy.SparseRewardModel(
            optional_transition_reward_matrix=new_reward_matrix)

    # rebuild matrix, add sink state and transitions to sink from all collapsed MEC states
    matrixBuilder = stormpy.SparseMatrixBuilder(rows=0, columns=0, entries=0, force_dimensions=False,
                                                has_custom_row_grouping=True, row_groups=0)
    cur_row = 0
    sink = quotient.matrix.nr_columns
    for state in range(quotient.matrix.nr_columns):
        matrixBuilder.new_row_group(cur_row)
        rows = quotient.matrix.get_rows_for_group(state)
        for row in rows:
            row_iter = quotient.matrix.row_iter(row, row)
            for entry in row_iter:
                assert entry.value() != 0, f"Something went wrong: An entry of the SparseMatrix quotient is 0 for the unfolding for comb {comb}"
                if (entry.column == state and entry.value() == 1):  # self-loop
                    matrixBuilder.add_next_value(cur_row, entry.column, entry.value())
                else:
                    matrixBuilder.add_next_value(cur_row, sink, 1)
            cur_row += 1

    # add self-loop on sink
    matrixBuilder.new_row_group(cur_row)
    matrixBuilder.add_next_value(cur_row, sink, 1)

    quotient_matrix_with_sink = matrixBuilder.build()

    # label initial state and label sink
    quotient_state_labeling = stormpy.storage.StateLabeling(quotient.matrix.nr_columns + 1)
    quotient_state_labeling.add_label("init")
    quotient_state_labeling.add_label_to_state("init", 0)
    quotient_state_labeling.add_label("term")
    quotient_state_labeling.add_label_to_state("term", sink)

    quotient_components_with_rewards = stormpy.SparseModelComponents(
        transition_matrix=quotient_matrix_with_sink,
        state_labeling=quotient_state_labeling,
        reward_models=quotient_reward_models)
    quotient_with_reward = stormpy.storage.SparseMdp(quotient_components_with_rewards)

    return quotient_with_reward


def transform_to_moa(model, equivClass, scheds_by_pred, numScheds, numInit, numSum, schedList, targets, coeff):
    curInitLists = {pred: range((numSum * pred) + 1, numSum * (pred + 1) + 1) for pred in equivClass}
    curTargetSets = {pred: set(targets[(numSum * pred):(numSum * (pred + 1))]) for pred in equivClass}
    curCoeffLists = {pred: coeff[((numSum + 1) * pred):((numSum + 1) * (pred + 1))] for pred in equivClass} # including bounds

    # Step 1: Collect state-scheduler combinations, also split by conjunct
    state_sched_comb = set()
    ind_dict = {}
    for i in chain.from_iterable(curInitLists.values()):
        states_i = list(model.parsed_model.labeling.get_states(f"init{i}"))
        assert len(states_i) == 1, f"No or more than a single state is labeled with init{i}"
        comb = (states_i[0], schedList[i - 1])
        state_sched_comb.add(comb)
        if comb in ind_dict.keys():
            ind_dict[comb].append(i)
        else:
            ind_dict[comb] = [i]
    common.colourinfo("State-scheduler combinations and associated initial state label indices: " + str(ind_dict))

    # Step 2: Construct goal unfolding wrt all relevant target states, combine and set up reward structures
    ## Construct all goal unfoldings
    unfoldings = {}
    for (comb, rel_ind) in ind_dict.items():
        rel_target_labels = set([targets[i - 1] for i in rel_ind])
        rel_target_states_dict = {target:set(model.parsed_model.labeling.get_states(target)) for target in rel_target_labels}
        rel_target_states = set.union(*rel_target_states_dict.values())

        # storm build unfolding differently to what we need / want, we want to transition to a new copy *after* seeing a target state
        # build memory structure for each set of target states
        memorystructures = []
        for i in rel_ind:
            goalstates = model.parsed_model.labeling.get_states(targets[i - 1])
            memoryBuilder = stormpy.storage.MemoryStructureBuilder(2, model.parsed_model, False)
            memoryBuilder.set_transition(0, 0, ~goalstates)
            memoryBuilder.set_transition(0, 1, goalstates)
            memoryBuilder.set_transition(1, 1, stormpy.BitVector(model.parsed_model.nr_states, True))
            memorystructures.append(memoryBuilder.build())

        # take the product of all memory structures
        product_memorystructure = memorystructures[0]
        if len(rel_ind) > 1:
            for i in range(2, len(rel_ind)):
                product_memorystructure = product_memorystructure.product(memorystructures[i])

        # take the product of the memory structure with the model -> goal unfolding!
        product_type = product_memorystructure.product_model(model.parsed_model)
        product_model = product_type.build()
        unfoldings[comb] = product_model


    ## Construct combined MDP
    matrixBuilder = stormpy.SparseMatrixBuilder(rows=0, columns=0, entries=0, force_dimensions=False,
                                          has_custom_row_grouping=True, row_groups=0)
    nr_comb = len(ind_dict.keys())
    cur_row = 0
    cur_group = 0
    successors = {}

    # initial state: fresh, transitions to initial state of each unfolding with prob
    accumulated_nr_states = 0
    matrixBuilder.new_row_group(0)
    successors[0] = set()
    for (comb, rel_ind) in ind_dict.items():
        init_label = "init" + str(rel_ind[0])
        init_states = list(unfoldings[comb].labeling.get_states(init_label))
        assert len(
            init_states) == 1, f"No or more than a single state is labeled with {init_label} in the goal unfolding for {comb}"
        mapped_init_state = accumulated_nr_states + init_states[0] + 1
        matrixBuilder.add_next_value(cur_row, mapped_init_state, 1 / nr_comb)  # todo vs exact?
        accumulated_nr_states += unfoldings[comb].nr_states
        successors[0].add(mapped_init_state)
    cur_row += 1
    cur_group += 1

    # add a copy of the unfolding for each state-sched combination
    accumulated_nr_states = 0
    new_target_states = {target:[] for target in set.union(*curTargetSets.values())}
    new_states_to_comb = {}
    for (comb, rel_ind) in ind_dict.items():
        rel_target_labels = set([targets[i - 1] for i in rel_ind])
        for state in range(unfoldings[comb].nr_states): #todo vs model.states
            # state: state in unfolding[comb]
            # cur_group: corresponding state in combined MDP
            successors[cur_group] = set()
            # cur_state_is_target = {target: (state in unfoldings[comb].labeling.get_states(target)) for target in rel_target_labels}
            matrixBuilder.new_row_group(cur_row)
            rows = unfoldings[comb].transition_matrix.get_rows_for_group(state)
            for row in rows:
                row_iter = unfoldings[comb].transition_matrix.row_iter(row, row)
                for entry in row_iter:
                    assert entry.value() != 0, f"Something went wrong: An entry of the SparseMatrix quotient is 0 for the unfolding for comb {comb}"
                    mapped_succ_state = entry.column + accumulated_nr_states + 1
                    matrixBuilder.add_next_value(cur_row, mapped_succ_state, entry.value())
                    successors[cur_group].add(mapped_succ_state)
                cur_row += 1
            for target in rel_target_labels:
                # remember which states correspond to target states
                if state in unfoldings[comb].labeling.get_states(target):
                    new_target_states[target].append(cur_group)
                # remember which states correspond to having already seen the target
                # if state in unfoldings[comb].labeling.get_states(target) or state in seen[target]:
                #    seen[target].extend(curr_succ)
            new_states_to_comb[cur_group] = comb
            cur_group += 1
        accumulated_nr_states += unfoldings[comb].nr_states

    processed_nr_states = cur_group
    processed_matrix = matrixBuilder.build()

    # Compute all successors of target states
    target_succ = {}
    for (target, target_states) in new_target_states.items():
        target_succ[target] = set()
        for state in target_states:
            visited = set()
            tmp = {state}
            while tmp != set():
                succ = tmp.pop()
                visited.add(succ)
                tmp.update(successors[succ].difference(visited)) # ensure we visit each state at most once
            target_succ[target].update(visited)

    ## Set up reward structures on each unfolded MDP, scaled by nr_comb
    common.colourinfo("Setting up reward structures...")
    reward_models = {}
    for (pred, targetSet) in curTargetSets.items():
        # for each target collect all coefficients for this target in this predicate
        accCoeffByTargetAndComb = {(target,comb):0 for target in targetSet for comb in ind_dict.keys()}
        for (comb, rel_ind) in ind_dict.items():
            for i in set(rel_ind).intersection(set(curInitLists[pred])): # both lists do not contain duplicates anyways
                accCoeffByTargetAndComb[(targets[i-1],comb)] += curCoeffLists[pred][i - (numSum * pred) - 1]

        transRewMatrixbuilder = stormpy.SparseMatrixBuilder(rows=0, columns=0, entries=0, force_dimensions=False,
                                                            has_custom_row_grouping=True, row_groups=0)
        cur_row = 0
        for state in range(0, processed_matrix.nr_columns):
            rows = processed_matrix.get_rows_for_group(state)
            transRewMatrixbuilder.new_row_group(cur_row)
            for row in rows:
                row_iter = processed_matrix.row_iter(row, row)
                for entry in row_iter:
                    accVal = 0
                    for target in targetSet:
                        if entry.column in target_succ[target] and (not state in target_succ[target]):
                            cur_comb = new_states_to_comb[entry.column]
                            accVal += accCoeffByTargetAndComb[(target, cur_comb)] * nr_comb
                    if accVal != 0:
                        print(str(state) + " to " + str(entry.column) + " has rew " + str(accVal))
                    transRewMatrixbuilder.add_next_value(row, entry.column, accVal)
                cur_row += 1
        transition_reward_matrix = transRewMatrixbuilder.build()
        reward_models[f"R{pred}"] = stormpy.SparseRewardModel(optional_transition_reward_matrix=transition_reward_matrix)

    state_labeling = stormpy.storage.StateLabeling(processed_nr_states)
    state_labeling.add_label("init")
    state_labeling.add_label_to_state("init", 0)
    components = stormpy.SparseModelComponents(transition_matrix=processed_matrix, state_labeling=state_labeling, reward_models=reward_models)
    processed_model = stormpy.storage.SparseMdp(components)

    return processed_model

def main():
    try:
        start_time = time.perf_counter()
        input_args = parseArguments()

        model = Model(input_args.modelPath)
        numPred = input_args.numPred  # l
        numScheds = input_args.numScheds # n
        numInit = input_args.numInit # m*l
        schedList = input_args.schedList # family of indices k_1 ... k_m / for m-o: k_1,1, ..., k_m,l
        targets = input_args.targets
        coeff = input_args.coefficient # q_1, ..., q_m, q / for m-o: q_1,1, ..., q_m,1, q_1, q_1,2, ..., q_m,l, q_l (coeff q_1, ...,q_l are interpreted as bound)
        compOp = input_args.comparisonOperator
        buechi = input_args.buechi

        exact = input_args.exact


        if exact:
            common.colourerror("Not implemented!")
            return 0

        # correctness checks
        if compOp in ['=', '!=']:
            epsilon = input_args.epsilon
        else:
            if not (input_args.epsilon == 0):
                common.colourerror("Approximate comparison is only supported for = and !=. Will treat epsilon as 0.")
            epsilon = 0

        if numInit < numScheds:
            common.colourerror("Unnecessary schedulers quantified: Number of initial state labels < number of schedulers. Will assume numScheds := numInit.")
            numScheds = numInit

        if numPred>1:
            assert (not buechi), "Multi-objective Buechi properties are currently not supported."
            assert compOp != '=', "= currently not supported for disjunctive properties"

        assert len(targets) == numInit, "Number of target labels does not match number of initial state labels."
        assert len(coeff) == (numInit+numPred), "Number of coefficients does not match number of initial state labels + number of predicates."
        assert len(schedList) == numInit, "Size of scheduler list does not match number of initial state labels."
        assert set(schedList) == set(range(1,numScheds+1)), "List of schedulers does not cover the range {1,...,numScheds} or exceeds it."

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
        if numPred == 1:
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
                                            compOp, coeff, exact, epsilon)
                modelchecker.modelCheck()
        else:
            # Step 0: partition
            numSum = int(numInit / numPred) # number of summands per predicate
            scheds_by_pred = { pred:set(schedList[(numSum*pred):(numSum*(pred+1))]) for pred in range(numPred) }
            partition = {}
            seenScheds = set()
            for pred in range(numPred):
                foundClass = False
                for predp in range(pred):
                    if scheds_by_pred[pred].intersection(scheds_by_pred[predp]) != set():
                        partition[predp].append(pred)
                        foundClass = True
                        break
                if not foundClass:
                    partition[pred] = [pred]
                    seenScheds = seenScheds.union(scheds_by_pred[pred])

            common.colourinfo("Partitioned property into classes of predicates: " +str(partition.values()))

            resList = []
            for repr in partition.keys():
                equivClass = partition[repr]
                common.colourinfo("Checking the following predicates: "+ str(equivClass))

                # Construct combined MDP
                common.colourinfo("Constructing combined MDP...")
                start_moa_preproc_time = time.perf_counter()
                processed_model = transform_to_moa(model, equivClass, scheds_by_pred, numScheds, numInit, numSum, schedList, targets, coeff)
                end_moa_preproc_time = time.perf_counter()
                common.colourinfo("Constructing the combined MDP took: " + str(round(end_moa_preproc_time - start_moa_preproc_time, 2)) + " seconds",
                                  False)
                ##### cast to reach
                # quotient_with_reward = cast_to_reach(processed_model, equivClass)
                ###

                if not input_args.checkModel:
                    common.colourinfo("Solving MOA query...")
                    formula_interm = "multi("
                    for pred in equivClass:
                        formula_interm += "R{\"R" + str(pred) + "\"}max=? [ C ], "
                    formula = formula_interm[:-2] + ")"
                    properties = stormpy.parse_properties(formula)
                    weightVector = [1 for _ in equivClass]

                    #### cast to reach
                    """formula_reach_interm = "multi("
                    for pred in equivClass:
                        formula_reach_interm += "R{\"R" + str(pred) + "\"}max=? [F \"term\"], "
                    formula_reach = formula_reach_interm[:-2] + ")"
                    properties_reach = stormpy.parse_properties(formula_reach)"""
                    ###

                    if exact:
                        pass
                    else:
                        ### reach reward
                        """env = stormpy.Environment()
                        weighted_reach_model_checker, _ = stormpy._core._make_weighted_objective_mdp_model_checker_Double(env,
                                                                                                                    quotient_with_reward,
                                                                                                                    properties_reach[
                                                                                                                        0].raw_formula)
                        weighted_reach_model_checker.set_weighted_precision(0.0001)  # todo decide precision
                        weighted_reach_model_checker.check(env, weightVector)
                        point_reach = weighted_reach_model_checker.get_achievable_point()"""


                        #### total reward
                        env = stormpy.Environment()
                        weighted_model_checker, _ = stormpy._core._make_weighted_objective_mdp_model_checker_Double(env,
                                                                                                                    processed_model,
                                                                                                                    properties[0].raw_formula)
                        weighted_model_checker.set_weighted_precision(0.0001) #todo decide precision
                        weighted_model_checker.check(env, weightVector)
                        point = weighted_model_checker.get_achievable_point()
                        # todo postprocessing to retain soundness? then add handling below

                        # todo vs compute min / max depending on comp. op??
                        bound_vec = [coeff[(numSum + 1) * (pred + 1) - 1] for pred in equivClass]
                        flag = 1
                        for i in range(len(equivClass)):
                            if compOp == '>':
                                if point[i] <= bound_vec[i]:
                                    flag = -1
                                    break
                            elif compOp == '>=':
                                if point[i] < bound_vec[i]:
                                    flag = -1
                                    break
                            elif compOp == '=':
                                if point[i] - bound_vec[i] > epsilon or bound_vec[i] - point[i] > epsilon:
                                    flag = -1
                                    break
                            elif compOp == '!=':
                                if point[i] - bound_vec[i] <= epsilon and bound_vec[i] - point[i] <= epsilon:
                                    flag = -1
                                    break
                            elif compOp == '<=':
                                if point[i] > bound_vec[i]:
                                    flag = -1
                                    break
                            elif compOp == '<':
                                if point[i] >= bound_vec[i]:
                                    flag = -1
                                    break
                        resList.append(flag)
                        if flag != 1:
                            break # if this subset of predicates does not hold (or it is unknown) then the full property does not hold (or it is unknown)

            # combine results from resList
            if not input_args.checkModel:
                if -1 in resList:
                    common.colourinfo("Property does not hold!")
                elif 0 in resList:
                    common.colourinfo("Result unknown")
                else:
                    common.colourinfo("Property holds!")
            # todo add statistics for MORelReach

        # Output statistics
        end_time = time.perf_counter()
        common.colourinfo(f"{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")}: Finished. Statistics:")
        common.colourinfo("Solving took: " + str(round(end_time - parsing_time, 2)) + " seconds", False) # everything except building the original MDP
        common.colourinfo("Total time (solving + building original MDP): " + str(round(end_time - start_time, 2)) + " seconds", False)

    except Exception as err:
        common.colourerror("Unexpected error encountered: " + str(err))


if __name__ == "__main__":
    main()
