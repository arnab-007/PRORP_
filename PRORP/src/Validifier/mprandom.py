from random import *
import decimal
from decimal import Decimal, Context, getcontext, setcontext, MAX_PREC, MAX_EMAX, MIN_EMIN
from operator import index as _index
from math import log2 as _log2, log10 as _log10, fabs as _fabs, lgamma as _lgamma, log as _log, floor as _floor
from math import sqrt as _sqrt, exp as _exp
import gmpy2 as gp
import time

#----------------- Arbitrary Precision Random number generator -----------


def mpuniform(precision=30):
    """ multiprecision uniform number
    """
    precision2 = int(_log2(10 ** precision))
    univariate = getrandbits(precision2)
    getcontext().prec = precision
    univariate = univariate / Decimal(10**precision)
    return univariate

def mpexpovariate(precision=30):
    """ Improved Von Neumann's algorithm by Charles F. F. Karney 
    """
    getcontext().prec = precision
    l = 0
    while True:
        x = mpuniform(precision)
        if x > 0.5:
            l += 1
            continue 
        n = 0; u = x
        while u > (u := mpuniform(precision)):
            n += 1
        if n % 2 == 1:
            l += 1
            continue
        else:
            return Decimal(0.5 * l) + x

def _half_exp_bernoulli(precision = 30):
    """ Exact Bernoulli variate with parameter 1 / sqrt(e)
    """
    if not (u1 := mpuniform(precision)) < 0.5: return True
    while True:
        if not (u2 := mpuniform(precision)) > u1: return False
        if not (u1 := mpuniform(precision)) > u2: return True 

def _general_exp_variate(x, param, precision = 30):
    """generalization of Von Neumann Trick
    """
    y = x; n= 0
    while True:
        z = mpuniform(precision)
        r = mpuniform(precision)
        if z > y or r > param:
            break
        y = z
        n += 1
    return (n % 2 == 0)

    # if not (u1 := mpuniform()) < x: return True
    # while True:
    #     if not (u2 := mpuniform()) > u1: return False
    #     if not (u1 := mpuniform()) > u2: return True 



def mpnormalvariate(mu=0.0, sigma=1.0, precision=30):
    """multi precision Normal distribution.

        uses Charles F. F. Karney method
        ref: https://arxiv.org/pdf/1303.6257.pdf
    """
    getcontext().prec = precision
    while True:
        k = 0
        # N1
        while not _half_exp_bernoulli(): pass
        while _half_exp_bernoulli():
            k += 1
        # N2
        check = True
        for i in range(k*(k-1)): check *= _half_exp_bernoulli()
        if not check: continue
        #N3
        x = mpuniform(precision = precision)
        #N4
        check = True
        for i in range(k+1): check *= _general_exp_variate(x, (2*k+x)/(2*k+2), precision)
        if check: break
    #N5
    x
    y = Decimal(k) + Decimal(x)
    #N6
    if random() > 0.5 : sgn = 1
    else: sgn = -1
    return Decimal(sgn) * y 

# def _logfact(k):
#     """logfactorial
#     """
#     a = [8.333333333333333e-02, -2.777777777777778e-03,
#         7.936507936507937e-04, -5.952380952380952e-04,
#         8.417508417508418e-04, -1.917526917526918e-03,
#         6.410256410256410e-03, -2.955065359477124e-02,
#         1.796443723688307e-01, -1.39243221690590e+00]
    
#     if k == 1 or k == 2 : 
#         return 0
#     elif k < 7 :
#         n = 7 -k
#     else:
#         n = 0
#     k0 = k + n
#     k2 = (1 / k0) ** 2
#     lg2pi = 1.8378770664093453e+00
#     gl0 = a[9]
#     for i in range(9, 0, -1):
#         gl0 *= k2
#         gl0 += a[i]
#     gl = gl0 / k0 + 0.5 * lg2pi + (k0 - 0.5) * _log(k0) - k0
#     if k < 7:
#         gl -= _log(k0 - 1)
#         k0  -= 1
#     return gl

def poissonvariate(lambd = 10):
    """PTRS
    """
    if lambd < 10 :
        exlam = _exp(-lambd)
        k = 0
        prod = 1
        while True:
            U = random()
            prod *= U
            if prod > exlam:
                k += 1
            else:
                return k
    elif lambd >= 10 :
        lnlam = _log(lambd)
        b = 0.931 + 2.53 * _sqrt(lambd)
        a = - 0.059 + 0.02483 * b
        vr = 0.9277 - 3.6224 / (b - 2)
        invalpha = 1.1239 + 1.1328 / (b - 3.4)
        
        while True:
            U, V = random() - 0.5, random()
            us = 0.5 - _fabs(U)
            k = _floor(( 2 * a / us + b) * U + lambd + 0.43)
            if (us >= 0.07) and (V <= vr):
                return k
            if (k <= 0) or (us < 0.013 and V > us):
                continue
            if (_log(V) + _log(invalpha) - _log(a / us**2 + b)) <= (-lambd + k * lnlam - _lgamma(k)):
                return k 
    
def mpbinomial(n = 10, p = 0.5, precision = 30, err = 0.01):
    """multi precision Binomial distribution
       it takes a parameter error as input for error allowance
    """
    start = time.time()
    precision = 4000 #max(precision, int(_log10(n)))
    context = Context(prec=precision)
    reverse = False
    if p == 1:
        return n
    elif p == 0:
        return 0
    if p > 0.5:
        p = 1 - p
        reverse = True
    p = context.create_decimal(str(p))
    err = context.create_decimal(str(err))
    if n > (1-2*p)**2 / (err**2 * p * (1-p)):
#        print("normal")
        z = mpnormalvariate(precision = precision)
        print("time taken", time.time() - start)
        if not reverse:
            return int(context.fma(context.sqrt(n*p*(1-p)), z, n * p))
        else:
            return n - int(context.fma(context.sqrt(n*p*(1-p)), z, n * p))
    if n < err / (2 * p**2):
#        print("poisson")
        z = poissonvariate(lambd = float(n * p))
        print("time taken", time.time() - start)
        if not reverse:
            return z
        else:
            return n - z
    else:
#        print("vanilla")
        z = binomialvariate(n = n, p = float(p))
        print("time taken", time.time() - start)
        if not reverse:
            return z
        else:
            return n - z
        
def mppoisson(lambd = 100, precision = 30, err = 0.01):
    """multi precision Poisson distribution
       it takes a parameter error as input for error allowance
    """
    precision = max(precision, int(_log10(lambd)))
    context = Context(prec=precision)
    err = context.create_decimal(str(err))
    if lambd > 12 / (err**2):
        z = mpnormalvariate(precision = precision)
        return int(context.fma(context.sqrt(lambd), z, lambd))
    else:
        z = poissonvariate(lambd=lambd)
        return z            
            
def binomialvariate(n=1, p=0.5):
    """Binomial random variable.

    Gives the number of successes for *n* independent trials
    with the probability of success in each trial being *p*:

        sum(random() < p for i in range(n))

    Returns an integer in the range:   0 <= X <= n

    """
    # Error check inputs and handle edge cases
    if n < 0:
        raise ValueError("n must be non-negative")
    if p <= 0.0 or p >= 1.0:
        if p == 0.0:
            return 0
        if p == 1.0:
            return n
        raise ValueError("p must be in the range 0.0 <= p <= 1.0")

    # Fast path for a common case
    if n == 1:
        return _index(random() < p)

    # Exploit symmetry to establish:  p <= 0.5
    if p > 0.5:
        return n - binomialvariate(n, 1.0 - p)

    if n * p < 10.0:
        # BG: Geometric method by Devroye with running time of O(np).
        # https://dl.acm.org/doi/pdf/10.1145/42372.42381
        x = y = 0
        c = _log2(1.0 - p)
        if not c:
            return x
        while True:
            y += _floor(_log2(random()) / c) + 1
            if y > n:
                return x
            x += 1

    # BTRS: Transformed rejection with squeeze method by Wolfgang Hörmann
    # https://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.47.8407&rep=rep1&type=pdf
    assert n*p >= 10.0 and p <= 0.5
    setup_complete = False

    spq = Decimal(_sqrt(n * p * (1.0 - p)))  # Standard deviation of the distribution
    b = Decimal('1.15') + Decimal('2.53') * spq
    a = Decimal('-0.0873') + Decimal('0.0248') * b + Decimal(0.01 * p)
    c = Decimal(n * p + 0.5)
    vr = Decimal('0.92') - Decimal('4.2') / b

    context = decimal.Context(prec=100)
    while True:

        u = mpuniform() #random()
        u -= Decimal('0.5')
        us = Decimal('0.5') - Decimal(_fabs(u))
        k = _floor((Decimal('2.0') * a / us + b) * u + c)
        if k < 0 or k > n:
            continue

        # The early-out "squeeze" test substantially reduces
        # the number of acceptance condition evaluations.
        v = mpuniform()
        if us >= 0.07 and v <= vr:
            # print("before")
            return k

        # Acceptance-rejection test.
        # Note, the original paper errorneously omits the call to log(v)
        # when comparing to the log of the rescaled binomial distribution.
        if not setup_complete:
            alpha = (Decimal(2.83) + Decimal(5.1) / b) * spq
            lpq = Decimal(_log(p / (1.0 - p)))
            m = _floor((n + 1) * p)         # Mode of the distribution
            h = Decimal(_lgamma(m + 1) + _lgamma(n - m + 1))
            setup_complete = True           # Only needs to be done once
        v *= alpha / (a / (us * us) + b)
        if _log(v) <= h - Decimal(_lgamma(k + 1) - _lgamma(n - k + 1)) + (k - m) * lpq:
            # print("after")
            return k

def vanbinomialvariate(n=1, p=0.5):
        """Binomial random variable.

        Gives the number of successes for *n* independent trials
        with the probability of success in each trial being *p*:

            sum(random() < p for i in range(n))

        Returns an integer in the range:   0 <= X <= n

        """
        start = time.time()
        gp.set_context(gp.context(precision = 3000))
        p, n = gp.mpfr(str(p)), gp.mpfr(str(n))
        
        # Error check inputs and handle edge cases
        if n < 0:
            raise ValueError("n must be non-negative")
        if p <= 0.0 or p >= 1.0:
            if p == 0.0:
                return 0
            if p == 1.0:
                return n
            raise ValueError("p must be in the range 0.0 <= p <= 1.0")

        # Exploit symmetry to establish:  p <= 0.5
        if p > 0.5:
            return n - vanbinomialvariate(n, 1.0 - p)

        if n * p < 10.0:
            # BG: Geometric method by Devroye with running time of O(np).
            # https://dl.acm.org/doi/pdf/10.1145/42372.42381
            x = y = 0
            c = gp.log2(1 - p)
            f = open("file.txt", "a")
            f.write(str(n*p)+ " n: " + str(n) + " p: " + str(p) + "\n")
            if not c:
                return x
            while True: 
                y += int(gp.mpfr(str(_log2(random()))) / c) + 1
                if y > n:
                    f.write("y: "+ str(y) + "x: "+ str(x) + "\n")
                    return x
                x += 1

        # BTRS: Transformed rejection with squeeze method by Wolfgang Hörmann
        # https://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.47.8407&rep=rep1&type=pdf
        assert n*p >= 10.0 and p <= 0.5
        setup_complete = False

        spq = gp.sqrt(gp.mul(gp.mul(n, p), (1 - p)))  # Standard deviation of the distribution
        b = gp.add(gp.mpfr('1.15'),  gp.mul(gp.mpfr('2.53'), spq))
        a = gp.add(gp.add(gp.mpfr('-0.0873'), gp.mul(gp.mpfr('0.0248'), b)), gp.mul(gp.mpfr('0.01'), p))
        c = gp.add(gp.mul(n, p), gp.mpfr('0.5'))
        vr = gp.sub(gp.mpfr('0.92'), gp.div(gp.mpfr('4.2'), b))


        while True:

            u = random()
            u -= 0.5
            us = 0.5 - _fabs(u)
            k = int(gp.mul(gp.add(gp.div(gp.mul(2, a), gp.mpfr(str(us))), b), gp.mpfr(str(u))) + c)
            #    print(f"k:{k}")
            if k < 0 or k > n:
                continue

            # The early-out "squeeze" test substantially reduces
            # the number of acceptance condition evaluations.
            v = gp.mpfr(random())
            if us >= 0.07 and v <= vr:
                print("vanbinomialvariate time taken : ", time.time() - start)
                return k
            
            #    print(f"u : {u}, us : {us}")

            # Acceptance-rejection test.
            # Note, the original paper errorneously omits the call to log(v)
            # when comparing to the log of the rescaled binomial distribution.
            if not setup_complete:
                alpha = gp.mul(gp.add(gp.mpfr('2.83'), gp.div(gp.mpfr('5.1'), b)), gp.mpfr(spq))
                ratio = p / (1 - p)
                lpq = gp.log2(gp.mpfr(str(ratio))) * gp.mpfr(_log(2)) 
                m = _floor((n + 1) * p)         # Mode of the distribution
                h1 = gp.mpfr(str(m + 1)); h2 = gp.mpfr(str(n - m + 1))
                h = gp.lgamma(h1)[0] + gp.lgamma(h2)[0]
                setup_complete = True           # Only needs to be done once
            v *= alpha / (a / (us * us) + b)
            logv = gp.log2(gp.mpfr(str(v))) * gp.mpfr(_log(2))       # mpfr log
            #    a1 = v.log10() * Decimal(_log(10))     # decimal log
            h_log = gp.sub(h, gp.add(gp.lgamma(gp.mpfr(str(k + 1)))[0], gp.lgamma(gp.mpfr(str(n - k + 1)))[0]))
            #    if _log(v) <= h - _lgamma(k + 1) - _lgamma(n - k + 1) + (k - m) * lpq:
            if logv <= h_log + (k - m) * lpq:
                print("vanbinomialvariate time taken : ", time.time() - start)
                return k


def StirlBinom(n=1, p=0.5):
        """Binomial random variable.

        Gives the number of successes for *n* independent trials
        with the probability of success in each trial being *p*:

            sum(random() < p for i in range(n))

        Returns an integer in the range:   0 <= X <= n

        """
        start = time.time()
        gp.set_context(gp.context(precision = 3000))
        p, n = gp.mpfr(str(p)), gp.mpfr(str(n))
        
        # Error check inputs and handle edge cases
        if n < 0:
            raise ValueError("n must be non-negative")
        if p <= 0.0 or p >= 1.0:
            if p == 0.0:
                return 0
            if p == 1.0:
                return n
            raise ValueError("p must be in the range 0.0 <= p <= 1.0")

        # Exploit symmetry to establish:  p <= 0.5
        if p > 0.5:
            return n - vanbinomialvariate(n, 1.0 - p)
        
        # BTRS: Transformed rejection with squeeze method by Wolfgang Hörmann
        # https://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.47.8407&rep=rep1&type=pdf
        #assert n*p >= 10.0 and p <= 0.5
        setup_complete = False

        spq = gp.sqrt(gp.mul(gp.mul(n, p), (1 - p)))  # Standard deviation of the distribution
        b = gp.add(gp.mpfr('1.15'),  gp.mul(gp.mpfr('2.53'), spq))
        a = gp.add(gp.add(gp.mpfr('-0.0873'), gp.mul(gp.mpfr('0.0248'), b)), gp.mul(gp.mpfr('0.01'), p))
        c = gp.add(gp.mul(n, p), gp.mpfr('0.5'))
        vr = gp.sub(gp.mpfr('0.92'), gp.div(gp.mpfr('4.2'), b))


        while True:

            u = random()
            u -= 0.5
            us = 0.5 - _fabs(u)
            k = int(gp.mul(gp.add(gp.div(gp.mul(2, a), gp.mpfr(str(us))), b), gp.mpfr(str(u))) + c)
            #    print(f"k:{k}")
            if k < 0 or k > n:
                continue

            # The early-out "squeeze" test substantially reduces
            # the number of acceptance condition evaluations.
            v = gp.mpfr(random())
            if us >= 0.07 and v <= vr:
                print("StirlBinom time taken : ", time.time() - start)
                return k
            
            #    print(f"u : {u}, us : {us}")

            # Acceptance-rejection test.
            # Note, the original paper errorneously omits the call to log(v)
            # when comparing to the log of the rescaled binomial distribution.
            if not setup_complete:
                alpha = gp.mul(gp.add(gp.mpfr('2.83'), gp.div(gp.mpfr('5.1'), b)), gp.mpfr(spq))
                ratio = p / (1 - p)
                lpq = gp.log2(gp.mpfr(str(ratio))) * gp.mpfr(_log(2)) 
                m = _floor((n + 1) * p)         # Mode of the distribution
                h1 = gp.mpfr(str(m + 1)); h2 = gp.mpfr(str(n - m + 1))
                h = gp.log(gp.sqrt(2 * gp.const_pi())) + gp.mul((h1 + 1/2),gp.log(h1)) - gp.mpfr(h1) + gp.log(gp.sqrt(2 * gp.const_pi())) + gp.mul((h2 + 1/2),gp.log(h2)) - gp.mpfr(h2)
                #h = gp.lgamma(h1)[0] + gp.lgamma(h2)[0]
                setup_complete = True           # Only needs to be done once
            v *= alpha / (a / (us * us) + b)
            logv = gp.log2(gp.mpfr(str(v))) * gp.mpfr(_log(2))       # mpfr log
            strilk = gp.log(gp.sqrt(2 * gp.const_pi())) + gp.mul((gp.mpfr(str(k)) + 1/2),gp.log(gp.mpfr(str(k)))) - gp.mpfr(gp.mpfr(str(k)))
            strilnk1 = gp.log(gp.sqrt(2 * gp.const_pi())) + gp.mul((gp.mpfr(str(n)) - gp.mpfr(str(k)) + 3/2),gp.log(gp.mpfr(str(n)) - gp.mpfr(str(k)) + 1)) - gp.mpfr(gp.mpfr(str(n)) - gp.mpfr(str(k)) + 1)
            h_log = gp.sub(h, gp.add(strilk, strilnk1))
            # h_log = gp.sub(h, gp.add(gp.lgamma(gp.mpfr(str(k + 1)))[0], gp.lgamma(gp.mpfr(str(n - k + 1)))[0]))
            if logv <= h_log + (k - m) * lpq:
                print("StirlBinom time taken : ", time.time() - start)
                return k


def BernBinom(n=1, p=0.5):
        """Binomial random variable.

        Gives the number of successes for *n* independent trials
        with the probability of success in each trial being *p*:

            sum(random() < p for i in range(n))

        Returns an integer in the range:   0 <= X <= n

        """
        start = time.time()
        u = gp.mpfr(str(mpuniform()))
        if u <= gp.mul(gp.mpfr(str(n)), gp.mpfr(str(p))):
            print("BernBinom time taken : ", time.time() - start)
            return 1
        else:
            print("BernBinom time taken : ", time.time() - start)
            return 0


if __name__ == '__main__':
    context = Context(prec=3000)
    setcontext(context)
    p = Decimal(1)
    for i in range(50):
        p /= 2
    N = Decimal(2**200)
    N = Decimal('316912650057057350374175801344')
    p = Decimal('2.524354896707237777317531408904915934954260592348873615264892578125e-29')
    print(N,p)
    print(vanbinomialvariate(N,p))
    # print(mpbinomial(N,p))
    print(BernBinom(N,p))
    print(StirlBinom(N,p))