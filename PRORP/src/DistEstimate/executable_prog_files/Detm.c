#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>
#include <stdbool.h>


typedef struct
{
    uint64_t x;  // 8-bit bitvector for x
    uint64_t count; // 8-bit bitvector for n
} Result;



Result Detm(uint64_t x, uint64_t count, int seed)
{

    srand48(seed);
    
    if (x <= 15)

    {

        x = x + 1;
        count = count + 1;
    }  

    Result result = {x,count};
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
    _Bool x_bits[16], count_bits[16];

    for (int i = 0; i < 16; i++) {
        x_bits[15 - i] = (_Bool)atoi(argv[i + 1]);         // argv[1] to argv[8]
        count_bits[15 - i] = (_Bool)atoi(argv[i + 17]);     // argv[9] to argv[16]
    }

    int seed = atoi(argv[33]);
    srand(seed);  // Or srand(time(NULL)); for randomness not controlled by user

    // Convert bit arrays into 8-bit integers using shifts
    uint16_t x = 0, count = 0;
    for (int i = 0; i < 16; i++) {
        x     |= (x_bits[i]     << i);
        count |= (count_bits[i] << i);
    }
   

    //srand(time(NULL)); // Seed randomness

    
    

    // Call Bin1 and store the result
    Result output = Detm(x, count, seed);
    //printf("%d\n",output.x);
    //printf("%d\n",output.n);
    uint64_t result = ((output.x % (1ULL << 16)) << 16) + (output.count % (1ULL << 16)) % (1ULL << 32);
    printf("%llu\n", result);

    return 0;
}








