import stormpy
from relreach.utility import common
from pycarl.gmp.gmp import Rational

from contextlib import redirect_stdout
import datetime
import os


class ModelChecker:
    def __init__(self, model, ind_dict, targets, compOp, coeff, exact, epsilon, witness, log_dir):
        self.model = model
        self.ind_dict = ind_dict
        self.targets = targets
        self.compOp = compOp
        self.coeff = coeff
        self.exact = exact
        self.epsilon = epsilon
        self.witness = witness
        self.log_dir = log_dir

    def store_witness(self, witness_dict, opt_string):
        common.colourinfo(f"{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")}: Storing {opt_string} witness schedulers...", False)
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        for comb, (witness, res_weighted) in witness_dict.items():
            file_name = f'{self.log_dir}/scheduler_{opt_string}_{comb}.txt'
            with open(file_name, 'w') as f:
                with redirect_stdout(f):
                    print(f"Witness for achieving value {res_weighted} for the weighted sum for state-sched combination {comb}")
                    if len(self.ind_dict[comb]) > 1:
                        print(f"Scheduler is defined on the goal unfolding wrt state-sched combination {comb}")
                    print(witness)

    # computing optimal values (as specified in formula) for a state-scheduler combination c with |relInd(c)|=1
    def modelCheckSingle(self, formula, state, schedind, rel_coeff, res_dict, witness_dict):
        properties = stormpy.parse_properties(formula)
        env = stormpy.Environment()

        if self.exact:
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

        if self.exact:
            res_weighted = Rational(rel_coeff) * res_at_state
            res_dict[(state, schedind)] = res_weighted
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

        if self.witness:
            witness_dict[(state, schedind)] = (res.scheduler, res_weighted)

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
                                                                                  [Rational(r) for r in rel_coeffs],
                                                                                  # weightVector
                                                                                  self.witness)
            res_dict[(state, schedind)] = res_weighted  # helper already did the weighting
        else:
            res_weighted, _, sched = stormpy.compute_rel_reach_helper(env,
                                                                      self.model,
                                                                      state,
                                                                      properties[0].raw_formula,
                                                                      rel_coeffs,  # weightVector
                                                                      self.witness)
            # StandardPcaaWeightVectorChecker currently returns res := (lower + upper)/2 for both under- and over-Approx
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

        if self.witness:
            witness_dict[(state, schedind)] = (sched, res_weighted)

        return res_dict, witness_dict

    # Main model-checking function
    def modelCheck(self):
        # Step 3: compute min and/or max for each state-scheduler combination
        # for each key, we store: if exact: single exact result, else tuples consisting of lower and upper bound
        common.colourinfo(f"{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")}: Computing min and/or max weighted sum for each state-scheduler combination...")
        res_min_dict = {k: [] for k in self.ind_dict.keys()}  # todo change to list?
        res_max_dict = {k: [] for k in self.ind_dict.keys()}
        if self.witness:
            witness_min_dict = {k: [] for k in self.ind_dict.keys()}
            witness_max_dict = {k: [] for k in self.ind_dict.keys()}
        else:
            witness_min_dict = None
            witness_max_dict = None

        for (state, schedind) in self.ind_dict.keys():
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

                    res_max_dict, witness_max_dict = self.modelCheckSingle(formula, state, schedind, rel_coeff,
                                                                           res_max_dict, witness_max_dict)

                else:
                    # we need to use multi-objective model-checking
                    rel_targets = [self.targets[i - 1] for i in rel_ind]
                    rel_coeffs = [self.coeff[i - 1] for i in rel_ind]

                    # compute_rel_reach_helper takes care of correct weighting with weightVector=rel_coeffs and optimizing in correct direction
                    formula_interm = "multi("
                    for target in rel_targets:
                        formula_interm += "Pmax=?  [F \"" + target + "\"], "
                    formula = formula_interm[:-2] + ")"

                    res_max_dict, witness_max_dict = self.modelCheckMulti(formula, state, schedind, rel_coeffs,
                                                                          res_max_dict, witness_max_dict)

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
        common.colourinfo(f"{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")}: Aggregating results and comparing with bound...")
        # Compute the sum(s)
        if self.compOp in ['<=', '<', '=', '!=']:
            max_sum_list = list(res_max_dict.values())
            if self.exact:
                max_sum = sum(max_sum_list)
                max_sum_lower, max_sum_upper = max_sum, max_sum
                common.colourinfo("Max weighted sum: " + str(max_sum), False)
            else:
                max_sum_lower = sum([l for (l, _) in max_sum_list])
                max_sum_upper = sum([u for (_, u) in max_sum_list])
                common.colourinfo("Lower bound for max weighted sum: " + str(max_sum_lower), False)
                common.colourinfo("Upper bound for max weighted sum: " + str(max_sum_upper), False)
            if self.witness:
                max_sum_approx = sum([approx_res for (_, approx_res) in witness_max_dict.values()])
        if self.compOp in ['>=', '>', '=', '!=']:
            min_sum_list = list(res_min_dict.values())
            if self.exact:
                min_sum = sum(min_sum_list)
                min_sum_lower, min_sum_upper = min_sum, min_sum
                common.colourinfo("Min weighted sum: " + str(min_sum), False)
            else:
                min_sum_lower = sum([l for (l, _) in min_sum_list])
                min_sum_upper = sum([u for (_, u) in min_sum_list])
                common.colourinfo("Lower bound for min weighted sum: " + str(min_sum_lower), False)
                common.colourinfo("Upper bound for min weighted sum: " + str(min_sum_upper), False)
            if self.witness:
                min_sum_approx = sum([approx_res for (_, approx_res) in witness_min_dict.values()])

        # Compare sum(s) to bound, output result with brief explanation and store witnesses if desired
        if self.exact:
            bound = Rational(self.coeff[-1])
            bound_upper = bound + Rational(self.epsilon)
            bound_lower = bound - Rational(self.epsilon)
        else:
            bound = self.coeff[-1]
            bound_upper = bound + self.epsilon
            bound_lower = bound - self.epsilon
        bound_upper_str = str(float(bound_upper)) + " (specified bound + epsilon)"
        bound_lower_str = str(float(bound_lower)) + " (specified bound - epsilon)"

        if self.compOp == '<=':
            if max_sum_lower > bound:
                common.colourinfo(
                    "Property does not hold! "
                    "The max weighted sum (in case of non-exact comp.: its lower bound) is > specified bound " + str(
                        bound))
                if self.witness:
                    self.store_witness(witness_max_dict, "max")
                    common.colourinfo("Maximizing schedulers written to " + self.log_dir, False)

            elif max_sum_upper > bound:
                # this can only happen if we do not do exact computations
                common.colourinfo(
                    "Result unknown. "
                    "The lower bound for the max weighted sum is <= specified bound " + str(
                        bound) + " but the upper bound is > that")
            else:  # max_sum_upper <= bound
                common.colourinfo(
                    "Property holds! "
                    "Max weighted sum (in case of non-exact comp.: its upper bound) <= specified bound " + str(bound))

        elif self.compOp == '<':
            if max_sum_lower >= bound:
                common.colourinfo(
                    "Property does not hold! "
                    "The max weighted sum (in case of non-exact comp.: its lower bound) is >= specified bound " + str(
                        bound))
                if self.witness:
                    self.store_witness(witness_max_dict, "max")
                    common.colourinfo("Maximizing schedulers written to " + self.log_dir, False)

            elif max_sum_upper >= bound:
                # this can only happen if we do not do exact computations
                common.colourinfo(
                    "Result unknown. "
                    "The lower bound for the max weighted sum is < specified bound " + str(
                        bound) + " but the upper bound is >= that")
            else:  # max_sum_upper < bound
                common.colourinfo(
                    "Property holds! "
                    "Max weighted sum (in case of non-exact comp.: its upper bound) < specified bound " + str(bound))

        elif self.compOp == '>=':
            if min_sum_upper < bound:
                common.colourinfo(
                    "Property does not hold! "
                    "The min weighted sum (in case of non-exact comp.: its upper bound) is < specified bound " + str(
                        bound))
                if self.witness:
                    self.store_witness(witness_min_dict, "min")
                    common.colourinfo("Minimizing schedulers written to " + self.log_dir, False)
            elif min_sum_lower < bound:
                common.colourinfo(
                    "Result unknown. "
                    "The upper bound for the min weighted sum is >= specified bound " + str(
                        bound) + " but the lower bound is < that")
            else:
                common.colourinfo(
                    "Property holds! "
                    "Min weighted sum (in case of non-exact comp.: its lower bound) >= specified bound " + str(bound))

        elif self.compOp == '>':
            if min_sum_upper <= bound:
                common.colourinfo(
                    "Property does not hold! "
                    "The min weighted sum (in case of non-exact comp.: its upper bound) is <= specified bound " + str(
                        bound))
                if self.witness:
                    self.store_witness(witness_min_dict, "min")
                    common.colourinfo("Minimizing schedulers written to " + self.log_dir, False)
            elif min_sum_lower <= bound:
                common.colourinfo(
                    "Result unknown. "
                    "The upper bound for the min weighted sum is > specified bound " + str(
                        bound) + " but the lower bound is <= that")
            else:
                common.colourinfo(
                    "Property holds! "
                    "Min weighted sum (in case of non-exact comp.: its lower bound) > specified bound " + str(bound))

        elif self.compOp == '=':
            if max_sum_lower > bound_upper:
                common.colourinfo(
                    "Property does not hold! "
                    "The max weighted sum (in case of non-exact comp.: its lower bound) is > " + bound_upper_str)
                if self.witness:
                    self.store_witness(witness_max_dict, "max")
                    common.colourinfo("Maximizing schedulers written to " + self.log_dir, False)
            elif max_sum_upper > bound_upper:
                # this can only happen for non-exact computation
                common.colourinfo(
                    "Result unknown. "
                    "The lower bound of the max weighted sum is <= " + bound_upper_str + " but the upper bound is > that")
            elif min_sum_upper < bound_lower:
                common.colourinfo(
                    "Property does not hold! "
                    "The min weighted sum (in case of non-exact comp.: its upper bound) is < " + bound_lower_str)
                if self.witness:
                    self.store_witness(witness_min_dict, "min")
                    common.colourinfo("Minimizing schedulers written to " + self.log_dir, False)
            elif min_sum_lower < bound_lower:
                common.colourinfo(
                    "Result unknown. "
                    "The upper bound of the min weighted sum is >= " + bound_lower_str + " but the lower bound is < that")
            else:  # max_sum_upper <= bound_upper and min_sum_lower >= bound_lower:
                common.colourinfo(
                    "Property holds! "
                    "Max weighted sum (in case of non-exact comp.: its upper bound) is <= " + bound_upper_str +
                    " and min weighted sum (in case of non-exact comp.: its lower bound) is >= " + bound_lower_str)

        elif self.compOp == '!=':
            if max_sum_upper < bound_lower:
                common.colourinfo(
                    "Property holds! "
                    "Max weighted sum (in case of non-exact comp.: its upper bound) is < " + bound_lower_str)
            elif min_sum_lower > bound_upper:
                common.colourinfo(
                    "Property holds! "
                    "Min weighted sum (in case of non-exact comp.: its lower bound) is > " + bound_upper_str)
            # now max_sum_upper >= bound_lower and min_sum_lower <= bound_upper so either No or inconclusive
            elif max_sum_lower < bound_lower:
                common.colourinfo(
                    "Result unknown. "
                    "The upper bound of the max weighted sum is >= " + bound_lower_str + " but the lower bound is <")
            elif min_sum_upper > bound_upper:
                common.colourinfo(
                    "Result unknown. "
                    "The lower bound of the min weighted sum is <= " + bound_upper_str + " but the upper bound is >")
            else:
                common.colourinfo("Property does not hold! ")
                common.colourinfo(
                    "Max weighted sum (in case of non-exact comp.: its lower bound) is >= " + bound_lower_str +
                    " and min weighted sum (in case of non-exact comp.: its upper bound) is <= " + bound_upper_str, False)
                common.colourinfo(
                    "Hence there must exist witness schedulers achieving a value in [" + str(
                        float(bound_lower)) + ", " + str(float(bound_upper)) + "] for the weighted sum", False)
                if self.witness:
                    lambda_witness = (bound - max_sum_approx) / (min_sum_approx - max_sum_approx)
                    common.colourinfo(
                        "Counterexample witness schedulers are given by the convex combination of maximizing and minimizing schedulers "
                        "w.r.t. lambda=" + str(lambda_witness))
                    self.store_witness(witness_max_dict, "max")
                    self.store_witness(witness_min_dict, "min")
                    common.colourinfo("Maximizing and minimizing schedulers written to " + self.log_dir, False)
