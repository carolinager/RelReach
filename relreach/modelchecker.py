import stormpy
from relreach.utility import common
from pycarl.gmp.gmp import Rational

from contextlib import redirect_stdout
import time


class ModelChecker:
    def __init__(self, model, make_copies, targets, compOp, coeff, exact, epsilon, witness):
        self.make_copies = make_copies
        self.model = model
        self.targets = targets
        self.compOp = compOp
        self.coeff = coeff
        self.exact = exact
        self.epsilon = epsilon
        self.witness = witness
        # if self.exact:
        #     self.coeff = stormpy.Rational(self.coeff)
        #     self.epsilon = stormpy.Rational(self.epsilon)

    def modelCheck(self):
        target_a = self.targets[0]
        target_b = self.targets[1]

        bound = self.coeff  # if we add coeff for the summands: self.coeff[2]
        res_first = None
        res_second = None

        if self.compOp in ['=', '<=', '<', '!=']:
            # "forall sched P(F a) - P(F b) < / <= bound" is violated iff "max {P(F a) - P(F b)} >= / > bound"
            # calculate max {P(F a) - P(F b)}
            if self.make_copies:
                # calculate max {P(F a) - P(F b)} directly as max {P(F a)} - min {P(F b)}
                formula_a = "Pmax=? [F \"" + target_a + "\"]"
                formula_b = "Pmin=? [F \"" + target_b + "\"]"
                properties_a = stormpy.parse_properties(formula_a)
                properties_b = stormpy.parse_properties(formula_b)

                env = stormpy.Environment()
                initial_state_1 = list(self.model.labeling.get_states("init1"))[0]
                initial_state_2 = list(self.model.labeling.get_states("init2"))[0]

                if self.exact:
                    env.solver_environment.set_force_exact()
                    env.solver_environment.set_linear_equation_solver_type(stormpy.EquationSolverType.eigen)
                    env.solver_environment.minmax_solver_environment.method = stormpy.MinMaxMethod.policy_iteration
                    res_a = stormpy.model_checking(self.model, properties_a[0].raw_formula, only_initial_states=True,
                                                   environment=env, extract_scheduler=self.witness)
                    res_b = stormpy.model_checking(self.model, properties_b[0].raw_formula, only_initial_states=True,
                                                   environment=env, extract_scheduler=self.witness)
                    # Unexpected error encountered: Unable to convert function return value to a Python type! The signature was
                    # 	(self: stormpy.core.ExplicitExactQuantitativeCheckResult, state: int) -> __gmp_expr<__mpq_struct [1], __mpq_struct [1]>

                    max_a = res_a.at(initial_state_1)
                    # float(res_a.at(initial_state_1).numerator()) / float(res_a.at(initial_state_1).numerator())
                    min_b = res_b.at(initial_state_2)

                    res = max_a - min_b
                    scheds_max = [res_a.scheduler, res_b.scheduler]
                    max_diff_lower, max_diff_upper = max_a - min_b, max_a - min_b

                else:  # make_copies, not exact
                    env.solver_environment.set_force_sound()
                    res_a = stormpy.model_checking(self.model, properties_a[0].raw_formula, only_initial_states=True,
                                                   environment=env, extract_scheduler=self.witness)
                    max_a = (res_a.at(initial_state_1))
                    # to remain sound we need to acknowledge that this is only an approximative result
                    max_a_under = max_a / (1 + 0.000001)
                    max_a_over = max_a / (1 - 0.000001)

                    res_b = stormpy.model_checking(self.model, properties_b[0].raw_formula, only_initial_states=True,
                                                   environment=env, extract_scheduler=self.witness)
                    min_b = (res_b.at(initial_state_2))
                    min_b_under = min_b / (1 + 0.000001)
                    min_b_over = min_b / (1 - 0.000001)

                    res = max_a - min_b
                    if self.witness:
                        scheds_max = [res_a.scheduler, res_b.scheduler]
                    max_diff_lower, max_diff_upper = max_a_under - min_b_over, max_a_over - min_b_under

            else:  # not make_copies
                formula_a_minus_b = "multi(Pmax=?  [F \"" + target_a + "\"], Pmax=?  [F \"" + target_b + "\"])"
                properties_a_minus_b = stormpy.parse_properties(formula_a_minus_b)
                env = stormpy.Environment()
                # env.solver_environment.set_force_sound()
                if self.exact:
                    env.solver_environment.set_force_exact()
                    env.solver_environment.set_linear_equation_solver_type(stormpy.EquationSolverType.eigen)
                    env.solver_environment.minmax_solver_environment.method = stormpy.MinMaxMethod.policy_iteration
                    res, _, sched = stormpy.compute_rel_reach_helper_exact(env, self.model,
                                                                                  properties_a_minus_b[0].raw_formula, computeScheduler=self.witness)
                    # todo , extract_scheduler=self.witness
                    if self.witness:
                        scheds_max = [sched]
                    res_lower, res_upper = res, res
                    # Unexpected error encountered: Unable to convert function return value to a Python type! The signature was
                    # 	(env: stormpy.core.Environment, model: storm::models::sparse::Mdp<__gmp_expr<__mpq_struct [1], __mpq_struct [1]>, storm::models::sparse::StandardRewardModel<__gmp_expr<__mpq_struct [1], __mpq_struct [1]> > >, formula: storm::logic::MultiObjectiveFormula) -> Tuple[__gmp_expr<__mpq_struct [1], __mpq_struct [1]>, __gmp_expr<__mpq_struct [1], __mpq_struct [1]>]
                else:
                    res, _, sched = stormpy.compute_rel_reach_helper(env, self.model,properties_a_minus_b[0].raw_formula, self.witness)
                    # todo , extract_scheduler=self.witness
                    if self.witness:
                        scheds_max = [sched]

                    # StandardPcaaWeightVectorChecker currently returns (lower + upper)/2 for both res_u and res_o
                    res_lower = res / (1 + 0.000001)
                    res_upper = res / (1 - 0.000001)

                max_diff_lower, max_diff_upper = res_lower, res_upper

            if self.compOp in ['=', '<=']:
                # For '<=': check whether max {P(F a) - P(F b)} <= bound. If not: prop does not hold. If yes: prop holds
                # For '=': check whether max {P(F a) - P(F b)} <= bound + epsilon. If not: prop does not hold. If yes: Other conjunct might not hold
                bound_x = bound + self.epsilon
                if max_diff_lower > bound_x:
                    common.colourerror(
                        "Property does not hold since max {P_init1(F " + self.targets[0] + ") - P_init2(F " +
                        self.targets[1] + ")} > " + str(bound_x))
                    # output witness for max i.e. write each scheduler maximizing the weighted sum to a file
                    if self.witness:
                        for i in range(len(scheds_max)):
                            file_name = 'logs/scheduler_max_' + str(i) + '_' + str(time.perf_counter()) + '.txt'
                            with open(file_name, 'w') as f:
                                with redirect_stdout(f):
                                    print(scheds_max[i])
                        common.colourerror("Maximizing witness schedulers written to files") #todo possibly for goal unfolding
                    return -1
                elif max_diff_upper > bound_x:
                    common.colourerror(
                        "Result unknown. The lower bound for max {P_init1(F " + self.targets[0] + ") - P_init2(F " +
                        self.targets[1] + ")} is <= " + str(bound_x) + " but the upper bound is > " + str(bound_x))
                    return 0
            elif self.compOp in ['<']:  # compOp = '<'
                # check whether max {P(F a) - P(F b)} < bound. If not: prop does not hold. If yes: prop holds
                if max_diff_lower >= bound:
                    common.colourerror(
                        "Property does not hold since max {P_init1(F " + self.targets[0] + ") - P_init2(F " +
                        self.targets[1] + ")} >= " + str(bound))
                    # output witness for max i.e. write each scheduler maximizing the weighted sum to a file
                    if self.witness:
                        for i in range(len(scheds_max)):
                            file_name = 'logs/scheduler_max_' + str(i) + '_' + str(time.perf_counter()) + '.txt'
                            with open(file_name, 'w') as f:
                                with redirect_stdout(f):
                                    print(scheds_max[i])
                        common.colourerror("Maximizing witness schedulers written to files")  # todo possibly for goal unfolding
                    return -1
                elif max_diff_upper >= bound:
                    common.colourerror(
                        "Result unknown. The lower bound for max {P_init1(F " + self.targets[0] + ") - P_init2(F " +
                        self.targets[1] + ")} is < " + str(bound) + " but the upper bound is >= " + str(bound))
                    return 0
            else:  # compOp = '!='
                # check whether max {P(F a) - P(F b)} < bound - epsilon. If yes: prop holds. If not: prop might still be sat by other disjunct
                bound_x = bound - self.epsilon
                if max_diff_lower >= bound_x:
                    common.colourerror(
                        "max {P_init1(F " + self.targets[0] + ") - P_init2(F " + self.targets[1] + ")} >= " + str(
                            bound) + "-" + str(self.epsilon))
                    v_max = res
                    res_first = -1
                elif max_diff_upper >= bound_x:
                    common.colourerror(
                        "lower bound for max {P_init1(F " + self.targets[0] + ") - P_init2(F " + self.targets[
                            1] + ")} is < " + str(bound) + "-" + str(
                            self.epsilon) + " but the upper bound is >= " + str(bound) + "-" + str(self.epsilon))
                    res_first = 0
                else:
                    common.colourerror(
                        "Property holds since upper bound for max {P_init1(F " + self.targets[0] + ") - P_init2(F " +
                        self.targets[
                            1] + ")} is < " + str(bound) + "-" + str(self.epsilon))
                    return 1
                assert (res_first != 1) and not (
                            res_first is None), "Something went wrong. res_first should be defined, but not 1 if we reach this statement"

        if self.compOp in ['=', '>=', '>', '!=']:
            # "forall sched P(F a) - P(F b) > / >= bound" is violated iff "min {P(F a) - P(F b)} <= / < bound"
            # calculate min {P(F a) - P(F b)}
            if self.make_copies:
                # calculate min {P(F a) - P(F b)} directly as min {P(F a)} - max {P(F b)}
                formula_a = "Pmin=? [F \"" + target_a + "\"]"
                formula_b = "Pmax=? [F \"" + target_b + "\"]"
                properties_a = stormpy.parse_properties(formula_a)
                properties_b = stormpy.parse_properties(formula_b)

                env = stormpy.Environment()
                initial_state_1 = list(self.model.labeling.get_states("init1"))[0]
                initial_state_2 = list(self.model.labeling.get_states("init2"))[0]

                if self.exact:
                    env.solver_environment.set_force_exact()
                    env.solver_environment.set_linear_equation_solver_type(stormpy.EquationSolverType.eigen)
                    env.solver_environment.minmax_solver_environment.method = stormpy.MinMaxMethod.policy_iteration
                    res_a = stormpy.model_checking(self.model, properties_a[0].raw_formula, only_initial_states=True,
                                                   environment=env)
                    res_b = stormpy.model_checking(self.model, properties_b[0].raw_formula, only_initial_states=True,
                                                   environment=env)

                    min_a = res_a.at(initial_state_1)
                    max_b = res_b.at(initial_state_2)

                    res = min_a - max_b
                    scheds_min = [res_a.scheduler, res_b.scheduler]
                    min_diff_upper, min_diff_lower = min_a - max_b, min_a - max_b

                else:  # make_copies, not exact
                    env.solver_environment.set_force_sound()
                    initial_state_1 = list(self.model.labeling.get_states("init1"))[0]
                    res_a = stormpy.model_checking(self.model, properties_a[0].raw_formula, only_initial_states=True,
                                                   environment=env)
                    min_a = (res_a.at(initial_state_1))
                    min_a_under = min_a / (1 + 0.000001)
                    min_a_over = min_a / (1 - 0.000001)

                    initial_state_2 = list(self.model.labeling.get_states("init2"))[0]
                    res_b = stormpy.model_checking(self.model, properties_b[0].raw_formula, only_initial_states=True,
                                                   environment=env)
                    max_b = (res_b.at(initial_state_2))
                    max_b_under = max_b / (1 + 0.000001)
                    max_b_over = max_b / (1 - 0.000001)

                    res = min_a - max_b
                    scheds_min = [res_a.scheduler, res_b.scheduler]
                    min_diff_upper, min_diff_lower = min_a_under - max_b_over, min_a_over - max_b_under

            else:  # not make_copies
                # calculate min {P(F a) - P(F b)} by computing - max {P(F b) - P(F a)}
                formula_b_minus_a = "multi(Pmax=?  [F \"" + target_b + "\"], Pmax=?  [F \"" + target_a + "\"])"
                properties_b_minus_a = stormpy.parse_properties(formula_b_minus_a)
                env = stormpy.Environment()  # standard precision is 0.000001
                # env.solver_environment.set_force_sound()
                if self.exact:
                    env.solver_environment.set_force_exact()
                    env.solver_environment.set_linear_equation_solver_type(stormpy.EquationSolverType.eigen)
                    env.solver_environment.minmax_solver_environment.method = stormpy.MinMaxMethod.policy_iteration
                    res, _, sched = stormpy.compute_rel_reach_helper_exact(env, self.model,
                                                                                  properties_b_minus_a[0].raw_formula, self.witness)
                    # todo extract schedulers
                    if self.witness:
                        scheds_min = [sched]
                    res_lower, res_upper = res, res
                else:
                    res, _, sched = stormpy.compute_rel_reach_helper(env, self.model, properties_a_minus_b[0].raw_formula, self.witness)
                    # StandardPcaaWeightVectorChecker currently returns (lower + upper)/2 for both res_u and res_o
                    if self.witness:
                        scheds_min = [sched]

                    res_lower, res_upper = res, res
                    res_lower = res / (1 + 0.000001)
                    res_upper = res / (1 - 0.000001)

                # results on original MDP: 2* results on transformed MDP
                min_diff_lower, min_diff_upper = - res_upper, - res_lower  # note reversal of lower + upper!

            if self.compOp in ['=', '>=']:
                # For '>=': check whether min {P(F a) - P(F b)} >= bound. If not: prop does not hold. If yes: prop holds
                # For '=': check whether min {P(F a) - P(F b)} >= bound - epsilon. If not: prop does not hold. If yes: prop holds since other conjunct must also hold if we reached this point
                bound_x = bound - self.epsilon
                if min_diff_upper < bound_x:
                    common.colourerror(
                        "Property does not hold since min {P_init1(F " + self.targets[0] + ") - P_init2(F " +
                        self.targets[1] + ")} <" + str(bound_x))

                    # output witness for min i.e. write each scheduler minimizing the weighted sum to a file
                    if self.witness:
                        for i in range(len(scheds_min)):
                            file_name = 'logs/scheduler_min_' + str(i) + '_' + str(time.perf_counter()) + '.txt'
                            with open(file_name, 'w') as f:
                                with redirect_stdout(f):
                                    print(scheds_min[i])
                        common.colourerror("Minimizing witness schedulers written to files")  # todo possibly for goal unfolding

                    return -1
                elif min_diff_lower < bound_x:
                    common.colourerror(
                        "Result unknown. The upper bound for min {P_init1(F " + self.targets[0] + ") - P_init2(F " +
                        self.targets[1] + ")} is >= " + str(bound_x) + " but the lower bound is < " + str(bound_x))
                    return 0
                # else:
                #     res = 1
            elif self.compOp in ['>']:  # compOp = '>'
                # check whether min {P(F a) - P(F b)} < bound. If not: prop does not hold. If yes: prop holds
                if min_diff_upper <= bound:
                    common.colourerror(
                        "Property does not hold since min {P_init1(F " + self.targets[0] + ") - P_init2(F " +
                        self.targets[1] + ")} <= " + str(bound))

                    # output witness for min i.e. write each scheduler minimizing the weighted sum to a file
                    if self.witness:
                        for i in range(len(scheds_min)):
                            file_name = 'logs/scheduler_min_' + str(i) + '_' + str(time.perf_counter()) + '.txt'
                            with open(file_name, 'w') as f:
                                with redirect_stdout(f):
                                    print(scheds_min[i])
                        common.colourerror("Minimizing witness schedulers written to files")  # todo possibly for goal unfolding

                    return -1
                elif min_diff_lower <= bound:
                    common.colourerror(
                        "Result unknown. The upper bound for min {P_init1(F " + self.targets[0] + ") - P_init2(F " +
                        self.targets[1] + ")} is > " + str(bound) + " but the lower bound is <= " + str(bound))
                    return 0
            else:  # compOp = '!=' i.e. exists =
                # check whether min {P(F a) - P(F b)} > bound + epsilon. If yes: prop holds. If not: prop does not hold or unknown since we wouldnt reach this point if first disjunct held.
                bound_x = bound + self.epsilon
                if min_diff_upper <= bound_x:
                    common.colourerror(
                        "min {P_init1(F " + self.targets[0] + ") - P_init2(F " + self.targets[1] + ")} <= " + str(
                            bound) + "+" + str(self.epsilon))
                    v_min = res
                    res_second = -1
                elif min_diff_lower <= bound_x:
                    common.colourerror(
                        "upper bound for min {P_init1(F " + self.targets[0] + ") - P_init2(F " + self.targets[
                            1] + ")} is > " + str(bound_x) + " but the lower bound is <= " + str(bound) + "+" + str(
                            self.epsilon))
                    res_second = 0
                else:
                    common.colourerror(
                        "Property holds since lower bound for min {P_init1(F " + self.targets[0] + ") - P_init2(F " +
                        self.targets[
                            1] + ")} is > " + str(bound) + "+" + str(self.epsilon))
                    return 1
                #
                assert (res_second != 1) and not (res_second is None), ("Something went wrong. "
                                                                        "res_second should be defined, "
                                                                        "but not 1 if we reach this statement")
                if res_first == 0 and res_second == 0:
                    common.colourerror("Result unknown.")
                    return 0
                elif res_first == -1 and res_second == -1:
                    common.colourerror(
                        "Property does not hold since max {P_init1(F " + self.targets[0] + ") - P_init2(F " +
                        self.targets[1] + ")} >= " + str(bound) + "-" + str(self.epsilon) +
                        " and min {P_init1(F " +
                        self.targets[0] + ") - P_init2(F " + self.targets[1] + ")} <= " + str(bound) + "+" + str(
                            self.epsilon))

                    if self.witness:
                        common.colourerror("Writing witness files...")
                        start_witness_time = time.perf_counter()
                        if max_diff_upper <= bound + self.epsilon:
                            # output witness for max i.e. write each scheduler maximizing the weighted sum to a file
                            for i in range(len(scheds_max)):
                                file_name = 'logs/scheduler_max_' + str(i) + '_' + str(time.perf_counter()) + '.txt'
                                with open(file_name, 'w') as f:
                                    with redirect_stdout(f):
                                        print(scheds_max[i])
                            common.colourerror(
                                "Maximizing schedulers are already witnesses. Schedulers written to files")  # todo possibly for goal unfolding
                        elif min_diff_lower >= bound - self.epsilon:
                            # output witness for min i.e. write each scheduler minimizing the weighted sum to a file
                            for i in range(len(scheds_min)):
                                file_name = 'logs/scheduler_min_' + str(i) + '_' + str(time.perf_counter()) + '.txt'
                                with open(file_name, 'w') as f:
                                    with redirect_stdout(f):
                                        print(scheds_min[i])
                            common.colourerror(
                                "Maximizing schedulers are already witnesses. Schedulers written to files")  # todo possibly for goal unfolding
                        else:
                            lambda_witness = (bound - v_max)/(v_min - v_max)
                            for i in range(len(scheds_max)):
                                file_name = 'logs/scheduler_max_' + str(i) + '_' + str(time.perf_counter()) + '.txt'
                                with open(file_name, 'w') as f:
                                    with redirect_stdout(f):
                                        print(scheds_max[i])
                            common.colourerror(
                                "Maximizing schedulers written to files")  # todo possibly for goal unfolding
                            for i in range(len(scheds_min)):
                                file_name = 'logs/scheduler_min_' + str(i) + '_' + str(time.perf_counter()) + '.txt'
                                with open(file_name, 'w') as f:
                                    with redirect_stdout(f):
                                        print(scheds_min[i])
                            common.colourerror(
                                "Minimizing schedulers written to files")  # todo possibly for goal unfolding
                            common.colourerror("Counterexample witness schedulers are the convex combination of min and max schedulers w.r.t. lambda=" + str(lambda_witness))
                        end_witness_time = time.perf_counter()
                        common.colourinfo("Writing witness files took: " + str(round(end_witness_time - start_witness_time, 2)) + " seconds", True)
                        # todo record time in the other cases
                    return -1
                elif res_first == -1 and res_second == 0:
                    common.colourerror("Result unknown")
                    return 0
                elif res_first == 0 and res_second == -1:
                    common.colourerror("Result unknown")
                    return 0

        # if compOp is '!=' we do not reach this
        assert self.compOp != '!=', "Something went wrong. If compOp is !=, we should have terminated earlier."
        common.colourinfo("All schedulers achieve P_init1(F " + self.targets[0] + ") - P_init2(F " + self.targets[
            1] + ")" + self.compOp + str(bound) + " wrt epsilon=" + str(self.epsilon))
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
