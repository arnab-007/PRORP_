import sys
import math
import json
import argparse
import itertools
import logging
from collections import defaultdict, Counter
from multiprocessing import Pool, cpu_count
from pathlib import Path
import subprocess
from valid_utils_new import *
from to_dimacs import generate_init_DIMACS_formula
from list_from_dimacs import extract_formula_from_DIMACS
from pysat.solvers import Solver

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

CURRENT_PATH = Path(__file__).resolve().parent.parent.parent
TEMP_PATH = CURRENT_PATH / "temp"
PROGFORMULA_PATH = CURRENT_PATH / "progformula"
RESULTS_PATH = CURRENT_PATH / "src/Validifier/Validifier_results"

def init_worker(formula, output_var_dict, init_list, samples_freq):
    """Initializer for worker processes — load CNF into solver once."""
    global global_solver, output_var_dict_global, init_list_global, samples_freq_global
    global_solver = Solver(name="cd")
    global_solver.append_formula(formula)
    output_var_dict_global = output_var_dict
    init_list_global = init_list
    samples_freq_global = samples_freq

def ValidExecute_fast(args):
    """Faster validator using incremental SAT with assumptions."""
    global global_solver, output_var_dict_global, init_list_global, samples_freq_global
    dnf_formula, shifted_clause = args
    sat_res = 1 - int(global_solver.solve(assumptions=shifted_clause))
    if sat_res:
        if not is_cnf_satisfied(init_list_global, dnf_formula):
            return (dnf_formula, samples_freq_global[dnf_formula])
        return None
    return (dnf_formula, 0)

def convert_sample(line: str, reversed_var_map: dict) -> str:
    """Convert a DIMACS sample line to a readable variable assignment."""
    return " && ".join(
        f"{'!' if int(tok) < 0 else ''}{reversed_var_map.get(abs(int(tok)))}"
        for tok in line.split()
        if int(tok) != 0
    )

def load_variable_mapping(mapping_path: Path, prog_variables: list) -> dict:
    """Load and filter variable mapping."""
    with mapping_path.open() as f:
        return {k: v for k, v in json.load(f).items()
                if "_" in k and k.split("_")[0] in prog_variables}

def save_json(data: dict, result_dir: Path, progname: str):
    """Save results to a unique JSON file."""
    result_dir.mkdir(parents=True, exist_ok=True)
    idx = 1
    while (result_dir / f"exp_{progname}_{idx}.json").exists():
        idx += 1
    with (result_dir / f"exp_{progname}_{idx}.json").open("w") as f:
        json.dump(data, f, indent=4)

def main():
    import multiprocessing
    multiprocessing.set_start_method("spawn", force=True)
    import time

    parser = argparse.ArgumentParser()
    parser.add_argument("--progname", type=str, default="Geo0")
    parser.add_argument("--epsilon", type=float, default=0.05)
    parser.add_argument("--delta", type=float, default=0.1)
    parser.add_argument("--iters", type=int, default=4)
    parser.add_argument("--num_bits", type=int, default=16, dest="num_bits")
    args = parser.parse_args()

    start = time.time()
    progname, epsilon, delta, k, num_bits = args.progname, args.epsilon, args.delta, args.iters, args.num_bits
    num_samples = math.ceil(0.5 * math.log(2 / delta) / epsilon**2)

    # === Load Program Config ===
    config = get_config(progname)
    prog_variables = config["Program_variables"]["Bools"]
    cand = config["Candidate"]["Expression"]
    init_states = config["Initial states"]["Expression"]
    num_ops = config["Program specification"]["operations per line"]
    lines = config["Program specification"]["number of lines"]

    init_list = [
        list(filter(None, clause.strip("() ").split("||")))
        for clause in init_states.split("&&")
    ]
    cand_list = [
        list(filter(None, term.strip("() ").split("&&"))) for term in cand.split("||")
    ]

    forward_var_map = {var: idx + 1 for idx, var in enumerate(prog_variables)}
    reversed_var_map = {idx: var for var, idx in forward_var_map.items()}
    num_vars = len(forward_var_map)

    # Write candidate and init DNF/CNF to files
    dimacs_cand = nnf_to_dimacs(cand_list, forward_var_map)
    dimacs_init = nnf_to_dimacs(init_list, forward_var_map)
    TEMP_PATH.mkdir(exist_ok=True)
    write_dnf_dimacs_to_file(
        dimacs_cand, num_vars, len(dimacs_cand), TEMP_PATH / f"candidate_dnf_{progname}"
    )
    write_cnf_dimacs_to_file(
        dimacs_init, num_vars, len(dimacs_init), TEMP_PATH / f"input_cnf_{progname}"
    )

    # === Sampling ===
    try:
        subprocess.run(
            [
                "python3",
                str(CURRENT_PATH / "src/Validifier/dnfstream.py"),
                "--eps", str(epsilon),
                "--delta", str(delta),
                "--dosample",
                "--numsamps", str(num_samples),
                str(TEMP_PATH / f"candidate_dnf_{progname}"),
                str(TEMP_PATH / f"samples_valid_{progname}.out"),
            ],
            capture_output=True, text=True, check=True
        )
    except subprocess.CalledProcessError as e:
        logging.error("dnfstream.py failed!\nSTDOUT:\n%s\nSTDERR:\n%s", e.stdout, e.stderr)
        sys.exit(1)

    # Convert samples to readable format
    with (TEMP_PATH / f"samples_valid_{progname}.out").open() as file:
        converted_lines = [convert_sample(line, reversed_var_map) for line in file.readlines()]
    with (TEMP_PATH / f"samples_converted_{progname}.txt").open("w") as file:
        file.write("\n".join(converted_lines))

    # === Load Variable Mapping ===
    variable_mapping = load_variable_mapping(PROGFORMULA_PATH / f"{progname}_var_mapping", prog_variables)

    min_indices, max_indices = defaultdict(lambda: float("inf")), defaultdict(lambda: -1)
    for key in variable_mapping:
        prefix, idx = key.split("_")
        idx = int(idx)
        min_indices[prefix] = min(min_indices[prefix], idx)
        max_indices[prefix] = max(max_indices[prefix], idx)

    # === Generate CNF ===
    cnf_prog_formula, num_vars = extract_formula_from_DIMACS(PROGFORMULA_PATH / f"{progname}_cnf")
    k_varmap, k_flat_varmap = generate_k_step_variable_mapping(variable_mapping, k, lines, num_vars)
    output_vars, _ = get_last_and_transformed_vars(k_varmap[0], 0)
    output_var_dict = {var: k_flat_varmap[var] for var in output_vars}
    reverse_map = {key: f"{key}_{max_indices[key]}" for key in max_indices}

    eq_clauses = generate_equivalence_clauses(k_flat_varmap, k_varmap, k, lines)
    cnf_init, _ = generate_init_DIMACS_formula(init_states, variable_mapping, min_indices)

    prog_k_steps = [cnf_prog_formula]
    for _ in range(k - 1):
        prog_k_steps.append(translate_formula(prog_k_steps[-1], num_vars))
    k_step_formula = list(itertools.chain.from_iterable(prog_k_steps))
    k_step_prog_formula = k_step_formula + eq_clauses
    reachability_formula = cnf_init + k_step_prog_formula

    # === Load Samples ===
    with (TEMP_PATH / f"samples_converted_{progname}.txt").open() as f:
        sampled_states = [line.strip() for line in f.readlines()]
    sample_freq = dict(Counter(sampled_states))
    sampled_states_decimal = list(set(convert_to_decimal(prog_variables, s) for s in sampled_states))
    sampled_states_dict = {convert_to_decimal(prog_variables, s): sample_freq[s] for s in sampled_states}

    # === Precompute shifted clauses ===
    shifted_clauses_map = {}
    for dnf in sample_freq:
        clause = generate_clause(dnf, reverse_map, output_var_dict)
        shifted_clause = [
            lit[0] + (k - 1) * num_vars if lit[0] > 0 else lit[0] - (k - 1) * num_vars
            for lit in clause
        ]
        shifted_clauses_map[dnf] = shifted_clause

    args_list = [(dnf, shifted_clauses_map[dnf]) for dnf in sample_freq]

    # === Parallel validation with incremental solver ===
    with Pool(
        processes=min(int(0.7 * cpu_count()), 20),
        initializer=init_worker,
        initargs=(reachability_formula, output_var_dict, init_list, sample_freq)
    ) as pool:
        results = pool.map(ValidExecute_fast, args_list)

    # === Compute results ===
    individual_dist = [res[1] for res in results if res and res[1]]
    estimated_dist = sum(individual_dist) / sum(sample_freq.values()) if sample_freq else 0.0

    counterexamples = [res[0] for res in results if res and res[1] > 0]
    counterexample_states = [convert_to_decimal(prog_variables, state) for state in counterexamples]
    unique_cex_states = list(set(counterexample_states))
    cex_dict = {state: sampled_states_dict[state] / num_samples for state in unique_cex_states}

    # === Save output ===
    result_data = {
        "input_dict": {
            "progname": progname,
            "candidate": cand,
            "init_states": init_states,
            "iterations": k,
        },
        "parameters_dict": {
            "epsilon": epsilon,
            "delta": delta,
            "t": len(sampled_states),
        },
        "output_dict": {
            "Sampled output states": sampled_states_decimal,
            "Validifier_value": estimated_dist,
            "counterexamples": cex_dict,
        },
    }
    save_json(result_data, RESULTS_PATH, progname)

    end = time.time()
    logging.info("Time taken (in seconds): %.2f", end - start)
    logging.info("Validifier outputs: %s", estimated_dist)

if __name__ == "__main__":
    main()




# # === Imports ===
# import os
# import sys
# import math
# import json
# import argparse
# import itertools
# from collections import defaultdict, Counter
# from multiprocessing import Pool, cpu_count
# import subprocess
# from valid_utils_new import *
# from to_dimacs import generate_init_DIMACS_formula
# from list_from_dimacs import extract_formula_from_DIMACS
# from pysat.solvers import Solver


# CURRENT_PATH = os.path.realpath("")
# PARENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
# sys.path.insert(0, PARENT_DIR)

# # === Globals for workers ===
# global_solver = None
# output_var_dict_global = None
# init_list_global = None
# samples_freq_global = None

# def init_worker(formula, output_var_dict, init_list, samples_freq):
#     """Initializer for worker processes — load CNF into solver once."""
#     global global_solver, output_var_dict_global, init_list_global, samples_freq_global
#     global_solver = Solver(name="cd") 
#     global_solver.append_formula(formula)  # Base reachability CNF

#     output_var_dict_global = output_var_dict
#     init_list_global = init_list
#     samples_freq_global = samples_freq

# def ValidExecute_fast(args):
#     """Faster validator using incremental SAT with assumptions."""
#     global global_solver, output_var_dict_global, init_list_global, samples_freq_global
#     dnf_formula, shifted_clause = args

#     # Run solver with assumptions
#     sat_res = 1 - int(global_solver.solve(assumptions=shifted_clause))

#     if sat_res:
#         if not is_cnf_satisfied(init_list_global, dnf_formula):
#             return (dnf_formula, samples_freq_global[dnf_formula])
#         return None
#     return (dnf_formula, 0)

# if __name__ == "__main__":
#     import multiprocessing
#     multiprocessing.set_start_method("spawn", force=True)  
#     import time
#     parser = argparse.ArgumentParser()
#     parser.add_argument("--progname", type=str, default="Geo0")
#     parser.add_argument("--epsilon", type=float, default=0.05)
#     parser.add_argument("--delta", type=float, default=0.1)
#     parser.add_argument("--iters", type=int, default=4)
#     parser.add_argument("--num_bits", type=int, help="default = 16", default=16, dest="num_bits")
    
#     args = parser.parse_args()

#     start = time.time()

#     progname, epsilon, delta, k, num_bits = args.progname, args.epsilon, args.delta, args.iters, args.num_bits
#     num_samples = math.ceil(0.5 * math.log(2 / delta) / epsilon**2)

#     # === Load Program Config ===
#     config = get_config(progname)
#     prog_variables = config["Program_variables"]["Bools"]
#     cand = config["Candidate"]["Expression"]
#     init_states = config["Initial states"]["Expression"]
#     num_ops = config["Program specification"]["operations per line"]
#     lines = config["Program specification"]["number of lines"]

#     init_list = [
#         list(filter(None, clause.strip("() ").split("||")))
#         for clause in init_states.split("&&")
#     ]
#     cand_list = [
#         list(filter(None, term.strip("() ").split("&&"))) for term in cand.split("||")
#     ]

#     forward_var_map = {var: idx + 1 for idx, var in enumerate(prog_variables)}
#     reversed_var_map = {idx: var for var, idx in forward_var_map.items()}
#     num_vars = len(forward_var_map)

#     dimacs_cand = nnf_to_dimacs(cand_list, forward_var_map)
#     dimacs_init = nnf_to_dimacs(init_list, forward_var_map)
#     write_dnf_dimacs_to_file(
#         dimacs_cand, num_vars, len(dimacs_cand), os.path.join(CURRENT_PATH, f"temp/candidate_dnf_{progname}")
#     )
#     write_cnf_dimacs_to_file(
#         dimacs_init, num_vars, len(dimacs_init), os.path.join(CURRENT_PATH, f"temp/input_cnf_{progname}")
#     )

#     # === Sampling ===
#     try:
#         subprocess.run(
#             [
#                 "python3",
#                 os.path.join(CURRENT_PATH, "src/Validifier/dnfstream.py"),
#                 "--eps", str(epsilon),
#                 "--delta", str(delta),
#                 "--dosample",
#                 "--numsamps", str(num_samples),
#                 os.path.join(CURRENT_PATH, f"temp/candidate_dnf_{progname}"),
#                 os.path.join(CURRENT_PATH, f"temp/samples_valid_{progname}.out"),
#             ],
#             capture_output=True, text=True, check=True
#         )
#     except subprocess.CalledProcessError as e:
#         print("dnfstream.py failed!")
#         print("STDOUT:\n", e.stdout)
#         print("STDERR:\n", e.stderr)
#         sys.exit(1)

#     def convert_sample(line):
#         return " && ".join(
#             f"{'!' if int(tok) < 0 else ''}{reversed_var_map.get(abs(int(tok)))}"
#             for tok in line.split()
#             if int(tok) != 0
#         )

#     with open(os.path.join(CURRENT_PATH, f"temp/samples_valid_{progname}.out")) as file:
#         converted_lines = [convert_sample(line) for line in file.readlines()]
#     with open(os.path.join(CURRENT_PATH, f"temp/samples_converted_{progname}.txt"), "w") as file:
#         file.write("\n".join(converted_lines))

#     # === Load Variable Mapping ===
#     with open(os.path.join(CURRENT_PATH, f"progformula/{progname}_var_mapping")) as f:
#         variable_mapping = {k: v for k, v in json.load(f).items()
#                             if "_" in k and k.split("_")[0] in prog_variables}

#     min_indices, max_indices = defaultdict(lambda: float("inf")), defaultdict(lambda: -1)
#     for key in variable_mapping:
#         prefix, idx = key.split("_")
#         idx = int(idx)
#         min_indices[prefix] = min(min_indices[prefix], idx)
#         max_indices[prefix] = max(max_indices[prefix], idx)

#     # === Generate CNF ===
#     cnf_prog_formula, num_vars = extract_formula_from_DIMACS(
#         os.path.join(CURRENT_PATH, f"progformula/{progname}_cnf")
#     )
#     k_varmap, k_flat_varmap = generate_k_step_variable_mapping(
#         variable_mapping, k, lines, num_vars
#     )
#     output_vars, _ = get_last_and_transformed_vars(k_varmap[0], 0)
#     output_var_dict = {var: k_flat_varmap[var] for var in output_vars}
#     reverse_map = {key: f"{key}_{max_indices[key]}" for key in max_indices}

#     eq_clauses = generate_equivalence_clauses(k_flat_varmap, k_varmap, k, lines)
#     cnf_init, _ = generate_init_DIMACS_formula(init_states, variable_mapping, min_indices)

#     prog_k_steps = [cnf_prog_formula]
#     for _ in range(k - 1):
#         prog_k_steps.append(translate_formula(prog_k_steps[-1], num_vars))

#     k_step_formula = list(itertools.chain.from_iterable(prog_k_steps))
#     k_step_prog_formula = k_step_formula + eq_clauses
#     reachability_formula = cnf_init + k_step_prog_formula  # list of CNF clauses

#     # === Load Samples ===
#     with open(os.path.join(CURRENT_PATH, f"temp/samples_converted_{progname}.txt")) as f:
#         sampled_states = [line.strip() for line in f.readlines()]
#     sample_freq = dict(Counter(sampled_states))

#     sampled_states_decimal = list(set(convert_to_decimal(prog_variables, s) for s in sampled_states))
#     sampled_states_dict = {convert_to_decimal(prog_variables, s): sample_freq[s] for s in sampled_states}

#     # === Precompute shifted clauses ===
#     shifted_clauses_map = {}
#     for dnf in sample_freq:
#         clause = generate_clause(dnf, reverse_map, output_var_dict)
#         shifted_clause = [
#             lit[0] + (k - 1) * num_vars if lit[0] > 0 else lit[0] - (k - 1) * num_vars
#             for lit in clause
#         ]
#         shifted_clauses_map[dnf] = shifted_clause

#     args_list = [(dnf, shifted_clauses_map[dnf]) for dnf in sample_freq]

#     # === Parallel validation with incremental solver ===
#     with Pool(
#         processes=min(int(0.7*cpu_count()), 20),
#         initializer=init_worker,
#         initargs=(reachability_formula, output_var_dict, init_list, sample_freq)
#     ) as pool:
#         results = pool.map(ValidExecute_fast, args_list)

#     # === Compute results ===
#     individual_dist = [res[1] for res in results if res and res[1]]
#     estimated_dist = sum(individual_dist) / sum(sample_freq.values())

#     counterexamples = [res[0] for res in results if res and res[1] > 0]
#     counterexample_states = [convert_to_decimal(prog_variables, state) for state in counterexamples]
#     unique_cex_states = list(set(counterexample_states))
#     cex_dict = {state: sampled_states_dict[state] / num_samples for state in unique_cex_states}

#     # === Save output ===
#     result_data = {
#         "input_dict": {
#             "progname": progname,
#             "candidate": cand,
#             "init_states": init_states,
#             "iterations": k,
#         },
#         "parameters_dict": {
#             "epsilon": epsilon,
#             "delta": delta,
#             "t": len(sampled_states),
#         },
#         "output_dict": {
#             "Sampled output states": sampled_states_decimal,
#             "Validifier_value": estimated_dist,
#             "counterexamples": cex_dict,
#         },
#     }

#     result_dir = os.path.join(CURRENT_PATH, "src/Validifier/Validifier_results")
#     os.makedirs(result_dir, exist_ok=True)

#     idx = 1
#     while os.path.exists(os.path.join(result_dir, f"exp_{progname}_{idx}.json")):
#         idx += 1
#     with open(os.path.join(result_dir, f"exp_{progname}_{idx}.json"), "w") as f:
#         json.dump(result_data, f, indent=4)

#     end = time.time()

#     print("Time taken (in seconds) :", end - start)

#     print("Validifier outputs:", estimated_dist)
