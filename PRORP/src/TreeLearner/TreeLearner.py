import argparse
import copy
import json
import os
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
from pathlib import Path
import logging
import pandas as pd

from DecisionTreeLearner import CustomDecisionTree
from utils import *
import numpy as np

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(message)s")


def df_to_dnf(df):
    feature_cols = [c for c in df.columns if c not in {"label", "weight", "member"}]

    clauses = []

    for _, row in df.iterrows():
        if row["label"] != 1:
            continue

        lits = []
        for f in feature_cols:
            if int(row[f]) == 1:
                lits.append(f)
            else:
                lits.append(f"!{f}")

        clauses.append("(" + " && ".join(lits) + ")")

    return " || ".join(clauses)


def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--progname", type=str, default="Geo0", dest="progname")
    parser.add_argument("--epsilon", type=float, default=0.05, dest="epsilon")
    parser.add_argument("--eta", type=float, default=0.05, dest="eta")
    parser.add_argument("--delta", type=float, default=0.1, dest="delta")
    parser.add_argument("--iters", type=int, default=4, dest="iters")
    parser.add_argument("--num_bits", type=int, default=16, dest="num_bits")
    parser.add_argument("--init_states", type=str, default="init", dest="initstates")
    parser.add_argument("--flag", type=int, default=1, dest="flag")
    args = parser.parse_args()
    return args


def read_json_with_lock(filepath):
    from filelock import FileLock

    lock = FileLock(str(filepath) + ".lock")
    with lock:
        with open(filepath, "r") as f:
            return json.load(f)


def write_json_with_lock(filepath, data):
    from filelock import FileLock

    lock = FileLock(str(filepath) + ".lock")
    with lock:
        with open(filepath, "w") as f:
            json.dump(data, f, indent=4)


def get_latest_result_file(directory: Path, prefix: str, progname: str) -> Path:
    files = sorted(directory.glob(f"{prefix}_{progname}_*.json"))
    if not files:
        return None
    return files[-1]


def remove_file_if_exists(path: Path):
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def read_validifier_samples(progname, valid_results_directory):
    valid_results_directory = Path(valid_results_directory)
    valid_results_directory.mkdir(parents=True, exist_ok=True)
    files = sorted(valid_results_directory.glob(f"exp_{progname}_*.json"))
    if not files:
        logging.warning(f"No validifier results found for {progname}")
        return {"output_dict": {"counterexamples": {}, "Validifier_value": 0}}, 0
    latest = files[-1]
    data = read_json_with_lock(latest)
    value = data["output_dict"]["Validifier_value"]
    # Remove the file after reading if not the only one
    if len(files) > 1:
        remove_file_if_exists(latest)
    return data, value


def read_distestimate_samples(progname, dist_results_directory):
    dist_results_directory = Path(dist_results_directory)
    dist_results_directory.mkdir(parents=True, exist_ok=True)
    files = sorted(dist_results_directory.glob(f"exp_{progname}_*.json"))
    if not files:
        logging.warning(f"No distestimate results found for {progname}")
        return {"output_dict": {"counterexamples": {}, "DistEstimate_value": 0}}, 0
    latest = files[-1]
    data = read_json_with_lock(latest)
    value = data["output_dict"]["DistEstimate_value"]
    # Remove the file after reading if not the only one
    if len(files) > 1:
        remove_file_if_exists(latest)
        remove_file_if_exists(latest.with_suffix(".json.lock"))
    return data, value


def dump_candidate(progname, candidate, parent_path):
    cand_file = Path(parent_path) / "candidate_files" / f"{progname}.json"
    with open(cand_file, "r") as file:
        data = json.load(file)
        data["Candidate"]["Expression"] = candidate
    with open(cand_file, "w") as file:
        json.dump(data, file, indent=4)


def execute_verifier(verifier_trigger_path, progname, epsilon, delta, k, num_bits):
    import subprocess

    try:
        subprocess.run(
            [
                "python3",
                verifier_trigger_path,
                "--progname",
                str(progname),
                "--epsilon",
                str(epsilon),
                "--delta",
                str(delta),
                "--iters",
                str(k),
                "--num_bits",
                str(num_bits),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        logging.error(f"Subprocess failed: {e.stderr}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")


def get_ratio(tree, mutation, leaf, distCurr, validCurr):
    if mutation == "split":
        try:
            gainvalid, gaindist = tree.split_node_bounds(leaf)
        except ValueError:
            return None
        move = ((gaindist + gainvalid), leaf, "split")
        return move
    elif mutation == "prune":
        try:
            tree_copy = copy.deepcopy(tree)
            tree_copy.prune_node(leaf)
        except ValueError:
            return None
        error_bounds = tree_copy.get_error_bounds()
        gaindist = distCurr - error_bounds["dist_error"]
        gainvalid = validCurr - error_bounds["valid_error"]
        if gaindist <= 0 or gainvalid <= 0:
            return None
        move = ((gaindist + gainvalid), leaf, "prune")
        return move


def Normalize(moves):
    total = sum([move[0] for move in moves])
    if total == 0:
        return [(1, move[1], move[2]) for move in moves]
    return [(move[0] / total, move[1], move[2]) for move in moves]


def MuteTree(tree, distUser, validUser, timeout=600):
    start = time.time()
    error_bounds = tree.get_error_bounds()
    logging.info(f"Before Muattion{error_bounds}")
    distCurr, validCurr = error_bounds["dist_error"], error_bounds["valid_error"]
    set_of_mutations = ["split"]
    mutation_counter = {"split": 0, "prune": 0}
    while time.time() - start < timeout:
        leaf_ids = tree.get_all_leaf_nodes()
        moves = []
        for mutation in set_of_mutations:
            with ThreadPoolExecutor(
                max_workers=min(20, int(0.7 * os.cpu_count()))
            ) as executor:
                mapped_moves = list(
                    filter(
                        None,
                        executor.map(
                            lambda leaf: get_ratio(
                                tree, mutation, leaf, distCurr, validCurr
                            ),
                            leaf_ids,
                        ),
                    )
                )
            moves += mapped_moves
        if not moves:
            logging.info("No more valid moves found. Exiting.")
            break
        moves = Normalize(moves)
        moves.sort(key=lambda x: x[0], reverse=True)
        logging.info(f"{moves=}")
        if random.random() < 0.9:
            _, leaf_id, mutation = moves[0]
        else:
            _, leaf_id, mutation = random.choices(
                moves, weights=[move[0] for move in moves]
            )[0]
        if mutation == "split":
            tree.split_node(leaf_id)
        elif mutation == "prune":
            tree.prune_node(leaf_id)
        error_bounds = tree.get_error_bounds()
        logging.info(f"After Mutation{error_bounds}")
        mutation_counter[mutation] += 1
        distCurr, validCurr = error_bounds["dist_error"], error_bounds["valid_error"]
        if distCurr <= distUser and validCurr <= validUser:
            logging.info("Successfully reached the desired user error bounds.")
            logging.info(f"Mutation counter: {mutation_counter}")
            return tree, distCurr, validCurr, mutation_counter
    logging.info(f"Mutation counter: {mutation_counter}")
    logging.info("Specified error bounds not met. Returning the last mutated tree.")
    return tree, distCurr, validCurr, mutation_counter


def TreeLearner():
    args = get_arguments()
    progname = args.progname
    epsilon = args.epsilon
    eta = args.eta
    delta = args.delta
    k = args.iters
    num_bits = args.num_bits
    init_states_FOL = args.initstates
    flag = args.flag

    PARENT_PATH = Path(__file__).resolve().parent.parent.parent
    DistEstimate_trigger_path = str(PARENT_PATH / "src/DistEstimate/DistEstimate.py")
    Validifier_trigger_path = str(PARENT_PATH / "src/Validifier/validifier.py")

    total_DistEstimate_time = total_TreeLearner_time = total_Validifier_time = 0
    config = get_config_prog(progname)
    prog_variables = config["Program_variables"]["Bools"]
    init_states_CNF = config["Initial states"]["Expression"]
    loop_guard = config["Initial states"]["Loop guard"]
    progvars = config["Program_variables"]["Vars"]
    progvarmap = config["Program_variables"]["Varmap"]

    if flag == 1:
        validifier_data, validifier_value = read_validifier_samples(
            progname, PARENT_PATH / "src/Validifier/Validifier_results"
        )
    else:
        validifier_data = {
            "output_dict": {"counterexamples": {}, "Validifier_value": 0}
        }
        validifier_value = 0

    distestimate_data, distestimate_value = read_distestimate_samples(
        progname, PARENT_PATH / "src/DistEstimate/DistEstimate_results"
    )
    initial_phase_start = time.time()
    number_of_vars = len(prog_variables)
    df = prepare_data(distestimate_data, validifier_data, prog_variables)
    if flag == 1:
        # for index, row in df.iterrows():
        #     print(row)
        X = df[list(df.columns[:-3])].values
        y = df["label"].values
        weights = df["weight"].values
        clf = CustomDecisionTree(max_depth=2 * int(number_of_vars))
        clf.fit_initial(X, y, weights, feature_names=df.columns[:-3])
        predictions = clf.predict(
            df[list(df.columns[:-3])].values,
            expected_labels=df["label"].values,
            weights=df["weight"].values,
            member=df["member"].values,
        )
        initial_dnf = clf.tree_to_dnf()
        intermediate_tree = clf
        logging.info(f"Initial phase DNF: {initial_dnf}")
    else:
        feature_cols = [c for c in df.columns if c not in {"label", "weight", "member"}]
        X = df[feature_cols].values
        y = df["label"].values
        weights = df["weight"].values
        initial_dnf = df_to_dnf(df)
        logging.info(f"Initial phase DNF: {initial_dnf}")

    initial_phase_TreeLearner_time = time.time() - initial_phase_start
    if progname == "Unif2" or progname == "Unif4":
        dump_candidate(progname, initial_dnf, PARENT_PATH)
    else:
        dump_candidate(progname, modify_cand(initial_dnf, loop_guard), PARENT_PATH)
    initial_validifier_start_time = time.time()
    execute_verifier(Validifier_trigger_path, progname, eta, delta, k, num_bits)
    initial_phase_validifier_time = time.time() - initial_validifier_start_time
    initial_DistEstimate_start_time = time.time()
    execute_verifier(DistEstimate_trigger_path, progname, epsilon, delta, k, num_bits)
    initial_phase_DistEstimate_time = time.time() - initial_DistEstimate_start_time
    validifier_data, validifier_value = read_validifier_samples(
        progname, PARENT_PATH / "src/Validifier/Validifier_results"
    )
    distestimate_data, distestimate_value = read_distestimate_samples(
        progname, PARENT_PATH / "src/DistEstimate/DistEstimate_results"
    )
    total_DistEstimate_time += initial_phase_DistEstimate_time
    total_Validifier_time += initial_phase_validifier_time
    total_TreeLearner_time += initial_phase_TreeLearner_time
    next_dnf = initial_dnf
    phase = 1
    total_mutation_counter = {"split": 0, "prune": 0}

    while (
        (distestimate_value >= epsilon or validifier_value >= eta)
        and (time.time() - initial_phase_start < 7200)
    ) and (flag == 1):
        logging.info(f"Phase: {phase + 1}")
        logging.info(f"DistEstimate value: {distestimate_value}")
        logging.info(f"Validifier value: {validifier_value}")
        phase += 1
        logging.info(
            f"Phase {phase} DNF before prediction: {intermediate_tree.tree_to_dnf()}"
        )
        next_phase_start = time.time()
        df_next = prepare_data(distestimate_data, validifier_data, prog_variables)
        intermediate_tree.predict(
            df_next[list(df_next.columns[:-3])].values,
            expected_labels=df_next["label"].values,
            weights=df_next["weight"].values,
            member=df_next["member"].values,
        )
        logging.info(
            f"Phase {phase} DNF after prediction: {intermediate_tree.tree_to_dnf()}"
        )
        (
            final_tree,
            tree_dist_error,
            tree_valid_error,
            mutation_counter,
        ) = MuteTree(intermediate_tree, epsilon, eta)
        Next_phase_DNF = final_tree.tree_to_dnf()
        for mutation, mutation_count in mutation_counter.items():
            total_mutation_counter[mutation] = (
                total_mutation_counter.get(mutation, 0) + mutation_count
            )
        next_phase_TreeLearner_time = time.time() - next_phase_start
        if progname == "Unif2":
            dump_candidate(progname, Next_phase_DNF, PARENT_PATH)
        else:
            dump_candidate(
                progname, modify_cand(Next_phase_DNF, loop_guard), PARENT_PATH
            )
        next_phase_validifier_start_time = time.time()
        execute_verifier(Validifier_trigger_path, progname, eta, delta, k, num_bits)
        next_phase_validifier_time = time.time() - next_phase_validifier_start_time
        next_phase_distEstimate_start_time = time.time()
        execute_verifier(
            DistEstimate_trigger_path, progname, epsilon, delta, k, num_bits
        )
        next_phase_distEstimate_time = time.time() - next_phase_distEstimate_start_time
        validifier_data, validifier_value = read_validifier_samples(
            progname, PARENT_PATH / "src/Validifier/Validifier_results"
        )
        distestimate_data, distestimate_value = read_distestimate_samples(
            progname, PARENT_PATH / "src/DistEstimate/DistEstimate_results"
        )
        intermediate_tree = final_tree
        total_DistEstimate_time += next_phase_distEstimate_time
        total_Validifier_time += next_phase_validifier_time
        total_TreeLearner_time += next_phase_TreeLearner_time
        logging.info(f"Next phase total time: {time.time() - next_phase_start}")
        logging.info(f"Next phase DistEstimate time: {next_phase_distEstimate_time}")
        logging.info(f"Next phase Validifier time: {next_phase_validifier_time}")
        logging.info(f"Next phase TreeLearner time: {next_phase_TreeLearner_time}")
        next_dnf = intermediate_tree.tree_to_dnf()
        if tree_dist_error > epsilon or tree_valid_error > eta:
            logging.warning(
                f"Skipping tree: error bounds not met ({tree_dist_error:.3f}, {tree_valid_error:.3f})"
            )

    Final_DistEstimate_value = distestimate_value
    Final_Validifier_value = validifier_value
    if progname == "Unif2" or progname == "Unif4":
        Final_candidate = next_dnf
    else:
        Final_candidate = modify_cand(next_dnf, loop_guard)
    Final_simplified_candidate = summarize_dnf(Final_candidate, progvars, progvarmap)
    logging.info(f"Final DistEstimate value: {distestimate_value}")
    logging.info(f"Final Validifier value: {validifier_value}")
    logging.info(f"Final candidate learnt: {Final_candidate}")
    logging.info(
        f"Height of learnt decision tree: {analyze_candidate(Final_candidate)[1]}"
    )
    logging.info(
        f"Number of terms in the candidate DNF: {analyze_candidate(Final_candidate)[0]}"
    )
    logging.info(f"Total DistEstimate time: {total_DistEstimate_time}")
    logging.info(f"Total Validifier time: {total_Validifier_time}")
    logging.info(f"Total TreeLearner time: {total_TreeLearner_time}")

    output_dict = {
        "Initial states": init_states_FOL,
        "Number of iterations": k,
        "Epsilon": epsilon,
        "Eta": eta,
        "Delta": delta,
        "Total number of phases": phase,
        "Total number of splits": total_mutation_counter["split"],
        "Total number of prune": total_mutation_counter["prune"],
        "Total DistEstimate time": total_DistEstimate_time,
        "Total Validifier time": total_Validifier_time,
        "Total TreeLearner time": total_TreeLearner_time,
        "Total time (seconds)": total_DistEstimate_time
        + total_Validifier_time
        + total_TreeLearner_time,
        "Final DistEstimate_value": Final_DistEstimate_value,
        "Final Validifier_value": Final_Validifier_value,
        "Height of final tree": analyze_candidate(Final_candidate)[1],
        "Number of DNF terms in candidate": analyze_candidate(Final_candidate)[0],
        "Final simplified candidate": str(Final_simplified_candidate),
        "Final candidate": Final_candidate,
    }

    result_dir = Path(PARENT_PATH) / f"results/results_{progname}_{num_bits}bits"
    result_dir.mkdir(parents=True, exist_ok=True)
    idx = 1
    while (result_dir / f"exp_{epsilon}_{eta}_{idx}.json").exists():
        idx += 1
    write_json_with_lock(result_dir / f"exp_{epsilon}_{eta}_{idx}.json", output_dict)


if __name__ == "__main__":
    start_time = time.time()
    TreeLearner()
    end_time = time.time()
    logging.info(f"Total time (seconds): {end_time - start_time}")


# from DecisionTreeLearner import CustomDecisionTree
# from concurrent.futures import ThreadPoolExecutor

# # from new_ex import initial_dist_data, initial_valid_data, second_phase_dist_data, second_phase_valid_data
# import pandas as pd
# import argparse
# import numpy as np
# import copy
# import random
# import time
# import os
# import sys
# import json
# import filelock
# from filelock import FileLock
# import subprocess
# from utils import *
# import re
# from itertools import product
# import networkx as nx
# import matplotlib.pyplot as plt
# from collections import defaultdict

# # PATH = os.path.realpath("")


# def get_ratio(tree, mutation, leaf, distCurr, validCurr):
#     # print(mutation)
#     if mutation == "split":
#         try:
#             """If trying to split a leaf node that has only one datapoint, it will raise a ValueError.
#             In this case, we would like to discard this move and try another one."""
#             gainvalid, gaindist = tree.split_node_bounds(leaf)
#             # print("split")
#             # print(gainvalid,gaindist)
#         except ValueError:
#             return None
#         # error_bounds = tree.get_error_bounds()
#         leaf_node_ids = tree.get_all_leaf_nodes()
#         tree_height = max(len(str(leaf_node_id)) for leaf_node_id in leaf_node_ids) + 1
#         max_height = len(tree.feature_names)

#         # if tree_height > int(0.50 * max_height):
#         #     move = (
#         #         (gaindist + gainvalid) / 1.75,
#         #         leaf,
#         #         "split",
#         #     )
#         # else:
#         move = ((gaindist + gainvalid), leaf, "split")
#         return move

#     elif mutation == "prune":
#         try:
#             """If trying to prune the root node that is the only node in the tree, it will raise a ValueError."""
#             tree_copy = copy.deepcopy(tree)
#             tree_copy.prune_node(leaf)
#         except ValueError:
#             return None
#         error_bounds = tree_copy.get_error_bounds()
#         gaindist = distCurr - error_bounds["dist_error"]
#         gainvalid = validCurr - error_bounds["valid_error"]
#         # print("prune")
#         # print(gainvalid, gaindist)
#         if gaindist <= 0 or gainvalid <= 0:
#             return None
#         # print("Prune selected")

#         # if gaindist + gainvalid < 0:
#         #     return None
#         move = ((gaindist + gainvalid), leaf, "prune")
#         return move


# def Normalize(moves):
#     """I want to perform weighted normalization here"""
#     total = sum([move[0] for move in moves])
#     if total == 0:
#         return [(1, move[1], move[2]) for move in moves]
#     moves = [(move[0] / total, move[1], move[2]) for move in moves]
#     return moves


# def retrain_tree(tree):
#     complete_data = tree.collect_all_data()
#     X = complete_data[list(complete_data.columns[:-3])].values
#     y = complete_data["label"].values
#     weights = complete_data["weight"].values
#     clf = CustomDecisionTree(max_depth=X.shape[1])
#     clf.fit_initial(X, y, weights, feature_names=complete_data.columns[:-3])
#     predictions = clf.predict(
#         complete_data[list(complete_data.columns[:-3])].values,
#         expected_labels=complete_data["label"].values,
#         weights=complete_data["weight"].values,
#         member=complete_data["member"].values,
#     )
#     error_bounds = clf.get_error_bounds()
#     distCurr, validCurr = error_bounds["dist_error"], error_bounds["valid_error"]
#     return clf, distCurr, validCurr, {}


# # TODO Need to record total mutations happening in all the phases
# def MuteTree(tree, distUser, validUser):
#     start = time.time()
#     error_bounds = tree.get_error_bounds()
#     distCurr, validCurr = error_bounds["dist_error"], error_bounds["valid_error"]
#     # set_of_mutations = ["split", "prune"]
#     set_of_mutations = ["split"]
#     mutation_counter = {"split": 0, "prune": 0}
#     while time.time() - start < 600:

#         leaf_ids = tree.get_all_leaf_nodes()
#         moves = []
#         for mutation in set_of_mutations:
#             with ThreadPoolExecutor(
#                 max_workers = min(20, int(0.7 * os.cpu_count()))
#             ) as executor:  # You can adjust number of workers
#                 mapped_moves = list(
#                     filter(
#                         None,
#                         executor.map(
#                             lambda leaf: get_ratio(
#                                 tree, mutation, leaf, distCurr, validCurr
#                             ),
#                             leaf_ids,
#                         ),
#                     )
#                 )
#             moves += mapped_moves
#         if not moves:
#             print("No more valid moves found. Exiting.")
#             break  # Exit the loop if no moves are available


#         moves = Normalize(moves)
#         moves.sort(key=lambda x: x[0], reverse=True)
#         if random.random() < 0.9: # 90% of the time, be greedy
#             _, leaf_id, mutation = moves[0]
#         else: # 10% of the time, make a random move to escape a local minimum
#             _, leaf_id, mutation = random.choices(moves, weights=[move[0] for move in moves])[0]
#         # _, leaf_id, mutation = random.choices( moves, weights=[move[0] for move in moves] )[0]
#         if mutation == "split":
#             tree.split_node(leaf_id)
#         elif mutation == "prune":
#             tree.prune_node(leaf_id)
#         error_bounds = tree.get_error_bounds()
#         mutation_counter[mutation] += 1
#         # tree_sequence[tree] = error_bounds
#         distCurr, validCurr = error_bounds["dist_error"], error_bounds["valid_error"]
#         if distCurr <= distUser and validCurr <= validUser:
#             print("Successfully reached the desired user error bounds.")
#             print("Mutation counter:", mutation_counter)
#             return tree, distCurr, validCurr, mutation_counter

#     print("Mutation counter:", mutation_counter)
#     print("Specified error bounds not met. Returning the last mutated tree.")
#     return tree, distCurr, validCurr, mutation_counter


# def get_arguments():
#     parser = argparse.ArgumentParser()

#     parser.add_argument(
#         "--progname", type=str, help="default = Geo0", default="Geo0", dest="progname"
#     )
#     parser.add_argument(
#         "--epsilon", type=float, help="default = 0.05", default=0.05, dest="epsilon"
#     )
#     parser.add_argument(
#         "--eta", type=float, help="default = 0.05", default=0.05, dest="eta"
#     )
#     parser.add_argument(
#         "--delta", type=float, help="default = 0.1", default=0.1, dest="delta"
#     )
#     parser.add_argument(
#         "--iters", type=int, help="default = 4", default=4, dest="iters"
#     )
#     parser.add_argument(
#         "--num_bits", type=int, help="default = 16", default=16, dest="num_bits"
#     )
#     parser.add_argument(
#         "--init_states", type=str, help="default = init", default="init", dest="initstates"
#     )
#     args = parser.parse_args()
#     progname = args.progname
#     epsilon = args.epsilon
#     eta = args.eta
#     delta = args.delta
#     k = args.iters
#     num_bits = args.num_bits
#     init_states_FOL = args.initstates
#     DistEstimate_trigger_path = os.path.join(
#         PARENT_PATH, "src/DistEstimate/", "DistEstimate.py"
#     )
#     Validifier_trigger_path = os.path.join(
#         PARENT_PATH, "src/Validifier/", "validifier.py"
#     )
#     return (
#         progname,
#         epsilon,
#         eta,
#         delta,
#         k,
#         DistEstimate_trigger_path,
#         Validifier_trigger_path,
#         num_bits,
#         init_states_FOL,
#     )


# def read_validifier_samples(
#     progname, valid_results_directory=f"{PARENT_PATH}/src/Validifier/Validifier_results"
# ):

#     if not os.path.exists(valid_results_directory):
#         os.makedirs(valid_results_directory)
#     existing_valid_files = os.listdir(valid_results_directory)
#     file_number = 1
#     while f"exp_{progname}_{file_number}.json" in existing_valid_files:
#         file_number += 1
#     if file_number > 1:
#         file_number = file_number - 1
#     # print(file_number)
#     validifier_path = os.path.join(
#         PARENT_PATH,
#         "src/Validifier/Validifier_results",
#         f"exp_{progname}_{file_number}.json",
#     )
#     # print(f"Checking for validifier results at: {validifier_path}")
#     if not os.path.exists(validifier_path):
#         print(f"Warning: No validifier results found at {validifier_path}")
#         validifier_value = 0
#         validifier_data = {
#             "output_dict": {"counterexamples": {}, "Validifier_value": 0}
#         }
#     else:
#         lock = FileLock(validifier_path + ".lock")  # Create a lock file
#         with lock:
#             with open(validifier_path, "r") as file:
#                 validifier_data = json.load(file)
#                 validifier_value = validifier_data["output_dict"]["Validifier_value"]

#     if file_number > 1:
#         os.remove(
#             os.path.join(
#                 valid_results_directory,
#                 f"exp_{progname}_{file_number}.json",
#             )
#         )

#     return validifier_data, validifier_value


# def read_distestimate_samples(
#     progname,
#     dist_results_directory=os.path.join(
#         PARENT_PATH, "src/DistEstimate/DistEstimate_results"
#     ),
# ):
#     if not os.path.exists(dist_results_directory):
#         os.makedirs(dist_results_directory)
#     existing_dist_files = os.listdir(dist_results_directory)
#     file_number = 1
#     while f"exp_{progname}_{file_number}.json" in existing_dist_files:
#         file_number += 1

#     if file_number > 1:
#         file_number = file_number - 1
#     # print(file_number)
#     DistEstimate_results_file_path = os.path.join(
#         PARENT_PATH,
#         "src/DistEstimate/DistEstimate_results",
#         f"exp_{progname}_{file_number}.json",
#     )
#     lock = FileLock(DistEstimate_results_file_path + ".lock")  # Create a lock file
#     with lock:
#         with open(
#             DistEstimate_results_file_path,
#             "r",
#         ) as file:
#             distestimate_data = json.load(file)
#             # initial_dist_list = distestimate_data["output_dict"]["counterexamples"]
#             distestimate_value = distestimate_data["output_dict"]["DistEstimate_value"]

#     if file_number > 1:

#         os.remove(
#             os.path.join(
#                 dist_results_directory,
#                 f"exp_{progname}_{file_number}.json",
#             )
#         )

#         os.remove(
#             os.path.join(
#                 dist_results_directory,
#                 f"exp_{progname}_{file_number}.json.lock",
#             )
#         )

#     return distestimate_data, distestimate_value


# def dump_candidate(progname, candidate):
#     with open(
#         os.path.join(PARENT_PATH, "candidate_files", progname + ".json"), "r"
#     ) as file:
#         data = json.load(file)
#         data["Candidate"]["Expression"] = candidate
#     with open(
#         os.path.join(PARENT_PATH, "candidate_files", progname + ".json"), "w"
#     ) as file:
#         json.dump(data, file, indent=4)


# def execute_verifier(verifier_trigger_path, progname, epsilon, delta, k, num_bits):
#     try:
#         # Run the first subprocess
#         result_verifier = subprocess.run(
#             [
#                 "python3",
#                 verifier_trigger_path,
#                 "--progname",
#                 str(progname),
#                 "--epsilon",
#                 str(epsilon),
#                 "--delta",
#                 str(delta),
#                 "--iters",
#                 str(k),
#                 "--num_bits",
#                 str(num_bits),
#             ],
#             capture_output=True,
#             text=True,
#             check=True,
#         )

#     except subprocess.CalledProcessError as e:
#         print(f"Subprocess failed with return code {e.returncode}")
#         print(f"Command: {e.cmd}")
#         print(f"Output: {e.output}")
#         print(f"Error: {e.stderr}")

#     except FileNotFoundError as e:
#         print(f"Executable not found: {e}")
#         print("Check that 'bash' is installed and paths are correct.")

#     except Exception as e:
#         print(f"An unexpected error occurred: {e}")


# def TreeLearner():

#     progname, epsilon, eta, delta, k, DistEstimate_trigger_path, Validifier_trigger_path, num_bits, init_states_FOL = (
#         get_arguments()
#     )

#     total_DistEstimate_time, total_TreeLearner_time, total_Validifier_time = 0, 0, 0
#     # cand_info = get_config_cand(progname)
#     config = get_config_prog(progname)
#     prog_variables = config["Program_variables"]["Bools"]
#     init_states_CNF = config["Initial states"]["Expression"]
#     loop_guard = config["Initial states"]["Loop guard"]
#     progvars = config["Program_variables"]["Vars"]
#     progvarmap = config["Program_variables"]["Varmap"]
#     print(init_states_CNF)
#     print(k)
#     validifier_data, validifier_value = read_validifier_samples(progname)
#     distestimate_data, distestimate_value = read_distestimate_samples(progname)
#     initial_phase_start = time.time()

#     number_of_vars = len(prog_variables)
#     df = prepare_data(distestimate_data, validifier_data, prog_variables)
#     X = df[list(df.columns[:-3])].values
#     y = df["label"].values
#     weights = df["weight"].values
#     clf = CustomDecisionTree(max_depth=2 * int(number_of_vars))
#     clf.fit_initial(X, y, weights, feature_names=df.columns[:-3])

#     predict_start = time.time()
#     predictions = clf.predict(
#         df[list(df.columns[:-3])].values,
#         expected_labels=df["label"].values,
#         weights=df["weight"].values,
#         member=df["member"].values,
#     )
#     print("Prediction time :", time.time() - predict_start)
#     # clf.save_tree(output_file=f"{PATH}/intermediate/{progname}_initial_tree")
#     print("Initial phase DNF:", clf.tree_to_dnf())

#     initial_phase_TreeLearner_time = time.time() - initial_phase_start
#     dump_candidate(progname, modify_cand(clf.tree_to_dnf(), loop_guard))

#     initial_validifier_start_time = time.time()
#     execute_verifier(Validifier_trigger_path, progname, eta, delta, k, num_bits)
#     initial_phase_validifier_time = time.time() - initial_validifier_start_time
#     initial_DistEstimate_start_time = time.time()
#     execute_verifier(DistEstimate_trigger_path, progname, epsilon, delta, k, num_bits)
#     initial_phase_DistEstimate_time = time.time() - initial_DistEstimate_start_time
#     # clf.save_tree(f"{PARENT_PATH}/intermediate/{progname}_initial_tree.png")
#     # print("Initial phase DistEstimate time :", initial_phase_DistEstimate_time)
#     validifier_data, validifier_value = read_validifier_samples(progname)
#     distestimate_data, distestimate_value = read_distestimate_samples(progname)
#     # print("Initial phase time :", time.time() - initial_phase_start)
#     total_DistEstimate_time += initial_phase_DistEstimate_time
#     total_Validifier_time += initial_phase_validifier_time
#     total_TreeLearner_time += initial_phase_TreeLearner_time
#     intermediate_tree = clf
#     phase = 1

#     total_mutation_counter = {"split": 0, "prune": 0}

#     while (distestimate_value >= epsilon or validifier_value >= eta) and (
#         time.time() - initial_phase_start < 7200
#     ):

#         print("Phase :", phase + 1)
#         print("DistEstimate value:", distestimate_value)
#         print("Validifier value:", validifier_value)
#         phase += 1
#         # log_error(
#         #     f"Phase:{phase}:(T1, D1) Learner errors",
#         #     intermediate_tree.get_error_bounds(),
#         # )
#         # df_verify = clf.collect_all_data()
#         # log_error(
#         #     f"Phase:{phase}:(T1, D1) DNF errors",
#         #     get_verified_error_bounds(df_verify, intermediate_tree.tree_to_dnf()),
#         # )

#         # # df_verify = intermediate_tree.collect_all_data()

#         # # log_error(
#         # #     f"Next phase: {phase}_D1 tree DNF errors",
#         # #     get_verified_error_bounds(df_verify, intermediate_tree.tree_to_dnf()),
#         # # )

#         print(f"Phase {phase} DNF before prediction:", intermediate_tree.tree_to_dnf())
#         next_phase_start = time.time()
#         df_next = prepare_data(distestimate_data, validifier_data, prog_variables)
#         intermediate_tree.predict(
#             df_next[list(df_next.columns[:-3])].values,
#             expected_labels=df_next["label"].values,
#             weights=df_next["weight"].values,
#             member=df_next["member"].values,
#         )
#         # log_error(
#         #     f"Phase:{phase}:(T1, D2) Learner errors",
#         #     intermediate_tree.get_error_bounds(),
#         # )

#         # df_verify = intermediate_tree.collect_all_data()

#         print(f"Phase {phase} DNF after prediction:", intermediate_tree.tree_to_dnf())

#         # log_error(
#         #     f"Phase:{phase} (T2, D1) DNF errors",
#         #     get_verified_error_bounds(df_verify, intermediate_tree.tree_to_dnf()),
#         # )
#         (
#             final_tree,
#             tree_dist_error,
#             tree_valid_error,
#             mutation_counter,
#         ) = MuteTree(intermediate_tree, epsilon, eta)
#         Next_phase_DNF = final_tree.tree_to_dnf()
#         for mutation, mutation_count in mutation_counter.items():
#             total_mutation_counter[mutation] = (
#                 total_mutation_counter.get(mutation, 0) + mutation_count
#             )
#         next_phase_TreeLearner_time = time.time() - next_phase_start
#         dump_candidate(progname, modify_cand(Next_phase_DNF, loop_guard))
#         next_phase_validifier_start_time = time.time()
#         execute_verifier(Validifier_trigger_path, progname, eta, delta, k, num_bits)
#         next_phase_validifier_time = time.time() - next_phase_validifier_start_time
#         next_phase_distEstimate_start_time = time.time()
#         execute_verifier(DistEstimate_trigger_path, progname, epsilon, delta, k, num_bits)
#         next_phase_distEstimate_time = time.time() - next_phase_distEstimate_start_time
#         validifier_data, validifier_value = read_validifier_samples(progname)
#         distestimate_data, distestimate_value = read_distestimate_samples(progname)
#         intermediate_tree = final_tree
#         total_DistEstimate_time += next_phase_distEstimate_time
#         total_Validifier_time += next_phase_validifier_time
#         total_TreeLearner_time += next_phase_TreeLearner_time

#         print("Next phase total time: ", time.time() - next_phase_start)
#         print("Next phase DistEstimate time :", next_phase_distEstimate_time)
#         print("Next phase Validifier time :", next_phase_validifier_time)
#         print("Next phase TreeLearner time :", next_phase_TreeLearner_time)

#         if tree_dist_error > epsilon or tree_valid_error > eta:
#             print(
#                 f"[Warning] Skipping tree: error bounds not met ({tree_dist_error:.3f}, {tree_valid_error:.3f})"
#             )
#             # break

#     # print(final_tree.print_leaf_datapoints())

#     # log_error("Logging for this program ended.\n")
#     Final_DistEstimate_value = distestimate_value
#     Final_Validifier_value = validifier_value
#     Final_candidate = intermediate_tree.tree_to_dnf()
#     Final_candidate = modify_cand(intermediate_tree.tree_to_dnf(), loop_guard)
#     Final_simplified_candidate = summarize_dnf(Final_candidate, progvars, progvarmap)
#     # final_tree.save_tree(output_file=f"{PATH}/final_trees/{progname}_final_tree")
#     print("Final DistEstimate value: ", distestimate_value)
#     print("Check for DistEstimate value :", Final_DistEstimate_value)
#     print("Final Validifier value: ", validifier_value)
#     print("Check for Validifier value :", Final_Validifier_value)
#     print("Final candidate learnt: ", Final_candidate)
#     print("Height of learnt decision tree: ", analyze_candidate(Final_candidate)[1])
#     print(
#         "Number of terms in the candidate DNF: ", analyze_candidate(Final_candidate)[0]
#     )
#     print("Total DistEstimate time :", total_DistEstimate_time)
#     print("Total Validifier time :", total_Validifier_time)
#     print("Total TreeLearner time :", total_TreeLearner_time)
#     output_dict = {
#         "Initial states": init_states_FOL,
#         "Number of iterations": k,
#         "Epsilon ": epsilon,
#         "Eta": eta,
#         "Delta ": delta,
#         "Total number of phases ": phase,
#         "Total number of splits": total_mutation_counter["split"],
#         "Total number of prune": total_mutation_counter["prune"],
#         "Total DistEstimate time ": total_DistEstimate_time,
#         "Total Validifier time ": total_Validifier_time,
#         "Total TreeLearner time ": total_TreeLearner_time,
#         "Total time (seconds) ": total_DistEstimate_time
#         + total_Validifier_time
#         + total_TreeLearner_time,
#         "Final DistEstimate_value": Final_DistEstimate_value,
#         "Final Validifier_value": Final_Validifier_value,
#         "Height of final tree": analyze_candidate(Final_candidate)[1],
#         "Number of DNF terms in candidate": analyze_candidate(Final_candidate)[0],
#         "Final simplified candidate": str(Final_simplified_candidate),
#         "Final candidate": Final_candidate,
#     }

#     result_dir = os.path.join(PARENT_PATH, f"results/results_{progname}_{num_bits}bits")
#     # result_dir = os.path.join(PARENT_PATH, f"results/results_k{k}_{num_bits}bits")
#     os.makedirs(result_dir, exist_ok=True)
#     idx = 1
#     while os.path.exists(os.path.join(result_dir, f"exp_{epsilon}_{eta}_{idx}.json")):
#         idx += 1

#     with open(os.path.join(result_dir, f"exp_{epsilon}_{eta}_{idx}.json"), "w") as f:
#         json.dump(output_dict, f, indent=4)

#     # final_tree.save_tree(output_file=f"{PATH}/final_trees/{progname}_final_tree")


# if __name__ == "__main__":

#     start_time = time.time()

#     TreeLearner()

#     end_time = time.time()

#     print("Total time (seconds) :", end_time - start_time)
