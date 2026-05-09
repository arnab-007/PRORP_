import argparse
import os
import math
import json
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, as_completed
import subprocess
import random
import re
import threading
import filelock
from filelock import FileLock
import fcntl

CURRENT_PATH = os.path.realpath("")
PARENT_PATH = os.path.dirname(CURRENT_PATH)
GRANDPARENT_PATH = os.path.dirname(PARENT_PATH)
assumed_shape = " "


def get_config(progname):
    with open(
        os.path.join(CURRENT_PATH, "candidate_files", progname + ".json"), "r"
    ) as f:
        config = json.load(f)
    return config

def nnf_to_dimacs(cnf_formula, variable_mapping):
    dimacs = []
    for clause in cnf_formula:
        dimacs_clause = []
        for literal in clause:
            literal = literal.strip()
            if literal.startswith('!'):
                dimacs_clause.append(-variable_mapping[literal[1:].strip()])
            else:
                dimacs_clause.append(variable_mapping[literal.strip()])

        dimacs.append(dimacs_clause)
    return dimacs


def write_cnf_dimacs_to_file(dimacs, num_vars, num_clauses, file_name):
    with open(file_name, 'w') as f:
        f.write(f"p cnf {num_vars} {num_clauses}\n")
        for clause in dimacs:
            f.write(" ".join(map(str, clause)) + " 0\n")
            
def convert_decimal_state_to_binary(n, num_states):
    if n == 0:
        assignment = [0] * (num_states)
    binary_str = ""
    while n > 0:
        binary_str = str(n % 2) + binary_str
        n = n // 2
    preassignment = [int(bit) for bit in binary_str]
    assignment = [0] * (num_states - len(preassignment)) + preassignment

    return assignment


def evaluate_loop_guard_condition(output, variables: list[str], formula: str) -> int:
    
    try:
        output = int(output)  # Make sure output is an int
    except ValueError:
        print(f"Invalid output value: {output}")
        return 0

    if len(variables) > output.bit_length():
        bits = format(output, f"0{len(variables)}b")
    else:
        # Still pad to full length just in case
        bits = format(output, f"0{len(variables)}b")[-len(variables) :]

    # Create variable-to-bit mapping
    context = {var: int(bit) for var, bit in zip(variables, bits)}

    # Safely translate the formula
    try:
        eval_formula = formula
        for var in variables:
            eval_formula = eval_formula.replace(var, str(context[var]))
        eval_formula = (
            eval_formula.replace("&&", " and ")
            .replace("||", " or ")
            .replace("!", " not ")
        )
        return int(eval(eval_formula))
    except Exception as e:
        print(f"Error evaluating formula: {e}")
        return 0


def parse_cnf_dimacs(filename):
    """
    Parses a CNF DIMACS file and converts it into a list of clauses.

    Parameters:
    filename (str): Path to the CNF DIMACS file.

    Returns:
    list of list of int: List of clauses where each clause is a list of literals.
    """
    clauses = []
    with open(filename, "r") as file:
        for line in file:
            line = line.strip()
            if line.startswith("p cnf"):
                continue  # Skip the problem line
            if line.startswith("c"):
                continue  # Skip comment lines
            if line:
                literals = list(map(int, line.split()))
                if literals[-1] == 0:
                    literals.pop()  # Remove trailing 0
                if literals:
                    clauses.append(literals)
    return clauses


def parse_dnf_dimacs(filename):
    """
    Parses a DNF DIMACS file and converts it into a list of terms.

    Parameters:
    filename (str): Path to the DNF DIMACS file.

    Returns:
    list of list of int: List of terms where each term is a list of literals.
    """
    terms = []
    with open(filename, "r") as file:
        for line in file:
            line = line.strip()
            if line.startswith("p dnf"):
                continue  # Skip the problem line
            if line.startswith("c"):
                continue  # Skip comment lines
            if line:
                literals = list(map(int, line.split()))
                if literals[-1] == 0:
                    literals.pop()  # Remove trailing 0
                if literals:
                    terms.append(literals)
    return terms


def evaluate_cnf(clauses, assignment):
    """
    Evaluate the CNF formula against the given assignment.

    Parameters:
    clauses (list of list of int): List of CNF clauses.
    assignment (list of bool): Boolean assignment to variables.

    Returns:
    bool: True if the assignment satisfies the CNF formula, False otherwise.
    """

    # print(assignment)
    # print(clauses)
    def literal_to_value(literal, assignment):
        if literal > 0:
            # print(f"Evaluating literal: {literal}, assignment: {assignment}")
            return assignment[literal - 1]
        else:
            return not assignment[-literal - 1]

    """
    def literal_to_value(literal, assignment):
        index = abs(literal) - 1  # Convert literal to zero-based index
        if index >= len(assignment) or index < 0:
            raise IndexError(f"Literal {literal} is out of bounds for assignment.")
        return assignment[index] if literal > 0 else not assignment[index]

    """
    for clause in clauses:
        clause_satisfied = False
        for literal in clause:
            if literal_to_value(literal, assignment):
                clause_satisfied = True
                break
        if not clause_satisfied:
            return False
    return True


def evaluate_dnf(terms, assignment):
    """
    Evaluate the DNF formula against the given assignment.

    Parameters:
    clauses (list of list of int): List of DNF terms.
    assignment (list of bool): Boolean assignment to variables.

    Returns:
    bool: True if the assignment satisfies the DNF formula, False otherwise.
    """

    # print(assignment)
    # print(clauses)
    def literal_to_value(literal, assignment):
        if literal > 0:
            # print(f"Evaluating literal: {literal}, assignment: {assignment}")
            return assignment[literal - 1]
        else:
            return not assignment[-literal - 1]

    """
    def literal_to_value(literal, assignment):
        index = abs(literal) - 1  # Convert literal to zero-based index
        if index >= len(assignment) or index < 0:
            raise IndexError(f"Literal {literal} is out of bounds for assignment.")
        return assignment[index] if literal > 0 else not assignment[index]

    """
    for term in terms:
        term_satisfied = True
        for literal in term:
            if not literal_to_value(literal, assignment):
                term_satisfied = False
                break
        if term_satisfied:
            return True
    return False


def read_file_to_list(filename):
    L = []
    with open(filename, "r") as file:
        for line in file:

            clause = [int(x) for x in line.split() if int(x) != 0]
            L.append(clause)
    return L


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--progname", type=str, default="Geo0", help="Program name")
    parser.add_argument("--epsilon", type=float, default=0.05, help="Epsilon value")
    parser.add_argument("--delta", type=float, default=0.1, help="Delta value")
    parser.add_argument("--iters", type=int, default=4, help="Number of iterations")
    parser.add_argument("--num_bits", type=int, help="default = 16", default=16, dest="num_bits")
    return parser.parse_args()

def setup_program(progname):
    source_file = os.path.join(CURRENT_PATH, f"src/DistEstimate/executable_prog_files/{progname}.c")
    output_binary = os.path.join(CURRENT_PATH, f"binaries/{progname}")
    #output_binary = progname
    
    subprocess.run(["gcc", source_file, "-o", output_binary], check=True)

def generate_samples(progname, epsilon, delta):
    random_seed = 42
    num_samples = math.ceil(0.5 * math.log(2 / delta) / epsilon**2)
    input_cnf_path = os.path.join(CURRENT_PATH,f"temp/input_cnf_{progname}")
    samples_dist_path = os.path.join(CURRENT_PATH,f"temp/samples_dist_{progname}.out")
    try:
        result = subprocess.run(
            ["/usr/local/bin/cmsgen", "-s", str(random_seed), f"--samples={num_samples}", 
             f"--samplefile={samples_dist_path}", input_cnf_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )

        if result.returncode not in (0, 10):
            raise RuntimeError(f"cmsgen failed with code {result.returncode}")

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"cmsgen execution failed: {e}")

    return f"{samples_dist_path}"

def preprocess_samples(filename):
    L = read_file_to_list(filename)
    return [[0 if x < 0 else 1 for x in state] for state in L]


def evaluate_results(results, config, progname):
    element_counts = {}
    for element in results:
        element_counts[element] = element_counts.get(element, 0) + 1

    num_states = len(config["Program_variables"]["Bools"])
    candidate_file = os.path.join(CURRENT_PATH,f"temp/candidate_dnf_{progname}")
    terms = parse_dnf_dimacs(candidate_file)

    rev_distance = 0
    counterexamples = []

    for element, count in element_counts.items():
        assignment = convert_decimal_state_to_binary(int(element), num_states)
        ind_distance = evaluate_dnf(terms, assignment) * count
        rev_distance += ind_distance
        if ind_distance == 0:
            counterexamples.append(element)

    distance = 1 - (rev_distance / len(results))
    return distance, {ce: element_counts[ce]/len(results) for ce in counterexamples}, element_counts

def save_experiment_results(args, config, distance, counterexamples, all_reachable_states):
    results_directory = os.path.join(CURRENT_PATH, "src/DistEstimate/DistEstimate_results")
    os.makedirs(results_directory, exist_ok=True)

    existing_files = os.listdir(results_directory)
    file_number = 1
    while f"exp_{args.progname}_{file_number}.json" in existing_files:
        file_number += 1

    save_path = os.path.join(results_directory, f"exp_{args.progname}_{file_number}.json")

    input_dict = {
        "progname": args.progname,
        "candidate": config["Candidate"]["Expression"],
        "init_states": config["Initial states"]["Expression"],
        "iterations": args.iters,
    }
    parameters_dict = {
        "epsilon": args.epsilon,
        "delta": args.delta,
        "m1": sum(all_reachable_states.values()),
    }
    output_dict = {
        "Reachability_dict": all_reachable_states,
        "DistEstimate_value": distance,
        "counterexamples": counterexamples,
    }

    # print("All reachable states", all_reachable_states)

    total_dict = {
        "input_dict": input_dict,
        "parameters_dict": parameters_dict,
        "output_dict": output_dict,
    }

    with open(save_path, "w") as json_file:
        json.dump(total_dict, json_file, indent=4)