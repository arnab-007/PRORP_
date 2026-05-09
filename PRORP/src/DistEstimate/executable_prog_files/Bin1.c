#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>

typedef struct
{
    uint64_t M; // 8-bit integer for M
    uint64_t n; // 8-bit boolean for n
    uint64_t x; // 8-bit boolean for x
} Result;

Result bin1(uint64_t M, uint64_t n, uint64_t x, float p1, int seed)
{
    if (n < M)
    {
        srand(seed); // Seed randomness
        double rand_float = drand48();
        int d = (rand_float < p1) ? 1 : 0;
        if (d)
        {
            x++;
        }
        n++;
    }

    Result result = {M, n, x};
    return result;
}

int main(int argc, char *argv[])
{
    if (argc != 50)
    {
        printf("Usage: %s <M7> <M6>...<M0> .. <n7>...<n0> .. <x7>...<x0>\n", argv[0]);
        return 1;
    }

    // Convert command-line arguments to boolean (_Bool)
    _Bool M_bits[16], n_bits[16], x_bits[16];
    for (int i = 0; i < 16; i++) {
        M_bits[i] = (_Bool)atoi(argv[i + 1]);
        n_bits[i] = (_Bool)atoi(argv[i + 17]);
        x_bits[i] = (_Bool)atoi(argv[i + 33]);
    }
    int seed = atoi(argv[49]);

    // Pack into uint8_t using bit shifting
    uint64_t M = 0, n = 0, x = 0;
    for (int i = 0; i < 16; i++) {
        M |= (M_bits[i] << i);
        n |= (n_bits[i] << i);
        x |= (x_bits[i] << i);
    }
    float p1 = 0.5;

    // Call Bin1 and store the result
    Result output = bin1(M, n, x, p1, seed);
    int result = ((1ULL << 32) * output.M + (1ULL << 16) * output.n + output.x) % (1ULL << 48);
    printf("%d\n", result);

    return 0;
}