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

gp.get_context().precision = 20000


def isSAT(dnfclause, sol):
    tmpRand = np.random.uniform(0, 1, max(len(dnfclause), len(sol)))
    idx = 0
    for lit in dnfclause:
        if -1 * lit in sol:
            return False
        elif lit not in sol:
            if (
                tmpRand[idx] > 0.5
            ):  # np.random.uniform(0, 1)    # delayed sample generation
                return False
            idx += 1
    return True


def ComputeNumSamples(t, p, thresh, m, delta, method, verbose):

    if verbose:
        print("sample n : {0}, p : {1}".format(t, str(p)))

    if method == 1:
        # vanilla version
        try:
            N = vanbinomial(t, p)
            N = int(N)
        except OverflowError:
            print("SAMPLING FAILURE!")
            exit("SAMPLING FAILURE!")

    elif method == 2:
        # improved version
        thresh1 = 12 * thresh**2 * m / delta
        thresh2 = (delta / (6 * m)) ** 0.5

        thresh1, thresh2 = mpfr(thresh1), mpfr(thresh2)

        if t * p >= thresh2:
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
            N = np.random.binomial(1, float(t * p))

    elif method == 3:
        # mp version
        N = mpbinomial(int(t), p, err=delta / (6 * m))

    return N


def getSolutionFromVanillaSampler(dnfClause, nVars):
    sol = []
    tmpRand = np.random.uniform(0, 1, nVars)
    for i in range(1, nVars + 1):
        if i in dnfClause:
            sol.append(i)
        else:
            if tmpRand[i - 1] > 0.5:
                sol.append(-i)
            else:
                sol.append(i)
    return sol


def GenerateSamples(N, dnfClause, delta, m, nVars, thresh):
    sampSet = []
    for j in range(N):
        sampSet.append(dnfClause)

    return sampSet


def dnfstream():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--eps", type=float, help="default = 0.2", default=0.2, dest="eps"
    )
    parser.add_argument(
        "--delta", type=float, help="default = 0.1", default=0.1, dest="delta"
    )
    parser.add_argument("--seed", type=int, dest="seed", default=42)
    parser.add_argument("--samp", type=int, dest="samp", default=1)
    parser.add_argument("--numsamps", type=int, dest="numsamps", default=500)
    parser.add_argument("input", help="input file")
    parser.add_argument("output", help="output file")
    parser.add_argument("--dosample", help="do sampling", action="store_true")
    parser.add_argument("--verbose", help="verbosity", action="store_true")

    args = parser.parse_args()

    # file handling
    inputFile = args.input
    outputFile = args.output
    f = open(inputFile, "r")
    lines = f.readlines()
    f.close()

    seed = args.seed
    sampMethod = args.samp
    do_sampling = args.dosample
    num_samples = args.numsamps
    # np.random.seed(seed)

    initLine = lines[0].strip().split()

    if initLine[0] == "p":
        nVars = initLine[2]
        nClause = initLine[3]

    # print(nVars, nClause)

    # parameters / initialization
    eps = args.eps
    delta = args.delta
    if args.samp == 1:
        delta *= 2
    m = int(nClause)
    n = int(nVars)
    thresh = max(
        12 * math.log(24 / delta) / eps**2, 6 * (math.log(6 / delta) + math.log(m))
    )
    # thresh = 4*math.log2(m+1)/(eps**2)*math.log2(1.0/delta)
    p = 1
    solset = []

    # multi-precision conversion
    thresh, p = mpfr(thresh), mpfr(p)
    # print("Threshold: ",thresh)
    # print(p)
    line = 0  # line 0 corresponds to p dnf
    cl = 0
    # for i in range(1, m+1):
    counter = 0
    while True:
        counter += 1
        if (
            lines[line].startswith("c")
            or lines[line].startswith("p")
            or lines[line].startswith("w")
        ):
            line += 1
            continue
        currClause = lines[line].strip().split()[:-1]
        line += 1
        currClause = list(map(int, currClause))
        clauseWidth = len(currClause)

        # print(f"adding clause {currClause}")
        t = mpfr(2 ** (n - clauseWidth))
        # print(solset)
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
                if np.random.uniform(0, 1) > p:  # this was 0.5 before
                    solset.remove(sol)
            # p = p / 2
            p = gp.div(p, 2)
        if args.verbose:
            print(f"p: {p} | thresh : {int(thresh)} | bucket : {len(solset)}")

        N_i = ComputeNumSamples(t, p, thresh, m, delta, sampMethod, args.verbose)
        # print(N_i)
        Npast = N_i
        while N_i + len(solset) > thresh:
            for sol in solset:
                if np.random.uniform(0, 1) > p:  # this was 0.5 before
                    solset.remove(sol)
            N_i = np.random.binomial(N_i, 1 / 2)
            p = p / 2
            if args.verbose:
                print(f"bucket reduced to : {len(solset)}")

        if args.verbose:
            print(f"old ni : {Npast}, new ni: {N_i}")

        sol = GenerateSamples(N_i, currClause, delta, m, n, thresh)
        solset += sol
        cl += 1
        if cl == m:
            break

        seed += 1

    # print(counter)
    modelCount = int(len(solset) / p)
    print(modelCount)
    samples = list()
    if do_sampling:
        # print("Solution set: ", solset)
        for _ in range(num_samples):
            sampled_element = list()
            # print(solset)
            sampled_element = sampled_element = list(random.choice(solset))

            # print("Initial sampled portion: ",sampled_element)
            tmpRand = np.random.uniform(0, 1, n)
            # print(tmpRand)
            idx = 0
            for lit in range(1, n + 1):
                if (lit in sampled_element) or ((-lit) in sampled_element):
                    idx += 1
                    continue
                else:
                    # print(tmpRand[idx])
                    if tmpRand[idx] > 0.5:

                        sampled_element.append(-lit)
                    else:
                        sampled_element.append(lit)

                idx += 1
            # print("Sampled element:", tuple(sorted(sampled_element, key=abs)))
            samples.append(sampled_element)
        samples = [" ".join(map(str, sample)) + " 0\n" for sample in samples]

        with open(outputFile, "w") as f:
            f.writelines(samples)


if __name__ == "__main__":

    start_time = time.time()

    dnfstream()

    end_time = time.time()

    print("time used by sampler (seconds) :", end_time - start_time)
