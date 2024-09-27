import argparse


def parseArguments():
    parser = argparse.ArgumentParser(description='Model checks an MDP against a relational reachability specification.')
    parser.add_argument('-m', '--modelPath', required=True, help='path to the MDP/DTMC model file in PRISM language')
    parser.add_argument('-t', '--targets', nargs='+', type=str, required=True)
    parser.add_argument('-cop', '--comparisonOperator', choices=['=', '<', '>', '<=', '>='], default='=', help='comparison Operator')
    parser.add_argument('-cM', '--checkModel', action='store_true', help='check if model file can be parsed')
    args = parser.parse_args()
    return args
