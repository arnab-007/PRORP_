import os
import sys
import json
import pandas as pd
import re
import pprint
from itertools import product
PATH = os.path.realpath("")
# Get the parent directory path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, parent_dir)
PARENT_PATH = os.path.dirname(parent_dir)
assumed_shape = " "


def log_error(
    message: str,
    error_dict: dict = None,
    file_path: str = f"{PARENT_PATH}/logs/terror_logging.txt",
):
    with open(file_path, "a") as f:
        f.write(message + "\n")
        if error_dict is not None:
            pp = pprint.PrettyPrinter(indent=4, width=80, stream=f)
            pp.pprint(error_dict)



from collections import defaultdict
import itertools

def summarize_dnf(dnf, progvars, var_bit_map, use_latex=False):
    """
    Summarizes a DNF string into a compact, human-readable representation.

    This single function encapsulates all the necessary logic for parsing,
    enumerating witnesses, finding patterns (intervals, modular congruences, etc.),
    and grouping the results into a final, readable summary.

    Args:
        dnf (str): The Disjunctive Normal Form formula as a string.
        progvars (list): A list of the program variable names (e.g., ["a", "b"]).
        var_bit_map (dict): A dictionary mapping program variables to their
                            constituent bit names.
        use_latex (bool): If True, formats the output using LaTeX.

    Returns:
        list: A list of strings, where each string is a compact summary
              of a group of satisfying assignments.
    """

    # === Nested Helper Functions ===

    def parse_clause(clause):
        lit_dict = {}
        for lit in clause.strip().split("&&"):
            lit = lit.strip().lstrip('(').rstrip(')')
            if lit.startswith("!"):
                lit_dict[lit[1:]] = 0
            else:
                lit_dict[lit] = 1
        return lit_dict

    def eval_bitvector_values(bits, lit_dict):
        vals = set()
        relevant_lit_dict = {k: v for k, v in lit_dict.items() if k in bits}
        constrained_indices = {i for i, bit in enumerate(bits) if bit in relevant_lit_dict}
        num_unconstrained = len(bits) - len(constrained_indices)
        fixed_val = 0
        for i, bit in enumerate(bits):
            if i in constrained_indices:
                bit_val = relevant_lit_dict[bit]
                fixed_val |= bit_val << (len(bits) - 1 - i)

        if num_unconstrained > 16:
            return None

        for i in range(1 << num_unconstrained):
            current_val = fixed_val
            temp_i = i
            for k, bit_name in reversed(list(enumerate(bits))):
                if k not in constrained_indices:
                    current_val |= (temp_i & 1) << (len(bits) - 1 - k)
                    temp_i >>= 1
            vals.add(current_val)
        return vals

    def _find_disjoint_intervals(values):
        if not values:
            return []
        intervals = []
        start = values[0]
        for i in range(1, len(values)):
            if values[i] != values[i-1] + 1:
                intervals.append((start, values[i-1]))
                start = values[i]
        intervals.append((start, values[-1]))
        return intervals

    def summarize_as_disjoint_intervals(var, values, use_latex=False):
        intervals = _find_disjoint_intervals(values)
        if all(s == e for s, e in intervals):
            if len(intervals) > 8: return None
            vals_str = ", ".join(str(s) for s, e in intervals)
            return f"{var} \\in \\{{{vals_str}\\}}" if use_latex else f"{var} in {{{vals_str}}}"

        if not 1 <= len(intervals) <= 8: return None
        union_symbol = " \\cup " if use_latex else " U "
        interval_strs = [f"[{s}, {e + 1})" for s, e in intervals]
        return f"{var} \\in {union_symbol.join(interval_strs)}" if use_latex else f"{var} in {union_symbol.join(interval_strs)}"

    def summarize_as_bitmask_pattern(var, bits, lit_dict, use_latex=False):
        relevant_lit_dict = {k: v for k, v in lit_dict.items() if k in bits}
        if not relevant_lit_dict: return f"{var} is unconstrained"
        
        if len(bits) == 1 and bits[0] in relevant_lit_dict:
            return f"{var} = {relevant_lit_dict[bits[0]]}"

        highest_constrained_pos = -1
        for i, bit_name in enumerate(reversed(bits)):
            if bit_name in relevant_lit_dict:
                highest_constrained_pos = i
        
        if highest_constrained_pos == -1: return None

        modulus = 1 << (highest_constrained_pos + 1)
        lower_bits = bits[-(highest_constrained_pos+1):]
        remainders = eval_bitvector_values(lower_bits, relevant_lit_dict)

        if remainders is None or len(remainders) > 32: return None

        summary = summarize_as_arithmetic_progression(f"{var} mod {modulus}", sorted(list(remainders)), use_latex)
        if not summary:
            summary = summarize_as_disjoint_intervals(f"{var} mod {modulus}", sorted(list(remainders)), use_latex)
        if not summary:
            remainders_str = ", ".join(map(str, sorted(list(remainders))))
            summary = f"{var} \\pmod{{{modulus}}} \\in \\{{{remainders_str}\\}}" if use_latex else f"{var} mod {modulus} in {{{remainders_str}}}"
        return summary
        
    def summarize_as_modular_congruence(var, values, use_latex=False):
        intervals = _find_disjoint_intervals(values)
        if len(intervals) < 3: return None
        expected_len = intervals[0][1] - intervals[0][0]
        expected_stride = intervals[1][0] - intervals[0][0]
        if expected_stride <= expected_len: return None
        for i in range(1, len(intervals)):
            if (intervals[i][1] - intervals[i][0]) != expected_len or (intervals[i][0] - intervals[i-1][0]) != expected_stride:
                return None
        modulus = expected_stride
        start, end = intervals[0][0], intervals[0][1]
        return f"{var} \\pmod{{{modulus}}} \\in [{start}, {end + 1})" if use_latex else f"{var} mod {modulus} in [{start}, {end + 1})"

    def summarize_as_modular_set_congruence(var, values, use_latex=False):
        if len(values) < 4: return None
        diffs = [b - a for a, b in zip(values, values[1:])]
        if not diffs: return None
        period = -1
        for p in range(1, min(len(diffs) // 2, 10) + 1):
            if diffs[:p] == diffs[p:2*p]:
                period = p
                break
        if period == -1: return None
        modulus = sum(diffs[:period])
        if modulus <= 1: return None
        remainders = set(v % modulus for v in values)
        if 1 < len(remainders) <= 8:
            reconstructed = set()
            min_k, max_k = values[0] // modulus, values[-1] // modulus
            for k in range(min_k, max_k + 2):
                for r in remainders:
                    val = k * modulus + r
                    if val >= values[0] and val <= values[-1]:
                        reconstructed.add(val)
            if set(values) == reconstructed:
                remainders_str = ", ".join(map(str, sorted(list(remainders))))
                return f"{var} \\pmod{{{modulus}}} \\in \\{{{remainders_str}\\}}" if use_latex else f"{var} mod {modulus} in {{{remainders_str}}}"
        return None

    def summarize_as_arithmetic_progression(var, values, use_latex=False):
        if len(values) < 3: return None
        diffs = {b - a for a, b in zip(values, values[1:])}
        if len(diffs) == 1:
            step = diffs.pop()
            if step <= 1: return None
            start, end = values[0], values[-1]
            if (end - start) % step != 0 or len(values) != ((end - start) // step + 1): return None
            k_end = (end - start) // step
            return f"{var} = {start} + {step}k \\text{{ for }} k \\in [0, {k_end}]" if use_latex else f"{var} = {start} + {step}·k for k = 0 to {k_end}"
        return None

    def enumerate_all_witnesses(dnf_str, progvars_list, var_map):
        all_witnesses = set()
        for clause_str in dnf_str.split("||"):
            if not clause_str.strip(): continue
            lit_dict = parse_clause(clause_str)
            per_var_vals = []
            for pv in progvars_list:
                vals = eval_bitvector_values(var_map.get(pv, []), lit_dict)
                if vals is None: return set()
                per_var_vals.append(sorted(list(vals)))
            for combo in itertools.product(*per_var_vals):
                witness = dict(zip(progvars_list, combo))
                all_witnesses.add(frozenset(witness.items()))
        return all_witnesses
        
    # === Main Logic ===

    clauses = [c.strip() for c in dnf.split("||") if c.strip()]
    
    if len(clauses) == 1:
        lit_dict = parse_clause(clauses[0])
        summaries = []
        for var in sorted(progvars):
            bits = var_bit_map.get(var, [])
            s = summarize_as_bitmask_pattern(var, bits, lit_dict, use_latex)
            if not s:
                vals = eval_bitvector_values(bits, lit_dict)
                if vals is None:
                    s = f"{var} has too many values to summarize"
                else:
                    vals = sorted(list(vals))
                    s = summarize_as_disjoint_intervals(var, vals, use_latex)
                    if not s: s = summarize_as_modular_congruence(var, vals, use_latex)
                    if not s: s = summarize_as_modular_set_congruence(var, vals, use_latex)
                    if not s: s = summarize_as_arithmetic_progression(var, vals, use_latex)
                    if not s:
                        s = f"{var} = {vals[0]}" if len(vals) == 1 else f"{var} has {len(vals)} possible values"
            summaries.append(s)
        return [", ".join(summaries)]

    all_witnesses = enumerate_all_witnesses(dnf, progvars, var_bit_map)
    if not all_witnesses:
        return ["No satisfying assignments found."]

    covered_witnesses = set()
    final_summaries = []

    while len(covered_witnesses) < len(all_witnesses):
        best_group, best_score = None, (-1, -1)
        uncovered_witnesses = [w for w in all_witnesses if w not in covered_witnesses]

        for r in range(len(progvars), -1, -1):
            for subset_of_vars in itertools.combinations(progvars, r):
                groups = defaultdict(list)
                for witness_fset in uncovered_witnesses:
                    witness_dict = dict(witness_fset)
                    key = tuple(sorted([(v, witness_dict[v]) for v in subset_of_vars]))
                    groups[key].append(witness_fset)
                for key, witnesses_in_group in groups.items():
                    score = (len(witnesses_in_group), r)
                    if score > best_score:
                        best_score = score
                        best_group = {"key": key, "witnesses": witnesses_in_group, "fixed_vars": subset_of_vars}
        
        if not best_group: break
            
        fixed_part_str = ", ".join(f"{v} = {val}" for v, val in best_group["key"])
        varying_vars = sorted([v for v in progvars if v not in best_group["fixed_vars"]])
        
        summary = fixed_part_str
        if varying_vars:
            varying_tuples = sorted({tuple(dict(w)[v] for v in varying_vars) for w in best_group["witnesses"]})
            projections = [sorted(list(set(t[i] for t in varying_tuples))) for i, var in enumerate(varying_vars)]
            
            is_independent = True
            if varying_vars:
                expected_size = 1
                for p in projections: expected_size *= len(p)
                if len(varying_tuples) != expected_size: is_independent = False

            if is_independent:
                summaries = []
                for i, var in enumerate(varying_vars):
                    vals = projections[i]
                    s = summarize_as_disjoint_intervals(var, vals, use_latex)
                    if not s: s = summarize_as_modular_congruence(var, vals, use_latex)
                    if not s: s = summarize_as_modular_set_congruence(var, vals, use_latex)
                    if not s: s = summarize_as_arithmetic_progression(var, vals, use_latex)
                    if not s:
                        vals_str = ", ".join(map(str, vals))
                        s = f"{var} in {{{vals_str}}}" if not use_latex else f"{var} \\in \\{{{vals_str}\\}}"
                    summaries.append(s)
                varying_summary = ", ".join(summaries)
            else:
                tup_strs = [f"({','.join(map(str, t))})" for t in varying_tuples]
                all_tups_str = ", ".join(tup_strs)
                var_list_str = ",".join(varying_vars)
                varying_summary = f"({var_list_str}) \\in \\{{{all_tups_str}\\}}" if use_latex else f"({var_list_str}) ∈ {{{all_tups_str}}}"

            summary = f"{fixed_part_str}, {varying_summary}" if fixed_part_str else varying_summary

        final_summaries.append(summary)
        for witness_fset in best_group["witnesses"]:
            covered_witnesses.add(witness_fset)

    plain_summary = sorted(final_summaries)
    return "\n".join(plain_summary)


def nnf_to_dimacs(cnf_formula, variable_mapping):
    dimacs = []
    for clause in cnf_formula:
        dimacs_clause = []
        for literal in clause:
            literal = literal.strip()
            if literal.startswith("!"):
                dimacs_clause.append(-variable_mapping[literal[1:].strip()])
            else:
                dimacs_clause.append(variable_mapping[literal.strip()])

        dimacs.append(dimacs_clause)
    return dimacs


def analyze_candidate(dnf_string):
    # Step 1: Split the DNF into clauses using '||'
    clauses = re.split(r'\s*\|\|\s*', dnf_string.strip())

    # Step 2: For each clause, split by '&&' and count the literals
    literal_counts = []
    for clause in clauses:
        # Strip outer parentheses, then split by &&
        clause = clause.strip()
        if clause.startswith('(') and clause.endswith(')'):
            clause = clause[1:-1]
        literals = [lit.strip() for lit in clause.split('&&') if lit.strip()]
        literal_counts.append(len(literals))

    # Step 3: Compute max and total clause count
    max_literals = max(literal_counts)
    num_clauses = len(clauses)

    return num_clauses, max_literals


def get_verified_error_bounds(df, cand):

    prog_variables = df.columns[:-3].tolist()
    dataset, weights, labels = (
        df.iloc[:, :-3].values.tolist(),
        df.iloc[:, -2].values.tolist(),
        df.iloc[:, -3].values.tolist(),
    )
    cand_list = [
        list(filter(None, term.strip("() ").split("&&"))) for term in cand.split("||")
    ]
    forward_var_map = {var: idx + 1 for idx, var in enumerate(prog_variables)}
    dimacs_cand_dnf = nnf_to_dimacs(cand_list, forward_var_map)

    entry_satisfies_dnf = list()
    for entry in dataset:
        # A DNF is satisfied if ANY of its clauses (AND-terms) are satisfied
        flag = any(
            all(
                (entry[abs(lit) - 1] == 1 if lit > 0 else entry[abs(lit) - 1] == 0)
                for lit in dnf_term
            )
            for dnf_term in dimacs_cand_dnf
        )
        entry_satisfies_dnf.append(int(flag))

        #print(entry_satisfies_dnf)

    valid_error = sum(
        w for w, a, b in zip(weights, entry_satisfies_dnf, labels) if a == 1 and b == 0
    )
    dist_error = sum(
        w for w, a, b in zip(weights, entry_satisfies_dnf, labels) if a == 0 and b == 1
    )

    return {"dist_error": dist_error, "valid_error": valid_error}
    

def modify_cand(dnf_string_1, cnf_string):


    # Step 1: Parse DNF
    dnf_clauses = []
    for clause in dnf_string_1.split('||'):
        clause = clause.strip().strip('()')
        dnf_clauses.append([lit.strip() for lit in clause.split('&&')])
    # Step 2: Parse CNF
    cnf_clauses = []
    for clause in cnf_string.split('&&'):
        clause = clause.strip().strip('()')
        cnf_clauses.append([lit.strip() for lit in clause.split('||')])
    # Step 3: Negate CNF to get a new DNF
    negated_clauses = []
    for clause in cnf_clauses:
        negated_clause = []
        for lit in clause:
            lit = lit.strip()
            negated_clause.append(lit[1:] if lit.startswith('!') else f'!{lit}')
        negated_clauses.append(negated_clause)

    # Step 5: Combine DNF clauses with negated CNF DNF clauses and handle contradictions
    final_clauses = []
    for dnf_clause in dnf_clauses:
        for neg_clause in negated_clauses:
            merged_clause = dnf_clause + neg_clause
            seen = set()
            contradiction = False
            cleaned_clause = []

            for lit in merged_clause:
                var = lit.lstrip('!')
                neg = lit.startswith('!')
                
                # Check for contradiction: A and !A
                if (var, not neg) in seen:
                    contradiction = True  # Found contradiction: A and !A
                    break
                if (var, neg) not in seen:
                    seen.add((var, neg))
                    cleaned_clause.append(lit)
            
            if not contradiction and cleaned_clause:
                final_clauses.append(sorted(set(cleaned_clause)))  # optional: sort for consistency
                
    # Step 6: Convert to string and output final DNF
    final_dnf_string = ' || '.join(f"({' && '.join(clause)})" for clause in final_clauses)


    return final_dnf_string

def get_config_prog(progname):
    with open(
        os.path.join(PARENT_PATH, "candidate_files", progname + ".json"), "r"
    ) as f:
        config = json.load(f)
    return config


def decimal_to_n_bit_binary(decimal, n):
    """Convert a decimal number to n-bit binary as a list of integers."""
    return list(map(int, format(decimal, f"0{n}b")))


def prepare_data(distestimate_data, validifier_data, prog_variables):
    """Convert a list of tuples into a DataFrame with binary representations, label, weight, and member."""
    records = []
    number_of_vars = len(prog_variables)
    initial_dist_dict = distestimate_data["output_dict"]["counterexamples"]
    initial_valid_dict = validifier_data["output_dict"]["counterexamples"]
    initial_dist_list = [element for element in initial_dist_dict.keys()]
    initial_valid_list = [element for element in initial_valid_dict.keys()]
    initial_dist_data = [
        (int(key), value, 1)
        for key, value in initial_dist_dict.items()
        if key in initial_dist_list
    ]
    for idx, (decimal, weight, label) in enumerate(initial_dist_data):
        var_binary = decimal_to_n_bit_binary(decimal, number_of_vars)
        records.append(var_binary + [label, weight, 1])
    columns = [prog_variables[i] for i in range(number_of_vars)] + [
        "label",
        "weight",
        "member",
    ]
    df1 = pd.DataFrame(records, columns=columns)
    records = []
    initial_valid_data = [
        (int(key), value, 0)
        for key, value in initial_valid_dict.items()
        if key in initial_valid_list
    ]
    for idx, (decimal, weight, label) in enumerate(initial_valid_data):
        var_binary = decimal_to_n_bit_binary(decimal, number_of_vars)
        records.append(var_binary + [label, weight, 0])
    columns = [prog_variables[i] for i in range(number_of_vars)] + [
        "label",
        "weight",
        "member",
    ]
    df2 = pd.DataFrame(records, columns=columns)
    dfs = [df for df in [df1, df2] if not df.empty]
    df = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
    return df


