from scipy.optimize import differential_evolution
from argparse import ArgumentParser
import datetime as dt
import csv

parser = ArgumentParser()
parser.add_argument('-i', default=400, type=int, required=False, help='maxiter=4000, 400')
parser.add_argument('-p', default=5, type=int, required=False, help='popsize=2, 10')
parser.add_argument('-m', default=0.5, type=float, required=False, help='mutation=0.5')
parser.add_argument('-r', default=0.3, type=float, required=False, help='recombination=0.3')
parser.add_argument('-e', default=5, type=int, required=False, help='per-capita electricity = 5, 10, 20 MWh/year')
# parser.add_argument('-n', default='APG_MY_Isolated', type=str, required=False, help='APG_Full, APG_PMY_Only, APG_BMY_Only, APG_MY_Isolated, SB, SW...')
parser.add_argument('-n', default=11, type=int, required=False, help='11,12,... 18, 21, 22, ..., 28, 30')
parser.add_argument('-t', default='HVAC', type=str, required=False, help='HVDC, HVAC')
parser.add_argument('-H', default='True', type=str, required=False, help='Hydrogen Firming=True,False')
parser.add_argument('-b', default='True', type=str, required=False, help='Battery Coopimisation=True,False')
parser.add_argument('-f', default='False', type=str, required=False, help='Fossil fuels=True,False')
parser.add_argument('-l', default='True', type=str, required=False, help='Data includes leap years=True,False')
parser.add_argument('-v', default=0, type=int, required=False, help='Verbose=0,1,2')
args = parser.parse_args()

# scenario = args.s
transmissionScenario = args.t
node = args.n
percapita = args.e
verbose = args.v

if args.H == "True":
    gasScenario = True
elif args.H == "False":
    gasScenario = False
else:
    print("-H must be True or False")
    exit()

if args.f == "True":
    fossilScenario = True
elif args.f == "False":
    fossilScenario = False
else:
    print("-f must be True or False")
    exit()

if args.b == "True":
    batteryScenario = True
elif args.b == "False":
    batteryScenario = False
else:
    print("-b must be True or False")
    exit()

if args.l == "True":
    leapYearData = True
elif args.l == "False":
    leapYearData = False
else:
    print("-l must be True or False")
    exit()

from Input import *
from Simulation import Reliability
from Network import Transmission


if __name__=='__main__':
    print('Results/Optimisation_resultx_{}_{}_{}_{}_{}.csv'.format(node,transmissionScenario,percapita,batteryScenario,gasScenario))
    with open('Results/Optimisation_resultx_{}_{}_{}_{}_{}.csv'.format(node,transmissionScenario,percapita,batteryScenario,gasScenario),newline="") as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            old_x = [float(num) for num in row]

    print(old_x)

    from Fill import Analysis
    Analysis(old_x,'_{}_{}_{}_{}_{}_{}.csv'.format(node,transmissionScenario,percapita,batteryScenario,gasScenario,args.i))