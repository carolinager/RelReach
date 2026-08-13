import sys
import re
import math

N = int(sys.argv[1])
file_name = f"rs_0.59-0.61_{N}.prism"

B = math.ceil(math.log(N, 2))
list_of_final_labels=[]

with open(file_name, 'w') as file_x:
    file_x.write("// Rejection Sampling\n")
    file_x.write("// biased coins\n")

    file_x.write("\n")
    file_x.write("mdp\n\n")
    file_x.write(f"const int N={N}; // N > 0, the algorithm samples uniformly from {{0, ..., N-1}}\n\n")

    file_x.write("const double bias_l = 59/100; // lower bound for bias towards 0\n")
    file_x.write("const double bias_u = 61/100; // upper bound for bias towards 0\n")

    file_x.write("\n")
    file_x.write("module main\n")
    file_x.write(f"    n : [0..{B}] init 0;\n")
    for i in range(1,B+1):
        file_x.write(f"    b{i} : [0..1] init 0;\n")

    for i in range(B):
        precond=f"(n={i})"
        for j in range(i+1,B+1):
            precond += f"&(b{j}=0)"
        postcond=f"(n'={i+1})&(b{i+1}'=1)"
        file_x.write("    [l] " + precond + f" -> bias_l : (n'={i+1}) + (1-bias_l) : " + postcond + ";\n")
        file_x.write("    [u] " + precond + f" -> bias_u : (n'={i+1}) + (1-bias_u) : " + postcond + ";\n")

    ## self-loop on state for {0,...,N-1}
    for n in range(N):
        bin_i = [int(i) for i in list(f'{n:0{B}b}')]
        precond = f"(n={B})"
        for i in range(1,B+1):
            precond += f"&(b{i}={bin_i[i-1]})"
        file_x.write("    [] " + precond + f" -> 1 : true;\n")
        list_of_final_labels.append(precond) # reuse later

    ## go back to initial state for {N,...,2^B-1}
    for n in range(N,2**B):
        bin_i = [int(i) for i in list(f'{n:0{B}b}')]
        precond = f"(n={B})"
        postcond = f"(n'=0)"
        for i in range(1,B+1):
            precond += f"&(b{i}={bin_i[i-1]})"
            postcond += f"&(b{i}'=0)"
        file_x.write("    [] " + precond + " -> 1 : " + postcond + f";\n")

    file_x.write("endmodule\n")
    file_x.write("\n")

    ## initial labels
    initial_label="(n=0)"
    for i in range(1,B+1):
        initial_label += f"&(b{i}=0)"

    for m in range(1,2*N+1):
        file_x.write(f"label \"init{m}\" = " + initial_label + ";\n")
    file_x.write("\n")

    ## final labels
    for n in range(0,N):
        file_x.write(f"label \"d{n}\" = " + list_of_final_labels[n] + ";\n")
    file_x.write("\n")
