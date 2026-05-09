#include <stdio.h>
#include <stdlib.h>
#include <math.h>



// int LoopModelBool(int retries, int retries_flag, int success, int seed) {
int LoopModelBool(int retries, int success, int seed) {
    srand48(seed);

    
    double c_status;
    int t = 0;


    if (success == 0 && retries < 48) {


        // Uniform sample [0, 10]
        // int delta = (int)(drand48() * 11);
        // t += delta;

        // Bernoulli(0.1)
        c_status = (drand48() < 0.625) ? 1 : 0;

        if (c_status == 1) 

        {
            success = 1;    
            
        } 

        else if (retries < 48)
        {
            // retries_flag = 0;
            retries = retries + 1;

            return (2*retries + success);
        }

        else 
        {
            // retries_flag = 1;
            return (2*retries + success);
        }

    }

    return (2*retries + success);

}



int main(int argc, char *argv[]) {
    if (argc != 11) {
        printf("Usage: %s <retry_bit0>..<retry_bit2> <success> <seed>\n", argv[0]);
        return 1;
    }


    int retries = 0;
    int retry_bits[8];
    for (int i = 0; i < 8; i++) {
        retry_bits[i] = atoi(argv[i + 1]);
        retries = retries + retry_bits[i]* (1 << (7-i));
    }


    // int retries_flag = atoi(argv[4]);
    int success = atoi(argv[9]);
    int seed = atoi(argv[10]);
    // printf("%d\n", retries);
    // printf("%d\n", retries_flag);
    // printf("%d\n", success);
    // int result = LoopModelBool(retries, retries_flag, success, seed);
    int result = LoopModelBool(retries, success, seed);
    printf("%d\n", result);

    return 0;
}

