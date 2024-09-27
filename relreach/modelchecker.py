import stormpy
from relreach.utility import common

class ModelChecker:
    def __init__(self, model, targets):
        self.model = model
        self.targets = targets  # object of property class


    def modelCheck(self):
        target_a = self.targets + "_1"
        target_b = self.targets + "_2"

        # calculate max {P(F a) - P(F b)}
        formula_a_minus_b = "multi(Pmax=?  [F \"" + target_a + "\"], Pmax=?  [F \"" + target_b + "\"])"
        properties_a_minus_b = stormpy.parse_properties(formula_a_minus_b)
        env = stormpy.Environment()
        max_diff_lower_half, max_diff_upper_half = stormpy.compute_rel_reach_helper(env, self.model.parsed_model, properties_a_minus_b[0].raw_formula)

        # results on original MDP: 2* results on transformed MDP
        max_diff_lower, max_diff_upper = 2 * max_diff_lower_half, 2* max_diff_upper_half

        # check whether max {P(F a) - P(F b)} <= 0
        if max_diff_lower > 0:
            common.colourinfo("Not all schedulers match the probabilities since max {P(F a) - P(F b)} > 0")
        elif max_diff_upper > 0:
            common.colourinfo("Result unknown. The lower bound for max {P(F a) - P(F b)} is <= 0 but the upper bound is > 0.")
        else:
            # calculate max {P(F b) - P(F a)} = - min {P(F a) - P(F b)}
            formula_b_minus_a = "multi(Pmax=?  [F \"" + target_b + "\"], Pmax=?  [F \"" + target_a + "\"])"
            properties_b_minus_a = stormpy.parse_properties(formula_b_minus_a)
            env = stormpy.Environment()
            neg_half_min_diff_lower, neg_half_min_diff_upper = stormpy.compute_rel_reach_helper(env, self.model.parsed_model, properties_b_minus_a[0].raw_formula)

            # results on original MDP: 2* results on transformed MDP
            min_diff_upper, min_diff_lower = - 2 * neg_half_min_diff_lower, - 2 * neg_half_min_diff_upper

            # check whether min {P(F a) - P(F b)} >= 0
            if min_diff_upper < 0:
                common.colourinfo("Not all schedulers match the probabilities since min {P(F a) - P(F b)} < 0")
            elif min_diff_lower < 0:
                common.colourinfo("Result unknown. The upper bound for min {P(F a) - P(F b)} is >= 0 but the lower bound is < 0.")
            else:
                print("All schedulers achieve P(F a) = P(F b)")


        # # Checking for existence of a scheduler:
        # # scheduler can only exist if max {P(F a) - P(F b)} >= 0 and min {P(F a) - P(F b)} <= 0
        # if max_diff_upper < 0:
        #     print("There does not exist a scheduler matching the probabilities since max {P(F a) - P(F b)} < 0")
        # elif max_diff_lower < 0:
        #     print("Result unknown. The upper bound for max {P(F a) - P(F b)} is >= 0 but the lower bound is < 0.")
        # elif min_diff_lower > 0:
        #     print("There does not exist a scheduler matching the probabilities since min {P(F a) - P(F b)} > 0")
        # elif min_diff_upper > 0:
        #     print("Result unknown. The lower bound for min {P(F a) - P(F b)} is <= 0 but the upper bound is > 0.")


