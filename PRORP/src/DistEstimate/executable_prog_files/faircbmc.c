#include <stdint.h>
#include <assert.h>

// Nondeterministic function stubs provided by CBMC
extern _Bool __VERIFIER_nondet_bool(void);
extern float __VERIFIER_nondet_float(void);

typedef struct {
    uint8_t count;
    _Bool ca;
    _Bool cb;
} Result;

Result Fair(uint8_t count, _Bool ca, _Bool cb, float p1, float p2)
{
    if (!ca && !cb)
    {
        // Simulate Bernoulli sampling
        ca = __VERIFIER_nondet_bool(); // Simulate: ca = bernoulli(p1)
        if (ca)
        {
            count++;
        }

        cb = __VERIFIER_nondet_bool(); // Simulate: cb = bernoulli(p2)
        if (cb)
        {
            count++;
        }
    }

    Result result = {count, ca, cb};
    return result;
}

int main()
{
    // Inputs as nondet
    uint8_t count = (__VERIFIER_nondet_bool() << 3) |
                    (__VERIFIER_nondet_bool() << 2) |
                    (__VERIFIER_nondet_bool() << 1) |
                    (__VERIFIER_nondet_bool() << 0);

    _Bool ca = __VERIFIER_nondet_bool();
    _Bool cb = __VERIFIER_nondet_bool();

    float p1 = __VERIFIER_nondet_float();  // assume a valid prob in [0,1] if needed
    float p2 = __VERIFIER_nondet_float();

    Result out = Fair(count, ca, cb, p1, p2);

    assert(out.count >= 0); // Any condition using output


    // Optionally add an assertion if you want CBMC to verify something
    // Example: assert(out.count <= 3);

    return 0;
}
