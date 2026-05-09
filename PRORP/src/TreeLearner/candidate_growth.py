import re
import os
import json
import random

CURRENT_PATH = os.path.realpath("")
PARENT_PATH = os.path.dirname(CURRENT_PATH)
PATH = os.path.dirname(PARENT_PATH)
assumed_shape = " "
from utils import *

def get_config(progname):
    with open(os.path.join(PATH, "candidate_files", progname + ".json"), "r") as f:
        config = json.load(f)
    return config


def DNF_sampler(dnf_string, variables):
    """
    Sample an assignment from a DNF string almost uniformly.
    
    Args:
        dnf_string (str): The DNF formula as a string.
        variables (list): List of all variables in the DNF formula.
        
    Returns:
        dict: A dictionary of sampled values for all variables.
    """
    # Parse the DNF string into terms
    term_list = parse_dnf(dnf_string)
    
    # Choose a term uniformly at random
    chosen_term = random.choice(term_list)
    
    # Determine the support variables of the chosen term
    support_vars = set(get_variables_from_literal(literal) for literal in chosen_term)
    support_vars = {key.strip().lstrip('!') for key in support_vars}
    # Determine the non-support variables
    non_support_vars = [var for var in variables if var not in support_vars]
    #print(non_support_vars)

    
    # Assign random values to non-support variables
    sampled_assignment = {var: random.randint(0, 1) for var in non_support_vars}
    #print(sampled_assignment)
    chosen_term = [var.strip() for var in chosen_term]
    # Assign fixed values to support variables based on the term
    for literal in chosen_term:
        var = get_variables_from_literal(literal)
        sampled_assignment[var] = 0 if literal.startswith("!") else 1
    
    return sampled_assignment


def substitute_values(formula, assignment):
    # Replace negations first
    formula = re.sub(r"!x(\d+)", lambda m: str(1 - assignment[f'x{m.group(1)}']), formula)
    # Replace normal variables
    formula = re.sub(r"x(\d+)", lambda m: str(assignment[f'x{m.group(1)}']), formula)
    # Replace '&&' with 'and' and '||' with 'or'
    formula = formula.replace("&&", " and ").replace("||", " or ")
    return formula



# Read the text file
with open(os.path.join(CURRENT_PATH, "results_log", "resultlog_ex7_k9"), "r") as file:
    log_data_k1 = file.read()
with open(os.path.join(CURRENT_PATH, "results_log", "resultlog_ex7_k10"), "r") as file:
    log_data_k2 = file.read()

# Extract the "Final candidate learnt" using regex
match_k1 = re.search(r"Final candidate learnt:\s*(\(.*\))", log_data_k1, re.DOTALL)
match_k2 = re.search(r"Final candidate learnt:\s*(\(.*\))", log_data_k2, re.DOTALL)

# Store the result in a string variable
final_candidate_k1 = match_k1.group(1) if match_k1 else ""
final_candidate_k2 = match_k2.group(1) if match_k2 else ""


# Print the extracted formula
#print(final_candidate_k1)
#print(final_candidate_k2)


with open(os.path.join(PATH, "program-list.txt"), "r") as f:
    prognames = f.read().strip().split("\n")


for progname in prognames:
    config = get_config(progname)
    prog_variables = config["Program_variables"]["Bools"]
    k = config["Program specification"]["iterations"]
    rand = config["Random_variables"]["Bools"]
    num_variables = len(prog_variables)

print(progname)
final_cand_k1_list_terms = final_candidate_k1.split('||')
final_cand_k1_list = list()
for term in final_cand_k1_list_terms:

    literals = term.split('&&')
    literals = [literal.strip("() ") for literal in literals]
    # Filter out empty strings
    literals = list(filter(None, literals))
    final_cand_k1_list.append(literals)


dnf_final_cand_k1 = final_cand_k1_list


final_cand_k2_list_terms = final_candidate_k2.split('||')
final_cand_k2_list = list()
for term in final_cand_k2_list_terms:

    literals = term.split('&&')
    literals = [literal.strip("() ") for literal in literals]
    # Filter out empty strings
    literals = list(filter(None, literals))
    final_cand_k2_list.append(literals)


dnf_final_cand_k2 = final_cand_k2_list





forward_variable_mapping = {prog_variables[i]: i + 1 for i in range(len(prog_variables))}
# Convert to DIMACS format
dimacs_final_cand_k1 = nnf_to_dimacs(dnf_final_cand_k1, forward_variable_mapping)
dimacs_final_cand_k2 = nnf_to_dimacs(dnf_final_cand_k2, forward_variable_mapping)

num_vars = len(forward_variable_mapping)  # Number of variables



# Write DIMACS formula to file
write_dnf_dimacs_to_file(dimacs_final_cand_k1, num_vars, len(dimacs_final_cand_k1), os.path.join(PATH, "candidate-dnf-k1"))
write_dnf_dimacs_to_file(dimacs_final_cand_k2, num_vars, len(dimacs_final_cand_k2), os.path.join(PATH, "candidate-dnf-k2"))



candidate_samples = []
for _ in range(10000):
  #print("Sampled Assignment:")
  sampled_assignment = DNF_sampler(final_candidate_k2, prog_variables)
  candidate_samples.append(sampled_assignment)
  #print(sampled_assignment)

#print(candidate_samples)
result = 0



for assignment in candidate_samples:
    result = result + eval(substitute_values(final_candidate_k1, assignment))/len(candidate_samples)

print("The ninth step invariant grows from the eighth step invariant by a factor of : ", (1/result))