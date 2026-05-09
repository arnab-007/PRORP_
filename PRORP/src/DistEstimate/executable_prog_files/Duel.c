#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>
#include <stdbool.h>

typedef struct
{
    _Bool c;
    _Bool t;
} Result;

Result Duel(_Bool c, _Bool t, float p1, float p2, int seed)
{

    srand48(seed);
    double rand_float1 = drand48();
    double rand_float2 = drand48();

    if (c == 1)
    {
        if (t == 1)
        {
            _Bool d1 = (rand_float1 < p1) ? 1 : 0;

            if (d1 == 1)
            {
                c = 0;
            }
            else
            {
                t = 0;
            }
        }
        else
        {
            _Bool d2 = (rand_float2 < p2) ? 1 : 0;

            if (d2 == 1)
            {
                c = 0;
            }
            else
            {
                t = 1;
            }
        }
    }
    Result result = {c, t};
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
    _Bool c = atoi(argv[1]);
    _Bool t = atoi(argv[2]);
    int seed = atoi(argv[3]);

    // srand(time(NULL)); // Seed randomness

    double p1 = 0.5;
    double p2 = 0.5;

    // Call Bin1 and store the result
    Result output = Duel(c, t, p1, p2, seed);
    // printf("%d\n",output.x);
    // printf("%d\n",output.n);
    int result = (output.c * 2 + output.t) % 4;
    printf("%d\n", result);

    return 0;
}