import stormpy
from relreach.utility import common
from pycarl.gmp.gmp import Rational

from contextlib import redirect_stdout
import time


class ModelChecker:
    def __init__(self, model, make_copies, state_sched_comb, ind_dict, targets, compOp, coeff, exact, epsilon, witness):
        self.make_copies = make_copies
        self.model = model
        self.state_sched_comb = state_sched_comb
        self.ind_dict = ind_dict
        self.targets = targets
        self.compOp = compOp
        self.coeff = coeff
        self.exact = exact
        self.epsilon = epsilon
        self.witness = witness
        # if self.exact:
        #     self.coeff = stormpy.Rational(self.coeff)
        #     self.epsilon = stormpy.Rational(self.epsilon)

    # computing optimal values (as specified in formula) for a state-scheduler combination c with |relInd(c)|=1
    def modelCheckSingle(self, formula, state, schedind, rel_coeff, res_dict, witness_dict):
        properties = stormpy.parse_properties(formula)
        env = stormpy.Environment()

        if self.exact:
            print("x")
            env.solver_environment.set_force_exact()
            env.solver_environment.set_linear_equation_solver_type(stormpy.EquationSolverType.eigen)
            env.solver_environment.minmax_solver_environment.method = stormpy.MinMaxMethod.policy_iteration
        else:
            env.solver_environment.set_force_sound()

        res = stormpy.model_checking(self.model,
                                     properties[0].raw_formula,
                                     only_initial_states=True,
                                     environment=env,
                                     extract_scheduler=self.witness)
        res_at_state = res.at(state)
        print("res at " + str((state, schedind)) + ": " + str(res_at_state))

        if self.exact:
            res_dict[(state, schedind)] = Rational(rel_coeff) * res_at_state
            print(Rational(rel_coeff) * res_at_state)
        else:
            res_weighted = rel_coeff * res_at_state
            # stormpy.model_checking currently does not return sound lower and upper bound but (lower + upper)/2
            # to remain sound we need to acknowledge that this is only an approximative result
            # we know res_at_state >= 0
            if rel_coeff >= 0:
                res_opt_under = res_weighted / (1 + 0.000001)
                res_opt_over = res_weighted / (1 - 0.000001)
            else:
                res_opt_under = res_weighted / (1 - 0.000001)
                res_opt_over = res_weighted / (1 + 0.000001)
            res_dict[(state, schedind)] = (res_opt_under, res_opt_over)
            print(res_opt_under)
            print(res_opt_over)

        if self.witness:
            witness_dict[(state, schedind)] = res.scheduler

        return res_dict, witness_dict

    # computing optimal values (as specified in formula) for a state-scheduler combination c with |relInd(c)|>1
    def modelCheckMulti(self, formula, state, schedind, rel_coeffs, res_dict, witness_dict):
        properties = stormpy.parse_properties(formula)
        env = stormpy.Environment()

        if self.exact:
            env.solver_environment.set_force_exact()
            env.solver_environment.set_linear_equation_solver_type(stormpy.EquationSolverType.eigen)
            env.solver_environment.minmax_solver_environment.method = stormpy.MinMaxMethod.policy_iteration
            res_weighted, resOver, sched = stormpy.compute_rel_reach_helper_exact(env,
                                                                         self.model,
                                                                         state,
                                                                         properties[0].raw_formula,
                                                                         [Rational(r) for r in rel_coeffs], # weightVector
                                                                         self.witness)
            res_dict[(state, schedind)] = res_weighted  # helper already did the weighting
        else:
            res_weighted, resOver, sched = stormpy.compute_rel_reach_helper(env,
                                                                   self.model,
                                                                   state,
                                                                   properties[0].raw_formula,
                                                                   rel_coeffs,  # weightVector
                                                                   self.witness)
            # StandardPcaaWeightVectorChecker currently returns res := (lower + upper)/2 for both res_u and res_o
            # where lower <= exact_res <= upper
            # and guarantees that | res - exact_res | <= | exact_res | * 0.000001
            # to remain sound we need to acknowledge that this is only an approximative result
            if res_weighted >= 0:
                res_under = res_weighted / (1 + 0.000001)
                res_over = res_weighted / (1 - 0.000001)
            else:
                res_under = res_weighted / (1 - 0.000001)
                res_over = res_weighted / (1 + 0.000001)
            res_dict[(state, schedind)] = (res_under, res_over)

        print("res at " + str((state, schedind)) + ": " + str(res_weighted))
        print(resOver)
        if self.witness:
            witness_dict[(state, schedind)] = sched

        return res_dict, witness_dict

    # Main model-checking function
    def modelCheck(self):
        # Step 3: compute min and/or max for each state-scheduler combination
        # for each key, we store: if exact: single exact result, else tuples consisting of lower and upper bound
        res_min_dict = {k: [] for k in self.state_sched_comb}  # todo change to list?
        res_max_dict = {k: [] for k in self.state_sched_comb}
        if self.witness:
            witness_min_dict = {k: [] for k in self.state_sched_comb}
            witness_max_dict = {k: [] for k in self.state_sched_comb}
            print(witness_max_dict)
        else:
            witness_min_dict = None
            witness_max_dict = None

        for (state, schedind) in self.state_sched_comb:
            rel_ind = self.ind_dict[(state, schedind)]

            # compute min and/or max
            if self.compOp in ['<=', '<', '=', '!=']:
                # forall sched P(F a) < bound iff max {P(F a)} < bound
                if len(rel_ind) == 1:
                    # we can use single-objective model-checking
                    rel_target = self.targets[rel_ind[0] - 1]
                    rel_coeff = self.coeff[rel_ind[0] - 1]
                    if rel_coeff >= 0:
                        # max {q * P(F a)} = q * max {P(F a)} for q>=0
                        formula = "Pmax=? [F \"" + rel_target + "\"]"
                    else:
                        # max {q * P(F a)} = q * min {P(F a)} for q<0
                        formula = "Pmin=? [F \"" + rel_target + "\"]"

                    res_max_dict, witness_max_dict = self.modelCheckSingle(formula, state, schedind, rel_coeff, res_max_dict, witness_max_dict)

                else:
                    # we need to use multi-objective model-checking
                    rel_targets = [self.targets[i - 1] for i in rel_ind]
                    rel_coeffs = [self.coeff[i - 1] for i in rel_ind]

                    # compute_rel_reach_helper takes care of correct weighting with weightVector=rel_coeffs and optimizing in correct direction
                    formula_interm = "multi("
                    for target in rel_targets:
                        formula_interm += "Pmax=?  [F \"" + target + "\"], "
                    formula = formula_interm[:-2] + ")"

                    res_max_dict, witness_max_dict = self.modelCheckMulti(formula, state, schedind, rel_coeffs, res_max_dict, witness_max_dict)

            if self.compOp in ['>=', '>', '=', '!=']:
                # forall sched P(F a) > bound iff min {P(F a)} > bound
                if len(rel_ind) == 1:
                    rel_target = self.targets[rel_ind[0] - 1]
                    rel_coeff = self.coeff[rel_ind[0] - 1]
                    if rel_coeff >= 0:
                        # max {q * P(F a)} = q * max {P(F a)} for q>=0
                        formula = "Pmin=? [F \"" + rel_target + "\"]"
                    else:
                        # max {q * P(F a)} = q * min {P(F a)} for q<0
                        formula = "Pmax=? [F \"" + rel_target + "\"]"

                    res_min_dict, witness_min_dict = self.modelCheckSingle(formula, state, schedind, rel_coeff,
                                                                           res_min_dict, witness_min_dict)

                else:
                    # we need to use multi-objective model-checking
                    rel_targets = [self.targets[i - 1] for i in rel_ind]
                    rel_coeffs = [self.coeff[i - 1] for i in rel_ind]

                    # compute_rel_reach_helper takes care of correct weighting with weightVector=rel_coeffs and optimizing in correct direction
                    formula_interm = "multi("
                    for target in rel_targets:
                        formula_interm += "Pmin=?  [F \"" + target + "\"], "
                    formula = formula_interm[:-2] + ")"

                    res_min_dict, witness_min_dict = self.modelCheckMulti(formula, state, schedind, rel_coeffs,
                                                                          res_min_dict, witness_min_dict)

        # Step 4: aggregate and compare
        if self.compOp in ['<=', '<', '=', '!=']:
            max_sum_list = list(res_max_dict.values())
            if self.exact:
                max_sum = sum(max_sum_list)
                max_sum_lower, max_sum_upper = max_sum, max_sum
                common.colourerror("Max weighted sum: " + str(max_sum))
            else:
                max_sum_lower = sum([l for (l, _) in max_sum_list])
                max_sum_upper = sum([u for (_, u) in max_sum_list])
                common.colourerror("Lower bound for max weighted sum: " + str(max_sum_lower))
                common.colourerror("Upper bound for max weighted sum: " + str(max_sum_upper))
        if self.compOp in ['>=', '>', '=', '!=']:
            min_sum_list = list(res_min_dict.values())
            if self.exact:
                min_sum = sum(min_sum_list)
                min_sum_lower, min_sum_upper = min_sum, min_sum
                common.colourerror("Min weighted sum: " + str(min_sum))
            else:
                min_sum_lower = sum([l for (l, _) in min_sum_list])
                min_sum_upper = sum([u for (_, u) in min_sum_list])
                common.colourerror("Lower bound for min weighted sum: " + str(min_sum_lower))
                common.colourerror("Upper bound for min weighted sum: " + str(min_sum_upper))


        # todo output witnesses
        if self.exact:
            bound = Rational(self.coeff[-1])
            bound_upper = bound + Rational(self.epsilon)
            bound_lower = bound - Rational(self.epsilon)
        else:
            bound = self.coeff[-1]
            bound_upper = bound + self.epsilon
            bound_lower = bound - self.epsilon
        if self.compOp == '<=':
            if max_sum_lower > bound:
                common.colourerror(
                    "Property does not hold! "
                    "The max weighted sum (in case of non-exact comp.: its lower bound) is > specified bound" + str(bound))
            elif max_sum_upper > bound:
                # this can only happen if we do not do exact computations
                common.colourerror(
                    "Result unknown. "
                    "The lower bound for the max weighted sum is <= specified bound" + str(bound) + " but the upper bound is > that")
            else:  # max_sum_upper <= bound
                common.colourerror(
                    "Property holds! "
                    "Max weighted sum (in case of non-exact comp.: its upper bound) <= specified bound " + str(bound))
        elif self.compOp == '<':
            if max_sum_lower >= bound:
                common.colourerror(
                    "Property does not hold! "
                    "The max weighted sum (in case of non-exact comp.: its lower bound) is >= specified bound " + str(bound))
            elif max_sum_upper >= bound:
                # this can only happen if we do not do exact computations
                common.colourerror(
                    "Result unknown. "
                    "The lower bound for the max weighted sum is < specified bound" + str(bound) + " but the upper bound is >= that")
            else:  # max_sum_upper < bound
                common.colourerror(
                    "Property holds! "
                    "Max weighted sum (in case of non-exact comp.: its upper bound) < specified bound" + str(bound))

        elif self.compOp == '>=':
            if min_sum_upper < bound:
                common.colourerror(
                    "Property does not hold! "
                    "The min weighted sum (in case of non-exact comp.: its upper bound) is < specified bound " + str(bound))

            elif min_sum_lower < bound:
                common.colourerror(
                    "Result unknown. "
                    "The upper bound for the min weighted sum is >= specified bound " + str(bound) + " but the lower bound is < that")
            else:
                common.colourerror(
                    "Property holds! "
                    "Min weighted sum (in case of non-exact comp.: its lower bound) >= specified bound " + str(bound))
        elif self.compOp == '>':
            if min_sum_upper <= bound:
                common.colourerror(
                    "Property does not hold! "
                    "The min weighted sum (in case of non-exact comp.: its upper bound) is <= specified bound " + str(bound))
            elif min_sum_lower <= bound:
                common.colourerror(
                    "Result unknown. "
                    "The upper bound for the min weighted sum is > specified bound " + str(bound) + " but the lower bound is <= that")
            else:
                common.colourerror(
                    "Property holds! "
                    "Min weighted sum (in case of non-exact comp.: its lower bound) > specified bound " + str(bound))

        elif self.compOp == '=':
            if max_sum_lower > bound_upper:
                common.colourerror(
                    "Property does not hold! "
                    "The max weighted sum (in case of non-exact comp.: its lower bound) is > specified bound + epsilon " + str(bound_upper))
            elif max_sum_upper > bound_upper:
                # this can only happen for non-exact computation
                common.colourerror(
                    "Result unknown. "
                    "The lower bound of the max weighted sum is <= specified bound + epsilon " + str(bound_upper) + " but the upper bound is > that")
            elif min_sum_upper < bound_lower:
                common.colourerror(
                    "Property does not hold! "
                    "The min weighted sum (in case of non-exact comp.: its upper bound) is < specified bound - epsilon " + str(bound_lower))
            elif min_sum_lower < bound_lower:
                common.colourerror(
                    "Result unknown. "
                    "The upper bound of the min weighted sum is >= specified bound - epsilon " + str(bound_lower) + " but the lower bound is < that")
            else: # max_sum_upper <= bound_upper and min_sum_lower >= bound_lower:
                common.colourerror(
                    "Property holds! "
                    "Max weighted sum (in case of non-exact comp.: its upper bound) is <= specified bound + epsilon " + str(bound_upper) +
                    " and min weighted sum (in case of non-exact comp.: its lower bound) is >= specified bound - epsilon " + str(bound_lower))

        elif self.compOp == '!=':
            if max_sum_upper < bound_lower:
                common.colourerror(
                    "Property holds! "
                    "Max weighted sum (in case of non-exact comp.: its upper bound) is < specified bound - epsilon " + str(bound_lower))
            elif min_sum_lower > bound_upper:
                common.colourerror(
                    "Property holds! "
                    "Min weighted sum (in case of non-exact comp.: its lower bound) is > specified bound + epsilon " + str(bound_upper))
            # now max_sum_upper >= bound_lower and min_sum_lower <= bound_upper so either No or inconclusive
            elif max_sum_lower < bound_lower:
                common.colourerror(
                    "Result unknown. "
                    "The upper bound of the max weighted sum is >= specified bound - epsilon " + str(bound_lower) + " but the lower bound is <")
            elif min_sum_upper > bound_upper:
                common.colourerror(
                    "Result unknown. "
                    "The lower bound of the min weighted sum is <= specified bound + epsilon " + str(bound_upper) + " but the upper bound is >")
            else:
                common.colourerror(
                    "Property does not hold! "
                    "Max weighted sum (in case of non-exact comp.: its lower bound) is >= specified bound - epsilon " + str(bound_lower) +
                    " and min weighted sum (in case of non-exact comp.: its upper bound) is <= specified bound + epsilon " + str(bound_upper) +
                    " and hence there must exist witnesses achieving a value in [" + str(bound_lower) + "," + str(bound_upper) + "]")

    def modelCheckOld(self):
        target_a = self.targets[0]
        target_b = self.targets[1]

        bound = self.coeff[-1]  # if we add coeff for the summands: self.coeff[2]
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
                print("< <= = !=")
                if self.exact:
                    env.solver_environment.set_force_exact()
                    env.solver_environment.set_linear_equation_solver_type(stormpy.EquationSolverType.eigen)
                    env.solver_environment.minmax_solver_environment.method = stormpy.MinMaxMethod.policy_iteration
                    res, _, sched = stormpy.compute_rel_reach_helper_exact(env, self.model,
                                                                           properties_a_minus_b[0].raw_formula,
                                                                           computeScheduler=self.witness)
                    # res, resOver, sched = stormpy.compute_rel_reach_helper_exact(env, self.model, list(self.model.labeling.get_states("init1"))[0], properties_a_minus_b[0].raw_formula, [Rational(1), Rational(-1)], self.witness)
                    # todo , extract_scheduler=self.witness
                    if self.witness:
                        scheds_max = [sched]
                    res_lower, res_upper = res, res
                    # Unexpected error encountered: Unable to convert function return value to a Python type! The signature was
                    # 	(env: stormpy.core.Environment, model: storm::models::sparse::Mdp<__gmp_expr<__mpq_struct [1], __mpq_struct [1]>, storm::models::sparse::StandardRewardModel<__gmp_expr<__mpq_struct [1], __mpq_struct [1]> > >, formula: storm::logic::MultiObjectiveFormula) -> Tuple[__gmp_expr<__mpq_struct [1], __mpq_struct [1]>, __gmp_expr<__mpq_struct [1], __mpq_struct [1]>]
                else:
                    res, resOver, sched = stormpy.compute_rel_reach_helper(env, self.model,
                                                                           properties_a_minus_b[0].raw_formula,
                                                                           self.witness)
                    # todo adjust new relreachhelper
                    # res, resOver, sched = stormpy.compute_rel_reach_helper(env, self.model, list(self.model.labeling.get_states("init1"))[0], properties_a_minus_b[0].raw_formula, [1,-1], self.witness)
                    print(res)
                    print(resOver)
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
                        common.colourerror(
                            "Maximizing witness schedulers written to files")  # todo possibly for goal unfolding
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
                        common.colourerror(
                            "Maximizing witness schedulers written to files")  # todo possibly for goal unfolding
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
                    if self.witness:
                        scheds_min = [res_a.scheduler, res_b.scheduler]
                    min_diff_upper, min_diff_lower = min_a_under - max_b_over, min_a_over - max_b_under

            else:  # not make_copies
                # calculate min {P(F a) - P(F b)} by computing - max {P(F b) - P(F a)}
                formula_b_minus_a = "multi(Pmax=?  [F \"" + target_b + "\"], Pmax=?  [F \"" + target_a + "\"])"
                properties_b_minus_a = stormpy.parse_properties(formula_b_minus_a)
                env = stormpy.Environment()  # standard precision is 0.000001
                # env.solver_environment.set_force_sound()
                print("> >= = !=")
                if self.exact:
                    env.solver_environment.set_force_exact()
                    env.solver_environment.set_linear_equation_solver_type(stormpy.EquationSolverType.eigen)
                    env.solver_environment.minmax_solver_environment.method = stormpy.MinMaxMethod.policy_iteration
                    res, _, sched = stormpy.compute_rel_reach_helper_exact(env, self.model,
                                                                           properties_b_minus_a[0].raw_formula,
                                                                           self.witness)
                    # res, resOver, sched = stormpy.compute_rel_reach_helper_exact(env, self.model, list(self.model.labeling.get_states("init1"))[0], properties_b_minus_a[0].raw_formula, [Rational(1), Rational(-1)],self.witness)
                    # todo extract schedulers
                    if self.witness:
                        scheds_min = [sched]
                    res_lower, res_upper = res, res
                else:
                    res, resOver, sched = stormpy.compute_rel_reach_helper(env, self.model,
                                                                           properties_a_minus_b[0].raw_formula,
                                                                           self.witness)
                    # todo adjust new relreachhelper
                    # res, resOver, sched = stormpy.compute_rel_reach_helper(env, self.model, list(self.model.labeling.get_states("init1"))[0], properties_b_minus_a[0].raw_formula, [1.0, -1.0], self.witness)
                    print(res)
                    print(resOver)
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
                        common.colourerror(
                            "Minimizing witness schedulers written to files")  # todo possibly for goal unfolding

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
                        common.colourerror(
                            "Minimizing witness schedulers written to files")  # todo possibly for goal unfolding

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
                            lambda_witness = (bound - v_max) / (v_min - v_max)
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
                            common.colourerror(
                                "Counterexample witness schedulers are the convex combination of min and max schedulers w.r.t. lambda=" + str(
                                    lambda_witness))
                        end_witness_time = time.perf_counter()
                        common.colourinfo("Writing witness files took: " + str(
                            round(end_witness_time - start_witness_time, 2)) + " seconds", True)
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
