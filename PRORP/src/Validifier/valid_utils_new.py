import pandas as pd
import os
import time
from datetime import datetime
import sys
import json
import argparse
import copy
from itertools import product
import dnfstream
#from sampler_for_cmsgen import convert_sample,cnf_to_dimacs
# Get the parent directory path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
# Add the parent directory to sys.path
sys.path.insert(0, parent_dir)
from to_dimacs import generate_init_DIMACS_formula,generate_final_DIMACS_formula
from list_from_dimacs import extract_formula_from_DIMACS
import itertools
from collections import Counter
import subprocess
CURRENT_PATH = os.path.realpath("")
PARENT_PATH = os.path.dirname(CURRENT_PATH)
PATH = os.path.dirname(PARENT_PATH)
assumed_shape = " "
import re



def parse_dnf(dnf_string):
    """
    Parse a DNF string into a list of terms, where each term is a list of literals.
    
    Args:
        dnf_string (str): The DNF formula string.
        
    Returns:
        list: A list of terms, where each term is a list of literals.
    """
    # Split by '||' to get terms
    terms = dnf_string.split("||")
    # Split each term by '&&' to get literals
    parsed_terms = [term.strip("() ").split("&&") for term in terms]
    return parsed_terms

def get_variables_from_literal(literal):
    """
    Extract the variable name from a literal.

    Args:
        literal (str): A literal in the form of 'x1' or '!x2'.

    Returns:
        str: The variable name (e.g., 'x1' for 'x1' or '!x1').
    """
    return literal.strip("!")


def get_unique_dict(input_dict):
    """
    Extract unique variables from the dictionary, ignoring whitespace and '!' in keys.

    Args:
        input_dict (dict): Input dictionary with potentially duplicate and malformed keys.

    Returns:
        dict: Dictionary with unique variables and their values.
    """
    unique_dict = {}
    
    for key, value in input_dict.items():
        # Normalize the variable name by stripping spaces and removing '!'
        normalized_key = key.strip().lstrip('!')
        
        # Add to the dictionary if the normalized key isn't already present
        if normalized_key not in unique_dict:
            unique_dict[normalized_key] = value


    terms = []
    for var, value in unique_dict.items():
        if value == 0:
            terms.append(f"!{var}")
        else:
            terms.append(f"{var}")
    return " && ".join(terms)

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

def write_dnf_dimacs_to_file(dimacs, num_vars, num_terms, file_name):
    with open(file_name, 'w') as f:
        f.write(f"p dnf {num_vars} {num_terms}\n")
        for term in dimacs:
            f.write(" ".join(map(str, term)) + " 0\n")



"""
[get_config] loads the json object in [progname]'s configuration file
"""
def get_config(progname):
    with open(os.path.join(CURRENT_PATH, "candidate_files", progname + ".json"), "r") as f:
        config = json.load(f)
    return config




def generate_DIMACS_formula(clauses):
    num_variables = len(set(abs(literal) for clause in clauses for literal in clause))
    num_clauses = len(clauses)

    dimacs_str = f"p cnf {num_variables} {num_clauses}\n"
    
    for clause in clauses:
        dimacs_str += ' '.join(str(i) for i in clause) + ' 0\n'
    
    return dimacs_str


def remove_duplicate_literals(clause):
    cleaned_clause = []
    for literal in clause:
        negated_literal = -literal
        if negated_literal not in clause:
            cleaned_clause.append(literal)
    return cleaned_clause

def DNF_to_CNF(dnf_formula):
    cnf_formula = []

    # If DNF formula is empty, return empty CNF formula
    if not dnf_formula:
        return cnf_formula

    # Initialize CNF formula with the first clause of DNF
    cnf_formula = [[literal] for literal in dnf_formula[0]]
    
    # Distribute each subsequent clause over the existing CNF formula
    for i in range(1, len(dnf_formula)):
        new_cnf_formula = []
        for clause in cnf_formula:
            for literal in dnf_formula[i]:
                
                new_clause = clause + [literal]
                
                new_cnf_formula.append(list(set(new_clause)))
        cnf_formula = new_cnf_formula

    # Remove duplicate literals (both x and -x) within the same clause
    cnf_formula = [remove_duplicate_literals(clause) for clause in cnf_formula]
    cnf_formula = [elem for elem in cnf_formula if elem]
    return cnf_formula

# Subroutine to find last variables and their transformed counterparts
def get_last_and_transformed_vars(original_dict, increment):
    # Dictionary to store the maximum suffix for each base
    max_suffix = {}
    min_suffix = {}
    # Identify the maximum suffix for each base
    for key in original_dict.keys():
        base, suffix = key.split('_')
        suffix = int(suffix)
        # Track the maximum suffix for each base
        if base not in max_suffix or suffix > max_suffix[base]:
            max_suffix[base] = suffix
               # Track the maximum suffix for each base
        if base not in min_suffix or suffix < min_suffix[base]:
            min_suffix[base] = suffix

    # Generate the last and transformed variables sets
    last_variables = [f"{base}_{max_suffix[base]}" for base in max_suffix]
    transformed_variables = [f"{base}_{min_suffix[base] + increment}" for base in min_suffix]

    return last_variables, transformed_variables






def generate_k_step_variable_mapping(variable_mapping,k,lines,num_variables):

    k_step_varmap = list()
    k_step_flat_varmap = {}
    k_step_varmap.append(variable_mapping)
    #init_varmap = variable_mapping
    # Transformation from one-step program formula to k-step variable mapping
    for i in range(k-1):
        new_dict = {}
        for key, value in variable_mapping.items():
            # Split the key into base letter and numeric suffix
            base, suffix = key.split('_')
            new_suffix = int(suffix) + lines  # Increment suffix by 'lines'
            # New key: base + incremented suffix
            new_key = f"{base}_{new_suffix}"
            # New value: original value + num_ops * lines
            new_value = value + num_variables    
            # Add to the new dictionary
            new_dict[new_key] = new_value
        variable_mapping = new_dict
        k_step_varmap.append(new_dict)
    
    
    for d in k_step_varmap:
        k_step_flat_varmap.update(d)


    return k_step_varmap, k_step_flat_varmap



def write_dimacs_to_file(dimacs, num_vars, num_clauses, file_name):
    with open(file_name, 'w') as f:
        f.write(f"p cnf {num_vars} {num_clauses}\n")
        for clause in dimacs:
            f.write(" ".join(map(str, clause)) + " 0\n")



def translate_formula(formula, increment):
    return [[literal + increment if literal > 0 else literal - increment for literal in clause] for clause in formula]



def convert_list_to_dimacs(num_variables, clauses):
    """
    Converts a list of clauses into DIMACS CNF format.

    Arguments:
    clauses -- A list of clauses where each clause is a list of integers.
    
    Returns:
    A string representing the formula in DIMACS CNF format.
    """
    
    # Count the number of clauses
    num_clauses = len(clauses)
    
    # Build the header for DIMACS format (p cnf <num_vars> <num_clauses>)
    dimacs_lines = [f"p cnf {num_variables} {num_clauses}"]
    
    # Add each clause, ending each line with "0"
    for clause in clauses:
        clause_str = " ".join(str(literal) for literal in clause)
        dimacs_lines.append(f"{clause_str} 0")
    
    # Join all lines into a single string, separated by newlines
    return "\n".join(dimacs_lines)

def renumber_dimacs(dimacs_str):
    lines = dimacs_str.strip().split('\n')
    
    # Extract the original number of variables
    header = lines[0]
    num_vars = int(header.split()[2])
    
    # Create a mapping for renumbering
    variable_map = {}
    new_var_id = 1
    
    for line in lines[1:]:
        if line.startswith('p'):
            continue
        for var in re.findall(r'-?\d+', line):
            var = int(var)
            if var != 0 and abs(var) not in variable_map:
                variable_map[abs(var)] = new_var_id
                new_var_id += 1
                if new_var_id > num_vars:
                    break
    
    # Apply the renumbering to the clauses
    new_lines = [header]
    for line in lines[1:]:
        if line.startswith('p'):
            continue
        new_clause = []
        for var in re.findall(r'-?\d+', line):
            var = int(var)
            if var != 0:
                new_var = variable_map.get(abs(var), None)
                if new_var is not None:
                    new_var = new_var if var > 0 else -new_var
                    new_clause.append(str(new_var))
        if new_clause:
            new_lines.append(' '.join(new_clause) + ' 0')
    
    return '\n'.join(new_lines), variable_map



def parse_satisfying_assignment(output):
    lines = output.splitlines()
    #print(lines)
    assignments = list()
    for line in lines:
        if line.startswith('v '):
            # Extract the assignments
            assignments.append(line[2:].split()) # Skip 'v ' at the start
            # Convert to integers and filter out the '0' at the end
    return [item for sublist in assignments for item in sublist if item != '0']
    #return []


def parse_witness(witness):
    """
    Parse the witness string into a dictionary of variable assignments.
    Example: '!x1 && !x2 && x3 && x4 && x5' -> {'x1': False, 'x2': False, 'x3': True, 'x4': True, 'x5': True}
    """
    assignment = {}
    # Remove spaces and split by '&&' to get individual literals
    literals = witness.replace(" ", "").split('&&')
    for literal in literals:
        if literal.startswith('!'):
            assignment[literal[1:]] = False  # Negative literal
        else:
            assignment[literal] = True  # Positive literal
    return assignment


def is_clause_satisfied(clause, assignment):
    """
    Check if at least one literal in the clause is satisfied by the witness.
    """
    for literal in clause:
        if literal.startswith('!'):
            var = literal[1:]
            if not assignment.get(var, False):  # Variable is False in witness
                return True
        else:
            var = literal
            if assignment.get(var, False):  # Variable is True in witness
                return True
    return False


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

def is_cnf_satisfied(cnf_formula, witness):
    """
    Check if the given witness satisfies the CNF formula.
    """
    # Parse the witness into a dictionary of variable assignments
    assignment = parse_witness(witness)
    
    # Check each clause in the CNF formula
    for clause in cnf_formula:
        if not is_clause_satisfied(clause, assignment):
            return False  # If any clause is not satisfied, the CNF is not satisfied
    return True  # All clauses are satisfied


def solve_cnf(file_path,processed_variable_map):
    result = subprocess.run(['cryptominisat5', file_path], capture_output=True, text=True, errors='ignore')

    #print(result)
    processed_assignment = list()
    assignment = parse_satisfying_assignment(result.stdout)
    if (len(assignment) != 0):
        #print("SAT")
        return 0
        '''
        for valuations in assignment:
            processed_assignment.append(processed_variable_map[valuations])
        '''
        #print(assignment)
    else: 
        #print("UNSAT")
        return 1
    


def solve_sat(dimacs_str: str):
    proc = subprocess.run(
        ["cryptominisat5", "--verb=0"],   # ← no "-" here
        input=dimacs_str,
        text=True,
        capture_output=True
    )

    if proc.returncode == 10:
        return 0
    elif proc.returncode == 20:
        return 1
    else:
        raise RuntimeError(
            f"CryptoMiniSat failed (code {proc.returncode})\n"
            f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )



def generate_clause(dnf_formula, reverse_mapping, variable_mapping):
    # Split the DNF formula into individual variables
    clauses = []
    terms = dnf_formula.split(' && ')
    #print(variable_mapping)
    
    for term in terms:
        # Remove '!' if it's negated and mark as negative
        if term.startswith('!'):
            var = term[1:] 
            # Remove '!'
            mapped_var = reverse_mapping.get(var)
            if mapped_var:
                clauses.append([-variable_mapping[mapped_var]]) 
                #print(clauses) # Negated variable
        else:
            mapped_var = reverse_mapping.get(term)
            if mapped_var:
                clauses.append([variable_mapping[mapped_var]])  # Positive variable
                
    return clauses


def extract_index(variable_mapping, literal):
    
    
    var_name = literal.lstrip('!')
        
    # Search for the variable name in the dictionary keys using regex
    for key in variable_mapping:
        match = re.match(f'{var_name}_(\d+)', key)  # Match pattern like 'x1_3'
        if match:
        # Extract the index from the matched key
            index = int(match.group(1))
            break

    return index



def parse_dimacs(dimacs_file):
    """
    Parse a DIMACS CNF file and return the clauses and the number of variables.
    
    Parameters:
        dimacs_file (str): Path to the DIMACS CNF file.
    
    Returns:
        (int, list of lists): Number of variables and list of clauses.
    """
    clauses = []
    num_vars = 0
    with open(dimacs_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('p'):
                # This is the problem line, e.g., 'p cnf 5 3' -> 5 variables, 3 clauses
                parts = line.split()
                num_vars = int(parts[2])
            elif line.startswith('c') or line == '':
                # Ignore comment lines or empty lines
                continue
            else:
                # Parse the clause and add to the clauses list
                clause = [int(x) for x in line.split() if x != '0']  # Exclude the trailing '0'
                clauses.append(clause)
    return num_vars, clauses







def evaluate_clause(clause, assignment):
    """
    Evaluate a single clause with a given assignment.
    
    Parameters:
        clause (list of int): A clause from the CNF formula.
        assignment (dict): A dictionary where keys are variable indices and values are True or False.
    
    Returns:
        bool: True if the clause is satisfied, False otherwise.
    """
    for literal in clause:
        var = abs(literal)
        value = assignment[var]
        if literal > 0 and value:
            return True
        if literal < 0 and not value:
            return True
    return False


def evaluate_formula(clauses, assignment):
    """
    Evaluate the entire CNF formula with a given assignment.
    
    Parameters:
        clauses (list of list of int): The list of clauses from the CNF formula.
        assignment (dict): A dictionary where keys are variable indices and values are True or False.
    
    Returns:
        bool: True if the entire formula is satisfied, False otherwise.
    """
    return all(evaluate_clause(clause, assignment) for clause in clauses)


def get_unique_assignments(num_vars, clauses, variables_of_interest):
    """
    Get unique satisfying assignments for the specified variables of interest.
    
    Parameters:
        num_vars (int): Total number of variables in the CNF formula.
        clauses (list of list of int): The list of clauses from the CNF formula.
        variables_of_interest (list of int): The list of variables.
    
    Returns:
        set of tuples: Unique satisfying assignments for the variables of interest.
    """
    satisfying_assignments = set()
    
    # Generate all possible assignments (2^num_vars possibilities)
    for assignment_tuple in itertools.product([False, True], repeat=num_vars):
        # Convert tuple to dictionary (1-based index)
        assignment = {i+1: assignment_tuple[i] for i in range(num_vars)}
        
        # Check if the assignment satisfies the formula
        if evaluate_formula(clauses, assignment):
            # Extract only the assignment for the variables of interest
            selected_assignment = tuple(assignment[var] for var in variables_of_interest)
            satisfying_assignments.add(selected_assignment)
    
    return satisfying_assignments



def convert_to_decimal(variable_order,expression):
    # Mapping of variables to their positions in the binary representation
    #variable_order = ['x1', 'x2', 'x3', 'x4', 'x5', 'x6', 'x7', 'x8', 'x9', 'x10', 'x11', 'x12', 'x13', 'x14', 'x15', 'x16', 'x17']
    expression = expression.replace(" ", "").split("&&")
    # Initialize a binary string
    binary_str = ""
    
    # Iterate over each variable in the order
    for var in variable_order:
        if f'!{var}' in expression:
            binary_str += '0'  # If the variable is negated, append '0'
        elif var in expression:
            binary_str += '1'  # If the variable is positive, append '1'
        else:
            binary_str += '0'  # If the variable is missing, assume '0'
    
    # Convert the binary string to a decimal number
    return int(binary_str, 2)





def cnf_to_dimacs(cnf_formula, variable_mapping):
    dimacs = []
    for clause in cnf_formula:
        dimacs_clause = []
        for literal in clause:
            if literal.startswith('!'):
                dimacs_clause.append(-variable_mapping[literal[1:]])
            else:
                dimacs_clause.append(variable_mapping[literal])
        dimacs.append(dimacs_clause)
    return dimacs



def extract_actual_vars(cnf_file_path):
    """
    Extracts actual variable numbers from a DIMACS CNF file.

    Arguments:
    cnf_file_path -- Path to the DIMACS CNF file.

    Returns:
    A list of actual variable numbers used in the CNF file.
    """
    actual_vars = set()
    try:
        with open(cnf_file_path, 'r') as file:
            for line in file:
                if line.startswith('c') or line.startswith('p'):
                    continue  # Skip comments and header lines
                # Extract literals from the clause line
                literals = map(int, line.split())
                for literal in literals:
                    if literal != 0:  # Skip the terminating 0
                        actual_vars.add(abs(literal))
    except Exception as e:
        print(f"Error extracting variables: {e}")

    return sorted(actual_vars)


def create_var_map(cnf_file_path, actual_vars):
    """
    Creates a variable mapping from sequential variables to actual variable numbers.

    Arguments:
    cnf_file_path -- Path to the DIMACS CNF file.
    actual_vars -- List of actual variable numbers.

    Returns:
    A dictionary mapping sequential variable indices to actual variable numbers.
    """
    var_map = {}
    try:
        with open(cnf_file_path, 'r') as file:
            lines = file.readlines()

            # Find the number of variables in the CNF file
            for line in lines:
                if line.startswith('p cnf'):
                    num_vars = int(line.split()[2])
                    break

            if num_vars != len(actual_vars):
                raise ValueError("Number of variables in CNF file does not match the length of actual_vars list.")

            # Create the variable map
            var_map = {i + 1: actual_vars[i] for i in range(num_vars)}

    except Exception as e:
        print(f"Error creating variable map: {e}")

    return var_map






def generate_equivalence_clauses(variable_map, k_step_varmap, k,lines):


    equivalence_clauses = list()
    for i in range (k-1):
        
        last_variables, transformed_variables = get_last_and_transformed_vars(k_step_varmap[i], lines)
        #print(last_variables)
        #print(transformed_variables)
        variable_pairs = list(zip(last_variables, transformed_variables))

        #print(variable_pairs)
        #clauses = generate_equivalence_clauses(variable_pairs,k_step_flat_varmap)
        clauses = []
        replaced_clauses = []
        for var1, var2 in variable_pairs:
        
            clause1 = [f"!{var1}", var2]  # (!var1 || var2)
            clause2 = [var1, f"!{var2}"]  # (var1 || !var2)
            clauses.append(clause1)
            clauses.append(clause2)
        
        for clause in clauses:
            new_clause = []
            for var in clause:
                if var.startswith('!'):
                    # Negated variable: replace with negative of its index in variable_map
                    var_index = variable_map.get(var[1:], None)
                    if var_index is not None:
                        new_clause.append(-var_index)
                    else:
                        # Non-negated variable: replace with its index in variable_map
                        var_index = variable_map.get(var, None)
                        if var_index is not None:
                            new_clause.append(var_index)
            replaced_clauses.append(new_clause)

        

        

        
        
        equivalence_clauses += [[abs(replaced_clauses[i][0]), replaced_clauses[i+1][0]] for i in range(0, len(replaced_clauses), 2)]
        equivalence_clauses += [[-abs(replaced_clauses[j][0]), -replaced_clauses[j+1][0]] for j in range(0, len(replaced_clauses), 2)]





        




        


    return equivalence_clauses




#functions for dnfstream :-


import gmpy2 as gp
from gmpy2 import mpq, mpfr
import numpy as np
import math
import os, sys
import random
import time
import argparse
import cProfile
from mprandom import mpbinomial
from mprandom import vanbinomialvariate as vanbinomial

gp.get_context().precision=20000


def isSAT(dnfclause, sol):    
    tmpRand = np.random.uniform(0, 1, max(len(dnfclause), len(sol)))     
    idx = 0
    for lit in dnfclause:
        if -1 * lit in sol :
            return False
        elif lit not in sol:
            if tmpRand[idx] > 0.5:    # np.random.uniform(0, 1)    # delayed sample generation
                return False
            idx += 1
    return True


def ComputeNumSamples(t, p, thresh, m, delta, method, verbose):



    if method == 1:
        # vanilla version
        try:
            N = vanbinomial(t,p)
            N = int(N)
        except OverflowError:
            print("SAMPLING FAILURE!")
            exit("SAMPLING FAILURE!")

    elif method == 2:
        # improved version
        thresh1 = 12 * thresh**2 * m / delta
        thresh2 = (delta / (6 * m))**0.5

        thresh1, thresh2 = mpfr(thresh1), mpfr(thresh2)

        if t * p >= thresh2 :
            if t <= thresh1:
                if verbose:
                    print("binomial")
                N = np.random.binomial(int(t), float(p))
            else:
                if verbose:
                    print("poisson")
                N = np.random.poisson(float(t * p))
        else:
            if verbose:
                print("small binomial")
            N = np.random.binomial(1, float(t*p))

    elif method == 3:
        # mp version
        N = mpbinomial(int(t), p, err=delta / (6 * m))

    return N


def getSolutionFromVanillaSampler(dnfClause, nVars):
    sol = []
    tmpRand = np.random.uniform(0,1,nVars)
    for i in range(1, nVars+1):
        if i in dnfClause:
            sol.append(i)
        else:
            if tmpRand[i-1] > 0.5:
                sol.append(-i)
            else:
                sol.append(i)
    return sol


def GenerateSamples(N, dnfClause, delta, m, nVars, thresh):
    sampSet = []
    for j in range(N):
        sampSet.append(dnfClause)

    return sampSet

def dnfstream2(eps, delta, numsamps, input_file):

    
    # file handling
    inputFile = input_file
    f = open(inputFile, "r")
    lines = f.readlines()
    f.close()

    seed = 10
    sampMethod = 1
    do_sampling = True
    num_samples = numsamps
    #np.random.seed(seed)

    initLine = lines[0].strip().split()

    if initLine[0] == "p":
        nVars = initLine[2]
        nClause = initLine[3]

    #print(nVars, nClause)


    # parameters / initialization

    if sampMethod == 1:
        delta *= 2
    m = int(nClause)
    n = int(nVars)
    thresh = max(12 * math.log(24/delta) / eps**2, 6*(math.log(6/delta) + math.log(m)))
    # thresh = 4*math.log2(m+1)/(eps**2)*math.log2(1.0/delta) 
    p = 1
    solset = []

    # multi-precision conversion
    thresh, p = mpfr(thresh), mpfr(p)
    #print("Threshold: ",thresh)
    #print(p)
    line = 0  # line 0 corresponds to p dnf
    cl = 0
    # for i in range(1, m+1):
    counter = 0
    while True:
        counter+=1
        if lines[line].startswith("c") or lines[line].startswith("p") or lines[line].startswith("w"):
            line += 1
            continue 
        currClause = lines[line].strip().split()[:-1]
        line += 1
        currClause = list(map(int, currClause))
        clauseWidth = len(currClause)

        #print(f"adding clause {currClause}")
        t = mpfr(2**(n-clauseWidth))
        #print(solset)
        for s in solset:
            if isSAT(currClause, s):
                solset.remove(s)
    
        if cl == 1 and p >= thresh / t:
            # pow = gp.ceil(gp.log2(p * t / thresh))
            pow = gp.ceil(gp.log2(gp.div(gp.mul(p, t), thresh)))
            # p = p / 2**pow
            p = gp.div(p, 2**pow)

        while p * t >= thresh:
            for sol in solset:
                if np.random.uniform(0,1) > p : # this was 0.5 before
                    solset.remove(sol)
            # p = p / 2
            p = gp.div(p,2)
        

        N_i = ComputeNumSamples(t, p, thresh, m, delta, sampMethod, True)
        #print(N_i)
        Npast = N_i
        while N_i + len(solset) > thresh:
            for sol in solset:
                if np.random.uniform(0,1) > p : # this was 0.5 before
                    solset.remove(sol)
            N_i = np.random.binomial(N_i , 1/2)
            p = p / 2
            
            # print(f"bucket reduced to : {len(solset)}")

        
        # print(f"old ni : {Npast}, new ni: {N_i}")

        sol = GenerateSamples(N_i, currClause, delta, m, n, thresh)
        solset += sol
        cl += 1
        if cl == m : break

        seed += 1

    #print(counter)
    modelCount = int(len(solset)/p)
    # print(modelCount)
    samples = list()
    if do_sampling:
        #print("Solution set: ", solset)
        for _ in range(num_samples):
            sampled_element = list()
            #print(solset)
            sampled_element = sampled_element = list(random.choice(solset))

            #print("Initial sampled portion: ",sampled_element)
            tmpRand = np.random.uniform(0, 1, n)    
            #print(tmpRand) 
            idx = 0
            for lit in range(1, n+1):
                if (lit in sampled_element) or ((-lit) in sampled_element):
                    idx += 1
                    continue
                else:
                    #print(tmpRand[idx])
                    if tmpRand[idx] > 0.5:

                        sampled_element.append(-lit)
                    else:
                        sampled_element.append(lit)
            
                idx += 1
            #print("Sampled element:", tuple(sorted(sampled_element, key=abs)))
            samples.append(sampled_element)
        samples = [" ".join(map(str, sample)) + " 0\n" for sample in samples]
        
        return samples
        
    
    





    
    
