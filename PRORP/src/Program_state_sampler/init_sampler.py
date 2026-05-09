import subprocess
import random
import re
import os
import json
import argparse
import filelock
from filelock import FileLock
import numpy as np
CURRENT_PATH = os.path.realpath("")
PATH = os.path.dirname(CURRENT_PATH)
assumed_shape = " "


def get_config(progname):
    with open(
        os.path.join(CURRENT_PATH, "candidate_files", progname + ".json"), "r"
    ) as f:
        config = json.load(f)
    return config


def read_dimacs_file(file_path):
    clauses = []
    num_variables = 0
    num_clauses = 0

    with open(file_path, "r") as file:
        for line in file:
            # Skip comments
            # if line.startswith('c'):
            # continue
            # Read problem line (e.g. "p cnf 8 4")
            if line.startswith("p"):
                _, _, num_vars, num_clauses = line.split()
                num_variables = int(num_vars)
                num_clauses = int(num_clauses)
            # Read clauses
            else:
                clause = list(map(int, line.split()))[:-1]  # remove the last zero
                print(clause)
                clauses.append(clause)
    return num_variables, clauses


def remove_duplicate_literals(clause):
    cleaned_clause = []
    for literal in clause:
        negated_literal = -literal
        if negated_literal not in clause:
            cleaned_clause.append(literal)
    return cleaned_clause


def negate_clause(clause):
    # Negate each literal in the clause
    return [-lit for lit in clause]


def nnf_to_dimacs(num_vars, clauses, output_file_path):
    with open(output_file_path, "w") as f:
        f.write(f"p dnf {num_vars} {len(clauses)}\n")
        for clause in clauses:
            f.write(" ".join(map(str, clause)) + " 0\n")


def negate_cnf(num_vars, clauses):
    # Negate the entire CNF formula (Apply De Morgan's Law)
    L = [negate_clause(clause) for clause in clauses]

    return L


def negate_cnf_to_dimacs(input_file_path, output_file_path):
    num_vars, clauses = read_dimacs_file(input_file_path)

    negated_clauses = negate_cnf(num_vars, clauses)

    # negated_clauses = process_and_remove_duplicates((negated_clauses))

    nnf_to_dimacs(num_vars, negated_clauses, output_file_path)


def process_and_remove_duplicates(L):
    # Step 1: Sort each inner list by absolute values
    L_sorted = [sorted(inner_list, key=abs) for inner_list in L]

    # Step 2: Remove duplicates by converting to a set of tuples, then back to a list of lists
    L_unique = list(map(list, set(tuple(sublist) for sublist in L_sorted)))

    # Step 3: Sort the outer list for consistent order
    L_unique.sort()

    return L_unique


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


def write_dnf_dimacs_to_file(dimacs, num_vars, num_terms, file_name):
    with open(file_name, "w") as f:
        f.write(f"p dnf {num_vars} {num_terms}\n")
        for term in dimacs:
            f.write(" ".join(map(str, term)) + " 0\n")


parser = argparse.ArgumentParser()
parser.add_argument(
    "--progname", type=str, help="default = Geo0", default="Geo0", dest="progname"
)
parser.add_argument(
    "--epsilon", type=float, help="default = 0.05", default=0.05, dest="epsilon"
)
parser.add_argument(
    "--eta", type=float, help="default = 0.05", default=0.05, dest="eta"
)
parser.add_argument(
    "--delta", type=float, help="default = 0.1", default=0.1, dest="delta"
)
parser.add_argument("--iters", type=int, help="default = 4", default=4, dest="iters")
parser.add_argument("--num_bits", type=int, help="default = 16", default=16, dest="num_bits")
parser.add_argument("--flag", type=int, default=1, dest="flag")
args = parser.parse_args()
progname = args.progname
epsilon = args.epsilon
delta = args.delta
k = args.iters
num_bits = args.num_bits
eta = args.eta
flag = args.flag
# Example usage:
input_file = f"input_cnf_{progname}"  # Path to the input CNF file
# output_file = f"input_negated_dnf_{progname}"  # Path to the output DNF file for negation
# negate_cnf_to_dimacs(input_file, output_file)


# Init_sampler_trigger_path_2 = os.path.join(CURRENT_PATH, "src/Program_state_sampler/", "state_sampler.sh")
# subprocess.run(["bash", Init_sampler_trigger_path_2], check=True)  # Running a shell script


random_seed = 42  # Replace with a dynamic value if needed


config = get_config(progname)
prog_variables = config["Program_variables"]["Bools"]
cand = config["Candidate"]["Expression"]
init_states = config["Initial states"]["Expression"]
init_dist_cand = f"({prog_variables[len(prog_variables) - 1]} && !{prog_variables[len(prog_variables) - 1]})"
init_valid_cand = f"({prog_variables[len(prog_variables) - 1]}) || (!{prog_variables[len(prog_variables) - 1]})"
DistEstimate_trigger_path = os.path.join(
    CURRENT_PATH, "src/DistEstimate/", "DistEstimate.py"
)
Validifier_trigger_path = os.path.join(CURRENT_PATH, "src/Validifier/", "validifier.py")


with open(
    os.path.join(CURRENT_PATH, "candidate_files", progname + ".json"), "r"
) as file:
    data = json.load(file)
    data["Candidate"]["Expression"] = init_valid_cand
with open(
    os.path.join(CURRENT_PATH, "candidate_files", progname + ".json"), "w"
) as file:
    json.dump(data, file, indent=4)

if (flag == 1):
    try:
        # Run the first subprocess
        
        result_validifier = subprocess.run(
            [
                "python3",
                Validifier_trigger_path,
                "--progname",
                str(progname),
                "--epsilon",
                str(eta),
                # str(0.1/np.sqrt(len(prog_variables))),
                "--delta",
                str(0.1),
                "--iters",
                str(k),
                "--num_bits", 
                str(num_bits),
            ],
            capture_output=True,
            text=True,
            check=True,  # Raise CalledProcessError if the subprocess fails
        )
        
    except subprocess.CalledProcessError as e:
        print(f"Subprocess failed with return code {e.returncode}")
        print(f"Command: {e.cmd}")
        print(f"Output: {e.output}")
        print(f"Error: {e.stderr}")

    except FileNotFoundError as e:
        print(f"Executable not found: {e}")
        print("Check that 'bash' is installed and paths are correct.")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")


with open(
    os.path.join(CURRENT_PATH, "candidate_files", progname + ".json"), "r"
) as file:
    data = json.load(file)
    data["Candidate"]["Expression"] = init_dist_cand
with open(
    os.path.join(CURRENT_PATH, "candidate_files", progname + ".json"), "w"
) as file:
    json.dump(data, file, indent=4)

cand_list = [
    list(filter(None, term.strip("() ").split("&&")))
    for term in init_dist_cand.split("||")
]

# === DIMACS Variable Mapping ===
forward_var_map = {var: idx + 1 for idx, var in enumerate(prog_variables)}
reversed_var_map = {idx: var for var, idx in forward_var_map.items()}
num_vars = len(forward_var_map)

# === Write DIMACS Files ===
dimacs_cand = nnf_to_dimacs(cand_list, forward_var_map)
write_dnf_dimacs_to_file(
    dimacs_cand, num_vars, len(dimacs_cand), os.path.join(CURRENT_PATH,f"temp/candidate_dnf_{progname}")
)

if (flag == 1):
    try:
        # Run the first subprocess
        result_distestimate = subprocess.run(
            [
                "python3",
                DistEstimate_trigger_path,
                "--progname",
                str(progname),
                "--epsilon",
                str(epsilon),
                # str(0.1/np.sqrt(len(prog_variables))),
                "--delta",
                str(0.1),
                "--iters",
                str(k),
                "--num_bits", 
                str(num_bits),
            ],
            capture_output=True,
            text=True,
            check=True,  # Raise CalledProcessError if the subprocess fails
        )

    except subprocess.CalledProcessError as e:
        print(f"Subprocess failed with return code {e.returncode}")
        print(f"Command: {e.cmd}")
        print(f"Output: {e.output}")
        print(f"Error: {e.stderr}")

    except FileNotFoundError as e:
        print(f"Executable not found: {e}")
        print("Check that 'bash' is installed and paths are correct.")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")

else:
    try:
        # Run the first subprocess
        result_distestimate = subprocess.run(
            [
                "python3",
                DistEstimate_trigger_path,
                "--progname",
                str(progname),
                "--epsilon",
                str(epsilon/3),
                # str(0.1/np.sqrt(len(prog_variables))),
                "--delta",
                str(0.1),
                "--iters",
                str(k),
                "--num_bits", 
                str(num_bits),
            ],
            capture_output=True,
            text=True,
            check=True,  # Raise CalledProcessError if the subprocess fails
        )

    except subprocess.CalledProcessError as e:
        print(f"Subprocess failed with return code {e.returncode}")
        print(f"Command: {e.cmd}")
        print(f"Output: {e.output}")
        print(f"Error: {e.stderr}")

    except FileNotFoundError as e:
        print(f"Executable not found: {e}")
        print("Check that 'bash' is installed and paths are correct.")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")



'''


def balance_lists(list1, list2):
    """
    Balance the number of elements in two lists by sampling uniformly at random from the larger list.
    
    Args:
    list1 (list): The first list (smaller or equal in size to list2).
    list2 (list): The second list (larger list from which to sample).
    
    Returns:
    tuple: A tuple containing list1 and the sampled version of list2 with the same length as list1.
    """
    if (len(list1) < len(list2)):
        sampled_list2 = random.sample(list2, len(list1))
        return list1, sampled_list2
    if (len(list1) > len(list2)):
        sampled_list1 = random.sample(list1, len(list2))
        return sampled_list1, list2
    if (len(list1) == len(list2)):
        return list1, list2
    


def sample_to_decimal(sample, number_of_vars):
    
    
    binary_string = ['0'] * number_of_vars
  
    for value in sample:
        if value == 0:
            continue  # Skip the terminating zero
        index = abs(value) - 1  # Convert variable to zero-based index
        if 0 <= index < number_of_vars:
            if value > 0:
                binary_string[index] = '1'  # Set bit to 1 for positive values
            else:
                binary_string[index] = '0'  # Set bit to 0 for negative values
        else:
            raise IndexError(f"Index {index} out of range for binary_string with length {number_of_vars}")
    
    # Join the bits to form a binary string and convert to decimal
    binary_str = ''.join(binary_string)
    return int(binary_str, 2)

# Read samples from the file and convert each sample to decimal
decimals_1 = []
with open(f'samples_plus_{progname}.out', 'r') as f:
    for line in f:
        # Convert the line into a list of integers
        sample = list((map(int, line.split())))
        decimal_value = sample_to_decimal(sample, len(prog_variables))
        decimals_1.append((decimal_value))

decimals_2 = []
with open(f'samples_minus_{progname}.out', 'r') as f:
    for line in f:
        # Convert the line into a list of integers
        sample = list((map(int, line.split())))
        decimal_value = sample_to_decimal(sample, len(prog_variables))
        decimals_2.append((decimal_value))


decimals_1 = sorted(list(set(decimals_1)))
decimals_2 = sorted(list(set(decimals_2)))
print(len(decimals_1))
print(len(decimals_2))
decimals_S, decimals_not_S = balance_lists(decimals_1, decimals_2)
decimals_S = sorted(list(set(decimals_S)))
decimals_not_S = sorted(list(set(decimals_not_S)))
#print(len(decimals_S))
#print(len(decimals_not_S))

decimals_1_print = [(element,1,1) for element in decimals_S]
decimals_2_print = [(element,1,0) for element in decimals_not_S]
#print("Initial states in S",decimals_1_print)
#print("Initial states not in S",decimals_2_print)



input_dict = {"progname":progname,"candidate":cand,"init_states":init_states}
output_dict = {"Sampled positive initial states":decimals_S,"Sampled negative initial states":decimals_not_S}
total_dict = {"input_dict":input_dict,"output_dict":output_dict}


results_directory = os.path.join(CURRENT_PATH, 'src/Program_state_sampler/Sampler_results')
if not os.path.exists(results_directory):
    os.makedirs(results_directory)



existing_files = os.listdir(results_directory)
file_number = 1


# Loop until you find an unused file name (exp1.json, exp2.json, etc.)
while f"init_{progname}_{file_number}.json" in existing_files:
    file_number += 1

# Create the new filename in the results subdirectory
filename = os.path.join(results_directory, f"init_{progname}_{file_number}.json")
lock = FileLock(filename + ".lock")  # Create a lock file

with lock:  # Lock file access
    # Write the data to the new file
    with open(filename, 'w') as json_file:
        json.dump(total_dict, json_file, indent=4)

'''
