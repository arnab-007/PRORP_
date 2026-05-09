import z3
import math
import json
import re

def dump_var_mapping(var_map, filename):
    json_filename = f"{filename}_var_mapping"  # Ensure proper JSON extension
    with open(json_filename, "w") as f:
        json.dump({str(key): value for key, value in var_map.items()}, f, indent=4)


def output_dimacs(cnf_goal, filename="problem.cnf"):
    variable_map = {}
    var_counter = 1
    for clause in cnf_goal:
        if z3.is_or(clause):  # Multiple literals
            for literal in clause.children():
                var = literal.arg(0) if z3.is_not(literal) else literal
                if var not in variable_map:
                    variable_map[var] = var_counter
                    var_counter += 1
        else:  # Single literal (unit clause)
            var = clause.arg(0) if z3.is_not(clause) else clause
            if var not in variable_map:
                variable_map[var] = var_counter
                var_counter += 1

    # Write DIMACS CNF to file
    with open(f"{filename}_cnf", "w") as f:
        f.write(f"p cnf {len(variable_map)} {len(cnf_goal)}\n")

        for clause in cnf_goal:
            if z3.is_or(clause):  # Handle OR clauses
                for literal in clause.children():
                    var = literal.arg(0) if z3.is_not(literal) else literal
                    dimacs_var = variable_map[var]
                    f.write(f"{'-' if z3.is_not(literal) else ''}{dimacs_var} ")
            else:  # Handle unit clauses
                var = clause.arg(0) if z3.is_not(clause) else clause
                dimacs_var = variable_map[var]
                f.write(f"{'-' if z3.is_not(clause) else ''}{dimacs_var} ")

            f.write("0\n")  # End of clause

    dump_var_mapping(variable_map, filename)

    print(f"\nCNF constraints successfully written to {filename}")


def add_bitmap(g_obj, bit_vec_len, var):
    bitmap = {}
    if bit_vec_len == 1:
        bitmap[f"{var}"] = z3.Bool(f"{var}")
        mask = z3.BitVecSort(bit_vec_len).cast(math.pow(2, 0))
        g_obj.add(bitmap[f"{var}"] == ((var & mask) == mask))
        return g_obj
    else:
        for i in range(bit_vec_len):
            bitmap[(f"{var}", i)] = z3.Bool(f"{var}"[:-2] + str(i) + f"{var}"[-2:])
            mask = z3.BitVecSort(bit_vec_len).cast(math.pow(2, i))
            g_obj.add(bitmap[(f"{var}", i)] == ((var & mask) == mask))
        return g_obj

    


# def add_bitmap(goal, bit_vec_len, bitvec_var):
    
#     bitmap = {}
#     full_name = bitvec_var.decl().name()
#     match = re.match(r"([a-zA-Z_]+)(\d+)$", full_name)
#     if not match:
#         raise ValueError(f"Cannot parse variable name '{full_name}' into prefix and suffix.")

#     prefix, suffix = match.group(1), match.group(2)

   
#     for i in range(bit_vec_len):
#         bool_name = f"{prefix}{i}_{suffix}"   # e.g., x0_2
#         bool_var = z3.Bool(bool_name)
#         mask = z3.BitVecVal(1 << i, bit_vec_len)
#         goal.add(bool_var == ((bitvec_var & mask) != 0))
#         bitmap[(prefix, i, suffix)] = bool_var

#     return bitmap



def check_status(constraints):
    solver = z3.Solver()
    solver.set("unsat_core", True)
    # Add Named Constraints for Unsat Core Tracking
    for idx, cons in enumerate(constraints):
        solver.assert_and_track(cons, f"Cons{idx}")
    # Check SAT/UNSAT
    result = solver.check()
    if result == z3.sat:
        # print("SAT")
        model = solver.model()
        # print("\n=== Model ===")
        # for d in model.decls():
        #     print(f"{d.name()} = {model[d]}")

    elif result == z3.unsat:
        print("UNSAT (No solution found)")
        print("\n=== Unsat Core ===")
        for c in solver.unsat_core():
            print(c)  # Print the constraints that caused UNSAT

    else:
        print("Unknown result")


# Check if it is SAT or UNSAT
# solver = z3.Solver()
# solver.add(*g)

# if solver.check() == z3.sat:
#     print("SAT")
#     model = solver.model()
#     print("\n=== Model ===")
#     for d in model.decls():
#         print(f"{d.name()} = {model[d]}")
# else:
#     print("UNSAT (No solution found)")


# solver = z3.Solver()
# solver.add(z3.UGT(x, 2))

# if solver.check() == z3.sat:
#     model = solver.model()
#     print("\n=== Variable Mapping ===")
#     for d in model.decls():
#         print(f"{d.name()} = {model[d]}")


# x, y, z = z3.BitVecs("x y z", 16)
# g = z3.Goal()
# g.add(x == y, z > z3.If(x < 0, x, -x))
# print(g)
# # t is a tactic that reduces a Bit-vector problem into propositional CNF
# t = z3.Then("simplify", "bit-blast", "tseitin-cnf")
# subgoal = t(g)
# assert len(subgoal) == 1
# # Traverse each clause of the first subgoal
# for c in subgoal[0]:
#     print(c)
