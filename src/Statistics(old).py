# Load profiles and generation mix data (LPGM) & energy generation, storage and transmission information (GGTA)
# based on x/capacities from Optimisation and flexible from Dispatch
# Copyright (c) 2019, 2020 Bin Lu, The Australian National University
# Licensed under the MIT Licence
# Correspondence: bin.lu@anu.edu.au

from Input import *
from Simulation import Reliability
from CoSimulation import Resilience
from DeficitSimulation import DeficitSimulation
from Network import Transmission

import numpy as np
import datetime as dt

def Debug(solution):
    """Debugging"""
    
    Load, PV, Wind = (solution.MLoad.sum(axis=1), solution.GPV.sum(axis=1), solution.GWind.sum(axis=1))
    Baseload, Peak = (solution.MBaseload.sum(axis=1), solution.MPeak.sum(axis=1))

    Discharge, Charge, Storage, P2V = (solution.Discharge, solution.Charge, solution.Storage, solution.P2V)
    DischargeD, ChargeD, StorageD = (solution.DischargeD, solution.ChargeD, solution.StorageD)
    Deficit, DeficitD, Spillage = (solution.Deficit, solution.DeficitD, solution.Spillage)

    PHS, DS = solution.CPHS * 1000, sum(solution.CDS) * 1000 # GWh to MWh
    efficiency, efficiencyD = solution.efficiency, solution.efficiencyD

    for i in range(intervals):
        # Energy supply-demand balance
        assert abs(Load[i] + Charge[i] + ChargeD[i] + Spillage[i]
                   - PV[i] - Wind[i] - Baseload[i] - Peak[i] - Discharge[i] + P2V[i] - Deficit[i]) <= 1

        # Discharge, Charge and Storage
        if i==0:
            assert abs(Storage[i] - 0.5 * PHS + Discharge[i] * resolution - Charge[i] * resolution * efficiency) <= 1
            assert abs(StorageD[i] - 0.5 * DS + DischargeD[i] * resolution - ChargeD[i] * resolution * efficiencyD) <= 1
        else:
            assert abs(Storage[i] - Storage[i - 1] + Discharge[i] * resolution - Charge[i] * resolution * efficiency) <= 1
            assert abs(StorageD[i] - StorageD[i - 1] + DischargeD[i] * resolution - ChargeD[i] * resolution * efficiencyD) <= 1

        # Capacity: PV, wind, Discharge, Charge and Storage
        # try:
        assert np.amax(PV) <= sum(solution.CPV) * 1000, print(np.amax(PV) - sum(solution.CPV) * 1000)
        assert np.amax(Wind) <= sum(solution.CWind) * 1000, print(np.amax(Wind) - sum(solution.CWind) * 1000)

        assert np.amax(Discharge) <= sum(solution.CPHP) * 1000, print(np.amax(Discharge) - sum(solution.CPHP) * 1000)
        assert np.amax(Charge) <= sum(solution.CPHP) * 1000, print(np.amax(Charge) - sum(solution.CPHP) * 1000)
        assert np.amax(Storage) <= solution.CPHS * 1000, print(np.amax(Storage) - solution.CPHS * 1000)
        assert np.amax(DischargeD) <= sum(solution.CDP) * 1000, print(np.amax(DischargeD) - sum(solution.CDP) * 1000)
        assert np.amax(ChargeD) <= sum(solution.CDP) * 1000, print(np.amax(ChargeD) - sum(solution.CDP) * 1000)
        assert np.amax(StorageD) <= sum(solution.CDS) * 1000, print(np.amax(StorageD) - sum(solution.CDS) * 1000)
        # except AssertionError:
        #     pass

    print('Debugging: everything is ok')

    return True

def LPGM(solution, RSim=None):
    """Load profiles and generation mix data"""

    C = np.stack([(solution.MLoad + solution.MLoadD).sum(axis=1), (solution.MLoad + solution.MChargeD + solution.MP2V).sum(axis=1),
                  solution.MHydro.sum(axis=1), solution.MBio.sum(axis=1), solution.GPV.sum(axis=1), solution.GWind.sum(axis=1), 
                  solution.GWindR.sum(axis=1),solution.Discharge, solution.Deficit, -1 * solution.Spillage, -1 * solution.Charge,
                  solution.Storage, solution.RDeficit.sum(axis=1), solution.RStorage.sum(axis=1),
                  solution.RDischarge.sum(axis=1), -1*solution.RCharge.sum(axis=1),-1*solution.RSpillage.sum(axis=1),
                  solution.FQ, solution.NQ, solution.NS, solution.NV, solution.AS, solution.SW, solution.TV])
    C = np.around(C.T)

    datentime = np.array([(dt.datetime(firstyear, 1, 1, 0, 0) + x * dt.timedelta(minutes=60 * resolution)).strftime('%a -%d %b %Y %H:%M') for x in range(intervals)])

    header = 'Date & time,Operational demand (original),Operational demand (adjusted),' \
             'Hydropower,Biomass,Solar photovoltaics,Wind,eventWind,' \
             'PHES-power,Energy deficit,Energy spillage,PHES-Charge,PHES-Storage,' \
             'eventDeficit,eventStorage,eventPHES-power,eventPHES-Charge,eventSpillage,' \
             'FNQ-QLD,NSW-QLD,NSW-SA,NSW-VIC,NT-SA,SA-WA,TAS-VIC'

    if RSim is None: 
        C = np.insert(C.astype('str'), 0, datentime, axis=1)
        np.savetxt('Results/S'+suffix, C, fmt='%s', delimiter=',', header=header, comments='')
    else: 
        C = np.around(np.hstack((C, (solution.MHydroR.sum(axis=1)+solution.MBioR.sum(axis=1)).reshape(-1,1))))
        header += ',eventH&B'
        C = np.insert(C.astype('str'), 0, datentime, axis=1)
        C = C[max(0, RSim[1] - solution.eventDur - 96):RSim[1] + 97, :] #2 days before event + 2 day after 
        np.savetxt('Results/SDeficit{}-'.format(RSim[0])+suffix, C, fmt='%s', delimiter=',', header=header, comments='')


    if scenario>=21 and RSim is None:
        header = 'Date & time,Operational demand (original),Operational demand (adjusted),' \
                 'Hydropower,Biomass,Solar photovoltaics,Wind,eventWind,' \
                 'PHES-power,Energy deficit,Energy spillage,Transmission,PHES-Charge,' \
                 'PHES-Storage'

        Topology = solution.Topology[np.where(np.in1d(np.array(['FNQ', 'NSW', 'NT', 'QLD', 'SA', 'TAS', 'VIC', 'WA']), coverage) == True)[0]]

        for j in range(nodes):
            C = np.stack([(solution.MLoad + solution.MLoadD)[:, j], (solution.MLoad + solution.MChargeD + solution.MP2V)[:, j],
                          solution.MHydro[:, j], solution.MBio[:, j], solution.MPV[:, j], solution.MWind[:, j], solution.MWindR[:, j],
                          solution.MDischarge[:, j], solution.MDeficit[:, j], -1 * solution.MSpillage[:, j], Topology[j], -1 * solution.MCharge[:, j],
                          solution.MStorage[:, j]])
            C = np.around(C.T)
            C = np.insert(C.astype('str'), 0, datentime, axis=1)
            np.savetxt('Results/S{}'.format(Nodel[j])+suffix, C, fmt='%s', delimiter=',', header=header, comments='')

    print('Load profiles and generation mix is produced.')

    return True

def GGTA(solution, verbose=False):
    """GW, GWh, TWh p.a. and A$/MWh information"""

    factor = np.genfromtxt('Data/factor.csv', dtype=None, delimiter=',', encoding=None)
    factor = dict(factor)

    CPV, CWind, CPHP, CPHS = (sum(solution.CPV), sum(solution.CWind), sum(solution.CPHP), solution.CPHS) # GW, GWh
    CapHydro, CapBio = CHydro.sum(), CBio.sum() # GW
    CapHydrobio = CapHydro + CapBio

    GPV, GWind, GHydro, GBio = map(lambda x: x * 0.000_001 * resolution / years, (solution.GPV.sum(), solution.GWind.sum(), solution.MHydro.sum(), solution.MBio.sum())) # TWh p.a.
    GHydrobio = GHydro + GBio
    CFPV = GPV / CPV / 8.76 if CPV > 0 else 0
    CFWind = GWind / CWind / 8.76 if CWind > 0 else 0

    CostPV = factor['PV'] * CPV # A$b p.a.
    CostWind = factor['Wind'] * CWind # A$b p.a.
    CostHydro = factor['Hydro'] * GHydro # A$b p.a.
    CostBio = factor['Hydro'] * GBio # A$b p.a.
    CostPH = factor['PHP'] * CPHP + factor['PHS'] * CPHS # A$b p.a.
    if scenario>=21:
        CostPH -= factor['LegPH']

    CostDC = np.array([factor['FQ'], factor['NQ'], factor['NS'], factor['NV'], factor['AS'], factor['SW'], factor['TV']])
    CostDC = (CostDC * solution.CDC).sum() # A$b p.a.
    if scenario>=21:
        CostDC -= factor['LegINTC']

    CostAC = factor['ACPV'] * CPV + factor['ACWind'] * CWind # A$b p.a.

    Energy = (MLoad + MLoadD).sum() * 0.000_000_001 * resolution / years # PWh p.a.
    Loss = np.sum(abs(solution.TDC), axis=0) * DCloss
    Loss = Loss.sum() * 0.000_000_001 * resolution / years # PWh p.a.

    LCOE = (CostPV + CostWind + CostHydro + CostBio + CostPH + CostDC + CostAC) / (Energy - Loss)
    LCOG = (CostPV + CostWind + CostHydro + CostBio) * 1000 / (GPV + GWind + GHydro + GBio)
    LCOGP = CostPV * 1000 / GPV if GPV!=0 else 0
    LCOGW = CostWind * 1000 / GWind if GWind!=0 else 0
    LCOGH = CostHydro * 1000 / GHydro if GHydro!=0 else 0
    LCOGB = CostBio * 1000 / GBio if GBio!=0 else 0

    LCOB = LCOE - LCOG
    LCOBS = CostPH / (Energy - Loss)
    LCOBT = (CostDC + CostAC) / (Energy - Loss)
    LCOBL = LCOB - LCOBS - LCOBT

    if verbose: 
        print('Levelised costs of electricity:')
        print('\u2022 LCOE:', LCOE)
        print('\u2022 LCOG:', LCOG)
        print('\u2022 LCOB:', LCOB)
        print('\u2022 LCOG-PV:', LCOGP, '(%s)' % CFPV)
        print('\u2022 LCOG-Wind:', LCOGW, '(%s)' % CFWind)
        print('\u2022 LCOG-Hydro:', LCOGH)
        print('\u2022 LCOG-Bio:', LCOGB)
        print('\u2022 LCOB-Storage:', LCOBS)
        print('\u2022 LCOB-Transmission:', LCOBT)
        print('\u2022 LCOB-Spillage & loss:', LCOBL)

    D = np.zeros((1, 22))
    D[0, :] = ([Energy * 1000, Loss * 1000, CPV, GPV, CWind, GWind, CapHydrobio, GHydrobio, CPHP, CPHS] 
              + list(solution.CDC) 
              + [LCOE, LCOG, LCOBS, LCOBT, LCOBL])

    np.savetxt('Results/GGTA'+suffix, D, fmt='%f', delimiter=',')
    print('Energy generation, storage and transmission information is produced.')

    return True

def TransmissionFactors(solution, flexible, RFlexible=None):
    
    if scenario>=21:
        solution.TDC= Transmission(solution, True, RFlexible is not None) # TDC(t, k), MW
    else:
        solution.TDC = np.zeros((intervals, len(DCloss))) # TDC(t, k), MW
        
        solution.MPeak = np.tile(flexible, (nodes, 1)).T # MW
        if RFlexible is not None:
            solution.MPeakR = np.tile(RFlexible, (nodes, 1)).T
        solution.MBaseload = GBaseload.copy() # MW

        solution.MPV = solution.GPV.sum(axis=1).reshape(-1,1) if solution.GPV.shape[1]>0 else np.zeros((intervals, 1), dtype=np.float64)
        solution.MWind = solution.GWind.sum(axis=1).reshape(-1,1) if solution.GWind.shape[1]>0 else np.zeros((intervals, 1), dtype=np.float64)

        solution.MDischarge = np.tile(solution.Discharge, (nodes, 1)).T
        solution.MDeficit = np.tile(solution.Deficit, (nodes, 1)).T
        solution.MCharge = np.tile(solution.Charge, (nodes, 1)).T
        solution.MStorage = np.tile(solution.Storage, (nodes, 1)).T
        solution.MSpillage = np.tile(solution.Spillage, (nodes, 1)).T

        solution.MChargeD = np.tile(solution.ChargeD, (nodes, 1)).T
        solution.MP2V = np.tile(solution.P2V, (nodes, 1)).T
            
    solution.CDC = np.amax(abs(solution.TDC), axis = 0) * 0.001
    solution.FQ, solution.NQ, solution.NS, solution.NV, solution.AS, solution.SW, solution.TV = map(lambda k: solution.TDC[:, k], range(solution.TDC.shape[1]))
    solution.Topology = np.array(
        [-1 *solution.FQ, -1 *(solution.NQ +solution.NS +solution.NV), -1 *solution.AS ,solution.FQ +solution.NQ, 
         solution.NS + solution.AS -solution.SW, -1 *solution.TV,solution.NV +solution.TV,solution.SW])

    solution.MHydro = np.tile(CHydro - CBaseload, (intervals, 1)) * 1000 # GW to MW
    solution.MHydro = np.minimum(solution.MHydro, solution.MPeak)
    solution.MBio = solution.MPeak - solution.MHydro
    solution.MHydro += solution.MBaseload

    if RFlexible is not None:
        solution.MHydroR = np.tile(CHydro - CBaseload, (intervals, 1)) * 1000 # GW to MW
        solution.MHydroR = np.minimum(solution.MHydroR, solution.MPeakR)
        solution.MBioR = solution.MPeakR - solution.MHydroR
        solution.MHydroR += solution.MBaseload
        
def Information(x, flexible, resilience=False):
    """Dispatch: Statistics.Information(x, Flex)"""

    start = dt.datetime.now()
    print("Statistics start at", start)

    S = Solution(x)
    Resilience(S, flexible=flexible, output=True)
    TransmissionFactors(S, flexible)
    
    if resilience is not True:
        Debug(S)
        GGTA(S) 
    LPGM(S)
    end = dt.datetime.now()
    print("Statistics took", end - start)

    return True

def DeficitInformation(capacities, flexible, NDeficitAnalysis=None):
    start =  dt.datetime.now()
    print("Deficit Statistics start at", start)
    
    S = Solution(capacities)

    DeficitAnalysis(capacities, flexible, NDeficitAnalysis)

    end = dt.datetime.now()
    print("Deficit Statistics took", end - start)
    return True
   
def DeficitAnalysis(capacities, flexible, N=1):   
    if N is None: 
        return True
    S = Solution(capacities)
    Deficit, DeficitD, RDeficit, RDeficitD = Resilience(S, flexible=flexible)
    topNDeficitIndx = np.flip(np.argpartition(RDeficit[:,0], -N)[-N:])
    
    for n, indx in enumerate(topNDeficitIndx):
        S = Solution(capacities)
        DeficitSimulation(S, flexible, CPeak.sum()*1000, RSim=indx,output=True)
        TransmissionFactors(S, S.flexible, S.RFlexible)
        LPGM(S, (n, indx))
    return True 

    
if __name__ == '__main__': 
    costCapacities = np.genfromtxt('CostOptimisationResults/Optimisation_resultx{}-None.csv'.format(scenario), delimiter=',')
    capacities = np.genfromtxt('Results/Optimisation_resultx'+suffix, delimiter=',')
    flexible = np.genfromtxt('Results/Dispatch_Flexible'+suffix, delimiter=',')
    
    S = Solution(capacities)
    S._evaluate()
    print(S.eventDeficit, S.cost, S.penalties)
    
    if eventZone != 'None':
        DeficitInformation(capacities, flexible, 1)
    
    Information(capacities, flexible)