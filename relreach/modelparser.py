import os
import stormpy
from pycarl.gmp.gmp import Rational
from relreach.utility import common

import itertools


def buildUnfoldedModel(initial_model, targets):
    builder = stormpy.ExactSparseMatrixBuilder(rows=0, columns=0, entries=0, force_dimensions=False,
                                               has_custom_row_grouping=True, row_groups=0)
    count_action = 0
    num_states = len(list(initial_model.states))

    # identify original initial states
    initial_states_1 = list(initial_model.labeling.get_states("init1"))
    initial_states_2 = list(initial_model.labeling.get_states("init2"))
    if len(initial_states_1) != 1 or len(initial_states_2) != 1:
        raise ValueError("The model does not have exactly 2 initial states.")
    init_1 = initial_states_1[0] + 1
    init_2 = initial_states_2[0] + num_states + 1

    # identify target states in first and second copy
    target_1 = [x + 1 for x in list(initial_model.labeling.get_states(targets))]
    target_2 = [x + num_states + 1 for x in list(initial_model.labeling.get_states(targets))]

    # add new initial state
    builder.new_row_group(count_action)
    builder.add_next_value(count_action, init_1, Rational(0.5))
    builder.add_next_value(count_action, init_2, Rational(0.5))
    count_action += 1


    # first copy
    for state in initial_model.states:
        builder.new_row_group(count_action)
        # if target_1: make absorbing
        if state in target_1:
            builder.add_next_value(count_action, state + 1, Rational(1))
            count_action += 1
        else:
            for action in state.actions:
                for tran in action.transitions:
                    va = Rational(tran.value())
                    builder.add_next_value(count_action, tran.column + 1, va)
                count_action += 1

    # second copy
    for state in initial_model.states:
        builder.new_row_group(count_action)
        # if target_2: make absorbing
        if state in target_2:
            builder.add_next_value(count_action, state + num_states + 1, Rational(1))
            count_action += 1
        else:
            for action in state.actions:
                for tran in action.transitions:
                    va = Rational(tran.value())
                    builder.add_next_value(count_action, tran.column + num_states + 1, va)
                count_action += 1

    # build transition matrix
    transition_matrix = builder.build()
    print(transition_matrix)

    # create new labeling
    state_labeling = stormpy.storage.StateLabeling(num_states * 2 + 1)
    state_labeling.add_label("init")
    state_labeling.add_label_to_state("init", 0)
    for label in initial_model.labeling.get_labels():
        state_labeling.add_label(label + "_1")
        state_labeling.add_label(label + "_2")
    for state in initial_model.states:
        for label in initial_model.labeling.get_labels_of_state(state):
            state_labeling.add_label_to_state(label + "_1", int(state) + 1)
            state_labeling.add_label_to_state(label + "_2", (int(state) + num_states + 1))
    # todo do we need to ensure initial_states[0] is labeled with init_1 (not init_2)? should be done automatically?

    components = stormpy.SparseExactModelComponents(transition_matrix=transition_matrix,
                                                    state_labeling=state_labeling)

    mdp = stormpy.storage.SparseExactMdp(components)
    return mdp


class Model:
    def __init__(self, model_path):
        self.list_of_states = []
        self.dict_of_acts = {}
        self.dict_of_acts_tran = {}
        self.has_rewards = False
        self.model_path = model_path
        self.parsed_model = None

    def parseModel(self, extra_processing, targets):
        try:
            if os.path.exists(self.model_path):
                initial_prism_program = stormpy.parse_prism_program(self.model_path)
                initial_model = stormpy.build_model(initial_prism_program)
                self.parsed_model = buildUnfoldedModel(initial_model, targets)
                common.colourinfo("Total number of states: " + str(len(self.parsed_model.states)))
                if len(list(self.parsed_model.reward_models.keys())) != 0:
                    self.has_rewards = True
                number_of_action = 0
                number_of_transition = 0
                if not extra_processing:
                    for state in self.parsed_model.states:
                        for action in state.actions:
                            number_of_action += 1
                            number_of_transition += len(action.transitions)
                else:
                    for state in self.parsed_model.states:
                        self.list_of_states.append(state.id)
                        list_of_act = []
                        for action in state.actions:
                            number_of_action += 1
                            list_of_tran = []
                            list_of_act.append(action.id)
                            number_of_transition += len(action.transitions)
                            for tran in action.transitions:
                                list_of_tran.append(str(tran.column) + ' ' + str(tran.value()))
                            self.dict_of_acts_tran[str(state.id) + ' ' + str(action.id)] = list_of_tran
                        self.dict_of_acts[state.id] = list_of_act

                common.colourinfo("Total number of actions: " + str(number_of_action), False)
                common.colourinfo("Total number of transitions: " + str(number_of_transition), False)
            else:
                common.colourother("Model file does not exist!")
        except IOError as e:
            common.colourerror("I/O error({0}): {1}".format(e.errno, e.strerror))
        except Exception as err:  # handle other exceptions such as attribute errors
            common.colourerror("Unexpected error in file {0} is {1}".format(self.model_path, err))

    def getListOfStates(self):
        return self.list_of_states

    def getDictOfActionsWithTransition(self):
        return self.dict_of_acts_tran

    def getDictOfActions(self):
        return self.dict_of_acts

    def getNumberOfActions(self):
        return len(set(itertools.chain.from_iterable(self.dict_of_acts.values())))

    def hasRewards(self):
        return self.has_rewards
