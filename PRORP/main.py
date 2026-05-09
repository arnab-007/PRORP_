import argparse
import subprocess
import random
import re
import math
import os
import json
import argparse
import time
CURRENT_PATH = os.path.realpath("")
assumed_shape = " "



def ApproxInv():

    parser = argparse.ArgumentParser()

    parser.add_argument("--progname", type=str, help="default = Geo0", default="Geo0", dest="progname")
    parser.add_argument("--epsilon", type=float, help="default = 0.05", default=0.05, dest="epsilon")
    parser.add_argument("--delta", type=float, help="default = 0.1", default=0.1, dest="delta")
    parser.add_argument("--seed", type=int, dest="seed", default=10)
    #parser.add_argument("--hops", type=int, dest="hops", default=4)
    parser.add_argument("--iters", type=int, dest="iters", default=64)
    args = parser.parse_args()

    # file handling
    progname = args.progname
    seed = args.seed
    epsilon = args.epsilon
    delta = args.delta
    #hops = args.hops
    iters = args.iters
    #np.random.seed(seed)

    Geo0_init_states = ["(!z7) && (!z6) && (!z5) && (!z4) && (!z3) && (!z2) && (!z1) && (!z0)", "(z6)", "(!z7) && (!z6) && (z5)", "(!z0 || !z1 || !z2 || z3 || z4 || !z6 || !z7) && (!z0 || z1 || z2 || z3 || z4 || z6) && (z1 || z3 || z7) && (z1 || !z2 || !z4 || !z5) && (!z0 || z1 || z2 || !z3 || !z4 || !z5 || z6 || !z7) && (!z0 || !z1 || !z2 || !z3 || z4 || z6 || !z7) && (!z0 || !z4 || z7) && (z0 || !z1 || !z2 || z3 || !z4 || z5 || z6 || !z7) && (!z3) && (z7)"]
    BigGeo0_init_states = ["(!z15) && (!z14) && (!z13) && (!z12) && (!z11) && (!z10) && (!z9) && (!z8) && (!z7) && (!z6) && (!z5) && (!z4) && (!z3) && (!z2) && (!z1) && (!z0)", "(z14)", "(!z15) && (!z14) && (!z13) && (!z12) && (!z11) && (!z10) && (!z9) && (!z8) && (z6)"]
    


    if (progname == "Geo0"):
        init_states = Geo0_init_states[2]
    if (progname == "BigGeo0"):
        init_states = BigGeo0_init_states[1]
    Validifier_trigger_path = os.path.join(CURRENT_PATH, "src/Validifier/", "validifier.py")
    Init_sampler_trigger_path = os.path.join(CURRENT_PATH, "src/Program_state_sampler/", "init_sampler.py")
    TreeLearner_trigger_path = os.path.join(CURRENT_PATH, "src/TreeLearner/", "TreeLearner.py")
    subprocess.run(["python3", "initgen.py", "--progname", str(progname), "--init_states", str(init_states)], check=True)
    
    
    subprocess.run(["python3", Validifier_trigger_path, "--progname", str(progname), "--epsilon", str(epsilon), "--delta", str(delta), "--iters", str(iters)], check=True)
    subprocess.run(["python3", Init_sampler_trigger_path, "--progname", str(progname)], check=True)
    cmd = ["python3", TreeLearner_trigger_path, "--progname", str(progname), "--epsilon", str(epsilon), "--delta", str(delta), "--iters", str(iters)]



    #result_validifier = subprocess.run(["python3", Validifier_trigger_path, "--epsilon", str(epsilon), "--delta", str(delta), "--iters", str(iters)], capture_output=True, text=True, check=True,)  
    with open(f"{progname}_{epsilon}_{delta}.out", "a") as log_file:  # "a" mode appends to the log file
        subprocess.run(cmd, stdout=log_file, stderr=log_file, text=True, check=True)
        
        

if __name__ == "__main__":
    
    start_time = time.time()

    ApproxInv()

    end_time = time.time()

    print("Time used by ApproxInv (seconds) :", end_time - start_time)