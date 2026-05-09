import random
from dist_utils import *
import numpy
import os
from numpy.random import default_rng


NUM_BITS = None
MASK = None
p = 0.5
p1 = 0.5
p2 = 0.5

def state_evaluation(binary_list):
    """Convert a list of bits (MSB first) to an integer."""
    return sum(b << (len(binary_list) - 1 - i) for i, b in enumerate(binary_list))

def run_parallel(samples, config, iters):
    multiprocessing.set_start_method("spawn", force=True)
    progname = config["Program_name"]
    num_variables = len(config["Program_variables"]["Bools"])
    prog_variables = config["Program_variables"]["Bools"]
    loop_guard = config["Initial states"]["Loop guard"]

    all_args = [
        (sample, progname, iters, num_variables, prog_variables, loop_guard)
        for sample in samples
    ]
    results = []

    with ThreadPoolExecutor(max_workers = min(20, int(0.7 * os.cpu_count()))) as executor:
        futures = [executor.submit(DistExecute, args) for args in all_args]
        for future in as_completed(futures):
            result = future.result()
            if not isinstance(result, str):  # ignore errors
                results.extend(result)
    return results


def Temp(k: int, z: int, flip: int, p1: float) -> int:

    iters = 0

    while flip == 0 and iters < k:
        seed = random.randint(0, 2**31 - 1)
        rng = default_rng(seed + iters)

        d = 1 if rng.random() < p1 else 0
        if d == 1:
            flip = 1
        else:
            z += 1
        
        if (z == 9):
            z = 17
        iters += 1

    return (2 * (z & MASK) + flip) % (2 ** (1 + NUM_BITS))

def BigGeo0(k: int, z: int, flip: int, p1: float) -> int:

    iters = 0

    while flip == 0 and iters < k:
        seed = random.randint(0, 2**31 - 1)
        rng = default_rng(seed + iters)

        d = 1 if rng.random() < p1 else 0
        if d == 1:
            flip = 1
        else:
            z += 1
        iters += 1

    return (2 * (z & MASK) + flip) % (2 ** (1 + NUM_BITS))

def BigGeo1(k: int, z: int, x: int, flip: int, p1: float) -> int:

    iters = 0

    while flip == 0 and iters < k:
        seed = random.randint(0, 2**31 - 1)
        rng = default_rng(seed + iters)

        d = 1 if rng.random() < p1 else 0
        if d == 1:
            flip = 1
        else:
            x = 2*x
            z += 1
        iters += 1

    result = (((1 << (NUM_BITS + 1)) * (z & MASK)) + (2 * (x & MASK)) + flip) % (2 ** (1 + 2*NUM_BITS))
    return result

def BigGeo2(k: int, z: int, x: int, flip: int, p1: float) -> int:

    iters = 0

    while flip == 0 and iters < k:
        seed = random.randint(0, 2**31 - 1)
        rng = default_rng(seed + iters)

        d = 1 if rng.random() < p1 else 0
        if d == 1:
            flip = 1
        else:
            x += 1
            z += 1
        iters += 1

    result = (((1 << (NUM_BITS + 1)) * (z & MASK)) + (2 * (x & MASK)) + flip) % (2 ** (1 + 2*NUM_BITS))
    return result


def Bin0(k: int, y: int, n: int, x: int, p1: float) -> int:
    iters = 0
    while n > 0 and iters < k:
        seed = random.randint(0, 2**31 - 1)
        rng = default_rng(seed + iters)

        d = 1 if rng.random() < p1 else 0
        if d == 1:
            x = (x + y) & MASK  # Ensure 16-bit
        n = (n - 1) & MASK  # Wrap around to stay 16-bit
        iters += 1

    result = (
        (1 << (2 * NUM_BITS)) * (y & MASK) + (1 << NUM_BITS) * (n & MASK) + (x & MASK)
    )
    return result


def Bin1(k: int, n: int, x: int, p1: float) -> int:
    iters = 0
    M = 128
    while n < M  and iters < k:
        seed = random.randint(0, 2**31 - 1)
        rng = default_rng(seed + iters)

        d = 1 if rng.random() < p1 else 0
        if d == 1:
            x = (x + 1) & MASK  # Ensure 16-bit
            n = (n + 1) & MASK  # Wrap around to stay 16-bit
        iters += 1

    result = (
        (1 << NUM_BITS) * (n & MASK) + (x & MASK)
    )
    return result


def BinMod(k: int, n: int, x: int, p1: float) -> int:
    iters = 0
    M = 512

    while n < M and iters < k:
        seed = random.randint(0, 2**31 - 1)
        rng = default_rng(seed + iters)

        d = 1 if rng.random() < p1 else 0
        if d == 1:
            x = (x + 1) & MASK   
            n = (n + 1) & MASK
        iters += 1

    # MODIFICATION: x := x mod 100
    x = x % 100
    result = (
        (1 << NUM_BITS) * (n & MASK) + (x & MASK)
    )
    return result



def Bin2(k: int, y: int, n: int, x: int, p1: float) -> int:
    iters = 0
    while n > 0 and iters < k:
        seed = random.randint(0, 2**31 - 1)
        rng = default_rng(seed + iters)

        d = 1 if rng.random() < p1 else 0
        if d == 1:
            x = (x + n) & MASK  # Ensure 16-bit
        else:
            x = (x + y) & MASK
            n = (n - 1) & MASK  # Wrap around to stay 16-bit

        iters += 1

    result = (
        (1 << (2 * NUM_BITS)) * (y & MASK) + (1 << NUM_BITS) * (n & MASK) + (x & MASK)
    )
    return result


def BiasDir(k: int, y: int, x: int, p1: float) -> int:
    iters = 0
    while (x == y) and iters < k:
        seed = random.randint(0, 2**31 - 1)
        rng = default_rng(seed + iters)

        d1 = 1 if rng.random() < p1 else 0
        if d1 == 1:
            x = 1 
        else:
            x = 0 

        d2 = 1 if rng.random() < p1 else 0
        if d2 == 1:
            y = 1 
        else:
            y = 0 
            

        iters += 1

    result = ( (2*y + x) )
    return result



def Unif(k: int, x: int, count: int, p1: float) -> int:

    iters = 0
    while x < 16 and iters < k:
        x = x + random.uniform(0, 2)
        count = count + 1

    result = ((x & MASK) << NUM_BITS) + (count & MASK)
    return result

def DepRV(k: int, y: int, n: int, x: int, p1: float) -> int:

    iters = 0

    while (n > 0) and (iters < k):
        seed = random.randint(0, 2**31 - 1)
        rng = default_rng(seed + iters)

        d = 1 if rng.random() < p1 else 0

        if d == 1:
            x = (x + 1) & MASK
        else:
            y = (y + 1) & MASK
        n = (n - 1) & MASK
        iters += 1

    # Encode result as 2^32*y + 2^16*n + x (mod 2^48)
    result = (
        (1 << (2 * NUM_BITS)) * (y & MASK) + (1 << NUM_BITS) * (n & MASK) + (x & MASK)
    ) % (1 << (3 * NUM_BITS))
    return result


def Detm(k: int, x: int, count: int) -> int:

    iters = 0
    while x <= 15 and iters < k:

        x = x + 1
        count = count + 1
        iters += 1

    result = ((x & MASK) << NUM_BITS) + (count & MASK)
    return result


def Duel(k: int, c: int, t: int, p1: float, p2: float) -> int:

    iters = 0
    while c == 1 and iters < k:

        seed = random.randint(0, 2**31 - 1)
        rng = default_rng(seed + iters)
        rand_float1 = rng.random()
        seed = random.randint(0, 2**31 - 1)
        rng = default_rng(seed + iters)
        rand_float2 = rng.random()

        if t == 1:
            d1 = 1 if rand_float1 < p1 else 0
            c = 0 if d1 == 1 else c
            t = t if d1 == 1 else 0
        else:
            d2 = 1 if rand_float2 < p2 else 0
            c = 0 if d2 == 1 else c
            t = t if d2 == 1 else 1

        iters += 1

    result = (c << 1) + t
    return result


def Fair(k: int, count: int, ca: int, cb: int, p1: float, p2: float) -> int:
    iters = 0
    while not (ca or cb) and iters < k:
        seed = random.randint(0, 2**31 - 1)
        rng = default_rng(seed + iters)
        rand_float1 = rng.random()
        seed = random.randint(0, 2**31 - 1)
        rng = default_rng(seed + iters)
        rand_float2 = rng.random()

        ca = 1 if rand_float1 < p1 else 0
        if ca:
            count = (count + 1) & MASK

        cb = 1 if rand_float2 < p2 else 0
        if cb:
            count = (count + 1) & MASK

        iters += 1

    # Encoding: 16-bit count + 2-bit ca/cb → 18-bit result
    result = (4 * (count & MASK) + 2 * (ca & 1) + (cb & 1)) % (1 << (NUM_BITS + 2))
    return result


def GeoAr(k: int, x: int, y: int, z: int, p1: float) -> int:
    iters = 0
    while z > 0 and iters < k:
        seed = random.randint(0, 2**31 - 1)
        rng = default_rng(seed + iters)
        rand_float1 = rng.random()

        y = y + 1

        d = 1 if rand_float1 < p1 else 0
        if d:
            z = 0
        else:
            x = x + y

        iters += 1

    # Pack x:bits 17-32, y:1-16, z:0 into a 33-bit value
    result = ((x & MASK) << (1 + NUM_BITS)) | ((y & MASK) << 1) | (z)
    return result


def LinExp(k: int, count: int, n: int, p1: float) -> int:
    iters = 0
    while n > 0 and iters < k:
        seed = random.randint(0, 2**31 - 1)
        rng = default_rng(seed + iters)
        rand_float1 = rng.random()
        seed = random.randint(0, 2**31 - 1)
        rng = default_rng(seed + iters)
        rand_float2 = rng.random()
        seed = random.randint(0, 2**31 - 1)
        rng = default_rng(seed + iters)
        rand_float3 = rng.random()

        x1 = 1 if rand_float1 < p1 else 0
        x2 = 1 if rand_float2 < p1 else 0
        x3 = 1 if rand_float3 < p1 else 0

        n = n - 1

        c1 = x1 | x2 | x3
        c2 = (not x1) | x2 | x3
        c3 = x1 | (not x2) | x3

        count = (count + c1 + c2 + c3) & MASK
        iters += 1

    # Encode (count << 16) | n into 32-bit integer
    result = ((count & MASK) << NUM_BITS) | (n & MASK)
    return result


def Mart(k: int, c: int, b: int, rounds: int, p1: float) -> int:
    iters = 0
    while b > 0 and iters < k:
        seed = random.randint(0, 2**31 - 1)
        rng = default_rng(seed + iters)
        rand_float1 = rng.random()

        d = 1 if rand_float1 < p1 else 0
        if d == 1:
            c = (c + b) & MASK
            b = 0
        else:
            c = (c - b) & MASK
            b = (2 * b) & MASK

        rounds = rounds + 1
        iters += 1

    # Final result packed as 48-bit: [c|b|rounds]
    result = (
        (2 ** (2 * NUM_BITS) * (c & MASK))
        + (2 ** (NUM_BITS) * (b & MASK))
        + (rounds & MASK)
    )
    return result


def Prinsys(k: int, x: int, p1: float, p2: float) -> int:

    iters = 0
    while x == 0 and iters < k:
        seed = random.randint(0, 2**31 - 1)
        rng = default_rng(seed + iters)
        rand_float1 = rng.random()
        rng = default_rng(seed + iters)
        rand_float2 = rng.random()
        d1 = 1 if rand_float1 < p1 else 0
        if d1 == 1:
            x = 0
        else:
            d2 = 1 if rand_float2 < p2 else 0
            x = 2 if d2 == 1 else 1

    return x % 256


def RevBin(k: int, z: int, x: int, p1: float) -> int:
    iters = 0
    while x > 0 and iters < k:
        seed = random.randint(0, 2**31 - 1)
        rng = default_rng(seed + iters)
        rand_float1 = rng.random()

        d = 1 if rand_float1 < p1 else 0
        if d == 1:
            x = (x - 1) & MASK

        z = (z + 1) & MASK
        iters += 1

    # Final result packed as 32-bit: [z|x]
    result = (2 ** (NUM_BITS) * (z & MASK)) + (x & MASK)
    return result


def Sum0(k: int, x: int, n: int, p1: float) -> int:
    iters = 0
    while n > 0 and iters < k:
        seed = random.randint(0, 2**31 - 1)
        rng = default_rng(seed + iters)
        rand_float1 = rng.random()

        if rand_float1 < p1:
            x = (x + n) & MASK

        n = (n - 1) & MASK
        iters += 1

    # Final result packed as 32-bit: [x|n]
    result = (2 ** (NUM_BITS) * (x & MASK)) + (n & MASK)
    return result


def ModSum(k: int, x: int, n: int, p1: float) -> int:
    iters = 0
    while n > 0 and iters < k:
        seed = random.randint(0, 2**31 - 1)
        rng = default_rng(seed + iters)

        # unbiased random bit
        if rng.random() < p1:
            x = x ^ (1 << (iters % (NUM_BITS - 1)))   # assign fresh bit

        n = (n - 1) & MASK
        iters += 1
    

    # Final result packed as 32-bit: [x|n]
    result = (2 ** (NUM_BITS) * (x & MASK)) + (n & MASK)
    return result


def MultiMode1(k: int, x: int, n: int, p1: float) -> int:
    iters = 0
    while n > 0 and iters < k:
        seed = random.randint(0, 2**31 - 1)
        rng = default_rng(seed + iters)

        bit = iters % (NUM_BITS - 1)   # never touch MSB
        b = rng.random() < 0.5

        if b:
            # state-dependent reinforcement
            if (x & (1 << bit)) == 0:
                # create a 1-cluster
                x = x | (1 << bit)
            else:
                # spread probability mass locally
                x = x | (1 << ((bit + 1) % (NUM_BITS - 1)))
                x = x | (1 << ((bit + 2) % (NUM_BITS - 1)))

        n = (n - 1) & MASK
        iters += 1
    

    # Final result packed as 32-bit: [x|n]
    result = (2 ** (NUM_BITS) * (x & MASK)) + (n & MASK)
    return result

# NUM_BITS = 16

def Unif1(k: int, x: int, n: int, p1: float) -> int:
    iters = 0
    bits = list(range(NUM_BITS - 1))
    while n > 0 and iters < k:
        seed = random.randint(0, 2**31 - 1)
        rng = default_rng(seed + iters)
        rng.shuffle(bits)
        for bit in bits:
            if rng.random() < 0.5:
                x ^= (1 << bit)
            
        n = (n - 1) & MASK
        iters += 1
    

    # Final result packed as 32-bit: [x|n]
    result = (2 ** (NUM_BITS) * (x & MASK)) + (n & MASK)
    return result



    

def Unif2(k: int, x: int, flip: int, p1: float) -> int:

    iters = 0
    LOW = NUM_BITS - 32
    y = 0
    base = x

    while flip == 1 and iters < k:
        seed = random.randint(0, 2**31 - 1)
        rng = default_rng(seed + iters)

        for i in range(LOW):
            if random.random() < p1:
                y |= (1 << i)

        iters += 1
        x = base + y 
        

    #x = x + y



    return (2 * (x & MASK) + flip) % (2 ** (1 + NUM_BITS))



def Unif3(k: int, x: int, n: int, p1: float) -> int:
    iters = 0

    # --------------------------------------------------
    # Bit-index sets (scale with NUM_BITS)
    # --------------------------------------------------
    S1 = [0, NUM_BITS // 4, NUM_BITS // 2]   # parity = 0
    S2 = [1, NUM_BITS // 3]                  # parity = 1

    while n > 0 and iters < k:
        seed = random.randint(0, 2**31 - 1)
        rng = default_rng(seed + iters)

        # --------------------------------------------------
        # Rotating bit (touches all bits over time)
        # --------------------------------------------------
        bit = iters % NUM_BITS
        b = rng.random() < p1

        # --------------------------------------------------
        # Noisy reinforcement (FoRT-visible randomness)
        # --------------------------------------------------
        if b:
            if (x & (1 << bit)) == 0:
                x = x | (1 << bit)
            else:
                x = x | (1 << ((bit + 1) % NUM_BITS))
                x = x | (1 << ((bit + 2) % NUM_BITS))

        # --------------------------------------------------
        # Enforce affine structure (absorbing)
        # --------------------------------------------------
        # Constraint 1: xor over S1 == 0
        p1_val = 0
        for i in S1:
            p1_val ^= (x >> i) & 1

        if p1_val == 1:
            x ^= (1 << S1[0])

        # Constraint 2: xor over S2 == 1
        p2_val = 0
        for j in S2:
            p2_val ^= (x >> j) & 1

        if p2_val == 0:
            x ^= (1 << S2[0])

        # --------------------------------------------------
        # Hash-style mixing to destroy structure of B
        # --------------------------------------------------
        h = 0
        for t in range(3):
            h ^= (x >> ((7 * t + 5) % NUM_BITS)) & 1

        x ^= (1 << ((h + 3) % NUM_BITS))

        # --------------------------------------------------
        # Loop bookkeeping
        # --------------------------------------------------
        n = (n - 1) & MASK
        iters += 1

        

    result = (2 ** (NUM_BITS) * (x & MASK)) + (n & MASK)
    return result



def Unif4(k: int, x: int, flip: int, p1: float) -> int:
    import random

    iters = 0
    base = x
    y = 0
    lengths = [1] + [(2**j - j - 1) for j in range(1, NUM_BITS)]
    total = sum(lengths)


    while flip == 1 and iters < k:

        
        u = random.randint(0, total - 1)

        s = 0
        for j in range(NUM_BITS):
            if u < s + lengths[j]:
                break
            s += lengths[j]

        
        offset = u - s

        
        if j == 0:
            y = 0
        else:
            a_j = (2**j) + j + 1
            y = a_j + offset

        iters += 1
        x = base + y
        
    return (2 * (x & MASK) + flip) % (2 ** (1 + NUM_BITS))









def DistExecute(args):

    # Unpacking args
    (
        L1,
        progname,
        k,
        num_variables,
        prog_variables,
        loop_guard,
    ) = args

    results = []

    seed = random.randint(0, 2**31 - 1)
    rand_bits = [random.randint(0, 1) for _ in range(20)]  # Safe upper bound
    if progname in {
        "MultiMode1",
        "Unif1",
        "Unif2",
        "Unif4",
        "Temp",
        "Duel",
        "BigGeo0",
        "BigGeo1",
        "BigGeo2",
        "LinExp",
        "DepRV",
        "RevBin",
        "GeoAr",
        "Sum0",
        "ModSum",
        "Bin0",
        "Bin1",
        "BinMod",
        "Bin2",
        "BiasDir",
        "Detm",
        "Fair",
        "Mart",
        "Prinsys",
    }:
        # Special handling depending on progname
        if progname == "Temp":
            z = state_evaluation(L1[:NUM_BITS])
            flip = state_evaluation([L1[-1]])
            output = Temp(k, z, flip, p)
        elif progname == "BigGeo0":
            z = state_evaluation(L1[:NUM_BITS])
            flip = state_evaluation([L1[-1]])
            output = BigGeo0(k, z, flip, p)
        elif progname == "BigGeo1":
            z = state_evaluation(L1[:NUM_BITS])
            x = state_evaluation(L1[NUM_BITS : 2 * NUM_BITS])
            flip = state_evaluation([L1[-1]])
            output = BigGeo1(k, z, x, flip, p)
        elif progname == "BigGeo2":
            z = state_evaluation(L1[:NUM_BITS])
            x = state_evaluation(L1[NUM_BITS : 2 * NUM_BITS])
            flip = state_evaluation([L1[-1]])
            output = BigGeo2(k, z, x, flip, p)
        elif progname == "LinExp":
            count = state_evaluation(L1[:NUM_BITS])
            n = state_evaluation(L1[NUM_BITS : 2 * NUM_BITS])
            output = LinExp(k, count, n, p)
        elif progname == "GeoAr":
            x = state_evaluation(L1[:NUM_BITS])
            y = state_evaluation(L1[NUM_BITS : 2 * NUM_BITS])
            z = state_evaluation([L1[-1]])
            output = GeoAr(k, x, y, z, p)
        elif progname == "Sum0":
            x = state_evaluation(L1[:NUM_BITS])
            n = state_evaluation(L1[-NUM_BITS:])
            output = Sum0(k, x, n, p)
        
        elif progname == "Bin0":
            y = state_evaluation(L1[:NUM_BITS])
            n = state_evaluation(L1[NUM_BITS : 2 * NUM_BITS])
            x = state_evaluation(L1[-NUM_BITS:])
            output = Bin0(k, y, n, x, p)

        elif progname == "Bin1":
            n = state_evaluation(L1[:NUM_BITS])
            x = state_evaluation(L1[-NUM_BITS:])
            output = Bin1(k, n, x, p)
        
        elif progname == "BinMod":
            n = state_evaluation(L1[:NUM_BITS])
            x = state_evaluation(L1[-NUM_BITS:])
            output = BinMod(k, n, x, p)

        elif progname == "Bin2":
            y = state_evaluation(L1[:NUM_BITS])
            n = state_evaluation(L1[NUM_BITS : 2 * NUM_BITS])
            x = state_evaluation(L1[-NUM_BITS:])
            output = Bin2(k, y, n, x, p)

        elif progname == "BiasDir":
            y = state_evaluation([L1[0]])
            x = state_evaluation([L1[1]])
            output = BiasDir(k, y, x, p)

        elif progname == "Detm":
            x = state_evaluation(L1[:NUM_BITS])
            count = state_evaluation(L1[-NUM_BITS:])
            output = Detm(k, x, count)
        elif progname == "DepRV":
            y = state_evaluation(L1[:NUM_BITS])
            n = state_evaluation(L1[NUM_BITS : 2 * NUM_BITS])
            x = state_evaluation(L1[-NUM_BITS:])
            output = DepRV(k, y, n, x, p)
        elif progname == "RevBin":
            z = state_evaluation(L1[:NUM_BITS])
            x = state_evaluation(L1[-NUM_BITS:])
            output = RevBin(k, z, x, p)
        elif progname == "Fair":
            count = state_evaluation(L1[:NUM_BITS])
            ca = state_evaluation([L1[-2]])
            cb = state_evaluation([L1[-1]])
            output = Fair(k, count, ca, cb, p1, p2)
        elif progname == "Mart":
            c = state_evaluation(L1[:NUM_BITS])
            b = state_evaluation(L1[NUM_BITS : 2 * NUM_BITS])
            rounds = state_evaluation(L1[-NUM_BITS:])
            output = Mart(k, c, b, rounds, p)

        # elif progname == "Prinsys":
        #     z = state_evaluation(L1[:NUM_BITS])
        #     flip = state_evaluation(L1[-1])
        #     output = BigGeo0(k, z, flip, p)

        elif progname == "Duel":
            c = state_evaluation([L1[0]])
            t = state_evaluation([L1[1]])
            output = Duel(k, c, t, p1, p2)

        elif progname == "Prinsys":
            x = state_evaluation(L1)
            output = Prinsys(k, x, p1, p2)

        elif progname == "MultiMode1":
            x = state_evaluation(L1[:NUM_BITS])
            n = state_evaluation(L1[-NUM_BITS:])
            output = MultiMode1(k, x, n, p)

        elif progname == "Unif1":
            x = state_evaluation(L1[:NUM_BITS])
            n = state_evaluation(L1[-NUM_BITS:])
            output = Unif1(k, x, n, p)

        elif progname == "Unif2":
            x = state_evaluation(L1[:NUM_BITS])
            flip = state_evaluation([L1[-1]]) 
            output = Unif2(k, x, flip, p)

        elif progname == "Unif4":
            x = state_evaluation(L1[:NUM_BITS])
            flip = state_evaluation([L1[-1]]) 
            output = Unif4(k, x, flip, p)

        elif progname == "ModSum":
            x = state_evaluation(L1[:NUM_BITS])
            n = state_evaluation(L1[-NUM_BITS:])
            output = ModSum(k, x, n, p)
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
        # results.append(output)
        if ((not flag) or progname == "Unif2" or progname == "Unif4"):
            results.append(output)

    return results


def main():
    args = parse_arguments()
    config = get_config(args.progname)
    config["Program_name"] = args.progname
    num_bits = args.num_bits
    global NUM_BITS, MASK
    NUM_BITS = args.num_bits
    MASK = (1 << NUM_BITS) - 1
    prog_variables = config["Program_variables"]["Bools"]
    init_states = config["Initial states"]["Expression"]
    
    # === Parse Expressions ===
    init_list = [
        list(filter(None, clause.strip("() ").split("||")))
        for clause in init_states.split("&&")
    ]
    forward_var_map = {var: idx + 1 for idx, var in enumerate(prog_variables)}
    num_vars = len(forward_var_map)
    dimacs_init = nnf_to_dimacs(init_list, forward_var_map)
    write_cnf_dimacs_to_file(
        dimacs_init,
        num_vars,
        len(dimacs_init),
        os.path.join(CURRENT_PATH, f"temp/input_cnf_{args.progname}"),
    )

    # setup_program(args.progname)
    sample_file = generate_samples(args.progname, args.epsilon, args.delta)
    samples = preprocess_samples(sample_file)

    output_results = run_parallel(samples, config, args.iters)
    distance, counterexamples, all_reachable_states = evaluate_results(
        output_results, config, args.progname
    )
    save_experiment_results(
        args, config, distance, counterexamples, all_reachable_states
    )
    print("DistEstimate outputs:", distance)


if __name__ == "__main__":
    main()
