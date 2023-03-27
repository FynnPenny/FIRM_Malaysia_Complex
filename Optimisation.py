# To optimise the configurations of energy generation, storage and transmission assets
# Copyright (c) 2019, 2020 Bin Lu, The Australian National University
# Licensed under the MIT Licence
# Correspondence: bin.lu@anu.edu.au

from scipy.optimize import differential_evolution
from argparse import ArgumentParser
import datetime as dt
import csv

parser = ArgumentParser()
parser.add_argument('-i', default=400, type=int, required=False, help='maxiter=4000, 400')
parser.add_argument('-p', default=1, type=int, required=False, help='popsize=2, 10')
parser.add_argument('-m', default=0.5, type=float, required=False, help='mutation=0.5')
parser.add_argument('-r', default=0.3, type=float, required=False, help='recombination=0.3')
parser.add_argument('-e', default=5, type=int, required=False, help='per-capita electricity = 5, 10, 20 MWh/year')
parser.add_argument('-n', default='APG', type=int, required=False, help='APG, MY1, SB, SW...')
parser.add_argument('-s', default='HVDC', type=int, required=False, help='HVDC, HVAC')
args = parser.parse_args()

scenario = args.s
node = args.n
percapita = args.e

from Input import *
from Simulation import Reliability
from Network import Transmission

def F(x):
    """This is the objective function."""

    ########## Separate the hydro and bio G for the cost calculations
    ###############################################################
    S = Solution(x)

    CGas = np.nan_to_num(np.array(S.CGas))

    Deficit_energy1, Deficit_power1, Deficit1, Discharge1 = Reliability(S, hydro=np.ones(intervals) * baseload.sum(), gas=np.zeros(intervals)) # Sj-EDE(t, j), MW
    Max_deficit1 = np.reshape(Deficit1, (-1, 8760)).sum(axis=-1) # MWh per year
    PHydro_Gas = Deficit_power1.max() * pow(10, -3) # GW
    
    Deficit_energy2, Deficit_power2, Deficit2, Discharge2 = Reliability(S, hydro=np.ones(intervals) * CHydro.sum() * pow(10, 3), gas=np.zeros(intervals))
    Max_deficit2 = np.reshape(Deficit2, (-1, 8760)).sum(axis=-1) # MWh per year
    PGas = Deficit_power2.max() * pow(10, -3) # GW
    
    GHydro = (Max_deficit1 - Max_deficit2).max() / 0.8
    GBio =
    GGas = Max_deficit2.max() / 0.8
    
    PenEnergy = max(0, GHydrobio - Flexiblemax) + max(0, GGas - Gasmax)
    PenPower = max(0,PHydro_Gas - (CPeak.sum() + CGas.sum())) + max(0, PGas - CGas.sum())
    
    Deficit_energy, Deficit_power, Deficit, Discharge = Reliability(S, hydro=np.ones(intervals) * CHydro.sum() * pow(10, 3), gas=np.ones(intervals) * CGas.sum() * pow(10, 3))
    PenDeficit = max(0, Deficit.sum() * resolution - S.allowance)

    gas = np.clip(Deficit2, 0, CGas.sum() * pow(10, 3))
    hydro = np.clip(Deficit1 - Deficit2, 0, CPeak.sum() * pow(10, 3)) + np.ones(intervals) * baseload.sum()

    Deficit_energy, Deficit_power, Deficit, Discharge = Reliability(S, hydro=hydro, gas=gas)

    GPHES = Discharge.sum() * resolution / years * pow(10,-6) # TWh per year

    TDC = Transmission(S) if 'Super' in node else np.zeros((intervals, len(DCloss))) # TDC: TDC(t, k), MW
    CDC = np.amax(abs(TDC), axis=0) * pow(10, -3) # CDC(k), MW to GW
    PenDC = max(0, CDC[11] - CDC11max) * pow(10, 3) # GW to MW
    PenDC += max(0, CDC[12] - CDC12max) * pow(10, 3) # GW to MW
    PenDC += max(0, CDC[13] - CDC13max) * pow(10, 3) # GW to MW
    PenDC *= pow(10, 3) # GW to MW

    GGas = Deficit2.sum() / years / 0.8
    GHydro = Deficit1.sum() / years / 0.8 - GGas
    GBio = 

    # Add bio costs in #####################################
    cost = factor * np.array([sum(S.CPV), sum(S.CWind), sum(S.CInter), sum(S.CPHP), S.CPHS] + list(CDC) + [sum(S.CPV), sum(S.CWind), GHydro * pow(10, -6), CGas.sum(), GGas * pow(10, -6), GPHES, -1, -1]) # $b p.a.
    cost = cost.sum()
    loss = np.sum(abs(TDC), axis=0) * DCloss
    loss = loss.sum() * pow(10, -9) * resolution / years # PWh p.a.
    LCOE = cost / abs(energy - loss)
    
    with open('Results/record.csv', 'a', newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(np.append(x,[PenDeficit+PenEnergy+PenPower+PenDC,LCOE]))

    Func = LCOE + PenDeficit + PenEnergy + PenPower + PenDC
    
    return Func

if __name__=='__main__':
    starttime = dt.datetime.now()
    print("Optimisation starts at", starttime)

    lb = [0.]       * pzones + [0.]     * wzones + contingency_ph   + contingency_b     + [0.]      + [0.]    * inters + [0.] * nodes
    ub = [10000.]   * pzones + [300]    * wzones + [10000.] * nodes + [10000.] * nodes  + [100000.] + [1000.] * inters + [50.] * nodes

    # start = np.genfromtxt('Results/init.csv', delimiter=',')

    result = differential_evolution(func=F, bounds=list(zip(lb, ub)), tol=0, # init=start,
                                    maxiter=args.i, popsize=args.p, mutation=args.m, recombination=args.r,
                                    disp=True, polish=False, updating='deferred', workers=-1)

    with open('Results/Optimisation_resultx.csv', 'w', newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(result.x)

    endtime = dt.datetime.now()
    print("Optimisation took", endtime - starttime)

    from Dispatch import Analysis
    # Analysis(result.x)
