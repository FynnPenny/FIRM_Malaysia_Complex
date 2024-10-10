# To optimise the configurations of energy generation, storage and transmission assets
# Copyright (c) 2019, 2020 Bin Lu, The Australian National University
# Licensed under the MIT Licence
# Correspondence: bin.lu@anu.edu.au

from scipy.optimize import differential_evolution
from argparse import ArgumentParser
import datetime as dt
import csv

parser = ArgumentParser()
# Differential Evolution Optimisation Parameters
parser.add_argument('-i', default=400, type=int, required=False, help='maxiter=4000, 400')
parser.add_argument('-p', default=5, type=int, required=False, help='popsize=2, 10')
parser.add_argument('-m', default=0.5, type=float, required=False, help='mutation=0.5')
parser.add_argument('-r', default=0.3, type=float, required=False, help='recombination=0.3')
parser.add_argument('-e', default=5, type=int, required=False, help='per-capita electricity = 5, 10, 20 MWh/year')
# Scenario Input Parameters
parser.add_argument('-n', default=11, type=int, required=False, help='11,12,... 18, 21, 22, ..., 28, 30')
parser.add_argument('-t', default='HVDC', type=str, required=False, help='HVDC, HVAC')
parser.add_argument('-H', default='True', type=str, required=False, help='Hydrogen Firming=True,False')
parser.add_argument('-b', default='True', type=str, required=False, help='Battery Coopimisation=True,False')
parser.add_argument('-g', default=None, type=float, required=False,help='Maximum Gas Capacity (MW)')
parser.add_argument('-G', default=None, type=float, required=False, help='Maximum annual gas generation (percent of total)')
parser.add_argument('-s', default=None, type=float, required=False, help='Shadow price on carbon emissions')
parser.add_argument('-f', default=1, type=int, required=False, help='Factor scenario=0,1,2,3')
# Additional 'features'
parser.add_argument('-a', default='True', type=str, required=False, help='run post analysis')
parser.add_argument('-l', default='True', type=str, required=False, help='Data includes leap years=True,False')
parser.add_argument('-q', default=0, type=int, required=False, help='Quick test run')
parser.add_argument('-P', default=0, type=int, required=False, help='Use results from previous run')
parser.add_argument('-v', default=1, type=int, required=False, help='Verbose=0,1,2')
args = parser.parse_args()

# scenario = args.s
maxit = args.i
transmissionScenario = args.t
node = args.n
percapita = args.e
gasCapLim = args.g
gasGenLim = args.G 
shadowPrice = args.s
factorScenario = args.f

runAnalysis = args.a
quick = args.q
previous = args.P
verbose = args.v

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
    suffix = '_{}_{}_{}_{}_{}_{}_{}_{}_quick'.format(node,transmissionScenario,percapita,batteryScenario,gasScenario,gasGenLim,shadowPrice,factorScenario)
else:
    suffix = '_{}_{}_{}_{}_{}_{}_{}_{}'.format(node,transmissionScenario,percapita,batteryScenario,gasScenario,gasGenLim,shadowPrice,factorScenario)

from Input import *
from Simulation import Reliability
from Network import Transmission

def F(x):
    '''This is the objective function.'''

    # Initialise the optimisation
    S = Solution(x)

    CGas = np.nan_to_num(np.array(S.CGas))
    
    # Simulation with only baseload
    if verbose > 1: print("Starting deficit calculation 1")
    Deficit_energy1, Deficit_power1, Deficit1, DischargePH1, DischargeB1 = Reliability(S, hydro=baseload, bio=np.zeros(intervals), gas=np.zeros(intervals)) # Sj-EDE(t, j), MW
    Max_deficit1 = yearfunc(Deficit1,np.sum) # MWh per year
    PFlexible_Gas = Deficit1.max() * pow(10, -3) # GW

    # Simulation with only baseload and hydro (cheapest)
    if verbose > 1: print("Starting deficit calculation 2")
    Deficit_energy2, Deficit_power2, Deficit2, DischargePH2, DischargeB2 = Reliability(S, hydro=np.ones(intervals) * CHydro.sum() * pow(10,3), bio=np.zeros(intervals), gas=np.zeros(intervals))
    Max_deficit2 = yearfunc(Deficit2,np.sum) # MWh per year
    PBio_Gas = Deficit2.max() * pow(10, -3) # GW

    # Simulation with only baseload, hydro and bio (next cheapest)
    if verbose > 1: print("Starting deficit calculation 3")
    Deficit_energy3, Deficit_power3, Deficit3, DischargePH3, DischargeB3 = Reliability(S, hydro=np.ones(intervals) * CHydro.sum() * pow(10,3), bio = np.ones(intervals) * CBio.sum() * pow(10, 3), gas=np.zeros(intervals))
    Max_deficit3 = yearfunc(Deficit3,np.sum) # MWh per year
    PGas = Deficit3.max() * pow(10, -3) # GW
    
    # Assume all storage provided by PHES (lowest efficiency i.e. worst cast). Look at maximum generation years for energy penalty function
    GHydro = resolution * (Max_deficit1 - Max_deficit2).max() / efficiencyPH + 8760*CBaseload.sum() * pow(10,3)
    GBio = resolution * (Max_deficit2 - Max_deficit3).max() / efficiencyPH
    GGas = resolution * (Max_deficit3).max() / efficiencyPH
    
    # Power and energy penalty functions
    PenEnergy = (max(0, GHydro - Hydromax) + max(0, GBio - Biomax) + max(0, GGas - Gasmax))*pow(10,3)
    PenPower = (max(0,PFlexible_Gas - (CPeak.sum() + CGas.sum())) + max(0, PBio_Gas - (CBio.sum() + CGas.sum())) + max(0, PGas - CGas.sum()))*pow(10,3)

    # Simulation with baseload, all existing capacity, and all hydrogen
    if verbose > 1: print("Starting deficit calculation final")
    Deficit_energy, Deficit_power, Deficit, DischargePH, DischargeB = Reliability(S, hydro=np.ones(intervals) * CHydro.sum() * pow(10,3), bio = np.ones(intervals) * CBio.sum() * pow(10, 3), gas=np.ones(intervals) * CGas.sum() * pow(10, 3))
    
    # Deficit penalty function
    PenDeficit = max(0, Deficit.sum() * resolution - S.allowance)*pow(10,3)
    # PenDeficit = (yearfunc(Deficit,np.sum) * resolution - S.allowance).clip(0,None).sum()*pow(10,3)

    # Existing capacity generation profiles (MW)
    gas = np.clip(Deficit3, 0, CGas.sum() * pow(10, 3))
    bio = np.clip(Deficit2 - Deficit3, 0, CBio.sum() * pow(10, 3))
    hydro = np.clip(Deficit1 - Deficit2, 0, CHydro.sum() * pow(10, 3)) + baseload

    # Simulation using the existing capacity generation profiles - required for storage average annual discharge+
    Deficit_energy, Deficit_power, Deficit, DischargePH, DischargeB = Reliability(S, hydro=hydro, bio=bio, gas=gas)

    # Discharged energy from storage systems (TWh per year)
    GPHES = DischargePH.sum() * resolution / years * pow(10,-6)
    GBattery = DischargeB.sum() * resolution / years * pow(10,-6)

    # Transmission capacity calculations
    TDC = Transmission(S) if node > 19 else np.zeros((intervals, len(TLoss))) # TDC: TDC(t, k), MW
    CDC = np.amax(abs(TDC), axis=0) * pow(10, -3) # CDC(k), MW to GW

    # Transmission penalty function
    PenDC = max(0, CDC[6] - CDC6max) * pow(10, 3) # GW to MW
    PenDC *= pow(10, 3) # Blow up penalty function 

    # Maximum annual electricity generated by existing capacity (MWh/year)
    GGas = resolution * gas.sum() / years / efficiencyPH 
    GHydro = resolution * hydro.sum() / years / efficiencyPH
    GBio = resolution * bio.sum() / years / efficiencyPH

    # Carbon price penalty ($B per year)
    shadowCost = shadowPrice * gasEmit * GGas * pow(10,-9) if shadowPrice else 0
    
    # Average annual electricity imported through external interconnections
    GInter = sum(sum(S.GInter)) * resolution / years if len(S.GInter) > 0 else 0

    # Levelised cost of electricity calculation
    cost = factor * np.array([sum(S.CPV),sum(S.CWind), GInter * pow(10,-6), sum(S.CPHP), S.CPHS, sum(S.CBP), S.CBS] + list(CDC) + [sum(S.CPV), sum(S.CWind), GHydro * pow(10, -6), GBio * pow(10,-6), CGas.sum(), GGas * pow(10, -6), GPHES, GBattery, 0, 0]) # $b p.a.
    cost = cost.sum() # Cost of all generation 
    loss = np.sum(abs(TDC), axis=0) * TLoss
    loss = loss.sum() * pow(10, -9) * resolution / years # PWh p.a.
    LCOE = cost / abs(energy - loss)
    
    if verbose > 1: print(LCOE)

    PenCarbon = shadowCost / abs(energy-loss) 

    with open('Results/record{}.csv'.format(suffix), 'a', newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(np.append(x,[PenDeficit+PenEnergy+PenPower+PenDC,PenDeficit,PenEnergy,PenPower,PenDC,PenCarbon,LCOE]))

    Func = LCOE + PenDeficit + PenEnergy + PenPower + PenDC + PenCarbon
    
    return Func 

if __name__=='__main__':
    starttime = dt.datetime.now()
    print("Optimisation starts at", starttime)

#    lb = [0.]       * pzones + [0.]     * wzones + contingency_ph   + contingency_b     + [0.]      + [0.]     + [0.]    * inters + [0.] * nodes
#    ub = [10000.]   * pzones + [300]    * wzones + [10000.] * nodes + [10000.] * nodes  + [100000.] + [100000] + [1000.] * inters + [50.] * nodes

    # lb = [0.]       * pzones + contingency_ph   + contingency_b                 + [0.]      + [0.]      + [0.]    * inters + ([0.] * (nodes - inters) + inters * [0])
    # ub = pv_ub + phes_ub + battery_ub + phes_s_ub + battery_s_ub + inter_ub + gas_ub

    lb = [0.] * pzones + [0.] * wzones + contingency_ph  + contingency_b  + [0.]      + [0.]         + [0.] * inters + ([0.] * (nodes - inters) + inters * [0])
    ub = pv_ub         + wind_ub       + phes_ub         + battery_ub     + phes_s_ub + battery_s_ub + inter_ub      + gas_ub

    # start = np.genfromtxt('Results/init.csv', delimiter=',')    

    disp = True if verbose > 0 else False

    if previous:
        prevbest = np.genfromtxt('Results/Optimisation_resultx{}.csv'.format(suffix), delimiter=',')
        prevbest = prevbest.reshape(1,-1)

        prevsols = np.genfromtxt('Results/record{}.csv'.format(suffix), delimiter=',',invalid_raise=False)
        prevsols = prevsols[-10:,:len(lb)] if prevsols.shape[0] > 10 else prevsols

        start = np.concatenate((prevsols,prevbest),0)

        result = differential_evolution(func=F, bounds=list(zip(lb, ub)), tol=0, init=start,
                                    maxiter=args.i, popsize=args.p, mutation=args.m, recombination=args.r,
                                    disp=disp, polish=False, updating='deferred', workers=-1)
    else:
        result = differential_evolution(func=F, bounds=list(zip(lb, ub)), tol=0, # init=start,
                                    maxiter=args.i, popsize=args.p, mutation=args.m, recombination=args.r,
                                    disp=disp, polish=False, updating='deferred', workers=-1)

    with open('Results/Optimisation_resultx{}.csv'.format(suffix), 'w', newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(result.x)

    endtime = dt.datetime.now()
    print("Optimisation took", endtime - starttime)

    if runAnalysis == "True":
        from Fill import Analysis
        Analysis(result.x,suffix)
