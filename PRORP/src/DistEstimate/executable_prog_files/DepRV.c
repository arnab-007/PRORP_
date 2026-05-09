#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>

typedef struct
{
    uint64_t y; // 8-bit integer for M
    uint64_t n; // 8-bit boolean for n
    uint64_t x; // 8-bit boolean for x
} Result;

Result DepRV(uint64_t y, uint64_t n, uint64_t x, float p1, int seed)
{
    if (n > 0)
    {
        srand48(seed);
        double rand_float = drand48();
        int d = (rand_float < p1) ? 1 : 0;
        if (d)
        {
            x = x + 1;
        }
        else
        {
            y = y + 1;
        }
        n = n - 1;
    }

    Result result = {y, n, x};
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
     _Bool y_bits[16], n_bits[16], x_bits[16];

    // Parse command-line args into Boolean arrays
    for (int i = 0; i < 16; i++) {
        y_bits[i] = (_Bool)atoi(argv[i + 1]);
        n_bits[i] = (_Bool)atoi(argv[i + 17]);
        x_bits[i] = (_Bool)atoi(argv[i + 33]);
    }

    int seed = atoi(argv[49]);
    srand(seed); // or use time(NULL) if you want randomness

    // Convert boolean bits to 8-bit integers using shifts
    uint64_t y = 0, n = 0, x = 0;
    for (int i = 0; i < 16; i++) {
        y |= (y_bits[i] << (15-i));
        n |= (n_bits[i] << (15-i));
        x |= (x_bits[i] << (15-i));
    }
    float p1 = 0.5;

    // Call Bin1 and store the result
    Result output = DepRV(y, n, x, p1, seed);
    uint64_t result = ((1ULL << 32) * (output.y % (1ULL << 16)) + (1ULL << 16) * (output.n % (1ULL << 16)) + (output.x % (1ULL << 16))) % (1ULL << 48);
    printf("%llu\n", result);

    return 0;
}