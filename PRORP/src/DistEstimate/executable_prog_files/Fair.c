#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>

/** 
int count , bool ca , c2 float p1 , p2
while not ( ca or c2 ):
    ca = bernoulli . rvs ( size =1 , p = p1 ) [0]
    if ca :
        count = count + 1
    c2 = bernoulli . rvs ( size =1 , p = p2 ) [0]
    if c2 :
        count = count + 1
*/

typedef struct
{
    uint64_t count;
    _Bool ca; 
   _Bool cb;
} Result;

Result Fair(uint64_t count, _Bool ca, _Bool cb, float p1, float p2, int seed)
{
    srand48(seed);
    if (!ca && !cb)
    {
        double rand_float1 = drand48();
        ca = (rand_float1 < p1) ? 1 : 0;
        if (ca)
        {
            count++;
        }
        double rand_float2 = drand48();
        cb = (rand_float2 < p2) ? 1 : 0;
        if (cb)
        {
            count++;
        }
    }

    Result result = {count, ca, cb};
    return result;
}

int main(int argc, char *argv[])
{
    
    if (argc != 20)
    {
        printf("Usage: %s Missing arguments\n", argv[0]);
        return 1;
    }
    /*
    if (argc != 7)
    {
        printf("Usage: %s <count3> <count2> <count1> <count0> <ca> <cb>\n", argv[0]);
        return 1;
    }
    */
    // Convert command-line arguments to boolean (_Bool)
    
    _Bool count_bits[16];
    for (int i = 0; i < 16; i++) {
        count_bits[i] = atoi(argv[1 + i]);
    }

    _Bool ca = atoi(argv[17]);
    _Bool cb = atoi(argv[18]);
    int seed = atoi(argv[19]);

    // Convert to 16-bit integer
    uint64_t count = 0;
    for (int i = 0; i < 16; i++) {
        count |= ((uint64_t)count_bits[i] << i);
    }
    //srand48(time(NULL));  // Seed randomness

    
    float p1 = 0.5;
    float p2 = 0.5;

    // CAll Geo0 and store the result
    Result output = Fair(count, ca, cb, p1, p2, seed);
    uint64_t result = (4*output.count + 2*output.ca + output.cb) % (1024*256);
    printf("%llu\n", result);


    return 0;
}