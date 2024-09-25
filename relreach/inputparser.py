import argparse


def parseArguments():
    parser = argparse.ArgumentParser(description='Model checks an MDP against a relational reachability specification.')
    parser.add_argument('-modelPath', required=True, help='path to the MDP/DTMC model file in PRISM language')
    # parser.add_argument('-hyperString', required=True, help='the specification string in HyperPCTL')
    # parser.add_argument('-stutterLength', required=False, help='Memory size for stutter scheduler')
    parser.add_argument('--checkModel', action='store_true', help='check if model file can be parsed')
    # parser.add_argument('--checkProperty', action='store_true', help='check if property file can be parsed')
    # parser.add_argument('--maxSchedProb', required=False, help='upper bound for the probabilities assigned by the scheduler')
    args = parser.parse_args()
    return args
