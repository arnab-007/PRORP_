#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>
#include <stdbool.h>

typedef struct
{
    uint64_t c;      // 8-bit bitvector for x
    uint64_t b;      // 8-bit bitvector for n
    uint64_t rounds; // 8-bit bitvector for z
} Result;

Result Mart(uint64_t c, uint64_t b, uint64_t rounds, float p1, int seed)
{

    srand48(seed);

    if (b > 0)
    {
        double rand_float = drand48();
        int d = (rand_float < p1) ? 1 : 0;
        if (d)
        {
            c = c + b;
            b = 0;
        }
        else
        {
            c = c - b;
            b = 2 * b;
        }
        rounds++;
    }

    Result result = {c, b, rounds};
    return result;
}

int main(int argc, char *argv[])
{
    if (argc != 50)
    {
        printf("Usage: %s Missing arguments\n", argv[0]);
        return 1;
    }

    // Convert command-line arguments to boolean (_Bool)
    _Bool c_bits[16], b_bits[16], rounds_bits[16];
    for (int i = 0; i < 16; i++) {
        c_bits[15 - i]      = atoi(argv[i + 1]);   // argv[1] to argv[8]
        b_bits[15 - i]      = atoi(argv[i + 17]);   // argv[9] to argv[16]
        rounds_bits[15 - i] = atoi(argv[i + 33]);  // argv[17] to argv[24]
    }

    // Convert to uint8_t using shifting
    uint64_t c = 0, b = 0, rounds = 0;
    for (int i = 0; i < 16; i++) {
        c      |= (c_bits[i] << i);
        b      |= (b_bits[i] << i);
        rounds |= (rounds_bits[i] << i);
    }

    int seed = atoi(argv[49]);
    double p1 = 0.5;

    // Call Bin1 and store the result
    Result output = Mart(c, b, rounds, p1, seed);
    // printf("%d\n",output.x);
    // printf("%d\n",output.n);
    uint64_t result = ((1ULL << 32) * (output.c % (1ULL << 16)) + (1ULL << 16) * (output.b % (1ULL << 16)) + (output.rounds % (1ULL << 16))) % (1ULL << 48);
    printf("%llu\n", result);
    return 0;
}