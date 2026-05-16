import random
import re
import os
import json
import numpy as np
import argparse

CURRENT_PATH = os.path.realpath("")
PATH = os.path.dirname(CURRENT_PATH)
assumed_shape = " "

"""
[get_config] loads the json object in [progname]'s configuration file
"""


def booleanize(precondition, varmap):
    def int_to_bitvec(val, width):
        return f"{val:0{width}b}"

    def expand_eq(var, val):
        bits = varmap[var]
        bitvec = int_to_bitvec(int(val), len(bits))
        return [f"{'' if b == '1' else '!'}{bit}" for bit, b in zip(bits, bitvec)]

    def expand_lt_optimized(var, val):
        bits = varmap[var]
        width = len(bits)
        val = int(val)
        bitvec = int_to_bitvec(val, width)

        clauses = []
        for i in range(width):
            if bitvec[i] == "1":
                # If all more significant bits match val up to here, then this bit must be 0
                prefix = [
                    f"{'' if bitvec[j] == '1' else '!'}{bits[j]}" for j in range(i)
                ]
                clause = prefix + [f"!{bits[i]}"]
                clauses.append(") && (".join(clause))
        return [" || ".join(clauses)] if clauses else ["False"]

    # pattern = r"(\w+)\s*(==|<)\s*(\d+)"
    pattern = r"\(?\s*(\w+)\s*(==|<|>)\s*(\d+)\s*\)?"

    output_clauses = []

    for match in re.finditer(pattern, precondition):
        var, op, val = match.groups()
        if var not in varmap:
            raise ValueError(f"Variable {var} not found in varmap.")
        if op == "==":
            output_clauses.extend(expand_eq(var, val))
        elif op == "<":
            output_clauses.extend(expand_lt_optimized(var, val))
        elif op == ">":
            if int(val) == 0:
                # (z > 0) == any bit of z is 1
                output_clauses.append(" || ".join([f"{bit}" for bit in varmap[var]]))
            else:
                output_clauses.extend(
                    [
                        f"!(({clause}))"
                        for clause in expand_lt_optimized(var, str(int(val) + 1))
                    ]
                )

        else:
            raise NotImplementedError(f"Operator {op} not supported.")

        if not output_clauses:
            raise ValueError(f"No boolean clauses generated from: {precondition}")

    return "(" + ") && (".join(output_clauses) + ")"


def Booleanize_precondition(progname, precondition_hl):
    with open(
        os.path.join(CURRENT_PATH, "candidate_files", progname + ".json"), "r"
    ) as file:
        data = json.load(file)

    variable_map = data["Program_variables"]["Varmap"]
    bool_init = booleanize(precondition_hl, variable_map)

    return bool_init


def generate_bit_names(var, num_bits):
    return [f"{var}{i}" for i in reversed(range(num_bits))]


def update_varmap(data, old_varmap, vars_to_expand, num_bits):

    # random_bools = set(data.get("Random_variables", {}).get("Bools", []))

    new_varmap = {}
    new_bools = []
    # print(vars_to_expand)
    for var, old_bits in old_varmap.items():
        if var in vars_to_expand:
            new_bits = generate_bit_names(var, num_bits)
            # print(new_bits)
            new_varmap[var] = new_bits
            # print(new_varmap)
        else:
            # Do NOT expand atomic booleans like 'flip'
            new_varmap[var] = old_bits
        for bit in new_bits:
            if bit not in new_bools:
                new_bools.append(bit)

    for var in old_varmap:
        if var not in vars_to_expand:
            for bit in old_varmap[var]:  # should be length 1
                if bit not in new_bools:
                    new_bools.append(bit)
    # print(new_varmap)
    # print(new_bools)
    # Add random variables
    # new_bools.update(random_bools)

    # Update JSON
    data["Program_variables"]["Varmap"] = new_varmap
    data["Program_variables"]["Bools"] = new_bools

    return data


def get_config(progname):
    with open(
        os.path.join(CURRENT_PATH, "candidate_files", progname + ".json"), "r"
    ) as f:
        config = json.load(f)
    return config


def generate_random_cnf(vars, num_clauses, clause_size):
    cnf = []
    for _ in range(num_clauses):
        clause = random.sample(vars, k=clause_size)  # Select `clause_size` variables
        clause = [
            random.choice([v, f"!{v}"]) for v in clause
        ]  # Randomly negate some literals
        cnf.append(clause)
    return cnf


# Example Usage


def uniform_fisher_yates_sample(variables, subset_size, rng):
    """Uniformly sample a subset of given size using Fisher-Yates shuffle with a high-quality PRNG."""
    shuffled = variables[:]  # Copy the list
    for i in range(subset_size):
        j = rng.integers(i, len(variables))  # High-quality uniform integer
        shuffled[i], shuffled[j] = shuffled[j], shuffled[i]  # Swap
    return shuffled[:subset_size]  # Return first k elements


def random_satisfiable_cnf(variables, number_of_clauses, seed=None):
    """
    Generate a random but satisfiable CNF formula over the given variables using high-quality uniform sampling.

    Parameters:
      variables (list): List of variable names (e.g., ["x1", "x2", "x3", ...]).
      number_of_clauses (int): Number of clauses to generate.
      seed (int, optional): Random seed for reproducibility.

    Returns:
      cnf (list): A list of unique clauses, where each clause is a list of tuples (var, polarity).
      assignment (dict): The satisfying assignment that makes the formula true.
    """

    # Use a high-quality PRNG (PCG64 or MT19937)
    rng = np.random.default_rng(seed)

    # Step 1: Generate a random assignment for all variables
    assignment = {var: bool(rng.integers(0, 2)) for var in variables}

    cnf = set()  # Using a set to avoid duplicate clauses
    while len(cnf) < number_of_clauses:
        # Randomly choose a clause size (at least one literal).
        clause_size = rng.integers(1, len(variables) + 1)
        # clause_size = 1
        # print(clause_size)
        # Use Fisher-Yates shuffle with a good PRNG
        clause_vars = uniform_fisher_yates_sample(variables, clause_size, rng)

        clause = []
        for var in clause_vars:
            polarity = bool(rng.integers(0, 2))  # True or False
            clause.append((var, polarity))

        # Ensure clause is satisfied by the chosen assignment
        if not any(
            (assignment[var] if polarity else not assignment[var])
            for var, polarity in clause
        ):
            # If no literal is satisfied, flip one randomly chosen literal to satisfy it
            i = rng.integers(0, len(clause))
            var, _ = clause[i]
            clause[i] = (var, assignment[var])

        # Convert clause to a **sorted tuple** to prevent duplicate unordered clauses
        clause_tuple = tuple(sorted(clause))
        cnf.add(clause_tuple)

    # Convert the set back to a list of lists
    return [list(clause) for clause in cnf], assignment


# Example usage:
if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--progname", type=str, help="default = Geo0", default="Geo0", dest="progname"
    )
    parser.add_argument(
        "--init_states",
        type=str,
        help="default = True",
        default="True",
        dest="init_states",
    )
    parser.add_argument(
        "--num_bits", type=int, help="default = 16", default=16, dest="num_bits"
    )
    args = parser.parse_args()
    progname = args.progname
    precondition = args.init_states
    num_bits = int(args.num_bits)

    # init_states = precondition

    if progname not in ("Duel", "Prinsys", "BiasDir"):
        with open(
            os.path.join(CURRENT_PATH, "candidate_files", progname + ".json"), "r"
        ) as file:
            data_old = json.load(file)
            old_varmap = data_old["Program_variables"]["Varmap"]
            vars_to_expand = {
                v
                for v in data_old["Program_variables"]["Vars"]
                if len(old_varmap.get(v, [])) >= 2
            }

        updated_data = update_varmap(
            data_old, old_varmap, vars_to_expand, args.num_bits
        )
        with open(
            os.path.join(CURRENT_PATH, "candidate_files", progname + ".json"), "w"
        ) as file:
            json.dump(updated_data, file, indent=4)

    with open(
        os.path.join(CURRENT_PATH, "candidate_files", progname + ".json"), "r"
    ) as file:
        data = json.load(file)
        loop_guard = data["Loop guard"]
        if progname not in (
            "Temp",
            "Fair",
            "BigGeo0",
            "BigGeo1",
            "BigGeo2",
            "BiasDir",
            "Duel",
            "GeoAr",
            "Unif2",
            "Unif4",
        ):
            loop_guard = Booleanize_precondition(progname, loop_guard)

        program_variables = data["Program_variables"]["Vars"]
        variable_map = data["Program_variables"]["Varmap"]
        if progname not in ("BigGeo2", "BigGeo0"):
            init_states = Booleanize_precondition(progname, precondition)
        else:
            init_states = precondition
        variables = data["Program_variables"]["Bools"]
        data["Initial states"]["Expression"] = init_states + " && " + loop_guard
        data["Initial states"]["Loop guard"] = loop_guard

    with open(
        os.path.join(CURRENT_PATH, "candidate_files", progname + ".json"), "w"
    ) as file:
        json.dump(data, file, indent=4)

    """
    number_of_clauses = 10
    cnf_formula, satisfying_assignment = random_satisfiable_cnf(variables, number_of_clauses)
    clauses = list()
    #print(cnf_formula)
    #print("Random Satisfiable CNF Formula:")
    for clause in cnf_formula:
        clauses.append(" || ".join([f"{'' if polarity else '!'}{var}" for var, polarity in clause]))
        #print(clauses)

    cnf_output = "(" + ") && (".join(clauses) + ")"
        
    #print("\nSatisfying Assignment:")
    
    for var, val in satisfying_assignment.items():
        print(f"{var} = {val}")
    
    print(cnf_output)
    """


"""
# Example usage:
if __name__ == "__main__":
    variables = ["x1", "x2", "x3", "x4", "x5"]
    number_of_clauses = 10
    cnf_formula, satisfying_assignment = random_satisfiable_cnf(variables, number_of_clauses)
    
    print("Random Satisfiable CNF Formula:")
    for clause in cnf_formula:
        print(" OR ".join([f"{'' if polarity else '~'}{var}" for var, polarity in clause]))
    
    print("\nSatisfying Assignment:")
    for var, val in satisfying_assignment.items():
        print(f"{var} = {val}")




        if (progname == "Geo0"):

        variables = ["z7", "z6", "z5", "z4", "z3", "z2", "z1", "z0"]
    if (progname == "Prinsys"):
        variables = ["x1", "x0"]
    if (progname == "Detm"):
        variables = ["x7", "x6", "x5", "x4", "x3", "x2", "x1", "x0", "count7", "count6", "count5", "count4", "count3", "count2", "count1", "count0"]
    if (progname == "Sum0"):
        variables = ["x7", "x6", "x5", "x4", "x3", "x2", "x1", "x0", "n7", "n6", "n5", "n4", "n3", "n2", "n1", "n0"]
    if (progname == "GeoAr"):
        variables = ["x7", "x6", "x5", "x4", "x3", "x2", "x1", "x0", "y7", "y6", "y5", "y4", "y3", "y2", "y1", "y0"]
    if (progname == "BigGeo0"):
        variables = ["z15", "z14", "z13", "z12", "z11", "z10", "z9", "z8", "z7", "z6", "z5", "z4", "z3", "z2", "z1", "z0"]
    if (progname == "Fair"):
        variables = ["count7", "count6", "count5", "count4", "count3", "count2", "count1", "count0"]
    if (progname == "LinExp"):
        variables = ["count7", "count6", "count5", "count4", "count3", "count2", "count1", "count0", "n7", "n6", "n5", "n4", "n3", "n2", "n1"]
    if (progname == "RevBin"):
        variables = ["z7", "z6", "z5", "z4", "z3", "z2", "z1", "z0", "x7", "x6", "x5", "x4", "x3", "x2", "x1", "x0"]
    if (progname == "DepRV"):
        variables = ["y7", "y6", "y5", "y4", "y3", "y2", "y1", "y0", "n7", "n6", "n5", "n4", "n3", "n2", "n1", "x7", "x6", "x5", "x4", "x3", "x2", "x1", "x0"]
    if (progname == "Mart"):
        variables = ["c7", "c6", "c5", "c4", "c3", "c2", "c1", "c0", "b7", "b6", "b5", "b4", "b3", "b2", "b1", "b0", "rounds7", "rounds6", "rounds5", "rounds4", "rounds3", "rounds2", "rounds1", "rounds0"]
    if (progname == "Bin0"):
        variables = ["y7", "y6", "y5", "y4", "y3", "y2", "y1", "y0", "n7", "n6", "n5", "n4", "n3", "n2", "n1", "x7", "x6", "x5", "x4", "x3", "x2", "x1", "x0"]
    if (progname == "Bin1"):
        variables = ["M7", "M6", "M5", "M4", "M3", "M2", "M1", "M0", "n7", "n6", "n5", "n4", "n3", "n2", "n1", "n0", "x7", "x6", "x5", "x4", "x3", "x2", "x1", "x0"]
    if (progname == "Duel"):
        variables = ["c","t"]
"""

# Example usage:
