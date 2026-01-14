import argparse


def parseArguments():
    parser = argparse.ArgumentParser(description='Model checks an MDP against a relational reachability specification.')
    parser.add_argument('-m', '--modelPath', required=True, help='path to the MDP/DTMC model file in PRISM language')
    parser.add_argument('-nSch', '--numScheds', required=True, type=int, help='number of schedulers')
    parser.add_argument('-nI', '--numInit', required=True, type=int, help='number of initial state labels')
    parser.add_argument('-schedL', '--schedList', required=True, nargs='+', type=int, help='family of scheduler indices')
    parser.add_argument('-t', '--targets', required=True, nargs='+', type=str, help='list of target labels')
    parser.add_argument('-coe', '--coefficient', required=True, nargs='+', type=float, help='list of coefficients')
    # optional, concerning property
    parser.add_argument('-cop', '--comparisonOperator', choices=['=', '<', '>', '<=', '>=', '!='], default='=', help='comparison operator. Default is =')
    parser.add_argument('-eps', '--epsilon', type=float, default=0, help='epsilon. Default is 0')
    parser.add_argument('-b', '--buechi', action='store_true', help='interpret targets as Buechi objectives')
    # optional, concerning computation
    parser.add_argument('-cM', '--checkModel', action='store_true', help='check if model file can be parsed')
    parser.add_argument('-ex', '--exact', action='store_true', help='activate exact computation')
    parser.add_argument('-wit', '--witness', action='store_true', help='output witness scheduler(s)')
    args = parser.parse_args()
    return args
