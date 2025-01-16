import argparse


def parseArguments():
    parser = argparse.ArgumentParser(description='Model checks an MDP against a relational reachability specification.')
    parser.add_argument('-m', '--modelPath', required=True, help='path to the MDP/DTMC model file in PRISM language')
    parser.add_argument('-nSch', '--numScheds', required=True, type=int, choices=[1,2], help='number of schedulers')
    parser.add_argument('-nI', '--numInit', required=True, type=int, choices=[1,2], help='number of initial states')
    parser.add_argument('-t', '--targets', nargs='+', type=str, required=True, help='target labels')
    #parser.add_argument('-coe', '--coefficient', nargs='+', type=int, default=[1, -1, 0], help='coefficient')
    parser.add_argument('-coe', '--coefficient', type=float, default=0, help='coefficient')
    parser.add_argument('-cop', '--comparisonOperator', choices=['=', '<', '>', '<=', '>=', '!='], default='=', help='comparison operator')
    parser.add_argument('-cM', '--checkModel', action='store_true', help='check if model file can be parsed')
    parser.add_argument('-ex', '--exact', action='store_true', help='activate exact computation')
    args = parser.parse_args()
    return args
