import stormpy
from relreach.utility import common
from pycarl.gmp.gmp import Rational

class ModelChecker:
    def __init__(self, model_list, make_copies, targets, property_list, compOp, coeff, exact):
        self.make_copies = make_copies
        self.model_list = model_list
        self.targets = targets
        self.property_list = property_list  # object of property class
        self.compOp = compOp
        self.coeff = coeff
        self.exact = exact
        if self.exact:
            self.coeff = stormpy.Rational(self.coeff)

    def modelCheck(self):
        if self.make_copies: # then we look for the first target in the first copy and for the second one in the second copy
            target_a = self.targets[0] + "_1"
            target_b = self.targets[1] + "_2"

            model_a = self.model_list[0]
            model_b = self.model_list[1]

            properties_a = self.property_list[0]
            properties_b = self.property_list[1]
        else:
            target_a = self.targets[0]
            target_b = self.targets[1]

            model = self.model_list[0]

            properties = self.property_list[0]

        bound = self.coeff # if we add coeff for the summands: self.coeff[2]

        if self.compOp in ['=', '<=', '<', '!=']:
        # "forall sched P(F a) - P(F b) < / <= bound" is violated iff "max {P(F a) - P(F b)} >= / > bound"
        # calculate max {P(F a) - P(F b)}
            if self.make_copies:
                env = stormpy.Environment()
                if self.exact:
                    common.colourerror("exact not implemented")
                    env.solver_environment.set_force_exact() # Unexpected error encountered: 'stormpy.core.SolverEnvironment' object has no attribute 'set_force_exact'
                    env.solver_environment.set_linear_equation_solver_type(stormpy.EquationSolverType.eigen)
                    env.solver_environment.minmax_solver_environment.method = stormpy.MinMaxMethod.policy_iteration
                    res_a = stormpy.model_checking(model_a, properties_a[0].raw_formula, only_initial_states=True, environment=env)
                    res_b = stormpy.model_checking(model_b, properties_b[0].raw_formula, only_initial_states=True, environment=env)

                    max_diff_lower, max_diff_upper = res_a - res_a, res_a - res_b
                else: # make_copies, not exact
                    # todo to retain a tolerance of 10^-6 we should use 10^-3 for model_checking though?
                    env.solver_environment.set_force_sound()
                    initial_state_1 = list(model_a.labeling.get_states("init1"))[0]
                    res_a = stormpy.model_checking(model_a, properties_a[0].raw_formula, only_initial_states=True, environment=env)
                    max_a = (res_a.at(initial_state_1))
                    # to remain sound we need to acknowledge that this is only an approximative result
                    max_a_under = max_a - 0.000001
                    max_a_over = max_a + 0.000001

                    initial_state_2 = list(model_b.labeling.get_states("init2"))[0]
                    res_b = stormpy.model_checking(model_b, properties_b[0].raw_formula, only_initial_states=True, environment=env)
                    min_b = (res_b.at(initial_state_2))
                    min_b_under = min_b - 0.000001
                    min_b_over = min_b + 0.000001

                    max_diff_lower, max_diff_upper = max_a_under - min_b_over, max_a_over - min_b_under

            else: # not make_copies
                formula_a_minus_b = "multi(Pmax=?  [F \"" + target_a + "\"], Pmax=?  [F \"" + target_b + "\"])"
                properties_a_minus_b = stormpy.parse_properties(formula_a_minus_b)
                env = stormpy.Environment()
                # env.solver_environment.set_force_sound()
                if self.exact:
                    env.solver_environment.set_force_exact()
                    env.solver_environment.set_linear_equation_solver_type(stormpy.EquationSolverType.eigen)
                    env.solver_environment.minmax_solver_environment.method = stormpy.MinMaxMethod.policy_iteration
                    res_lower, res_upper = stormpy.compute_rel_reach_helper_exact(env, model, properties_a_minus_b[0].raw_formula)
                else:
                    res_lower, res_upper = stormpy.compute_rel_reach_helper(env, model, properties_a_minus_b[0].raw_formula)

                max_diff_lower, max_diff_upper = res_lower, res_upper

            if self.compOp in ['=', '<=']:
                # check whether max {P(F a) - P(F b)} >= bound
                if max_diff_lower > bound:
                    common.colourerror("Property does not hold since max {P_init1(F " + self.targets[0] + ") - P_init2(F " + self.targets[1] + ")} > " + str(bound))
                    return -1
                elif max_diff_upper > bound:
                    common.colourerror("Result unknown. The lower bound for max {P_init1(F " + self.targets[0] + ") - P_init2(F " + self.targets[1] + ")} is <= " + str(bound) + " but the upper bound is > " + str(bound))
                    return 0
            elif self.compOp in ['<']: # compOp = '<'
                # check whether max {P(F a) - P(F b)} > bound
                if max_diff_lower >= bound:
                    common.colourerror(
                        "Property does not hold since max {P_init1(F " + self.targets[0] + ") - P_init2(F " + self.targets[1] + ")} >= " + str(bound))
                    return -1
                elif max_diff_upper >= bound:
                    common.colourerror(
                        "Result unknown. The lower bound for max {P_init1(F " + self.targets[0] + ") - P_init2(F " + self.targets[1] + ")} is < " + str(bound) + " but the upper bound is >= " + str(bound))
                    return 0
            else: # compOp = '!='
                #todo
                print("todo")
                return 0

        if self.compOp in ['=', '>=', '>', '!=']:
        # "forall sched P(F a) - P(F b) > / >= bound" is violated iff "min {P(F a) - P(F b)} <= / < bound"
        # calculate min {P(F a) - P(F b)} = - max {P(F b) - P(F a)}
            if self.make_copies:
                env = stormpy.Environment()
                if self.exact:
                    common.colourerror("exact not implemented")
                    env.solver_environment.set_force_exact()  # Unexpected error encountered: 'stormpy.core.SolverEnvironment' object has no attribute 'set_force_exact'
                    env.solver_environment.set_linear_equation_solver_type(stormpy.EquationSolverType.eigen)
                    env.solver_environment.minmax_solver_environment.method = stormpy.MinMaxMethod.policy_iteration
                    res_a = stormpy.model_checking(model_a, properties_a[0].raw_formula, only_initial_states=True,
                                                   environment=env)
                    res_b = stormpy.model_checking(model_b, properties_b[0].raw_formula, only_initial_states=True,
                                                   environment=env)

                    min_diff_lower, min_diff_upper = res_a - res_b, res_a - res_b
                else: # make_copies, not exact
                    # todo to retain a tolerance of 10^-6 we should use 10^-3 for model_checking though?
                    env.solver_environment.set_force_sound()
                    initial_state_1 = list(model_a.labeling.get_states("init1"))[0]
                    res_a = stormpy.model_checking(model_a, properties_a[0].raw_formula, only_initial_states=True, environment=env)
                    min_a = (res_a.at(initial_state_1))
                    min_a_under = min_a - 0.000001
                    min_a_over = min_a + 0.000001

                    initial_state_2 = list(model_b.labeling.get_states("init2"))[0]
                    res_b = stormpy.model_checking(model_b, properties_b[0].raw_formula, only_initial_states=True, environment=env)
                    max_b = (res_b.at(initial_state_2))
                    max_b_under = max_b - 0.000001
                    max_b_over = max_b + 0.000001

                    min_diff_upper, min_diff_lower = min_a_under - max_b_over, min_a_over - max_b_under

            else: # not make_copies
                formula_b_minus_a = "multi(Pmax=?  [F \"" + target_b + "\"], Pmax=?  [F \"" + target_a + "\"])"
                properties_b_minus_a = stormpy.parse_properties(formula_b_minus_a)
                env = stormpy.Environment() # standard precision is 0.000001
                #env.solver_environment.set_force_sound()
                if self.exact:
                    env.solver_environment.set_force_exact()
                    env.solver_environment.set_linear_equation_solver_type(stormpy.EquationSolverType.eigen)
                    env.solver_environment.minmax_solver_environment.method = stormpy.MinMaxMethod.policy_iteration
                    res_lower, res_upper = stormpy.compute_rel_reach_helper_exact(env, model, properties_b_minus_a[0].raw_formula)
                else:
                    res_lower, res_upper = stormpy.compute_rel_reach_helper(env, model, properties_b_minus_a[0].raw_formula)

            # results on original MDP: 2* results on transformed MDP
                min_diff_lower, min_diff_upper = - res_upper, - res_lower # note reserval of lower + upper!

            if self.compOp in ['=', '>=']:
                # check whether min {P(F a) - P(F b)} <= bound
                if min_diff_upper < bound:
                    common.colourerror("Property does not hold since min {P_init1(F " + self.targets[0] + ") - P_init2(F " + self.targets[1] + ")} <" + str(bound))
                    return -1
                elif min_diff_lower < bound:
                    common.colourerror("Result unknown. The upper bound for min {P_init1(F " + self.targets[0] + ") - P_init2(F " + self.targets[1] + ")} is >= " + str(bound) + " but the lower bound is < " + str(bound))
                    return 0
            elif self.compOp in ['>']: # compOp = '>'
                # check whether min {P(F a) - P(F b)} < bound
                if min_diff_upper <= bound:
                    common.colourerror(
                        "Property does not hold since min {P_init1(F " + self.targets[0] + ") - P_init2(F " + self.targets[1] + ")} <= " + str(bound))
                    return -1
                elif min_diff_lower <= bound:
                    common.colourerror(
                        "Result unknown. The upper bound for min {P_init1(F " + self.targets[0] + ") - P_init2(F " + self.targets[1] + ")} is > " + str(bound) + " but the lower bound is <= " + str(bound))
                    return 0
            else: # compOp = '!='
                #todo
                print("todo")
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


