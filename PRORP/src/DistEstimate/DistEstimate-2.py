from dist_utils import *
def unpack_result(result):
    x = (result >> 16) & 0xFFFF
    # y = (result >> 16) & 0xFFFF
    n = result & 0xFFFF
    return x, n



def DistExecute(args):
    lock = threading.Lock()

    def run_command(executable, *params):
        with lock:
            result = subprocess.run(
                [executable] + list(map(str, params)),
                capture_output=True,
                text=True
            )
            return result.stdout.strip()

    #os.path.join(CURRENT_PATH, f"binaries/{progname}")

    # Specific wrappers
    runners = {
        "ex5": lambda *p: run_command(os.path.join(CURRENT_PATH, f"binaries/ex5"), *p),
        "ex6": lambda *p: run_command(os.path.join(CURRENT_PATH, f"binaries/ex6"), *p),
        "ex7": lambda *p: run_command(os.path.join(CURRENT_PATH, f"binaries/ex7"), *p),
        "ex8": lambda *p: run_command(os.path.join(CURRENT_PATH, f"binaries/ex8"), *p),
        "ex9": lambda *p: run_command(os.path.join(CURRENT_PATH, f"binaries/ex9"), *p),
        "ex10": lambda *p: run_command(os.path.join(CURRENT_PATH, f"binaries/ex10"), *p),
        "ex11": lambda *p: run_command(os.path.join(CURRENT_PATH, f"binaries/ex11"), *p),
        "ex12": lambda *p: run_command(os.path.join(CURRENT_PATH, f"binaries/ex12"), *p),
        "Prinsys": lambda *p: run_command(os.path.join(CURRENT_PATH, f"binaries/Prinsys"), *p),
        "Geo0": lambda *p: run_command(os.path.join(CURRENT_PATH, f"binaries/Geo0"), *p),
        "BigGeo0": lambda *p: run_command(os.path.join(CURRENT_PATH, f"binaries/BigGeo0"), *p),
        "LinExp": lambda *p: run_command(os.path.join(CURRENT_PATH, f"binaries/LinExp"), *p),
        "GeoAr": lambda *p: run_command(os.path.join(CURRENT_PATH, f"binaries/GeoAr"), *p),
        "Sum0": lambda *p: run_command(os.path.join(CURRENT_PATH, f"binaries/Sum0"), *p),
        "Bin0": lambda *p: run_command(os.path.join(CURRENT_PATH, f"binaries/Bin0"), *p),
        "Bin1": lambda *p: run_command(os.path.join(CURRENT_PATH, f"binaries/Bin1"), *p),
        "Bin2": lambda *p: run_command(os.path.join(CURRENT_PATH, f"binaries/Bin2"), *p),
        "Detm": lambda *p: run_command(os.path.join(CURRENT_PATH, f"binaries/Detm"), *p),
        "Fair": lambda *p: run_command(os.path.join(CURRENT_PATH, f"binaries/Fair"), *p),
        "Mart": lambda *p: run_command(os.path.join(CURRENT_PATH, f"binaries/Mart"), *p),
        "DepRV": lambda *p: run_command(os.path.join(CURRENT_PATH, f"binaries/DepRV"), *p),
        "RevBin": lambda *p: run_command(os.path.join(CURRENT_PATH, f"binaries/RevBin"), *p),
        "Duel": lambda *p: run_command(os.path.join(CURRENT_PATH, f"binaries/Duel"), *p),
    }

    # Unpacking args
    (
        L1,
        progname,
        source_file,
        output_binary,
        k,
        num_variables,
        prog_variables,
        loop_guard,
    ) = args

    results = []

    for iters in range(k):
        seed = random.randint(0, 2**31 - 1)
        rand_bits = [random.randint(0, 1) for _ in range(20)]  # Safe upper bound
        if progname in {"ex7", "ex11","Duel", "Geo0", "BigGeo0", "LinExp", "DepRV", "RevBin", "GeoAr", "Sum0", "Bin0", "Bin1", "Bin2", "Detm", "Fair", "Mart", "Prinsys"}:
            # Special handling depending on progname
            if progname == "ex7":
                output = runners["ex7"](*L1, *rand_bits[:5], seed)
            elif progname == "ex11":
                output = runners["ex11"](*L1[:num_variables], *rand_bits[:4], seed)
            elif progname == "Geo0":
                output = runners["Geo0"](*L1[:num_variables], seed)
            elif progname == "BigGeo0":
                output = runners["BigGeo0"](*L1[:num_variables], seed)
            elif progname == "LinExp":
                output = runners["LinExp"](*L1[:num_variables],  seed)
            elif progname == "GeoAr":
                output = runners["GeoAr"](*L1[:num_variables], seed)
            elif progname == "Sum0":
                output = runners["Sum0"](*L1[:num_variables], seed)
            elif progname == "Bin0":
                output = runners["Bin0"](*L1[:num_variables], seed)
            elif progname == "Bin1":
                output = runners["Bin1"](*L1[:num_variables], seed)
            elif progname == "Bin2":
                output = runners["Bin2"](*L1[:num_variables], seed)
            elif progname == "Detm":
                output = runners["Detm"](*L1[:num_variables], seed)
            elif progname == "DepRV":
                output = runners["DepRV"](*L1[:num_variables], seed)
            elif progname == "RevBin":
                output = runners["RevBin"](*L1[:num_variables], seed)
            elif progname == "Fair":
                output = runners["Fair"](*L1[:num_variables], seed)
            elif progname == "Mart":
                output = runners["Mart"](*L1[:num_variables], seed)
            elif progname == "Prinsys":
                output = runners["Prinsys"](*L1[:num_variables], seed)
            elif progname == "Duel":
                output = runners["Duel"](*L1[:num_variables], seed)
            else:
                raise ValueError(f"Unknown program name: {progname}")
        # print("Output: ", output)
        # print([int(bit) for bit in bin(int(output))[2:].zfill(num_variables)])
        # Convert output and evaluate
        # print(output)
        # x, n = unpack_result(int(output))

        # print(f"x = {x}, n = {n}")
        if isinstance(output, bytes):
            output = output.decode().strip()

        L1 = [int(bit) for bit in bin(int(output))[2:].zfill(num_variables)]
        # print(output)
        # print(loop_guard)
        flag = evaluate_loop_guard_condition(output, prog_variables, loop_guard)
        #results.append(output)
        if (not flag):
            results.append(output)
            #print("flag", flag)
            #print(r)
            break


    return results

def run_parallel(samples, config, iters):
    multiprocessing.set_start_method("spawn", force=True)
    progname = config["Program_name"]
    source_file = os.path.join(CURRENT_PATH, f"src/DistEstimate/executable_prog_files/{progname}.c")
    output_binary = progname
    num_variables = len(config["Program_variables"]["Bools"])
    prog_variables = config["Program_variables"]["Bools"]
    loop_guard = config["Initial states"]["Loop guard"]

    all_args = [(sample, progname, source_file, output_binary, iters, num_variables, prog_variables, loop_guard)
                for sample in samples]
    results = []

    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = [executor.submit(DistExecute, args) for args in all_args]
        for future in as_completed(futures):
            result = future.result()
            if not isinstance(result, str):  # ignore errors
                results.extend(result)
    return results



def main():
    args = parse_arguments()
    config = get_config(args.progname)
    config["Program_name"] = args.progname 
    prog_variables = config["Program_variables"]["Bools"]
    init_states = config["Initial states"]["Expression"]
    # === Parse Expressions ===
    init_list = [list(filter(None, clause.strip("() ").split("||"))) for clause in init_states.split("&&") ]
    forward_var_map = {var: idx + 1 for idx, var in enumerate(prog_variables)} 
    num_vars = len(forward_var_map)
    dimacs_init = nnf_to_dimacs(init_list, forward_var_map)
    write_cnf_dimacs_to_file(dimacs_init, num_vars, len(dimacs_init), os.path.join(CURRENT_PATH,f"temp/input_cnf_{args.progname}") )
    
    setup_program(args.progname)
    sample_file = generate_samples(args.progname, args.epsilon, args.delta)
    samples = preprocess_samples(sample_file)
    output_results = run_parallel(samples, config, args.iters)
    distance, counterexamples, all_reachable_states = evaluate_results(output_results, config, args.progname)
    save_experiment_results(args, config, distance, counterexamples, all_reachable_states)
    print("DistEstimate outputs:", distance)

if __name__ == "__main__":
    main()
