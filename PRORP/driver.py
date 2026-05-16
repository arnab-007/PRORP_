import subprocess
import os
import time
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
import itertools

CURRENT_PATH = os.path.realpath("")
SHARED_INPUT_DIR = "/shared/input/"  # Read-only shared input
OUTPUT_BASE_DIR = "/shared/output/"  # Workers write here

M = 512
p = 0.5


def get_init_states(progname, k, M):
    INIT_STATES_MAP = {
        "MultiMode1": [f"(x == 0 && n < {k})"],
        "Unif1": [f"(x == 0 && n < {k})"],
        "Unif2": ["(x == 251)"],
        "Unif4": ["(x == 0)"],
        "Unif3": [f"(x == 0 && n < {k})"],
        "Temp": ["(z == 0)"],
        "BigGeo0": ["(z14)"],
        "BigGeo1": ["(z == 0 && x == 16)"],
        "BigGeo2": ["(z == 0 && x == 16)", "(z < 64 && x < 16)"],
        "LinExp": [f"(count < 64 && n < {k})"],
        "Sum0": [f"(x == 64 && n < {k/2})"],
        "ModSum": [f"(x == 0 && n < {k})"],
        "Prinsys": ["(x == 0)"],
        "Detm": ["(count == 0)"],
        # "Fair": ["(count == 0)", "(count < 64)"],
        "Fair": ["(count < 64)"],
        "Mart": ["(c == 0 && b == 64 && rounds == 0)"],
        "GeoAr": ["(x == 0 && y == 0)"],
        "Bin0": [f"(x == 0 && y == 2 && n == {k})", f"(x < 64 && y == 2 && n == {k})"],
        "Bin1": [f"(x == 0 && n == {M - k/2})", f"(x < 32 && n == {M - k/2})"],
        "BinMod": [f"(x == 0 && n == {M - k/2})"],
        "Bin2": [
            f"(x == 0 && y == 8 && n < {k/2})",
            f"(x < 32 && y == 8 && n < {k/2})",
        ],
        "BiasDir": ["(x == 0 && y == 0)", "(x == 1 && y == 1)"],
        "DepRV": [
            f"(x == 0 && y == 0 && n == {k})",
        ],
        #   f"(x == 8 && y == 16 && n == {k})"],
        "RevBin": [f"(x == {k/2} && z < 16)"],
        "Duel": ["(t == 0)", "(t == 1)"],
    }
    return INIT_STATES_MAP.get(progname, [])


def ApproxInv(progname, iters, epsilon, eta, delta, mode, worker_id):
    print(
        f"Running PRORP({progname},k={iters}, ε={epsilon}, η={eta}, δ={delta}), mode={mode}"
    )
    worker_output_dir = os.path.join(
        os.path.expanduser("~"), "ApproxInv_Output", f"worker_{worker_id}"
    )
    os.makedirs(worker_output_dir, exist_ok=True)

    k_values = [iters]
    num_bits_values = [16]
    for num_bits in num_bits_values:
        for k in k_values:
            init_states_list = get_init_states(progname, k, M)
            for init_states in init_states_list:
                Progformula_path = os.path.join(
                    CURRENT_PATH, "progformula/", "EXIST_progs.py"
                )
                subprocess.run(
                    ["python3", Progformula_path, str(progname), str(num_bits), str(p)],
                    check=True,
                )
                subprocess.run(
                    [
                        "python3",
                        "initgen.py",
                        "--progname",
                        str(progname),
                        "--init_states",
                        str(init_states),
                        "--num_bits",
                        str(num_bits),
                    ],
                    check=True,
                )
                Validifier_trigger_path = os.path.join(
                    CURRENT_PATH, "src/Validifier/", "validifier.py"
                )
                Init_sampler_trigger_path = os.path.join(
                    CURRENT_PATH, "src/Program_state_sampler/", "init_sampler.py"
                )
                TreeLearner_trigger_path = os.path.join(
                    CURRENT_PATH, "src/TreeLearner/", "TreeLearner.py"
                )
                subprocess.run(
                    [
                        "python3",
                        Init_sampler_trigger_path,
                        "--progname",
                        str(progname),
                        "--epsilon",
                        str(epsilon),
                        "--eta",
                        str(eta),
                        "--delta",
                        str(delta),
                        "--iters",
                        str(k),
                        "--num_bits",
                        str(num_bits),
                        "--flag",
                        str(mode),
                    ],
                    check=True,
                )
                cmd = [
                    "python3",
                    TreeLearner_trigger_path,
                    "--progname",
                    str(progname),
                    "--epsilon",
                    str(epsilon),
                    "--eta",
                    str(eta),
                    "--delta",
                    str(delta),
                    "--iters",
                    str(k),
                    "--num_bits",
                    str(num_bits),
                    "--init_states",
                    str(init_states),
                    "--flag",
                    str(mode),
                ]
                log_path = os.path.join(
                    CURRENT_PATH,
                    f"logs/logs_{num_bits}bits/{progname}_{epsilon}_{delta}.out",
                )
                log_dir = os.path.dirname(log_path)
                os.makedirs(log_dir, exist_ok=True)
                with open(log_path, "a") as log_file:
                    log_file.write(f"\n--- Run at {datetime.now()} ---\n")
                    subprocess.run(
                        cmd, stdout=log_file, stderr=log_file, text=True, check=True
                    )


if __name__ == "__main__":

    if len(sys.argv) == 7:
        progname = sys.argv[1]
        iters = int(sys.argv[2])
        epsilon = float(sys.argv[3])
        eta = float(sys.argv[4])
        delta = float(sys.argv[5])
        mode = int(sys.argv[6])
        input_list = [(progname, iters, epsilon, eta, delta, mode)]
    elif sys.argv[1] == "all":
        for mode in [1]:
            input_list = [
                # ("Unif1", 64, 0.05, 0.05, 0.1, mode),
                # ("Unif2", 1, 0.05, 0.05, 0.1, mode),
                # ("Unif2", 1, 0.05, 0.05, 0.1, mode),
                # ("MultiMode1", 64, 0.05, 0.05, 0.1, mode),
                # ("Unif1", 64, 0.05, 0.05, 0.1, mode),
                # ("Unif3", 64, 0.05, 0.05, 0.1, mode),
                # ("ModSum", 64, 0.05, 0.05, 0.1, mode),
                # ("ModSum", 96, 0.05, 0.05, 0.1, mode),
                # ("ModSum", 128, 0.05, 0.05, 0.1, mode),
                # ("ModSum", 160, 0.05, 0.05, 0.1, mode),
                # ("Duel", 32, 0.05, 0.05, 0.1),
                # ("Bin1", 32, 0.05, 0.05, 0.1),
                # ("Prinsys", 32, 0.05, 0.05, 0.1),
                ("LinExp", 64, 0.05, 0.05, 0.1, mode),
                ("Fair", 64, 0.05, 0.05, 0.1, mode),
                ("Sum0", 64, 0.05, 0.05, 0.1, mode),
                ("BigGeo0", 64, 0.05, 0.05, 0.1, mode),
                # ("Detm", 32, 0.05, 0.05, 0.1),
                ("DepRV", 64, 0.05, 0.05, 0.1, mode),
                # ("Bin0", 32, 0.05, 0.05, 0.1),
                # ("Bin2", 32, 0.05, 0.05, 0.1),
                ("RevBin", 64, 0.05, 0.05, 0.1, mode),
                # ("BiasDir", 32, 0.05, 0.05, 0.1),
                # ("BigGeo1", 32, 0.05, 0.05, 0.1),
                ("Mart", 64, 0.05, 0.05, 0.1, mode),
                # ("GeoAr", 32, 0.05, 0.05, 0.1),
                # ("BigGeo2", 32, 0.05, 0.05, 0.1),
            ]

            for worker_id, args in enumerate(input_list):
                ApproxInv(*args, worker_id)

    print("All tasks completed.")


# if progname == "BigGeo0":
#                 init_states_list = ["(z == 0)"]
#                 # init_states_list = [f"(z{7*int((num_bits/8))})", f"(z{5*int((num_bits/8))})", f"(z{3*int((num_bits/8))})",]
#             if progname == "BigGeo1":
#                 init_states_list = ["(z == 0 && x == 16)"]
#                                     #"(z < 64 && x < 16)",]
#             if progname == "BigGeo2":
#                 init_states_list = ["(z == 0 && x == 16)", "(z < 64 && x < 16)",]
#             if progname == "LinExp":
#                 init_states_list = [f"(count == 0 && n < {k})", f"(count == 0 && n < {k})"]
#             if progname == "Sum0":
#                 init_states_list = [f"(x == 0 && n == {k})"]
#                 # init_states_list = [f"(x < 8 && n < {k})", f"(x == 64 && n < {k})"]
#             if progname == "Prinsys":
#                 init_states_list = ["(x == 0)"]
#             if progname == "Detm":
#                 init_states_list = ["(count == 0)"]
#             if progname == "Fair":
#                 init_states_list = ["(count == 0)", "(count < 64)",]
#             if progname == "Mart":
#                 init_states_list = ["(c == 0 && b == 64 && rounds == 0)", ]
#                                     # "(c < 32 && b == 64 && rounds == 32)",]
#             if progname == "GeoAr":
#                 init_states_list = ["(x == 0 && y == 0)"]
#                                     #, "(x < 64 && y == 16)",]
#             if progname == "Bin0":
#                 init_states_list = [f"(x == 0 && y == 2 && n == {k})", f"(x < 64 && y == 2 && n == {k})"]
#             if progname == "Bin1":
#                 init_states_list = [f"(x == 0 && n == {M - k/2})", f"(x < 32 && n == {M - k/2})"]
#             if progname == "Bin2":
#                 init_states_list = [f"(x == 0 && y == 8 && n < {k/2})", f"(x < 32 && y == 8 && n < {k/2})"]
#             if progname == "BiasDir":
#                 init_states_list = ["(x == 0 && y == 0)", "(x == 1 && y == 1)",]
#             if progname == "DepRV":
#                 init_states_list = [f"(x == 0 && y == 0 && n == {k})", f"(x == 8 && y == 16 && n == {k})"]
#             if progname == "RevBin":
#                 init_states_list = [f"(x < {k/2} && z == 0)"]
#                                     #f"(x == {k/2} && z < 16)"]
#             if progname == "Duel":
#                 init_states_list = ["(t == 0)", "(t == 1)",]
