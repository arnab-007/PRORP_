#include <stdlib.h>
#include <time.h>
#include <stdio.h> 

int Geo0(int z, int flip, float p1, int seed) {
    if (flip == 0) {
        //float rand_float = (float)rand() / RAND_MAX;
        srand48(seed);
        double rand_float = drand48();
        //printf("p1 = %f\n", p1);
        //printf("rand_float = %lf\n", rand_float);
        //printf("RAND_MAX = %d\n", RAND_MAX);
        int d = (rand_float < p1) ? 1 : 0;  
        //printf("%d\n",d);
        if (d) {
            flip = 1;
            //printf("Flip changed to 1!\n");
        }
        else {
             z++;  
             // Increment z when flip == 1
        }
    }

    return (2*(z) + (flip));
}




int main(int argc, char *argv[]) {


    //if (argc != 10) { // Check if exactly 9 arguments are provided
        //printf("Usage: %s <z0> <z1> <z2> <z3> <z4> <z5> <z6> <z7> <r1>\n", argv[0]);
        //return 1;
    //}


    if (argc != 11) { // Check if exactly 11 arguments are provided
        printf("Usage: %s Missing arguments\n", argv[0]);
        return 1;
    }

    // Convert command-line arguments to _Bool
    _Bool z7 = atoi(argv[1]);
    _Bool z6 = atoi(argv[2]);
    _Bool z5 = atoi(argv[3]);
    _Bool z4 = atoi(argv[4]);
    _Bool z3 = atoi(argv[5]);
    _Bool z2 = atoi(argv[6]);
    _Bool z1 = atoi(argv[7]);
    _Bool z0 = atoi(argv[8]);
    _Bool r1 = atoi(argv[9]);
    int seed = atoi(argv[10]);


    //srand48(time(seed));   // Seed randomness
    int z = (128*(int)z7 + 64*(int)z6 + 32*(int)z5 + 16*(int)z4 + 8*(int)z3 + 4*(int)z2 + 2*(int)z1 + (int)z0);
    //int z = (64*(int)z6 + 32*(int)z5 + 16*(int)z4 + 8*(int)z3 + 4*(int)z2 + 2*(int)z1 + (int)z0);
    int flip = (int)r1;
    float p1 = 0.5;
    // Call func1 with the arguments
    int result = Geo0(&z, &flip, p1, seed) % 512;
    printf("%d\n", result);
    //printf("Value of z = %d, flip = %d\n", result/2,result%2);
    

    
    return 0;
    
}
