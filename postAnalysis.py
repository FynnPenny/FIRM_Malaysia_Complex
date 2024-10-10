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
parser.add_argument('-n', default=11, type=int, required=False, help='11,12,... 18, 21, 22, ..., 28, 30')
parser.add_argument('-t', default='HVDC', type=str, required=False, help='HVDC, HVAC')
parser.add_argument('-a', default=1, type=int, required=False, help='run post analysis')
parser.add_argument('-q', default=0, type=int, required=False, help='Quick test run')
parser.add_argument('-H', default='True', type=str, required=False, help='Hydrogen Firming=True,False')
parser.add_argument('-g', default=None, type=float, required=False,help='Maximum Gas Capacity (MW)')
parser.add_argument('-G', default=None, type=float, required=False, help='Maximum annual gas generation (percent of total)')
parser.add_argument('-b', default='True', type=str, required=False, help='Battery Coopimisation=True,False')
parser.add_argument('-f', default=0, type=float, required=False, help='Fossil fuels=0,2,5 percent of total supply')
parser.add_argument('-l', default='True', type=str, required=False, help='Data includes leap years=True,False')
parser.add_argument('-v', default=1, type=int, required=False, help='Verbose=0,1,2')
args = parser.parse_args()

# scenario = args.s
maxit = args.i
transmissionScenario = args.t
node = args.n
percapita = args.e
verbose = args.v
gasCapLim = args.g
gasGenLim = args.G 
fossil = args.f
quick = args.q

if args.H == "True":
    gasScenario = True
elif args.H == "False":
    gasScenario = False
else:
    print("-H must be True or False")
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

if quick:
    suffix = '_{}_{}_{}_{}_{}_{}_quick'.format(node,transmissionScenario,percapita,batteryScenario,gasScenario,gasGenLim)
else:
    suffix = '_{}_{}_{}_{}_{}_{}'.format(node,transmissionScenario,percapita,batteryScenario,gasScenario,gasGenLim)

# from Input import *
# from Simulation import Reliability
# from Network import Transmission

if __name__=='__main__':
    if quick:
        suffix = '_{}_{}_{}_{}_{}_{}_quick'.format(node,transmissionScenario,percapita,batteryScenario,gasScenario,gasGenLim)
    else:
        suffix = '_{}_{}_{}_{}_{}_{}'.format(node,transmissionScenario,percapita,batteryScenario,gasScenario,gasGenLim)

    print('Results/Optimisation_resultx{}.csv'.format(suffix))
    with open('Results/Optimisation_resultx{}.csv'.format(suffix),newline="") as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            old_x = [float(num) for num in row]

    print(old_x)

    from Fill import Analysis
    Analysis(old_x,'{}'.format(suffix))