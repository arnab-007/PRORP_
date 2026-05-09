#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>
#include <stdbool.h>


typedef struct
{
    uint64_t count;  // 8-bit bitvector for count
    uint64_t n; // 8-bit bitvector for n
} Result;



Result LinExp(uint64_t count, uint64_t n, float p1, int seed)
{
    if (n > 0)
    {
        srand48(seed);
        double rand_float1 = drand48();
        double rand_float2 = drand48();
        double rand_float3 = drand48();
        
        uint64_t x1 = (rand_float1 < p1) ? 1 : 0;
        uint64_t x2 = (rand_float2 < p1) ? 1 : 0;
        uint64_t x3 = (rand_float3 < p1) ? 1 : 0;
       
        n = n - 1;
        uint64_t c1 = x1 || x2 || x3;
        uint64_t c2 = !x1 || x2 || x3;
        uint64_t c3 = x1 || !x2 || x3;
       
        //count += (int)c1 + (int)c2 + (int)c3;
        count += c1 + c2 + c3;
        
    }

    Result result = {count,n};
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
    _Bool count_bits[16], n_bits[16];
    for (int i = 0; i < 16; i++) {
        count_bits[15 - i] = atoi(argv[i + 1]);  // argv[1] to argv[16]
        n_bits[15 - i]     = atoi(argv[i + 17]); // argv[17] to argv[32]
    }

    int seed = atoi(argv[33]); // argv[33] = seed

    // Convert to 16-bit unsigned integers
    uint64_t count = 0, n = 0;
    for (int i = 0; i < 16; i++) {
        count |= ((uint16_t)count_bits[i] << i);
        n     |= ((uint16_t)n_bits[i]     << i);
    }

    
    double p1 = 0.5;

    // Call Bin1 and store the result
    Result output = LinExp(count, n, p1, seed);
    //printf("%d\n",output.count);
    //printf("%d\n",output.n);
    uint64_t result = ((1ULL << 16)*(output.count % (1ULL << 16)) + (output.n % (1ULL << 16))) % (1ULL << 32);
    printf("%llu\n", result);

    return 0;
}








