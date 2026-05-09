import z3
from utilities import add_bitmap, output_dimacs, check_status
import os
CURRENT_PATH = os.path.realpath("")
# EXAMPLE Geo0

globM = 512

def Temp(path, p1, NUM_BITS):
    z_1 = z3.BitVec("z_1", NUM_BITS)
    z_2 = z3.BitVec("z_2", NUM_BITS)
    flip_1 = z3.BitVec("flip_1", 1)
    flip_2 = z3.BitVec("flip_2", 1)
    d = z3.BitVec("d", 1)
    rand = z3.BitVec("rand", 4)  # 4-bit random number for Bernoulli
    g = z3.Goal()
    
    # Encode symbolic bitmap layout for CNF output
    g = add_bitmap(g, NUM_BITS, z_1)
    g = add_bitmap(g, 1, flip_1)
    g = add_bitmap(g, 1, d)
    g = add_bitmap(g, 4, rand)
    g = add_bitmap(g, 1, flip_2)
    g = add_bitmap(g, NUM_BITS, z_2)

    # Constraints for the Bernoulli sampling and state updates
    constraints = [
        # Bernoulli(d ~ Bernoulli(p1))
        d == z3.If(z3.ULT(rand, int(16 * p1)),
                   z3.BitVecVal(1, 1),
                   z3.BitVecVal(0, 1)),

        # Transition logic
        z3.If(
            z3.And(flip_1 == 0, d == 0),
            z3.And(
                flip_2 == flip_1,  # stays 0
                z_2 == z3.If(
                    z_1 == z3.BitVecVal(9, NUM_BITS),
                    z3.BitVecVal(17, NUM_BITS),      # reset case
                    z_1 + z3.BitVecVal(1, NUM_BITS)  # increment
                )
            ),
            z3.And(
                flip_2 == z3.If(d == 1, z3.BitVecVal(1, 1), flip_1),
                z_2 == z_1  # z unchanged if flipped
            )
        )
    ]
    
    g.add(*constraints)

    # Convert to CNF
    t = z3.Then("simplify", "bit-blast", "tseitin-cnf")
    subgoal = t(g)
    assert len(subgoal) == 1
    cnf_goal = subgoal[0]
    
    output_dimacs(cnf_goal, path)
    # Optional sanity check
    check_status(constraints)



def Geo0(path, p, NUM_BITS):
    # EXAMPLE Geo0
    z_1 = z3.BitVec("z_1", NUM_BITS)  # 8-bit integer
    z_2 = z3.BitVec("z_2", NUM_BITS)  # 8-bit integer
    flip_1 = z3.BitVec("flip_1", 1)  # 1-bit indicator
    flip_2 = z3.BitVec("flip_2", 1)
    d1 = z3.BitVec("d1", 1)  # 1-bit Bernoulli sample
    rand1 = z3.BitVec("rand1", 1)  # 4-bit random number
    d2 = z3.BitVec("d2", 1)  # 1-bit Bernoulli sample
    rand2 = z3.BitVec("rand2", 4)  # 4-bit random number
    g = z3.Goal()
    g = add_bitmap(g, NUM_BITS, z_1)
    g = add_bitmap(g, 1, flip_1)
    g = add_bitmap(g, 1, d1)
    g = add_bitmap(g, 1, rand1)

    g = add_bitmap(g, 1, d2)
    g = add_bitmap(g, 4, rand2)
    g = add_bitmap(g, 1, flip_2)
    g = add_bitmap(g, NUM_BITS, z_2)

    """
    constraints = [
        z3.UGT(rand0, 0b1010),
        # rand == 0b1010,
        d0 == z3.If(z3.ULT(rand0, 0b1), z3.BitVecVal(1, 1), z3.BitVecVal(0, 1)),
        flip_1 == z3.If(d0 == 1, z3.BitVecVal(1, 1), flip0),
        z_2 == z3.If(d0 == 0, z_1 + z3.BitVecVal(1, NUM_BITS), z_1),
    ]
    """
    constraints = [
    d2 == z3.If(z3.ULT(rand2, 0b1),
                z3.BitVecVal(1, 1),
                z3.BitVecVal(0, 1)),

    z3.If(
        d2 == 1,
        z3.And(
            d1 == z3.If(
                z3.And(z3.ULT(rand1, int(16*p)), flip_1 == 0),
                z3.BitVecVal(1, 1),
                z3.BitVecVal(0, 1)
            ),
            flip_2 == z3.If(d1 == 1, z3.BitVecVal(1, 1), flip_1),
            z_2 == z3.If(z3.And(d1 == 0, flip_1 == 0),
                         z3.BitVecVal(1, NUM_BITS) + z_1,
                         z_1)
        ),
        z3.And(
            z_2 == z_1,
            flip_2 == flip_1
        )
    )
    ]

    g.add(*constraints)
    t = z3.Then("simplify", "bit-blast", "tseitin-cnf")
    subgoal = t(g)
    assert len(subgoal) == 1
    cnf_goal = subgoal[0]
    output_dimacs(cnf_goal, path)
    # optional
    check_status(constraints)

def BigGeo0(path, p, NUM_BITS):
    z_1 = z3.BitVec("z_1", NUM_BITS)  # 8-bit integer
    z_2 = z3.BitVec("z_2", NUM_BITS)  # 8-bit integer
    flip_1 = z3.BitVec("flip_1", 1)  # 1-bit indicator
    flip_2 = z3.BitVec("flip_2", 1)
    d1 = z3.BitVec("d1", 1)  # 1-bit Bernoulli sample
    rand1 = z3.BitVec("rand1", 4)  # 4-bit random number
    d2 = z3.BitVec("d2", 1)  # 1-bit Bernoulli sample
    rand2 = z3.BitVec("rand2", 1)  # 4-bit random number
    g = z3.Goal()
    g = add_bitmap(g, NUM_BITS, z_1)
    g = add_bitmap(g, 1, flip_1)
    g = add_bitmap(g, 1, d1)
    g = add_bitmap(g, 4, rand1)
    g = add_bitmap(g, 1, rand2)
    g = add_bitmap(g, 1, flip_2)
    g = add_bitmap(g, NUM_BITS, z_2)

    constraints = [
    d2 == z3.If(z3.ULT(rand2, 0b1),
                z3.BitVecVal(1, 1),
                z3.BitVecVal(0, 1)),

    z3.If(
        d2 == 1,
        z3.And(
            d1 == z3.If(
                z3.And(z3.ULT(rand1, int(16*p)), flip_1 == 0),
                z3.BitVecVal(1, 1),
                z3.BitVecVal(0, 1)
            ),
            flip_2 == z3.If(d1 == 1, z3.BitVecVal(1, 1), flip_1),
            z_2 == z3.If(z3.And(d1 == 0, flip_1 == 0),
                         z3.BitVecVal(1, NUM_BITS) + z_1,
                         z_1)
        ),
        z3.And(
            z_2 == z_1,
            flip_2 == flip_1
        )
    )
    ]
    g.add(*constraints)
    t = z3.Then("simplify", "bit-blast", "tseitin-cnf")
    subgoal = t(g)
    assert len(subgoal) == 1
    cnf_goal = subgoal[0]
    output_dimacs(cnf_goal, path)
    # optional
    check_status(constraints)

def BigGeo1(path, p, NUM_BITS):
    z_1 = z3.BitVec("z_1", NUM_BITS)
    z_2 = z3.BitVec("z_2", NUM_BITS)
    x_1 = z3.BitVec("x_1", NUM_BITS)
    x_2 = z3.BitVec("x_2", NUM_BITS)
    flip_1 = z3.BitVec("flip_1", 1)
    flip_2 = z3.BitVec("flip_2", 1)
    d1 = z3.BitVec("d1", 1)
    rand1 = z3.BitVec("rand1", 4)
    d2 = z3.BitVec("d2", 1)
    rand2 = z3.BitVec("rand2", 1)
    
    g = z3.Goal()
    g = add_bitmap(g, NUM_BITS, z_1)
    g = add_bitmap(g, NUM_BITS, x_1)
    g = add_bitmap(g, 1, flip_1)
    g = add_bitmap(g, 1, d1)
    g = add_bitmap(g, 4, rand1)
    g = add_bitmap(g, 1, rand2)
    g = add_bitmap(g, 1, flip_2)
    g = add_bitmap(g, NUM_BITS, z_2)
    g = add_bitmap(g, NUM_BITS, x_2)

    constraints = [
        d2 == z3.If(z3.ULT(rand2, 0b1),
                    z3.BitVecVal(1, 1),
                    z3.BitVecVal(0, 1)),
        
        z3.If(
            d2 == 1,
            z3.And(
                d1 == z3.If(
                    z3.And(z3.ULT(rand1, int(16 * p)), flip_1 == 0),
                    z3.BitVecVal(1, 1),
                    z3.BitVecVal(0, 1)
                ),
                flip_2 == z3.If(d1 == 1, z3.BitVecVal(1, 1), flip_1),
                z_2 == z3.If(z3.And(d1 == 0, flip_1 == 0),
                             z3.BitVecVal(1, NUM_BITS) + z_1,
                             z_1),
                # If d1 is 0 and flip is 0, update x to 2*x (left shift by 1)
                x_2 == z3.If(z3.And(d1 == 0, flip_1 == 0),
                             x_1 << 1,
                             x_1)
            ),
            z3.And(
                z_2 == z_1,
                x_2 == x_1,
                flip_2 == flip_1
            )
        )
    ]
    
    g.add(*constraints)
    t = z3.Then("simplify", "bit-blast", "tseitin-cnf")
    subgoal = t(g)
    assert len(subgoal) == 1
    cnf_goal = subgoal[0]
    output_dimacs(cnf_goal, path)
    # optional
    check_status(constraints)


def BigGeo2(path, p, NUM_BITS):
    z_1 = z3.BitVec("z_1", NUM_BITS)
    z_2 = z3.BitVec("z_2", NUM_BITS)
    x_1 = z3.BitVec("x_1", NUM_BITS)
    x_2 = z3.BitVec("x_2", NUM_BITS)
    flip_1 = z3.BitVec("flip_1", 1)
    flip_2 = z3.BitVec("flip_2", 1)
    d1 = z3.BitVec("d1", 1)
    rand1 = z3.BitVec("rand1", 4)
    d2 = z3.BitVec("d2", 1)
    rand2 = z3.BitVec("rand2", 1)
    
    g = z3.Goal()
    g = add_bitmap(g, NUM_BITS, z_1)
    g = add_bitmap(g, NUM_BITS, x_1)
    g = add_bitmap(g, 1, flip_1)
    g = add_bitmap(g, 1, d1)
    g = add_bitmap(g, 4, rand1)
    g = add_bitmap(g, 1, rand2)
    g = add_bitmap(g, 1, flip_2)
    g = add_bitmap(g, NUM_BITS, z_2)
    g = add_bitmap(g, NUM_BITS, x_2)

    constraints = [
        d2 == z3.If(z3.ULT(rand2, 0b1),
                    z3.BitVecVal(1, 1),
                    z3.BitVecVal(0, 1)),
        
        z3.If(
            d2 == 1,
            z3.And(
                d1 == z3.If(
                    z3.And(z3.ULT(rand1, int(16 * p)), flip_1 == 0),
                    z3.BitVecVal(1, 1),
                    z3.BitVecVal(0, 1)
                ),
                flip_2 == z3.If(d1 == 1, z3.BitVecVal(1, 1), flip_1),
                z_2 == z3.If(z3.And(d1 == 0, flip_1 == 0),
                             z3.BitVecVal(1, NUM_BITS) + z_1,
                             z_1),
                # If d1 is 0 and flip is 0, update x by adding 1
                x_2 == z3.If(z3.And(d1 == 0, flip_1 == 0),
                             z3.BitVecVal(1, NUM_BITS) + x_1,
                             x_1)
            ),
            z3.And(
                z_2 == z_1,
                x_2 == x_1,
                flip_2 == flip_1
            )
        )
    ]
    
    g.add(*constraints)
    t = z3.Then("simplify", "bit-blast", "tseitin-cnf")
    subgoal = t(g)
    assert len(subgoal) == 1
    cnf_goal = subgoal[0]
    output_dimacs(cnf_goal, path)
    # optional
    check_status(constraints)



def LinExp(path, p, NUM_BITS):
    x_1 = z3.BitVec("x_1", 1)
    x_2 = z3.BitVec("x_2", 1)
    x_3 = z3.BitVec("x_3", 1)
    d = z3.BitVec("d", 1)
    rand1 = z3.BitVec("rand1", 4)
    rand2 = z3.BitVec("rand2", 4)
    rand3 = z3.BitVec("rand3", 4)
    rand4 = z3.BitVec("rand4", 1)
    n_1 = z3.BitVec("n_1", NUM_BITS)
    n_2 = z3.BitVec("n_2", NUM_BITS)
    c1 = z3.BitVec("c1", 1)
    c2 = z3.BitVec("c2", 1)
    c3 = z3.BitVec("c3", 1)
    count_1 = z3.BitVec("count_1", NUM_BITS)
    count_2 = z3.BitVec("count_2", NUM_BITS)
    g = z3.Goal()
    g = add_bitmap(g, 1, x_1)
    g = add_bitmap(g, 1, x_2)
    g = add_bitmap(g, 1, x_3)
    g = add_bitmap(g, 4, rand1)
    g = add_bitmap(g, 4, rand2)
    g = add_bitmap(g, 4, rand3)
    g = add_bitmap(g, NUM_BITS, n_1)
    g = add_bitmap(g, NUM_BITS, n_2)
    g = add_bitmap(g, 1, c1)
    g = add_bitmap(g, 1, c2)
    g = add_bitmap(g, 1, c3)
    g = add_bitmap(g, NUM_BITS, count_1)
    g = add_bitmap(g, NUM_BITS, count_2)

    constraints = [d == z3.If(z3.ULT(rand4, 0b1), z3.BitVecVal(1, 1),
                z3.BitVecVal(0, 1)),
        
        z3.If(d == 1, z3.And(x_1
        == z3.If(
            z3.And(z3.ULT(rand1, int(16*p)), z3.UGT(n_1, 0)),
            z3.BitVecVal(1, 1),
            z3.BitVecVal(0, 1),
        ),
        x_2
        == z3.If(
            z3.And(z3.ULT(rand2, int(16*p)), z3.UGT(n_1, 0)),
            z3.BitVecVal(1, 1),
            z3.BitVecVal(0, 1),
        ),
        x_3
        == z3.If(
            z3.And(z3.ULT(rand3, int(16*p)), z3.UGT(n_1, 0)),
            z3.BitVecVal(1, 1),
            z3.BitVecVal(0, 1),
        ),
        n_2 == z3.If(z3.UGT(n_1, 0), n_1 - z3.BitVecVal(1, NUM_BITS), n_1),
        c1
        == z3.If(
            z3.And(z3.UGT(n_1, 0), z3.Or(x_1 != 0, x_2 != 0, x_3 != 0)),
            z3.BitVecVal(1, 1),
            c1,
        ),
        c2
        == z3.If(
            z3.And(z3.UGT(n_1, 0), z3.Or(x_1 != 1, x_2 != 0, x_3 != 0)),
            z3.BitVecVal(1, 1),
            c2,
        ),
        c3
        == z3.If(
            z3.And(z3.UGT(n_1, 0), z3.Or(x_1 != 0, x_2 != 1, x_3 != 0)),
            z3.BitVecVal(1, 1),
            c3,
        ),
        count_2 == z3.If(
        z3.UGT(n_1, 0),
        count_1 
        + z3.If(c1 == 1, z3.BitVecVal(1, NUM_BITS), z3.BitVecVal(0, NUM_BITS))
        + z3.If(c2 == 1, z3.BitVecVal(1, NUM_BITS), z3.BitVecVal(0, NUM_BITS))
        + z3.If(c3 == 1, z3.BitVecVal(1, NUM_BITS), z3.BitVecVal(0, NUM_BITS)),
        count_1,
        )), (z3.And(count_2 == count_1, n_2 == n_1))),
    ]
    g.add(*constraints)
    t = z3.Then("simplify", "bit-blast", "tseitin-cnf")
    subgoal = t(g)
    assert len(subgoal) == 1
    cnf_goal = subgoal[0]
    output_dimacs(cnf_goal, path)
    # optional
    check_status(constraints)


def DepRV(path, p, NUM_BITS):
    d1 = z3.BitVec("d1", 1)
    rand1 = z3.BitVec("rand1", 4)
    x_1 = z3.BitVec("x_1", NUM_BITS)
    x_2 = z3.BitVec("x_2", NUM_BITS)
    y_1 = z3.BitVec("y_1", NUM_BITS)
    y_2 = z3.BitVec("y_2", NUM_BITS)
    n_1 = z3.BitVec("n_1", NUM_BITS)
    n_2 = z3.BitVec("n_2", NUM_BITS)
    d2 = z3.BitVec("d2", 1)
    rand2 = z3.BitVec("rand2", 1)
    g = z3.Goal()
    g = add_bitmap(g, 1, d1)
    g = add_bitmap(g, 4, rand1)
    g = add_bitmap(g, 1, d2)
    g = add_bitmap(g, 1, rand2)
    g = add_bitmap(g, NUM_BITS, x_1)
    g = add_bitmap(g, NUM_BITS, x_2)
    g = add_bitmap(g, NUM_BITS, y_1)
    g = add_bitmap(g, NUM_BITS, y_2)
    g = add_bitmap(g, NUM_BITS, n_1)
    g = add_bitmap(g, NUM_BITS, n_2)
    constraints = [
        d2 == z3.If(z3.ULT(rand2, 0b1), z3.BitVecVal(1, 1), z3.BitVecVal(0, 1)),
        z3.If(
            d2 == 1,
            z3.And(
                d1
                == z3.If(
                    z3.And(z3.ULT(rand1, int(16*p)), z3.UGT(n_1, 0)),
                    z3.BitVecVal(1, 1),
                    z3.BitVecVal(0, 1),
                ),
                x_2
                == z3.If(
                    z3.And(d1 == 1, z3.UGT(n_1, 0)), x_1 + z3.BitVecVal(1, NUM_BITS), x_1
                ),
                y_2
                == z3.If(
                    z3.And(d1 == 0, z3.UGT(n_1, 0)), y_1 + z3.BitVecVal(1, NUM_BITS), y_1
                ),
                n_2 == z3.If(z3.UGT(n_1, 0), n_1 - z3.BitVecVal(1, NUM_BITS), n_1),
            ),
            z3.And(x_2 == x_1, n_2 == n_1, y_2 == y_1),
        ),
    ]
    g.add(*constraints)
    t = z3.Then("simplify", "bit-blast", "tseitin-cnf")
    subgoal = t(g)
    assert len(subgoal) == 1
    cnf_goal = subgoal[0]
    output_dimacs(cnf_goal, path)
    # optional
    check_status(constraints)



def Bin0(path, p, NUM_BITS):
    d1 = z3.BitVec("d1", 1)
    rand1 = z3.BitVec("rand1", 4)
    x_1 = z3.BitVec("x_1", NUM_BITS)
    x_2 = z3.BitVec("x_2", NUM_BITS)
    y_1 = z3.BitVec("y_1", NUM_BITS)
    y_2 = z3.BitVec("y_2", NUM_BITS)
    n_1 = z3.BitVec("n_1", NUM_BITS)
    n_2 = z3.BitVec("n_2", NUM_BITS)
    d2 = z3.BitVec("d2", 1)
    rand2 = z3.BitVec("rand2", 1)
    g = z3.Goal()
    g = add_bitmap(g, 1, d1)
    g = add_bitmap(g, 4, rand1)
    g = add_bitmap(g, 1, d2)
    g = add_bitmap(g, 1, rand2)
    g = add_bitmap(g, NUM_BITS, x_1)
    g = add_bitmap(g, NUM_BITS, x_2)
    g = add_bitmap(g, NUM_BITS, y_1)
    g = add_bitmap(g, NUM_BITS, y_2)
    g = add_bitmap(g, NUM_BITS, n_1)
    g = add_bitmap(g, NUM_BITS, n_2)
    # Shared conditions
    n_positive = z3.UGT(n_1, 0)
    rand1_heads = z3.ULT(rand1, int(16*p))
    rand2_heads = z3.ULT(rand2, 0b1)

    # Define constraints using z3.Implies
    constraints = [ 
        # Outer coin toss d2
        d2 == z3.If(rand2_heads, z3.BitVecVal(1, 1), z3.BitVecVal(0, 1)),

        # Inner coin toss d1 (only meaningful if d2 fires)
        z3.Implies(
            z3.And(d2 == 1, n_positive),
            d1 == z3.If(rand1_heads, z3.BitVecVal(1, 1), z3.BitVecVal(0, 1))
        ),

        # x update only if d2 and d1 fire under n > 0
        z3.Implies(
            z3.And(d2 == 1, d1 == 1, n_positive),
            x_2 == x_1 + y_1
        ),
        z3.Implies(
            z3.Or(d2 == 0, d1 == 0, z3.Not(n_positive)),
            x_2 == x_1
        ),

        # y is always unchanged
        y_2 == y_1,

        # n update only if d2 fires
        z3.Implies(
            z3.And(d2 == 1, n_positive),
            n_2 == n_1 - z3.BitVecVal(1, NUM_BITS)
        ),
        z3.Implies(
            z3.Or(d2 == 0, z3.Not(n_positive)),
            n_2 == n_1
        ),
    ]

    g.add(*constraints)
    t = z3.Then("simplify", "bit-blast", "tseitin-cnf")
    subgoal = t(g)
    assert len(subgoal) == 1
    cnf_goal = subgoal[0]
    output_dimacs(cnf_goal, path)
    # optional
    check_status(constraints)


def Bin1(path, p, NUM_BITS):
    d1 = z3.BitVec("d1", 1)
    rand1 = z3.BitVec("rand1", 4)
    x_1 = z3.BitVec("x_1", NUM_BITS)
    x_2 = z3.BitVec("x_2", NUM_BITS)
    n_1 = z3.BitVec("n_1", NUM_BITS)
    n_2 = z3.BitVec("n_2", NUM_BITS)
    d2 = z3.BitVec("d2", 1)
    rand2 = z3.BitVec("rand2", 1)
    
    g = z3.Goal()
    g = add_bitmap(g, 1, d1)
    g = add_bitmap(g, 4, rand1)
    g = add_bitmap(g, 1, d2)
    g = add_bitmap(g, 1, rand2)
    g = add_bitmap(g, NUM_BITS, x_1)
    g = add_bitmap(g, NUM_BITS, x_2)
    g = add_bitmap(g, NUM_BITS, n_1)
    g = add_bitmap(g, NUM_BITS, n_2)
    
    # Shared conditions
    M = globM
    loop_condition = z3.ULT(n_1, M)
    rand1_heads = z3.ULT(rand1, int(16 * p))
    rand2_heads = z3.ULT(rand2, 0b1)

    # Define constraints using z3.Implies
    constraints = [
        # Outer coin toss d2
        d2 == z3.If(rand2_heads, z3.BitVecVal(1, 1), z3.BitVecVal(0, 1)),

        # Inner coin toss d1 (only meaningful if d2 fires and loop condition holds)
        z3.Implies(
            z3.And(d2 == 1, loop_condition),
            d1 == z3.If(rand1_heads, z3.BitVecVal(1, 1), z3.BitVecVal(0, 1))
        ),

        # x update only if d2 and d1 fire and x < M
        z3.Implies(
            z3.And(d2 == 1, d1 == 1, loop_condition),
            x_2 == x_1 + z3.BitVecVal(1, NUM_BITS)
        ),
        z3.Implies(
            z3.Or(d2 == 0, d1 == 0, z3.Not(loop_condition)),
            x_2 == x_1
        ),

        # n update only if d2 and d1 fire and x < M
        z3.Implies(
            z3.And(d2 == 1, d1 == 1, loop_condition),
            n_2 == n_1 + z3.BitVecVal(1, NUM_BITS)
        ),
        z3.Implies(
            z3.Or(d2 == 0, d1 == 0, z3.Not(loop_condition)),
            n_2 == n_1
        ),
    ]

    g.add(*constraints)
    t = z3.Then("simplify", "bit-blast", "tseitin-cnf")
    subgoal = t(g)
    assert len(subgoal) == 1
    cnf_goal = subgoal[0]
    output_dimacs(cnf_goal, path)
    # optional
    check_status(constraints)



def BinMod(path, p, NUM_BITS):
    # --------------------------------------------------
    # Bit-vector declarations
    # --------------------------------------------------
    d1 = z3.BitVec("d1", 1)
    d2 = z3.BitVec("d2", 1)

    rand1 = z3.BitVec("rand1", 4)
    rand2 = z3.BitVec("rand2", 1)

    x_1 = z3.BitVec("x_1", NUM_BITS)
    x_2 = z3.BitVec("x_2", NUM_BITS)
    x_3 = z3.BitVec("x_3", NUM_BITS)   # OUTPUT = x mod 7

    n_1 = z3.BitVec("n_1", NUM_BITS)
    n_2 = z3.BitVec("n_2", NUM_BITS)

    # --------------------------------------------------
    # Goal and bitmaps
    # --------------------------------------------------
    g = z3.Goal()

    g = add_bitmap(g, 1, d1)
    g = add_bitmap(g, 1, d2)
    g = add_bitmap(g, 4, rand1)
    g = add_bitmap(g, 1, rand2)

    g = add_bitmap(g, NUM_BITS, x_1)
    g = add_bitmap(g, NUM_BITS, x_2)
    g = add_bitmap(g, NUM_BITS, x_3)

    g = add_bitmap(g, NUM_BITS, n_1)
    g = add_bitmap(g, NUM_BITS, n_2)

    # --------------------------------------------------
    # Constants and conditions
    # --------------------------------------------------
    M = globM  # BitVecVal(M, NUM_BITS)

    loop_condition = z3.ULT(n_1, M)

    rand2_heads = z3.ULT(rand2, z3.BitVecVal(1, 1))            # prob 1/2
    rand1_heads = z3.ULT(rand1, z3.BitVecVal(int(16 * p), 4))  # prob p

    # --------------------------------------------------
    # Constraints
    # --------------------------------------------------
    constraints = [

        # outer coin toss
        d2 == z3.If(rand2_heads,
                    z3.BitVecVal(1, 1),
                    z3.BitVecVal(0, 1)),

        # inner coin toss (only if outer coin fires and loop holds)
        z3.Implies(
            z3.And(d2 == 1, loop_condition),
            d1 == z3.If(rand1_heads,
                        z3.BitVecVal(1, 1),
                        z3.BitVecVal(0, 1))
        ),

        # x update
        z3.Implies(
            z3.And(d2 == 1, d1 == 1, loop_condition),
            x_2 == x_1 + z3.BitVecVal(1, NUM_BITS)
        ),
        z3.Implies(
            z3.Or(d2 == 0, d1 == 0, z3.Not(loop_condition)),
            x_2 == x_1
        ),

        # n update
        z3.Implies(
            z3.And(d2 == 1, d1 == 1, loop_condition),
            n_2 == n_1 + z3.BitVecVal(1, NUM_BITS)
        ),
        z3.Implies(
            z3.Or(d2 == 0, d1 == 0, z3.Not(loop_condition)),
            n_2 == n_1
        ),

        # --------------------------------------------------
        # OUTPUT: x_3 = x_2 mod 100
        # --------------------------------------------------
        x_3 == z3.URem(x_2, z3.BitVecVal(100, NUM_BITS))
    ]

    g.add(*constraints)

    # --------------------------------------------------
    # CNF generation
    # --------------------------------------------------
    t = z3.Then("simplify", "bit-blast", "tseitin-cnf")
    subgoal = t(g)
    assert len(subgoal) == 1

    cnf_goal = subgoal[0]
    output_dimacs(cnf_goal, path)

    # optional sanity check
    check_status(constraints)


def Bin2(path, p, NUM_BITS):
    d1 = z3.BitVec("d1", 1)
    rand1 = z3.BitVec("rand1", 4)
    x_1 = z3.BitVec("x_1", NUM_BITS)
    x_2 = z3.BitVec("x_2", NUM_BITS)
    y_1 = z3.BitVec("y_1", NUM_BITS)
    y_2 = z3.BitVec("y_2", NUM_BITS)
    n_1 = z3.BitVec("n_1", NUM_BITS)
    n_2 = z3.BitVec("n_2", NUM_BITS)
    d2 = z3.BitVec("d2", 1)
    rand2 = z3.BitVec("rand2", 1)
    
    g = z3.Goal()
    g = add_bitmap(g, 1, d1)
    g = add_bitmap(g, 4, rand1)
    g = add_bitmap(g, 1, d2)
    g = add_bitmap(g, 1, rand2)
    g = add_bitmap(g, NUM_BITS, x_1)
    g = add_bitmap(g, NUM_BITS, x_2)
    g = add_bitmap(g, NUM_BITS, y_1)
    g = add_bitmap(g, NUM_BITS, y_2)
    g = add_bitmap(g, NUM_BITS, n_1)
    g = add_bitmap(g, NUM_BITS, n_2)
    
    # Shared conditions
    n_positive = z3.UGT(n_1, 0)
    rand1_heads = z3.ULT(rand1, int(16*p))
    rand2_heads = z3.ULT(rand2, 0b1)

    # Define constraints using z3.Implies
    constraints = [
        # Outer coin toss d2
        d2 == z3.If(rand2_heads, z3.BitVecVal(1, 1), z3.BitVecVal(0, 1)),

        # Inner coin toss d1 (only meaningful if d2 fires and n > 0)
        z3.Implies(
            z3.And(d2 == 1, n_positive),
            d1 == z3.If(rand1_heads, z3.BitVecVal(1, 1), z3.BitVecVal(0, 1))
        ),

        # x update for d1=1 case (if d2 fires and n > 0)
        z3.Implies(
            z3.And(d2 == 1, d1 == 1, n_positive),
            x_2 == x_1 + n_1
        ),
        # x update for d1=0 case (if d2 fires and n > 0)
        z3.Implies(
            z3.And(d2 == 1, d1 == 0, n_positive),
            x_2 == x_1 + y_1
        ),
        # x is unchanged if loop doesn't run
        z3.Implies(
            z3.Or(d2 == 0, z3.Not(n_positive)),
            x_2 == x_1
        ),

        # y is always unchanged
        y_2 == y_1,

        # n update only if d2 fires, n>0, and d1=0
        z3.Implies(
            z3.And(d2 == 1, d1 == 0, n_positive),
            n_2 == n_1 - z3.BitVecVal(1, NUM_BITS)
        ),
        z3.Implies(
            z3.Or(d2 == 0, d1 == 1, z3.Not(n_positive)),
            n_2 == n_1
        ),
    ]

    g.add(*constraints)
    t = z3.Then("simplify", "bit-blast", "tseitin-cnf")
    subgoal = t(g)
    assert len(subgoal) == 1
    cnf_goal = subgoal[0]
    output_dimacs(cnf_goal, path)
    # optional
    check_status(constraints)

def BiasDir(path, p, NUM_BITS):
    d1 = z3.BitVec("d1", 1)      # Corresponds to d1 in Python code (for x's update)
    rand1 = z3.BitVec("rand1", 4)
    d2 = z3.BitVec("d2", 1)      # Probabilistic guard for the entire step
    rand2 = z3.BitVec("rand2", 1)
    d3 = z3.BitVec("d3", 1)      # Corresponds to d2 in Python code (for y's update)
    rand3 = z3.BitVec("rand3", 4) # A second random source for y's update
    
    x_1 = z3.BitVec("x_1", 1)
    x_2 = z3.BitVec("x_2", 1)
    y_1 = z3.BitVec("y_1", 1)
    y_2 = z3.BitVec("y_2", 1)
    
    g = z3.Goal()
    g = add_bitmap(g, 1, d1)
    g = add_bitmap(g, 4, rand1)
    g = add_bitmap(g, 1, d2)
    g = add_bitmap(g, 1, rand2)
    g = add_bitmap(g, 1, d3)
    g = add_bitmap(g, 4, rand3)
    g = add_bitmap(g, 1, x_1)
    g = add_bitmap(g, 1, x_2)
    g = add_bitmap(g, 1, y_1)
    g = add_bitmap(g, 1, y_2)

    # Shared conditions
    loop_condition = (x_1 == y_1)
    rand1_heads = z3.ULT(rand1, int(16 * p)) # For updating x
    rand2_heads = z3.ULT(rand2, 0b1)         # For the step to occur
    rand3_heads = z3.ULT(rand3, int(16 * p)) # For updating y

    # Define constraints using z3.Implies
    constraints = [
        # Outer coin toss d2
        d2 == z3.If(rand2_heads, z3.BitVecVal(1, 1), z3.BitVecVal(0, 1)),

        # Inner coin toss d1 (for x), only meaningful if step happens and loop condition holds
        z3.Implies(
            z3.And(d2 == 1, loop_condition),
            d1 == z3.If(rand1_heads, z3.BitVecVal(1, 1), z3.BitVecVal(0, 1))
        ),
        
        # Inner coin toss d3 (for y), also only meaningful if step happens and loop condition holds
        z3.Implies(
            z3.And(d2 == 1, loop_condition),
            d3 == z3.If(rand3_heads, z3.BitVecVal(1, 1), z3.BitVecVal(0, 1))
        ),

        # x is updated based on d1 if the loop runs
        z3.Implies(
            z3.And(d2 == 1, loop_condition),
            x_2 == z3.If(d1 == 1, z3.BitVecVal(1, 1), z3.BitVecVal(0, 1))
        ),
        # x is unchanged if the loop does not run
        z3.Implies(
            z3.Or(d2 == 0, z3.Not(loop_condition)),
            x_2 == x_1
        ),
        
        # y is updated based on d3 if the loop runs
        z3.Implies(
            z3.And(d2 == 1, loop_condition),
            y_2 == z3.If(d3 == 1, z3.BitVecVal(1, 1), z3.BitVecVal(0, 1))
        ),
        # y is unchanged if the loop does not run
        z3.Implies(
            z3.Or(d2 == 0, z3.Not(loop_condition)),
            y_2 == y_1
        ),
    ]

    g.add(*constraints)
    t = z3.Then("simplify", "bit-blast", "tseitin-cnf")
    subgoal = t(g)
    assert len(subgoal) == 1
    cnf_goal = subgoal[0]
    output_dimacs(cnf_goal, path)
    # optional
    check_status(constraints)



def Detm(path, p, NUM_BITS):
    x_1 = z3.BitVec("x_1", NUM_BITS)
    x_2 = z3.BitVec("x_2", NUM_BITS)
    count_1 = z3.BitVec("count_1", NUM_BITS)
    count_2 = z3.BitVec("count_2", NUM_BITS)
    d1 = z3.BitVec("d1_", 1)
    rand1 = z3.BitVec("rand1_", 1)
    g = z3.Goal()
    g = add_bitmap(g, NUM_BITS, x_1)
    g = add_bitmap(g, NUM_BITS, x_2)
    g = add_bitmap(g, NUM_BITS, count_1)
    g = add_bitmap(g, NUM_BITS, count_2)
    g = add_bitmap(g, 1, d1)
    g = add_bitmap(g, 1, rand1)
    constraints = [
        d1 == z3.If(z3.ULT(rand1, 0b1), z3.BitVecVal(1, 1), z3.BitVecVal(0, 1)),
        z3.If(d1 == 1, z3.And(x_2 == z3.If(z3.ULT(x_1, 16), x_1 + z3.BitVecVal(1, NUM_BITS), x_1),
        count_2 == z3.If(z3.ULT(x_1, 16), count_1 + z3.BitVecVal(1, NUM_BITS), count_1)), z3.And(count_2 == count_1, x_2 == x_1))
        
    ]
    g.add(*constraints)
    t = z3.Then("simplify", "bit-blast", "tseitin-cnf")
    subgoal = t(g)
    assert len(subgoal) == 1
    cnf_goal = subgoal[0]
    output_dimacs(cnf_goal, path)
    # optional
    check_status(constraints)


"""
int x , y , z , float p
while not ( z == 0) :
    y = y + 1
    d = b e r n o u l l i. rvs ( size =1 , p = p ) [0]
    if ( d ) :
        z = 0
    else :
        x = x + y
"""


def GeoAr(path, p, NUM_BITS):
    d1 = z3.BitVec("d1", 1)
    rand1 = z3.BitVec("rand1", 4)
    z_1 = z3.BitVec("z_1", 1)
    z_2 = z3.BitVec("z_2", 1)
    y_1 = z3.BitVec("y_1", NUM_BITS)
    y_2 = z3.BitVec("y_2", NUM_BITS)
    x_1 = z3.BitVec("x_1", NUM_BITS)
    x_2 = z3.BitVec("x_2", NUM_BITS)
    d2 = z3.BitVec("d2", 1)
    rand2 = z3.BitVec("rand2", 1)
    g = z3.Goal()
    g = add_bitmap(g, 1, d1)
    g = add_bitmap(g, 4, rand1)
    g = add_bitmap(g, 1, d2)
    g = add_bitmap(g, 1, rand2)
    g = add_bitmap(g, 1, z_1)
    g = add_bitmap(g, 1, z_2)
    g = add_bitmap(g, NUM_BITS, x_1)
    g = add_bitmap(g, NUM_BITS, x_2)
    g = add_bitmap(g, NUM_BITS, y_1)
    g = add_bitmap(g, NUM_BITS, y_2)
    constraints = [
        d2 == z3.If(z3.ULT(rand2, 0b1), z3.BitVecVal(1, 1), z3.BitVecVal(0, 1)),
        z3.If(d2 == 1, z3.And(y_2 == z3.If(z_1 != 0, y_1 + z3.BitVecVal(1, NUM_BITS), y_1),
        d1
        == z3.If(
            z3.And(z3.ULT(rand1, int(16*p)), z_1 != 0),
            z3.BitVecVal(1, 1),
            z3.BitVecVal(0, 1),
        ),
        z_2
        == z3.If(
            z3.And(d1 == 1, z_1 != 0),
            z3.BitVecVal(0, 1),
            z_1,
        ),
        x_2
        == z3.If(
            z3.And(d1 == 0, z_1 != 0),
            x_1 + y_2,
            x_1,
        )), z3.And(z_2 == z_1, y_2 == y_1, x_2 == x_1))       
    ]
    g.add(*constraints)
    t = z3.Then("simplify", "bit-blast", "tseitin-cnf")
    subgoal = t(g)
    assert len(subgoal) == 1
    cnf_goal = subgoal[0]
    output_dimacs(cnf_goal, path)
    # optional
    check_status(constraints)



def ModSumOld(path, p, NUM_BITS):
    # --------------------------------------------------
    # Bit-vector declarations
    # --------------------------------------------------
    x_1 = z3.BitVec("x_1", NUM_BITS)   # input x
    x_2 = z3.BitVec("x_2", NUM_BITS)   # after update
    x_3 = z3.BitVec("x_3", NUM_BITS)   # after mod 100

    n_1 = z3.BitVec("n_1", NUM_BITS)   # input n
    n_2 = z3.BitVec("n_2", NUM_BITS)   # after decrement

    d1 = z3.BitVec("d1", 1)            # Bernoulli(p1)
    rand1 = z3.BitVec("rand1", 4)      # randomness for p1

    # --------------------------------------------------
    # Goal and bitmap
    # --------------------------------------------------
    g = z3.Goal()

    g = add_bitmap(g, NUM_BITS, x_1)
    g = add_bitmap(g, NUM_BITS, x_2)
    g = add_bitmap(g, NUM_BITS, x_3)

    g = add_bitmap(g, NUM_BITS, n_1)
    g = add_bitmap(g, NUM_BITS, n_2)

    g = add_bitmap(g, 1, d1)
    g = add_bitmap(g, 4, rand1)

    # --------------------------------------------------
    # Conditions
    # --------------------------------------------------
    loop_condition = z3.UGT(n_1, z3.BitVecVal(0, NUM_BITS))
    rand1_heads = z3.ULT(rand1, z3.BitVecVal(int(16 * p), 4))

    # --------------------------------------------------
    # Constraints
    # --------------------------------------------------
    constraints = [

        # Bernoulli(p1)
        d1 == z3.If(
            rand1_heads,
            z3.BitVecVal(1, 1),
            z3.BitVecVal(0, 1)
        ),

        # x update: x + n if d1 fires
        z3.Implies(
            z3.And(loop_condition, d1 == 1),
            x_2 == x_1 + n_1
        ),
        z3.Implies(
            z3.Or(d1 == 0, z3.Not(loop_condition)),
            x_2 == x_1
        ),

        # n always decrements if loop condition holds
        z3.Implies(
            loop_condition,
            n_2 == n_1 - z3.BitVecVal(1, NUM_BITS)
        ),
        z3.Implies(
            z3.Not(loop_condition),
            n_2 == n_1
        ),

        # --------------------------------------------------
        # MODIFICATION: x := x mod 800
        # --------------------------------------------------
        x_3 == z3.URem(x_2, z3.BitVecVal(800, NUM_BITS))
    ]

    g.add(*constraints)

    # --------------------------------------------------
    # CNF generation
    # --------------------------------------------------
    t = z3.Then("simplify", "bit-blast", "tseitin-cnf")
    subgoal = t(g)
    assert len(subgoal) == 1

    cnf_goal = subgoal[0]
    output_dimacs(cnf_goal, path)

    # Optional consistency check
    check_status(constraints)


def ModSum(path, p, NUM_BITS):

    x_1 = z3.BitVec("x_1", NUM_BITS)
    x_2 = z3.BitVec("x_2", NUM_BITS)

    n_1 = z3.BitVec("n_1", NUM_BITS)
    n_2 = z3.BitVec("n_2", NUM_BITS)

    it_1 = z3.BitVec("it_1", NUM_BITS)
    it_2 = z3.BitVec("it_2", NUM_BITS)

    d1 = z3.BitVec("d1", 1)
    rand1 = z3.BitVec("rand1", 1)

    g = z3.Goal()
    for v in [x_1, x_2, n_1, n_2, it_1, it_2]:
        g = add_bitmap(g, NUM_BITS, v)
    g = add_bitmap(g, 1, d1)
    g = add_bitmap(g, 1, rand1)

    loop_condition = z3.UGT(n_1, z3.BitVecVal(0, NUM_BITS))
    rand1_heads = rand1 == z3.BitVecVal(1, 1)

    # # ---- key change: only NUM_BITS-1 bits are randomized ----
    # bit_index = it_1 & z3.BitVecVal(NUM_BITS - 2, NUM_BITS)
    # flip_mask = z3.BitVecVal(1, NUM_BITS) << bit_index

    # bit_index = it_1 % (NUM_BITS - 1)
    bit_index = z3.URem(
        it_1,
        z3.BitVecVal(NUM_BITS - 1, NUM_BITS)
    )

    # flip_mask = 1 << bit_index
    flip_mask = z3.BitVecVal(1, NUM_BITS) << bit_index


    constraints = [
        d1 == z3.If(rand1_heads,
                    z3.BitVecVal(1, 1),
                    z3.BitVecVal(0, 1)),

        z3.Implies(z3.And(loop_condition, d1 == 1),
                   x_2 == x_1 ^ flip_mask),
        z3.Implies(z3.Or(d1 == 0, z3.Not(loop_condition)),
                   x_2 == x_1),

        z3.Implies(loop_condition,
                   n_2 == n_1 - z3.BitVecVal(1, NUM_BITS)),
        z3.Implies(z3.Not(loop_condition),
                   n_2 == n_1),

        z3.Implies(loop_condition,
                   it_2 == it_1 + z3.BitVecVal(1, NUM_BITS)),
        z3.Implies(z3.Not(loop_condition),
                   it_2 == it_1)
    ]

    g.add(*constraints)

    # --------------------------------------------------
    # CNF generation
    # --------------------------------------------------
    t = z3.Then("simplify", "bit-blast", "tseitin-cnf")
    subgoal = t(g)
    assert len(subgoal) == 1

    cnf_goal = subgoal[0]
    output_dimacs(cnf_goal, path)
    check_status(constraints)





"""
int x , float p1 , p2
while ( x == 0) :
    d1 = b e r n o u l l i. rvs ( size =1 , p = p1 ) [0]
    if ( d1 ) :
        x = 0
    else :
        d2 = b e r n o u l l i. rvs ( size =1 , p = p2 ) [0]
        if ( d2 ) :
            x = -1
        else :
            x = 1
"""


def Prinsys(path, p, NUM_BITS):
    d1 = z3.BitVec("d1", 1)
    rand1 = z3.BitVec("rand1", 4)
    d2 = z3.BitVec("d2", 1)
    rand2 = z3.BitVec("rand2", 4)
    d3 = z3.BitVec("d3", 1)
    rand3 = z3.BitVec("rand3", 1)
    x_1 = z3.BitVec("x_1", 2)
    x_6 = z3.BitVec("x_6", 2)
    x_5 = z3.BitVec("x_5", 2)
    f1 = z3.BitVec("f1", 1)
    f2 = z3.BitVec("f2", 1)
    x_2 = z3.BitVec("x_2", 2)
    x_3 = z3.BitVec("x_3", 2)
    x_4 = z3.BitVec("x_4", 2)
    g = z3.Goal()
    g = add_bitmap(g, 1, d1)
    g = add_bitmap(g, 4, rand1)
    g = add_bitmap(g, 1, d2)
    g = add_bitmap(g, 4, rand2)
    g = add_bitmap(g, 1, d3)
    g = add_bitmap(g, 1, rand3)
    g = add_bitmap(g, 2, x_1)
    g = add_bitmap(g, 2, x_6)
    g = add_bitmap(g, 2, x_2)
    g = add_bitmap(g, 2, x_3)
    g = add_bitmap(g, 2, x_4)
    g = add_bitmap(g, 2, x_5)
    g = add_bitmap(g, 1, f1)
    g = add_bitmap(g, 1, f2)
    constraints = [
        d3 == z3.If(z3.ULT(rand3, 0b1), z3.BitVecVal(1, 1), z3.BitVecVal(0, 1)),
        z3.If(
            d3 == 1,
            z3.And(
                d1
                == z3.If(
                    z3.And(z3.ULT(rand1, int(16*p)), x_1 == 0),
                    z3.BitVecVal(1, 1),
                    z3.BitVecVal(0, 1),
                ),
                d2
                == z3.If(
                    z3.And(z3.ULT(rand2, int(16*p)), d1 == 0, x_1 == 0),
                    z3.BitVecVal(1, 1),
                    z3.BitVecVal(0, 1),
                ),
                f1 == z3.If(d1 == 1, z3.BitVecVal(1, 1), z3.BitVecVal(0, 1)),
                f2
                == z3.If(
                    z3.And(d1 == 0, d2 == 1), z3.BitVecVal(1, 1), z3.BitVecVal(0, 1)
                ),
                x_2 == z3.If(z3.And(x_1 == 0, d1 == 1), 0, x_1),
                x_3
                == z3.If(z3.And(x_1 == 0, d1 == 0, d2 == 1), z3.BitVecVal(2, 2), x_1),
                x_4 == z3.If(z3.And(x_1 == 0, d1 == 0, d2 == 0), 1, x_1),
                x_5 == z3.If(f2 == 1, x_3, x_4),
                x_6 == z3.If(f1 == 1, x_2, x_5),
            ),
            z3.And(x_6 == x_1),
        ),
    ]
    g.add(*constraints)
    t = z3.Then("simplify", "bit-blast", "tseitin-cnf")
    subgoal = t(g)
    assert len(subgoal) == 1
    cnf_goal = subgoal[0]
    output_dimacs(cnf_goal, path)
    # optional
    check_status(constraints)




def Sum0(path, p, NUM_BITS):
    d1 = z3.BitVec("d1", 1)
    rand1 = z3.BitVec("rand1", 4)
    x_1 = z3.BitVec("x_1", NUM_BITS)
    x_2 = z3.BitVec("x_2", NUM_BITS)
    n_1 = z3.BitVec("n_1", NUM_BITS)
    n_2 = z3.BitVec("n_2", NUM_BITS)
    d2 = z3.BitVec("d2", 1)
    rand2 = z3.BitVec("rand2", 1)
    g = z3.Goal()
    g = add_bitmap(g, 1, d1)
    g = add_bitmap(g, 4, rand1)
    g = add_bitmap(g, NUM_BITS, x_1)
    g = add_bitmap(g, NUM_BITS, x_2)
    g = add_bitmap(g, NUM_BITS, n_1)
    g = add_bitmap(g, NUM_BITS, n_2)
    g = add_bitmap(g, 1, rand2)
    g = add_bitmap(g, 1, d2)


    constraints = [
        d2 == z3.If(z3.ULT(rand2, 0b1), z3.BitVecVal(1, 1), z3.BitVecVal(0, 1)),
        z3.If(d2 == 1, z3.And(d1
        == z3.If(
            z3.And(z3.ULT(rand1, int(16*p)), z3.UGT(n_1, 0)),
            z3.BitVecVal(1, 1),
            z3.BitVecVal(0, 1),
        ),
        x_2 == z3.If(z3.And(d1 == 1, z3.UGT(n_1, 0)), x_1 + n_1, x_1),
        n_2 == z3.If(z3.UGT(n_1, 0), n_1 - z3.BitVecVal(1, NUM_BITS), n_1)), z3.And(x_2 == x_1, n_2 == n_1))
    ]
    g.add(*constraints)
    t = z3.Then("simplify", "bit-blast", "tseitin-cnf")
    subgoal = t(g)
    assert len(subgoal) == 1
    cnf_goal = subgoal[0]
    output_dimacs(cnf_goal, path)
    # optional
    check_status(constraints)


def Fair(path, p, NUM_BITS):
    ca_1 = z3.BitVec("ca_1", 1)
    ca_2 = z3.BitVec("ca_2", 1)
    rand1 = z3.BitVec("rand1", 4)
    d3 = z3.BitVec("d3", 1)
    rand3 = z3.BitVec("rand3", 1)
    cb_1 = z3.BitVec("cb_1", 1)
    cb_2 = z3.BitVec("cb_2", 1)
    rand2 = z3.BitVec("rand2", 4)
    count1 = z3.BitVec("count1", NUM_BITS)
    count_1 = z3.BitVec("count_1", NUM_BITS)
    count_2 = z3.BitVec("count_2", NUM_BITS)
    g = z3.Goal()
    g = add_bitmap(g, 1, ca_1)
    g = add_bitmap(g, 1, ca_2)
    g = add_bitmap(g, 4, rand1)
    g = add_bitmap(g, 1, cb_1)
    g = add_bitmap(g, 1, cb_2)
    g = add_bitmap(g, 4, rand2)
    g = add_bitmap(g, NUM_BITS, count1)
    g = add_bitmap(g, NUM_BITS, count_1)
    g = add_bitmap(g, NUM_BITS, count_2)
    g = add_bitmap(g, 1, d3)
    g = add_bitmap(g, 1, rand3)

    constraints = [
        d3 == z3.If(z3.ULT(rand3, 0b1), z3.BitVecVal(1, 1), z3.BitVecVal(0, 1)),
        z3.If(
            d3 == 1,
            z3.And(
                ca_2
                == z3.If(
                    z3.And(z3.ULT(rand1, int(16*p)), ca_1 == 0, cb_1 == 0),
                    z3.BitVecVal(1, 1),
                    z3.BitVecVal(0, 1),
                ),
                count1
                == z3.If(
                    z3.And(ca_2 == 1, ca_1 == 0, cb_1 == 0),
                    count_1 + z3.BitVecVal(1, NUM_BITS),
                    count_1,
                ),
                cb_2
                == z3.If(
                    z3.And(z3.ULT(rand2, int(16*p)), ca_1 == 0, cb_1 == 0),
                    z3.BitVecVal(1, 1),
                    z3.BitVecVal(0, 1),
                ),
                count_2
                == z3.If(
                    z3.And(cb_2 == 1, ca_1 == 0, cb_1 == 0),
                    count1 + z3.BitVecVal(1, NUM_BITS),
                    count1,
                ),
            ),
            z3.And(count_2 == count_1, ca_2 == ca_1, cb_2 == cb_1),
        ),
    ]
    g.add(*constraints)
    t = z3.Then("simplify", "bit-blast", "tseitin-cnf")
    subgoal = t(g)
    assert len(subgoal) == 1
    cnf_goal = subgoal[0]
    output_dimacs(cnf_goal, path)
    # optional
    check_status(constraints)


def RevBin(path, p, NUM_BITS):
    d1 = z3.BitVec("d1", 1)
    rand1 = z3.BitVec("rand1", 4)
    x_1 = z3.BitVec("x_1", NUM_BITS)
    x_2 = z3.BitVec("x_2", NUM_BITS)
    z_1 = z3.BitVec("z_1", NUM_BITS)
    z_2 = z3.BitVec("z_2", NUM_BITS)
    d2 = z3.BitVec("d2", 1)
    rand2 = z3.BitVec("rand2", 1)
    g = z3.Goal()
    g = add_bitmap(g, 1, d1)
    g = add_bitmap(g, 4, rand1)
    g = add_bitmap(g, 1, d2)
    g = add_bitmap(g, 1, rand2)
    g = add_bitmap(g, NUM_BITS, x_1)
    g = add_bitmap(g, NUM_BITS, x_2)
    g = add_bitmap(g, NUM_BITS, z_1)
    g = add_bitmap(g, NUM_BITS, z_2)
    constraints = [
        d2 == z3.If(z3.ULT(rand2, 0b1), z3.BitVecVal(1, 1), z3.BitVecVal(0, 1)),
        z3.If(
            d2 == 1,
            z3.And(
                d1
                == z3.If(
                    z3.And(z3.ULT(rand1, int(16*p)), z3.UGT(x_1, 0)),
                    z3.BitVecVal(1, 1),
                    z3.BitVecVal(0, 1),
                ),
                x_2
                == z3.If(
                    z3.And(d1 == 1, z3.UGT(x_1, 0)), x_1 - z3.BitVecVal(1, NUM_BITS), x_1
                ),
                z_2 == z3.If(z3.UGT(x_1, 0), z_1 + z3.BitVecVal(1, NUM_BITS), z_1),
            ),
            z3.And(x_2 == x_1, z_2 == z_1),
        ),
    ]
    g.add(*constraints)
    t = z3.Then("simplify", "bit-blast", "tseitin-cnf")
    subgoal = t(g)
    assert len(subgoal) == 1
    cnf_goal = subgoal[0]
    output_dimacs(cnf_goal, path)
    # optional
    check_status(constraints)

def Mart(path, p, NUM_BITS):
    d1 = z3.BitVec("d1", 1)
    rand1 = z3.BitVec("rand1", 4)
    c_1 = z3.BitVec("c_1", NUM_BITS)
    c_2 = z3.BitVec("c_2", NUM_BITS)
    b_1 = z3.BitVec("b_1", NUM_BITS)
    b_2 = z3.BitVec("b_2", NUM_BITS)
    rounds_1 = z3.BitVec("rounds_1", NUM_BITS)
    rounds_2 = z3.BitVec("rounds_2", NUM_BITS)
    d2 = z3.BitVec("d2", 1)
    rand2 = z3.BitVec("rand2", 1)
    g = z3.Goal()
    g = add_bitmap(g, 1, d1)
    g = add_bitmap(g, 4, rand1)
    g = add_bitmap(g, 1, d2)
    g = add_bitmap(g, 1, rand2)
    g = add_bitmap(g, NUM_BITS, c_1)
    g = add_bitmap(g, NUM_BITS, c_2)
    g = add_bitmap(g, NUM_BITS, b_1)
    g = add_bitmap(g, NUM_BITS, b_2)
    g = add_bitmap(g, NUM_BITS, rounds_1)
    g = add_bitmap(g, NUM_BITS, rounds_2)
    constraints = [
        d2 == z3.If(z3.ULT(rand2, 0b1), z3.BitVecVal(1, 1), z3.BitVecVal(0, 1)),
        z3.If(
            d2 == 1,
            z3.And(
                d1
                == z3.If(
                    z3.And(z3.ULT(rand1, int(16*p)), z3.UGT(b_1, 0)),
                    z3.BitVecVal(1, 1),
                    z3.BitVecVal(0, 1),
                ),
                c_2 == z3.If(z3.And(d1 == 1, z3.UGT(b_1, 0)), c_1 + b_1, c_1 - b_1),
                b_2
                == z3.If(z3.And(d1 == 1, z3.UGT(b_1, 0)), z3.BitVecVal(0, NUM_BITS), 2 * b_1),
                rounds_2
                == z3.If(z3.UGT(b_1, 0), rounds_1 + z3.BitVecVal(1, NUM_BITS), rounds_1),
            ),
            z3.And(c_2 == c_1, b_2 == b_1, rounds_2 == rounds_1),
        ),
    ]
    g.add(*constraints)
    t = z3.Then("simplify", "bit-blast", "tseitin-cnf")
    subgoal = t(g)
    assert len(subgoal) == 1
    cnf_goal = subgoal[0]
    output_dimacs(cnf_goal, path)
    # optional
    check_status(constraints)


def Duel(path, p, NUM_BITS):
    d1 = z3.BitVec("d1", 1)
    rand1 = z3.BitVec("rand1", 4)
    c_1 = z3.BitVec("c_1", 1)
    c_2 = z3.BitVec("c_2", 1)
    c_3 = z3.BitVec("c_3", 1)
    c_4 = z3.BitVec("c_4", 1)
    t_1 = z3.BitVec("t_1", 1)
    t_2 = z3.BitVec("t_2", 1)
    t_3 = z3.BitVec("t_3", 1)
    t_4 = z3.BitVec("t_4", 1)
    f_1 = z3.BitVec("f_1", 1)
    d2 = z3.BitVec("d2", 1)
    rand2 = z3.BitVec("rand2", 4)
    d3 = z3.BitVec("d3", 1)
    rand3 = z3.BitVec("rand3", 1)
    g = z3.Goal()
    g = add_bitmap(g, 1, d1)
    g = add_bitmap(g, 4, rand1)
    g = add_bitmap(g, 1, d2)
    g = add_bitmap(g, 4, rand2)
    g = add_bitmap(g, 1, c_1)
    g = add_bitmap(g, 1, c_2)
    g = add_bitmap(g, 1, c_3)
    g = add_bitmap(g, 1, c_4)
    g = add_bitmap(g, 1, t_1)
    g = add_bitmap(g, 1, t_2)
    g = add_bitmap(g, 1, t_3)
    g = add_bitmap(g, 1, t_4)
    g = add_bitmap(g, 1, f_1)
    g = add_bitmap(g, 1, d3)
    g = add_bitmap(g, 1, rand3)
    constraints = [
        d3 == z3.If(z3.ULT(rand3, 0b1), z3.BitVecVal(1, 1), z3.BitVecVal(0, 1)),
        z3.If(
            d3 == 1,
            z3.And(
                d1
                == z3.If(
                    z3.And(z3.ULT(rand1, int(16*p)), c_1 == 1),
                    z3.BitVecVal(1, 1),
                    z3.BitVecVal(0, 1),
                ),
                d2
                == z3.If(
                    z3.And(z3.ULT(rand2, int(16*p)), c_1 == 1),
                    z3.BitVecVal(1, 1),
                    z3.BitVecVal(0, 1),
                ),
                # f_1 == z3.If(z3.And(t_1 == 1, c_1 == 1), 1, 0),
                f_1 == z3.If(z3.And(t_1 == z3.BitVecVal(1, 1), c_1 == z3.BitVecVal(1, 1)), z3.BitVecVal(1, 1), z3.BitVecVal(0, 1)),

                c_2 == z3.If(z3.And(d1 == 1, t_1 == 1, c_1 == 1), 0, c_1),
                t_2
                == z3.If(
                    z3.And(d1 == 0, t_1 == 1, c_1 == 1), z3.BitVecVal(1, 1) - t_1, t_1
                ),
                c_3 == z3.If(z3.And(d2 == 1, t_1 == 0, c_1 == 1), 0, c_1),
                t_3
                == z3.If(
                    z3.And(d2 == 0, t_1 == 0, c_1 == 1), z3.BitVecVal(1, 1) - t_1, t_1
                ),
                c_4 == z3.If(z3.And(f_1 == z3.BitVecVal(1, 1), c_1 == z3.BitVecVal(1, 1)), c_2, c_3),

                t_4 == z3.If(z3.And(f_1 == 0, c_1 == 1), t_2, t_3),
            ),
            z3.And(c_4 == c_1, t_4 == t_1),
        ),
    ]
    g.add(*constraints)
    t = z3.Then("simplify", "bit-blast", "tseitin-cnf")
    subgoal = t(g)
    assert len(subgoal) == 1
    cnf_goal = subgoal[0]
    output_dimacs(cnf_goal, path)
    # optional
    check_status(constraints)


def MultiMode1(path, p, NUM_BITS):
    # --------------------------------------------------
    # Bit-vector declarations
    # --------------------------------------------------
    x_1 = z3.BitVec("x_1", NUM_BITS)   # input x
    x_2 = z3.BitVec("x_2", NUM_BITS)   # output x

    n_1 = z3.BitVec("n_1", NUM_BITS)   # input n
    n_2 = z3.BitVec("n_2", NUM_BITS)   # output n

    it_1 = z3.BitVec("it_1", NUM_BITS) # loop counter
    it_2 = z3.BitVec("it_2", NUM_BITS)

    d1 = z3.BitVec("d1", 1)            # Bernoulli(1/2)
    rand1 = z3.BitVec("rand1", 1)      # unbiased random bit

    # --------------------------------------------------
    # Goal and bitmap
    # --------------------------------------------------
    g = z3.Goal()

    g = add_bitmap(g, NUM_BITS, x_1)
    g = add_bitmap(g, NUM_BITS, x_2)
    g = add_bitmap(g, NUM_BITS, n_1)
    g = add_bitmap(g, NUM_BITS, n_2)
    g = add_bitmap(g, NUM_BITS, it_1)
    g = add_bitmap(g, NUM_BITS, it_2)
    g = add_bitmap(g, 1, d1)
    g = add_bitmap(g, 1, rand1)

    # --------------------------------------------------
    # Conditions
    # --------------------------------------------------
    loop_condition = z3.UGT(n_1, z3.BitVecVal(0, NUM_BITS))
    rand1_heads = rand1 == z3.BitVecVal(1, 1)

    # --------------------------------------------------
    # Bit index: iters % (NUM_BITS - 1)
    # --------------------------------------------------
    bit_index = z3.URem(
        it_1,
        z3.BitVecVal(NUM_BITS - 1, NUM_BITS)
    )

    bit_mask      = z3.BitVecVal(1, NUM_BITS) << bit_index
    bit_mask_p1   = z3.BitVecVal(1, NUM_BITS) << (
                        z3.URem(bit_index + 1,
                                z3.BitVecVal(NUM_BITS - 1, NUM_BITS))
                    )
    bit_mask_p2   = z3.BitVecVal(1, NUM_BITS) << (
                        z3.URem(bit_index + 2,
                                z3.BitVecVal(NUM_BITS - 1, NUM_BITS))
                    )

    bit_is_zero = (x_1 & bit_mask) == z3.BitVecVal(0, NUM_BITS)

    # --------------------------------------------------
    # Constraints
    # --------------------------------------------------
    constraints = [

        # Bernoulli(1/2)
        d1 == z3.If(
            rand1_heads,
            z3.BitVecVal(1, 1),
            z3.BitVecVal(0, 1)
        ),

        # -----------------------------
        # x update (nonlinear)
        # -----------------------------
        z3.Implies(
            z3.And(loop_condition, d1 == 1, bit_is_zero),
            x_2 == x_1 | bit_mask
        ),

        z3.Implies(
            z3.And(loop_condition, d1 == 1, z3.Not(bit_is_zero)),
            x_2 == (x_1 | bit_mask_p1 | bit_mask_p2)
        ),

        z3.Implies(
            z3.Or(d1 == 0, z3.Not(loop_condition)),
            x_2 == x_1
        ),

        # -----------------------------
        # n decrement
        # -----------------------------
        z3.Implies(
            loop_condition,
            n_2 == n_1 - z3.BitVecVal(1, NUM_BITS)
        ),
        z3.Implies(
            z3.Not(loop_condition),
            n_2 == n_1
        ),

        # -----------------------------
        # iters increment
        # -----------------------------
        z3.Implies(
            loop_condition,
            it_2 == it_1 + z3.BitVecVal(1, NUM_BITS)
        ),
        z3.Implies(
            z3.Not(loop_condition),
            it_2 == it_1
        )
    ]

    g.add(*constraints)

    # --------------------------------------------------
    # CNF generation (same as your pipeline)
    # --------------------------------------------------
    t = z3.Then("simplify", "bit-blast", "tseitin-cnf")
    subgoal = t(g)
    assert len(subgoal) == 1

    cnf_goal = subgoal[0]
    output_dimacs(cnf_goal, path)

    check_status(constraints)

def Unif1(path, p, NUM_BITS):

    # --------------------------------------------------
    # State variables (one-step unrolling)
    # --------------------------------------------------
    x_1  = z3.BitVec("x_1",  NUM_BITS)
    x_2  = z3.BitVec("x_2",  NUM_BITS)

    n_1  = z3.BitVec("n_1",  NUM_BITS)
    n_2  = z3.BitVec("n_2",  NUM_BITS)

    it_1 = z3.BitVec("it_1", NUM_BITS)
    it_2 = z3.BitVec("it_2", NUM_BITS)

    # --------------------------------------------------
    # Random inputs: one Bernoulli coin per bit
    # --------------------------------------------------
    rand = [
        z3.BitVec(f"rand_{i}", 1)
        for i in range(NUM_BITS - 4)
    ]

    d = [
        z3.BitVec(f"d_{i}", 1)
        for i in range(NUM_BITS - 4)
    ]

    # --------------------------------------------------
    # Goal + bitmaps (PRORP standard)
    # --------------------------------------------------
    g = z3.Goal()

    for v in [x_1, x_2, n_1, n_2, it_1, it_2]:
        g = add_bitmap(g, NUM_BITS, v)

    for r in rand:
        g = add_bitmap(g, 1, r)

    for di in d:
        g = add_bitmap(g, 1, di)

    # --------------------------------------------------
    # Loop guard
    # --------------------------------------------------
    loop_condition = z3.UGT(n_1, z3.BitVecVal(0, NUM_BITS))

    # --------------------------------------------------
    # rand_heads guards
    # --------------------------------------------------
    rand_heads = [
        rand[i] == z3.BitVecVal(1, 1)
        for i in range(NUM_BITS - 4)
    ]

    # --------------------------------------------------
    # Flip mask construction
    # --------------------------------------------------
    flip_mask = z3.BitVecVal(0, NUM_BITS)

    for i in range(NUM_BITS - 1):
        flip_mask = flip_mask | z3.If(
            d[i] == z3.BitVecVal(1, 1),
            z3.BitVecVal(1 << i, NUM_BITS),
            z3.BitVecVal(0, NUM_BITS)
        )

    # --------------------------------------------------
    # Constraints
    # --------------------------------------------------
    constraints = []

    # Bernoulli choices
    for i in range(NUM_BITS - 4):
        constraints.append(
            d[i] == z3.If(
                rand_heads[i],
                z3.BitVecVal(1, 1),
                z3.BitVecVal(0, 1)
            )
        )

    # x update (all flips applied at once)
    constraints += [
        z3.Implies(
            loop_condition,
            x_2 == x_1 ^ flip_mask
        ),

        z3.Implies(
            z3.Not(loop_condition),
            x_2 == x_1
        ),

        # n update
        z3.Implies(
            loop_condition,
            n_2 == n_1 - z3.BitVecVal(1, NUM_BITS)
        ),

        z3.Implies(
            z3.Not(loop_condition),
            n_2 == n_1
        ),

        # iteration counter
        z3.Implies(
            loop_condition,
            it_2 == it_1 + z3.BitVecVal(1, NUM_BITS)
        ),

        z3.Implies(
            z3.Not(loop_condition),
            it_2 == it_1
        )
    ]

    g.add(*constraints)

    # --------------------------------------------------
    # CNF generation
    # --------------------------------------------------
    t = z3.Then("simplify", "bit-blast", "tseitin-cnf")
    subgoal = t(g)
    assert len(subgoal) == 1

    cnf_goal = subgoal[0]
    output_dimacs(cnf_goal, path)
    check_status(constraints)


def Unif2(path, p, NUM_BITS):
    from functools import reduce
    import operator

    # --------------------------------------------------
    # Parameters
    # --------------------------------------------------
    LOW = NUM_BITS - 32
    p_thresh = int(16 * p)

    # --------------------------------------------------
    # Bit-vector declarations
    # --------------------------------------------------
    x_1 = z3.BitVec("x_1", NUM_BITS)   # input x
    x_2 = z3.BitVec("x_2", NUM_BITS)   # output x

    base = z3.BitVec("base", NUM_BITS)
    y    = z3.BitVec("y", NUM_BITS)

    # PRORP iteration coin
    flip_1    = z3.BitVec("flip_1", 1)
    rand_flip = z3.BitVec("rand_flip", 4)

    # Randomness for y bits
    rand_y = [z3.BitVec(f"rand_y_{i}", 4) for i in range(LOW)]

    # --------------------------------------------------
    # Goal and bitmap
    # --------------------------------------------------
    g = z3.Goal()

    for v in [x_1, x_2, base, y]:
        g = add_bitmap(g, NUM_BITS, v)

    g = add_bitmap(g, 1, flip_1)
    g = add_bitmap(g, 4, rand_flip)

    for rv in rand_y:
        g = add_bitmap(g, 4, rv)

    # --------------------------------------------------
    # Constraints
    # --------------------------------------------------
    constraints = []

    # PRORP iteration coin
    constraints.append(
        flip_1 ==
        z3.If(
            z3.ULT(rand_flip, z3.BitVecVal(p_thresh, 4)),
            z3.BitVecVal(1, 1),
            z3.BitVecVal(0, 1)
        )
    )

    # Snapshot base value
    constraints.append(base == x_1)

    # --------------------------------------------------
    # Construct y bitwise (FUNCTIONAL, CORRECT)
    # --------------------------------------------------
    y_parts = []

    for i in range(LOW):
        bitmask = z3.BitVecVal(1 << i, NUM_BITS)

        y_parts.append(
            z3.If(
                z3.And(
                    flip_1 == z3.BitVecVal(1, 1),
                    z3.ULT(rand_y[i], z3.BitVecVal(p_thresh, 4))
                ),
                bitmask,
                z3.BitVecVal(0, NUM_BITS)
            )
        )

    # MSB always zero
    y_parts.append(z3.BitVecVal(0, NUM_BITS))

    # Bitwise OR of all parts
    y_expr = reduce(operator.or_, y_parts, z3.BitVecVal(0, NUM_BITS))
    constraints.append(y == y_expr)

    # --------------------------------------------------
    # x update (OVERWRITE semantics)
    # --------------------------------------------------
    constraints.append(
        z3.Implies(
            flip_1 == z3.BitVecVal(1, 1),
            x_2 == base + y
        )
    )

    constraints.append(
        z3.Implies(
            flip_1 == z3.BitVecVal(0, 1),
            x_2 == x_1
        )
    )

    # --------------------------------------------------
    # Add constraints
    # --------------------------------------------------
    g.add(*constraints)

    # --------------------------------------------------
    # CNF generation (PRORP pipeline)
    # --------------------------------------------------
    t = z3.Then("simplify", "bit-blast", "tseitin-cnf")
    subgoal = t(g)
    assert len(subgoal) == 1

    cnf_goal = subgoal[0]
    output_dimacs(cnf_goal, path)

    check_status(constraints)











def Unif3(path, p, NUM_BITS):

    # --------------------------------------------------
    # Bit-vector declarations
    # --------------------------------------------------
    x_1  = z3.BitVec("x_1",  NUM_BITS)
    x_2  = z3.BitVec("x_2",  NUM_BITS)

    n_1  = z3.BitVec("n_1",  NUM_BITS)
    n_2  = z3.BitVec("n_2",  NUM_BITS)

    it_1 = z3.BitVec("it_1", NUM_BITS)
    it_2 = z3.BitVec("it_2", NUM_BITS)

    # PRORP randomness
    coin = z3.BitVec("coin", 1)      # fair coin
    rand = z3.BitVec("rand", 1)      # Bernoulli(1/2)

    # --------------------------------------------------
    # Goal and bitmaps
    # --------------------------------------------------
    g = z3.Goal()
    for v in [x_1, x_2, n_1, n_2, it_1, it_2]:
        g = add_bitmap(g, NUM_BITS, v)

    g = add_bitmap(g, 1, coin)
    g = add_bitmap(g, 1, rand)

    # --------------------------------------------------
    # Execution condition
    # --------------------------------------------------
    exec_cond = z3.And(
        coin == z3.BitVecVal(1, 1),
        z3.UGT(n_1, z3.BitVecVal(0, NUM_BITS))
    )

    # --------------------------------------------------
    # Rotating bit index
    # --------------------------------------------------
    bit = z3.URem(it_1, z3.BitVecVal(NUM_BITS, NUM_BITS))
    bit_mask = z3.BitVecVal(1, NUM_BITS) << bit

    bit_p1 = z3.BitVecVal(1, NUM_BITS) << z3.URem(bit + 1, z3.BitVecVal(NUM_BITS, NUM_BITS))
    bit_p2 = z3.BitVecVal(1, NUM_BITS) << z3.URem(bit + 2, z3.BitVecVal(NUM_BITS, NUM_BITS))

    bit_is_zero = (x_1 & bit_mask) == z3.BitVecVal(0, NUM_BITS)

    # --------------------------------------------------
    # Affine constraint indices
    # --------------------------------------------------
    i1 = 0
    i2 = NUM_BITS // 4
    i3 = NUM_BITS // 2

    j1 = 1
    j2 = NUM_BITS // 3

    # --------------------------------------------------
    # Parity computations
    # --------------------------------------------------
    p1 = (
        z3.Extract(i1, i1, x_1) ^
        z3.Extract(i2, i2, x_1) ^
        z3.Extract(i3, i3, x_1)
    )

    p2 = (
        z3.Extract(j1, j1, x_1) ^
        z3.Extract(j2, j2, x_1)
    )

    # --------------------------------------------------
    # Hash-based mixing
    # --------------------------------------------------
    # --------------------------------------------------
    # Hash-based mixing (FIXED)
    # --------------------------------------------------
    h = (
        z3.Extract(0, 0, z3.LShR(x_1, 5 % NUM_BITS)) ^
        z3.Extract(0, 0, z3.LShR(x_1, 12 % NUM_BITS)) ^
        z3.Extract(0, 0, z3.LShR(x_1, 19 % NUM_BITS))
    )  # h : BitVec(1)

    h_ext = z3.ZeroExt(NUM_BITS - 1, h)  # BitVec(NUM_BITS)

    hash_index = z3.URem(
        h_ext + z3.BitVecVal(3, NUM_BITS),
        z3.BitVecVal(NUM_BITS, NUM_BITS)
    )

    hash_mask = z3.BitVecVal(1, NUM_BITS) << hash_index



    # --------------------------------------------------
    # x after noisy reinforcement
    # --------------------------------------------------
    x_noise = z3.If(
        bit_is_zero,
        x_1 | bit_mask,
        x_1 | bit_p1 | bit_p2
    )

    # --------------------------------------------------
    # x after affine enforcement
    # --------------------------------------------------
    x_affine_1 = z3.If(
        p1 == z3.BitVecVal(1, 1),
        x_noise ^ z3.BitVecVal(1 << i1, NUM_BITS),
        x_noise
    )

    x_affine_2 = z3.If(
        p2 == z3.BitVecVal(0, 1),
        x_affine_1 ^ z3.BitVecVal(1 << j1, NUM_BITS),
        x_affine_1
    )

    # --------------------------------------------------
    # x after hash mixing
    # --------------------------------------------------
    x_final = x_affine_2 ^ hash_mask

    # --------------------------------------------------
    # Constraints
    # --------------------------------------------------
    constraints = [

        # Noisy + structured update
        z3.Implies(
            z3.And(exec_cond, rand == z3.BitVecVal(1, 1)),
            x_2 == x_final
        ),

        # No-op when rand == 0
        z3.Implies(
            z3.And(exec_cond, rand == z3.BitVecVal(0, 1)),
            x_2 == x_1
        ),

        # Stutter
        z3.Implies(
            z3.Not(exec_cond),
            x_2 == x_1
        ),

        # n update
        z3.Implies(exec_cond, n_2 == n_1 - 1),
        z3.Implies(z3.Not(exec_cond), n_2 == n_1),

        # iters update
        z3.Implies(exec_cond, it_2 == it_1 + 1),
        z3.Implies(z3.Not(exec_cond), it_2 == it_1),
    ]

    g.add(*constraints)

    # --------------------------------------------------
    # CNF generation
    # --------------------------------------------------
    t = z3.Then("simplify", "bit-blast", "tseitin-cnf")
    subgoal = t(g)
    assert len(subgoal) == 1

    output_dimacs(subgoal[0], path)
    check_status(constraints)



def Unif4(path, p, NUM_BITS):

    import z3

    # compute lengths and starts
    lengths = [1] + [(2**j - j - 1) for j in range(1, NUM_BITS)]
    a_vals  = [0] + [(2**j + j + 1) for j in range(1, NUM_BITS)]

    x_1 = z3.BitVec("x_1", NUM_BITS)
    x_2 = z3.BitVec("x_2", NUM_BITS)
    flip_1 = z3.BitVec("flip_1", 1)
    flip_2 = z3.BitVec("flip_2", 1)
    member_1 = z3.BitVec("member_1", 1)
    member_2 = z3.BitVec("member_2", 1)

    coin = z3.BitVec("coin", 1)   # PRORP iteration coin
    j    = z3.BitVec("j", NUM_BITS)
    offset = z3.BitVec("offset", NUM_BITS)
    y    = z3.BitVec("y", NUM_BITS)

    g = z3.Goal()

    # bitmaps
    for v in [x_1,x_2,j,offset,y,coin,flip_1,flip_2,member_1,member_2]:
        if v.size() > 1:
            g = add_bitmap(g, NUM_BITS, v)
        else:
            g = add_bitmap(g, 1, v)

    constraints = []

    # CASE 1: flip_1 == 0 -> stutter
    constraints.append(
        z3.Implies(flip_1 == 0,
                   z3.And(
                       x_2 == x_1,
                       flip_2 == z3.BitVecVal(0,1),
                       member_2 == z3.BitVecVal(0,1)
                   ))
    )

    # CASE 2: flip_1 == 1 AND coin == 0 -> stop unrolling
    stop = z3.And(flip_1 == 1, coin == 0)
    constraints.append(
        z3.Implies(stop,
                   z3.And(
                       x_2 == x_1,
                       flip_2 == z3.BitVecVal(1,1),
                       member_2 == z3.BitVecVal(0,1)
                   ))
    )

    # CASE 3: flip_1 == 1 AND coin == 1 -> perform update
    run = z3.And(flip_1 == 1, coin == 1)

    Sconds = []

    for j_idx in range(NUM_BITS):
        lj = lengths[j_idx]
        aj = a_vals[j_idx]

        if lj <= 0:
            # skip empty segments (they occur for small j)
            continue

        if j_idx == 0:
            Sconds.append(
                z3.And(j == z3.BitVecVal(0,NUM_BITS),
                       y == z3.BitVecVal(0,NUM_BITS))
            )
        else:
            Sconds.append(
                z3.And(
                    j == z3.BitVecVal(j_idx,NUM_BITS),
                    offset >= z3.BitVecVal(0,NUM_BITS),
                    offset <  z3.BitVecVal(lj,NUM_BITS),
                    y == z3.BitVecVal(aj,NUM_BITS) + offset
                )
            )

    S_formula = z3.Or(*Sconds)

    constraints.append(z3.Implies(run, S_formula))
    constraints.append(z3.Implies(run, x_2 == x_1 + y))
    constraints.append(z3.Implies(run, flip_2 == z3.BitVecVal(1,1)))
    constraints.append(z3.Implies(run, member_2 == z3.BitVecVal(1,1)))

    g.add(*constraints)

    # bit-blast + CNF
    t = z3.Then("simplify","bit-blast","tseitin-cnf")
    cnf_goal = t(g)[0]
    output_dimacs(cnf_goal, path)









    



if __name__ == "__main__":
    import sys
    if len(sys.argv) != 4:
        print("Usage: python EXIST_progs.py <ProgramName> <NUM_BITS> <probability>")
        sys.exit(1)

    progname = sys.argv[1]
    NUM_BITS = int(sys.argv[2])
    p = float(sys.argv[3])
    formula_path = os.path.join(CURRENT_PATH, "progformula/", progname)
    if progname == "Temp":
        Temp(formula_path, p, NUM_BITS)
    elif progname == "Fair":
        Fair(formula_path, p, NUM_BITS)
    elif progname == "Sum0":
        Sum0(formula_path, p, NUM_BITS)
    elif progname == "ModSum":
        ModSum(formula_path, p, NUM_BITS)
    elif progname == "LinExp":
        LinExp(formula_path, p, NUM_BITS)
    elif progname == "BigGeo0":
        BigGeo0(formula_path, p, NUM_BITS)
    elif progname == "BigGeo1":
        BigGeo1(formula_path, p, NUM_BITS)
    elif progname == "BigGeo2":
        BigGeo2(formula_path, p, NUM_BITS)
    elif progname == "Geo0":
        Geo0(formula_path, p, NUM_BITS)
    elif progname == "GeoAr":
        GeoAr(formula_path, p, NUM_BITS)
    elif progname == "Detm":
        Detm(formula_path, p, NUM_BITS)
    elif progname == "Bin0":
        Bin0(formula_path, p, NUM_BITS)
    elif progname == "Bin1":
        Bin1(formula_path, p, NUM_BITS)
    elif progname == "BinMod":
        BinMod(formula_path, p, NUM_BITS)
    elif progname == "Bin2":
        Bin2(formula_path, p, NUM_BITS)
    elif progname == "BiasDir":
        BiasDir(formula_path, p, NUM_BITS)
    elif progname == "DepRV":
        DepRV(formula_path, p, NUM_BITS)
    elif progname == "RevBin":
        RevBin(formula_path, p, NUM_BITS)
    elif progname == "Prinsys":
        Prinsys(formula_path, p, NUM_BITS)
    elif progname == "Mart":
        Mart(formula_path, p, NUM_BITS)
    elif progname == "Duel":
        Duel(formula_path, p, NUM_BITS)
    elif progname == "MultiMode1":
        MultiMode1(formula_path, p, NUM_BITS)
    elif progname == "Unif1":
        Unif1(formula_path, p, NUM_BITS)
    elif progname == "Unif2":
        Unif2(formula_path, p, NUM_BITS)
    elif progname == "Unif4":
        Unif4(formula_path, p, NUM_BITS)
    # elif progname == "ModSum":
    #     ModSum(formula_path, p, NUM_BITS)
    else:
        print(f"Unknown function: {progname}")
