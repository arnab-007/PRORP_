#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>
#include <stdbool.h>


typedef struct
{
    uint64_t x;  // 8-bit bitvector for x
    uint64_t n; // 8-bit bitvector for n
} Result;



Result Sum0(uint64_t x, uint64_t n, float p1, int seed)
{

    srand48(seed);
    double rand_float = drand48();
        
    if (n > 0)
    {
        // printf("%f\n",rand_float);
        x = (rand_float < p1) ? (x + n) : x;
        
        
    }

    n = n - 1;  
    // printf("%llu\n", x);
    Result result = {x,n};
    return result;
}


int main(int argc, char *argv[])
{
    if (argc != 34)
    {
        printf("Usage: %s Missing arguments\n", argv[0]);
        return 1;
    }

    // Convert command-line arguments to boolean (_Bool)
    _Bool x_bits[16], n_bits[16];

    // Read x15 to x0 from argv[1] to argv[16]
    for (int i = 0; i < 16; i++) {
        x_bits[i] = atoi(argv[1 + i]);
    }

    // Read n15 to n0 from argv[17] to argv[32]
    for (int i = 0; i < 16; i++) {
        n_bits[i] = atoi(argv[17 + i]);
    }

    int seed = atoi(argv[33]);

    // Pack bits into uint16_t
    uint64_t x = 0, n = 0;
    for (int i = 0; i < 16; i++) {
        x |= ((uint16_t)x_bits[i] << (15-i));
        n |= ((uint16_t)n_bits[i] << (15-i));
    }
    double p1 = 0.5;

    // Call Bin1 and store the result
    Result output = Sum0(x, n, p1, seed);
    //printf("%d\n",output.x);
    //printf("%d\n",output.n);
    uint64_t result = (((output.x % (65536)) << 16) + (output.n % (65536)));
    // printf("%llu\n", output.n);
    printf("%llu\n", result);

    return 0;
}








