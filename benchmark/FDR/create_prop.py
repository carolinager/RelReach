import sys
import re

N = int(sys.argv[1])


## Property for RelProp
prop_file_name = f"prop_{N}.txt"
prop_file_name_a = f"prop_0.59-0.61_{N}.txt"

with open(prop_file_name, 'w') as prop_file:
    with open(prop_file_name_a, 'w') as prop_file_a:
        prop_file.write(f"--modelPath ./benchmark/FDR/{file_name} ")
        prop_file_a.write(f"--modelPath ./benchmark/FDR/{file_name_a} ")
        for prop_file_x in [prop_file, prop_file_a]:
            prop_file_x.write(f"--numPred {N} --numInit {2*N} --numScheds 1 ")
            prop_file_x.write("--schedList ")
            for i in range(2*N):
                prop_file_x.write("1 ")
            prop_file_x.write("--targets ")
            for i in range(N-1):
                prop_file_x.write(f"d{i} d{i+1} ")
            prop_file_x.write(f"d{N-1} d0 ")
            prop_file_x.write("--coefficient ")
            for i in range(N):
                prop_file_x.write("1 -1 0 ")
            prop_file_x.write("-cop !=")

## Property for HyperProb
prop_file_name = f"prop_HyperProb_{N}.txt"
prop_file_name_eps = f"prop_HyperProb_eps_{N}.txt"

disjuncts=[]
disjuncts_eps=[]
for i in range(N-1):
    disjuncts.append(f"((P(F d{i}(s1)) < P(F d{i+1}(s1))) | (P(F d{i}(s1)) > P(F d{i+1}(s1))))")
    disjuncts_eps.append(f"((P(F d{i}(s1)) < P(F d{i+1}(s1)) - 0.13 ) | (P(F d{i}(s1)) > P(F d{i+1}(s1)) + 0.13))")
disjuncts.append(f"((P(F d{N-1}(s1)) < P(F d0(s1))) | (P(F d{N-1}(s1)) > P(F d0(s1))))")
disjuncts_eps.append(f"((P(F d{i}(s1)) < P(F d{i+1}(s1)) - 0.13 ) | (P(F d{i}(s1)) > P(F d{i+1}(s1)) + 0.13 ))")

with open(prop_file_name, 'w') as prop_file:
    with open(prop_file_name_eps, 'w') as prop_file_eps:
        for prop_file_x in [prop_file, prop_file_eps]:
            prop_file_x.write("AS sh . A s1 . (init1(s1) -> ")
            for i in range(N-1):
                prop_file_x.write("(")

        prop_file.write(disjuncts[0])
        for i in range(1,N):
            prop_file.write(f" | {disjuncts[i]})")

        prop_file_eps.write(disjuncts_eps[0])
        for i in range(1,N):
            prop_file_eps.write(f" | {disjuncts_eps[i]})")

        for prop_file_x in [prop_file, prop_file_eps]:
            prop_file_x.write(" )")

## Property for HyperPAYNT
# Syntax: "bound -- P1 op P2" means "P1 + bound op P2"
prop_file_name = f"sketch_{N}.props"
prop_file_name_eps = f"sketch_eps_{N}.props"

with open(prop_file_name, 'w') as prop_file:
    with open(prop_file_name_eps, 'w') as prop_file_eps:
        for prop_file_x in [prop_file, prop_file_eps]:
            prop_file_x.write("ES sched1\n")
            prop_file_x.write("E s0(sched1)\n")
            prop_file_x.write("Restrict s0 init1\n")

        for i in range(N-1):
            prop_file.write(f"P{{s0}}[F \"d{i}\"] <= P{{s0}}[F \"d{i+1}\"]\n")
            prop_file.write(f"P{{s0}}[F \"d{i+1}\"] <= P{{s0}}[F \"d{i}\"]\n")
        prop_file.write(f"P{{s0}}[F \"d{N-1}\"] <= P{{s0}}[F \"d{0}\"]\n")
        prop_file.write(f"P{{s0}}[F \"d{0}\"] <= P{{s0}}[F \"d{N-1}\"]\n")

        for i in range(N-1):
            prop_file_eps.write(f"-0.13 -- P{{s0}}[F \"d{i}\"] <= P{{s0}}[F \"d{i+1}\"]\n")
            prop_file_eps.write(f"-0.13 -- P{{s0}}[F \"d{i+1}\"] <= P{{s0}}[F \"d{i}\"]\n")
        prop_file_eps.write(f"-0.13 -- P{{s0}}[F \"d{N-1}\"] <= P{{s0}}[F \"d{0}\"]\n")
        prop_file_eps.write(f"-0.13 -- P{{s0}}[F \"d{0}\"] <= P{{s0}}[F \"d{N-1}\"]\n")
