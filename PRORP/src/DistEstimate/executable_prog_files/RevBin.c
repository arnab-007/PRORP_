#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>

typedef struct
{
    uint64_t z;
    uint64_t x;
} Result;

Result RevBin(uint64_t z, uint64_t x, float p1, int seed)
{
    if (x > 0)
    {
        srand48(seed);
        double rand_float = drand48();
        int d = (rand_float < p1) ? 1 : 0;
        if (d)
        {
            x = x - 1;
        }
        z = z + 1;
    }

    Result result = {z, x};
    return result;
}

int main(int argc, char *argv[])
{
    if (argc != 34)
    {
        printf("Usage: %s <M7> <M6>...<M0> .. <n7>...<n0> .. <x7>...<x0>\n", argv[0]);
        return 1;
    }
    _Bool z[16];
    for (int i = 0; i < 16; i++) {
        z[15 - i] = atoi(argv[i + 1]); // Highest bit first
    }

    // Parse 16-bit x
    _Bool x[16];
    for (int i = 0; i < 16; i++) {
        x[15 - i] = atoi(argv[i + 17]); // Highest bit first
    }

    // Parse seed
    int seed = atoi(argv[33]);

    srand(time(NULL)); // Optional: you could also use `srand(seed);` for deterministic behavior

    // Convert boolean arrays to 16-bit integers
    uint16_t z_val = 0, x_val = 0;
    for (int i = 0; i < 16; i++) {
        z_val |= (z[i] << i);
        x_val |= (x[i] << i);
    }

    // Convert command-line arguments to boolean (_Bool)
    float p1 = 0.5;

    // Call Bin1 and store the result
    Result output = RevBin(z_val, x_val, p1, seed);
    uint64_t result = ((1ULL << 16) * (output.z % (1ULL << 16)) + (output.x % (1ULL << 16))) % (1ULL << 32);
    
    printf("%llu\n", result);

    return 0;
}