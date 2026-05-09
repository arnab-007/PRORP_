#include <iostream>
#include <random>
#include <chrono>

int Geo0(int &z, int &flip, float p1, std::mt19937 &gen, std::uniform_real_distribution<> &dist) {
    if (flip == 0) {
        double rand_float = dist(gen);  // Uniform in [0, 1)

        int d = (rand_float < p1) ? 1 : 0;
        if (d) {
            flip = 1;
        } else {
            z++;  // Increment z when flip == 0
        }
    }

    return (2 * z + flip);
}

int main(int argc, char *argv[]) {
    if (argc != 10) {
        std::cerr << "Usage: " << argv[0] << " <z7> <z6> <z5> <z4> <z3> <z2> <z1> <z0> <flip> <r1>" << std::endl;
        return 1;
    }

    // Parse bits
    int z7 = std::atoi(argv[1]);
    int z6 = std::atoi(argv[2]);
    int z5 = std::atoi(argv[3]);
    int z4 = std::atoi(argv[4]);
    int z3 = std::atoi(argv[5]);
    int z2 = std::atoi(argv[6]);
    int z1 = std::atoi(argv[7]);
    int z0 = std::atoi(argv[8]);
    int flip = std::atoi(argv[9]);
    float p1 = 0.5;

    // Compose z as an 8-bit int
    int z = 128 * z7 + 64 * z6 + 32 * z5 + 16 * z4 + 8 * z3 + 4 * z2 + 2 * z1 + z0;

    // 🔥 Setup high-quality RNG
    std::random_device rd;
    std::mt19937 gen(rd());  // Mersenne Twister engine
    std::uniform_real_distribution<> dist(0.0, 1.0);  // Uniform float in [0, 1)

    int result = Geo0(z, flip, p1, gen, dist) % 512;
    std::cout << result << std::endl;

    return 0;
}
