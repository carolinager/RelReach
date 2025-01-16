import stormpy
from relreach.utility import common
from pycarl.gmp.gmp import Rational

class ModelChecker:
    def __init__(self, model, make_copies, targets, properties, compOp, coeff, exact):
        self.make_copies = make_copies
        self.model = model
        self.targets = targets
        self.properties = properties  # object of property class
        self.compOp = compOp
        self.coeff = coeff
        self.exact = exact
        if self.exact:
            self.coeff = stormpy.Rational(self.coeff)

    def modelCheck(self):
        # if self.make_copies: # then we look for the first target in the first copy and for the second one in the second copy
        #     target_a = self.targets[0] + "_1"
        #     target_b = self.targets[1] + "_2"
        # else:
        #     target_a = self.targets[0]
        #     target_b = self.targets[1]

        # todo adjust for approx comparison operators?
        # todo add weights ?
        bound = self.coeff # if we add coeff for the summands: self.coeff[2]

        # calculate max {P(F a) - P(F b)}
        if self.compOp in ['=', '<=', '<']:
            #formula_a_minus_b = "multi(Pmax=?  [F \"" + target_a + "\"], Pmax=?  [F \"" + target_b + "\"])"
            #properties_a_minus_b = stormpy.parse_properties(formula_a_minus_b)
            env = stormpy.Environment()
            # env.solver_environment.set_force_sound()
            if self.exact:
                env.solver_environment.set_force_exact()
                env.solver_environment.set_linear_equation_solver_type(stormpy.EquationSolverType.eigen)
                env.solver_environment.minmax_solver_environment.method = stormpy.MinMaxMethod.policy_iteration
                res_lower, res_upper = stormpy.compute_rel_reach_helper_exact(env, self.model.parsed_model,
                                                                        self.properties[0].raw_formula)
            else:
                res_lower, res_upper = stormpy.compute_rel_reach_helper(env, self.model.parsed_model, self.properties[0].raw_formula)

            # if we made copies: results on original MDP = 2* results on transformed MDP
            if self.make_copies:
                max_diff_lower, max_diff_upper = 2 * res_lower, 2* res_upper
            else:
                max_diff_lower, max_diff_upper = res_lower, res_upper

            if self.compOp in ['=', '<=']:
                # check whether max {P(F a) - P(F b)} <= bound
                if max_diff_lower > bound:
                    common.colourerror("Property does not hold since max {P_init1(F " + self.targets[0] + ") - P_init2(F " + self.targets[1] + ")} > " + str(bound))
                    return -1
                elif max_diff_upper > bound:
                    common.colourerror("Result unknown. The lower bound for max {P_init1(F " + self.targets[0] + ") - P_init2(F " + self.targets[1] + ")} is <= " + str(bound) + " but the upper bound is > " + str(bound))
                    return 0
            else: # compOp = '<'
                # check whether max {P(F a) - P(F b)} < bound
                if max_diff_lower >= bound:
                    common.colourerror(
                        "Property does not hold since max {P_init1(F " + self.targets[0] + ") - P_init2(F " + self.targets[1] + ")} >= " + str(bound))
                    return -1
                elif max_diff_upper >= bound:
                    common.colourerror(
                        "Result unknown. The lower bound for max {P_init1(F " + self.targets[0] + ") - P_init2(F " + self.targets[1] + ")} is < " + str(bound) + " but the upper bound is >= " + str(bound))
                    return 0

        # calculate max {P(F b) - P(F a)} = - min {P(F a) - P(F b)}
        if self.compOp in ['=', '>=', '>']:
            #formula_b_minus_a = "multi(Pmax=?  [F \"" + target_b + "\"], Pmax=?  [F \"" + target_a + "\"])"
            #properties_b_minus_a = stormpy.parse_properties(formula_b_minus_a)
            env = stormpy.Environment() # standard precision is 0.000001
            env.solver_environment.set_force_sound()
            if self.exact:
                env.solver_environment.set_linear_equation_solver_type(stormpy.EquationSolverType.eigen)
                env.solver_environment.minmax_solver_environment.method = stormpy.MinMaxMethod.policy_iteration
                res_lower, res_upper = stormpy.compute_rel_reach_helper_exact(env, self.model.parsed_model,
                                                                        self.properties[0].raw_formula)
            else:
                res_lower, res_upper = stormpy.compute_rel_reach_helper(env, self.model.parsed_model, self.properties[0].raw_formula)

            # results on original MDP: 2* results on transformed MDP
            if self.make_copies:
                min_diff_upper, min_diff_lower = - 2 * res_lower, - 2 * res_upper
            else:
                min_diff_upper, min_diff_lower = - res_lower, - res_upper

            if self.compOp in ['=', '>=']:
                # check whether min {P(F a) - P(F b)} >= bound
                if min_diff_upper < bound:
                    common.colourerror("Property does not hold since min {P_init1(F " + self.targets[0] + ") - P_init2(F " + self.targets[1] + ")} <" + str(bound))
                    return -1
                elif min_diff_lower < bound:
                    common.colourerror("Result unknown. The upper bound for min {P_init1(F " + self.targets[0] + ") - P_init2(F " + self.targets[1] + ")} is >= " + str(bound) + " but the lower bound is < " + str(bound))
                    return 0
            else: # compOp = '>'
                # check whether min {P(F a) - P(F b)} > bound
                if min_diff_upper <= bound:
                    common.colourerror(
                        "Property does not hold since min {P_init1(F " + self.targets[0] + ") - P_init2(F " + self.targets[1] + ")} <= " + str(bound))
                    return -1
                elif min_diff_lower <= bound:
                    common.colourerror(
                        "Result unknown. The upper bound for min {P_init1(F " + self.targets[0] + ") - P_init2(F " + self.targets[1] + ")} is > " + str(bound) + " but the lower bound is <= " + str(bound))
                    return 0

        common.colourinfo("All schedulers achieve P_init1(F " + self.targets[0] + ") - P_init2(F " + self.targets[1] + ")" + self.compOp + str(bound))
        return 1

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


