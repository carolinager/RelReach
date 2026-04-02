import argparse


def parseArguments():
    parser = argparse.ArgumentParser(description='Model checks an MDP against a relational property.')
    parser.add_argument('-m', '--modelPath', required=True, help='path to the MDP/DTMC model file in PRISM language')
    parser.add_argument('-nSch', '--numScheds', required=True, type=int, help='number of schedulers')
    parser.add_argument('-nI', '--numInit', required=True, type=int, help='number of initial state labels')
    parser.add_argument('-schedL', '--schedList', required=True, nargs='+', type=int, help='family of scheduler indices. Length must equal numInit.')
    parser.add_argument('-t', '--targets', required=True, nargs='+', type=str, help='list of target labels. Length must equal numInit.')
    parser.add_argument('-coe', '--coefficient', required=True, nargs='+', type=float, help='list of coefficients. Length must equal numInit+1.')
    # optional, concerning property
    parser.add_argument('-cop', '--comparisonOperator', choices=['=', '<', '>', '<=', '>=', '!='], default='=', help='comparison operator. Default is =')
    parser.add_argument('-eps', '--epsilon', type=float, default=0, help='epsilon. Default is 0. Currently only support same epsilon for all predicates')
    parser.add_argument('-b', '--buechi', action='store_true', help='interpret targets as Buechi objectives. Currently only supported for a single predicate')
    # optional, concerning computation
    parser.add_argument('-cM', '--checkModel', action='store_true', help='check if model file can be parsed')
    args = parser.parse_args()
    return args
