#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>


typedef struct
{
    uint64_t y;  // 8-bit integer for M
    uint64_t n; // 8-bit boolean for n
    uint64_t x; // 8-bit boolean for x
} Result;

Result Bin0(uint64_t y, uint64_t n, uint64_t x, float p1, int seed)
{
    if (n > 0)
    {
        srand48(seed);
        double rand_float = drand48();
        int d = (rand_float < p1) ? 1 : 0;
        if (d)
        {
            x = x + y;
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

    // Convert command-line arguments to boolean (_Bool) for 16-bit y, n, x
    _Bool y15 = atoi(argv[1]);
    _Bool y14 = atoi(argv[2]);
    _Bool y13 = atoi(argv[3]);
    _Bool y12 = atoi(argv[4]);
    _Bool y11 = atoi(argv[5]);
    _Bool y10 = atoi(argv[6]);
    _Bool y9  = atoi(argv[7]);
    _Bool y8  = atoi(argv[8]);
    _Bool y7  = atoi(argv[9]);
    _Bool y6  = atoi(argv[10]);
    _Bool y5  = atoi(argv[11]);
    _Bool y4  = atoi(argv[12]);
    _Bool y3  = atoi(argv[13]);
    _Bool y2  = atoi(argv[14]);
    _Bool y1  = atoi(argv[15]);
    _Bool y0  = atoi(argv[16]);

    _Bool n15 = atoi(argv[17]);
    _Bool n14 = atoi(argv[18]);
    _Bool n13 = atoi(argv[19]);
    _Bool n12 = atoi(argv[20]);
    _Bool n11 = atoi(argv[21]);
    _Bool n10 = atoi(argv[22]);
    _Bool n9  = atoi(argv[23]);
    _Bool n8  = atoi(argv[24]);
    _Bool n7  = atoi(argv[25]);
    _Bool n6  = atoi(argv[26]);
    _Bool n5  = atoi(argv[27]);
    _Bool n4  = atoi(argv[28]);
    _Bool n3  = atoi(argv[29]);
    _Bool n2  = atoi(argv[30]);
    _Bool n1  = atoi(argv[31]);
    _Bool n0  = atoi(argv[32]);

    _Bool x15 = atoi(argv[33]);
    _Bool x14 = atoi(argv[34]);
    _Bool x13 = atoi(argv[35]);
    _Bool x12 = atoi(argv[36]);
    _Bool x11 = atoi(argv[37]);
    _Bool x10 = atoi(argv[38]);
    _Bool x9  = atoi(argv[39]);
    _Bool x8  = atoi(argv[40]);
    _Bool x7  = atoi(argv[41]);
    _Bool x6  = atoi(argv[42]);
    _Bool x5  = atoi(argv[43]);
    _Bool x4  = atoi(argv[44]);
    _Bool x3  = atoi(argv[45]);
    _Bool x2  = atoi(argv[46]);
    _Bool x1  = atoi(argv[47]);
    _Bool x0  = atoi(argv[48]);

    int seed = atoi(argv[49]);
    srand(time(NULL));  // seed randomness

    // Convert 16 Booleans to 16-bit integers
    uint64_t y = 0, n = 0, x = 0;

    y |= (y15 << 15) | (y14 << 14) | (y13 << 13) | (y12 << 12) |
        (y11 << 11) | (y10 << 10) | (y9  << 9)  | (y8  << 8)  |
        (y7  << 7)  | (y6  << 6)  | (y5  << 5)  | (y4  << 4)  |
        (y3  << 3)  | (y2  << 2)  | (y1  << 1)  | y0;

    n |= (n15 << 15) | (n14 << 14) | (n13 << 13) | (n12 << 12) |
        (n11 << 11) | (n10 << 10) | (n9  << 9)  | (n8  << 8)  |
        (n7  << 7)  | (n6  << 6)  | (n5  << 5)  | (n4  << 4)  |
        (n3  << 3)  | (n2  << 2)  | (n1  << 1)  | n0;

    x |= (x15 << 15) | (x14 << 14) | (x13 << 13) | (x12 << 12) |
        (x11 << 11) | (x10 << 10) | (x9  << 9)  | (x8  << 8)  |
        (x7  << 7)  | (x6  << 6)  | (x5  << 5)  | (x4 << 4)   |
        (x3  << 3)  | (x2  << 2)  | (x1  << 1)  | x0;

    float p1 = 0.5;

    // Call Bin1 and store the result
    Result output = Bin0(y, n, x, p1, seed);
    uint64_t result = ((1ULL << 32) * (output.y % (1ULL << 16)) + (1ULL << 16) * (output.n % (1ULL << 16)) + (output.x % (1ULL << 16))) % (1ULL << 48);

    printf("%llu\n", result);

    return 0;
}