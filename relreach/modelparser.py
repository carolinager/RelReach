import os
import stormpy
from z3 import RealVal
from relreach.utility import common

import itertools


def buildUnfoldedModel(initial_model):
    file_str = ""
    file_str += "builder = stormpy.ExactSparseMatrixBuilder(rows=0, columns=0, entries=0, force_dimensions=False, has_custom_row_grouping=True, row_groups=0)\n"
    count_action = 0
    num_states = len(list(initial_model.states))

    # add new initial state
    # todo identify original initial states
    file_str += "\nbuilder.new_row_group(" + str(count_action) + ")\n"
    va = RealVal(0.5).as_fraction().limit_denominator(10000)
    file_str += "builder.add_next_value(" + str(count_action) + ", "
    file_str += str(0) + ", stormpy.Rational(" + str( #todo
        va.numerator) + ")/ stormpy.Rational(" + str(
        va.denominator) + "))\n"
    file_str += "builder.add_next_value(" + str(count_action) + ", "
    file_str += str(1) + ", stormpy.Rational(" + str( # todo ##################
        va.numerator) + ")/ stormpy.Rational(" + str(
        va.denominator) + "))\n"
    count_action += 1

    # first copy
    for state in initial_model.states:
        file_str += "\nbuilder.new_row_group(" + str(count_action) + ")\n"
        for action in state.actions:
            for tran in action.transitions:
                va = RealVal(tran.value()).as_fraction().limit_denominator(10000)
                file_str += "builder.add_next_value(" + str(count_action) + ", "
                file_str += str(tran.column + 1) + ", stormpy.Rational(" + str(
                    va.numerator) + ")/ stormpy.Rational(" + str(
                    va.denominator) + "))\n"
            count_action += 1

    # second copy
    for state in initial_model.states:
        file_str += "\nbuilder.new_row_group(" + str(count_action) + ")\n"
        for action in state.actions:
            for tran in action.transitions:
                va = RealVal(tran.value()).as_fraction().limit_denominator(10000)
                file_str += "builder.add_next_value(" + str(count_action) + ", "
                file_str += str(tran.column + num_states + 1) + ", stormpy.Rational(" + str(
                    va.numerator) + ")/ stormpy.Rational(" + str(
                    va.denominator) + "))\n"
            count_action += 1

    file_str += "\ntransition_matrix = builder.build()\n"
    loc = {}
    exec(file_str, {"stormpy": stormpy}, loc)
    # creating new transition matrix
    transition_matrix = loc["transition_matrix"]
    # old
    # state_labeling = initial_model.labeling

    print(transition_matrix)

    # creating new label mode
    state_labeling = stormpy.storage.StateLabeling(num_states * 2 + 1)
    state_labeling.add_label("init")
    state_labeling.add_label_to_state("init", 0)
    for label in initial_model.labeling.get_labels():
        state_labeling.add_label(label + "_1")
        state_labeling.add_label(label + "_2")
    for state in initial_model.states:
        print(type(state), state)
        for label in initial_model.labeling.get_labels_of_state(state):
            print(label)
            state_labeling.add_label_to_state(label + "_1", int(state) + 1)
            state_labeling.add_label_to_state(label + "_2", (int(state) + num_states + 1))

    # # creating new rewards model
    # if len(list(initial_model.reward_models.keys())) > 0:
    #     reward = {}
    #     if len(list(initial_model.reward_models.keys())) > 1:
    #         common.colourother(
    #             "Multiple reward models not supported. Using rewards model: " + str(
    #                 list(initial_model.reward_models.keys())[0]))
    #     reward_models = initial_model.reward_models.get(list(initial_model.reward_models.keys())[0]).state_rewards
    #     state_rewards = []
    #     for rew in reward_models:
    #         rew_fraction = RealVal(rew).as_fraction().limit_denominator(10000)
    #         state_rewards.append(
    #             stormpy.Rational(rew_fraction.numerator) / stormpy.Rational(rew_fraction.denominator))
    #     reward[list(initial_model.reward_models.keys())[0]] = stormpy.storage.SparseExactRewardModel(
    #         optional_state_reward_vector=state_rewards)
    #     components = stormpy.SparseExactModelComponents(reward_models=reward, transition_matrix=transition_matrix,
    #                                                     state_labeling=state_labeling)
    # else:
    #     components = stormpy.SparseExactModelComponents(transition_matrix=transition_matrix,
    #                                                     state_labeling=state_labeling)

    components = stormpy.SparseExactModelComponents(transition_matrix=transition_matrix,
                                                    state_labeling=state_labeling)

    mdp = stormpy.storage.SparseExactMdp(components)
    print(mdp)
    return mdp


class Model:
    def __init__(self, model_path):
        self.list_of_states = []
        self.dict_of_acts = {}
        self.dict_of_acts_tran = {}
        self.has_rewards = False
        self.model_path = model_path
        self.parsed_model = None

    def parseModel(self, extra_processing):
        try:
            if os.path.exists(self.model_path):
                initial_prism_program = stormpy.parse_prism_program(self.model_path)
                initial_model = stormpy.build_model(initial_prism_program)
                self.parsed_model = buildUnfoldedModel(initial_model)
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
