#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>
#include <stdbool.h>


typedef struct
{
    uint8_t x;  // 8-bit bitvector for x
} Result;



Result Prinsys(uint8_t x, float p1, float p2, int seed)
{

    srand48(seed);
    double rand_float1 = drand48();
    double rand_float2 = drand48();
        
    if (x == 0)
    {
        
        _Bool d1 = (rand_float1 < p1) ? 1 : 0;

        if (d1 == 1)
        {
            x = 0;
        }
        else
        {
            _Bool d2 = (rand_float2 < p2) ? 1 : 0;

            if (d2 == 1)
            {
                x = 2;
            }
            else
            {
                x = 1;
            }
        }
        
        
    }

    

    Result result = {x};
    return result;
}


int main(int argc, char *argv[])
{
    if (argc != 4)
    {
        printf("Usage: %s Missing arguments\n", argv[0]);
        return 1;
    }

    // Convert command-line arguments to boolean (_Bool)
    _Bool x1 = atoi(argv[1]) ;
    _Bool x0 = atoi(argv[2]) ;
    int seed = atoi(argv[3]) ;
   

    //srand(time(NULL)); // Seed randomness

    // Convert boolean values to an 8-bit integer z
    uint8_t x = (2 * x1 + x0);
    
    double p1 = 0.5;
    double p2 = 0.5;

    // Call Bin1 and store the result
    Result output = Prinsys(x, p1, p2, seed);
    //printf("%d\n",output.x);
    //printf("%d\n",output.n);
    int result = output.x % 256 ;
    printf("%d\n", result);

    return 0;
}








