import argparse


def parseArguments():
    parser = argparse.ArgumentParser(description='Model checks an MDP against a relational reachability specification.')
    parser.add_argument('-modelPath', required=True, help='path to the MDP/DTMC model file in PRISM language')
    #parser.add_argument('-target', required=True, help='target label')
    parser.add_argument('-targets', nargs='+', type=str)
    parser.add_argument('--checkModel', action='store_true', help='check if model file can be parsed')
    # parser.add_argument('--checkProperty', action='store_true', help='check if property file can be parsed')
    args = parser.parse_args()
    return args
