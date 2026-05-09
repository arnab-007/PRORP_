#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>
#include <stdbool.h>


typedef struct
{
    uint64_t x;  // 8-bit bitvector for x
    uint64_t y; // 8-bit bitvector for n
    uint64_t z; // 8-bit bitvector for z
} Result;



Result GeoAr(uint64_t x, uint64_t y, uint64_t z, float p1, int seed)
{

    srand48(seed);
    
        
    if (z > 0)
    {
        y = y + 1;
        double rand_float = drand48();
        int d = (rand_float < p1) ? 1 : 0;  

        if (d)
        {
            z = 0;
        } 
        else
        {
            x = x + y;
        }
        
        
    }

    

    Result result = {x,y,z};
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
    // Convert command-line arguments to boolean (_Bool)
    _Bool x_bits[16], y_bits[16], z_bits[16];

    for (int i = 0; i < 16; i++) {
        x_bits[15 - i] = atoi(argv[1 + i]);
        y_bits[15 - i] = atoi(argv[17 + i]);
        z_bits[15 - i] = atoi(argv[33 + i]);
    }

    int seed = atoi(argv[49]);

    // Pack bits into 64-bit integers
    uint64_t x = 0, y = 0, z = 0;
    for (int i = 0; i < 16; i++) {
        if (x_bits[i]) x |= ((uint64_t)1 << i);
        if (y_bits[i]) y |= ((uint64_t)1 << i);
        if (z_bits[i]) z |= ((uint64_t)1 << i);
    }

    double p1 = 0.5;

    // Call Bin1 and store the result
    Result output = GeoAr(x, y, z, p1, seed);
    //printf("%d\n",output.x);
    //printf("%d\n",output.n);

    
    uint64_t result = ((output.x % (1ULL << 16)) << 32)
           + ((output.y % (1ULL << 16)) << 16)
           + (output.z % (1ULL << 16));

    printf("%llu\n", result);

    return 0;
}








