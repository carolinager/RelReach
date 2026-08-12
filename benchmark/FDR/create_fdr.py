import sys
import re

N = int(sys.argv[1])
file_name = f"fdr_0.59-0.61_{N}.prism"

with open(file_name, 'w') as file_x:
    file_x.write("// https://zenodo.org/records/10438916\n")
    file_x.write("// Fast Dice Roller Algorithm for uniform random sampling using coin flips [J. Lumbroso, arXiv:1304.1916, 2013]\n")
    file_x.write("// The given encoding is based on a transformation to a probabilistic program by Daniel Zilken\n")
    file_x.write("// Extended to biased coins by Lina Gerlach\n")
    file_x.write("\n")
    file_x.write("mdp\n\n")
    file_x.write(f"const int N={N}; // N > 0, the algorithm samples uniformly from {{0, ..., N-1}}\n\n")

    file_x.write("const double bias_l = 59/100; // lower bound for bias towards 0\n")
    file_x.write("const double bias_u = 61/100; // upper bound for bias towards 0\n")

    file_x.write("\n")
    file_x.write("formula decrHeads = 2*c >= N ? N : 0;\n")
    file_x.write("formula decrTails = 2*c+1 >= N ? N : 0;\n")
    file_x.write("module main\n")
    file_x.write("    v : [0..N] init 1;\n")
    file_x.write("    c : [0..N] init 0;\n")
    file_x.write("    [l] v<N -> bias_l : (v' =min(N,2*v-decrHeads)) & (c'=2*c-decrHeads) + (1-bias_l) : (v' =min(N,2*v-decrTails)) & (c'=2*c+1-decrTails);\n")
    file_x.write("    [u] v<N -> bias_u : (v' =min(N,2*v-decrHeads)) & (c'=2*c-decrHeads) + (1-bias_u) : (v' =min(N,2*v-decrTails)) & (c'=2*c+1-decrTails);\n")
    file_x.write("    [] v=N -> 1 : true;\n")
    file_x.write("endmodule\n")
    file_x.write("\n")

    for i in range(1,2*N+1):
        file_x.write(f"label \"init{i}\" = (v=1)&(c=0);\n")
    file_x.write("\n")

    for i in range(0,N):
        file_x.write(f"label \"d{i}\" = (v=N)&(c={i});\n")
    file_x.write("\n")
