# Modelling input and assumptions
# Copyright (c) 2019, 2020 Bin Lu, The Australian National University
# Licensed under the MIT Licence
# Correspondence: bin.lu@anu.edu.au

import numpy as np
from Optimisation import scenario, node, percapita

###### NODAL LISTS ######
Nodel = np.array(['ME', 'SB', 'TE', 'PA', 'SE', 'PE', 'JO', 'KT', 'KD', 'SW', 'TH', 'IN', 'PH'])
PVl =   np.array(['ME']*1 + ['SB']*1 + ['TE']*1 + ['PA']*1 + ['SE']*1 + ['PE']*1 + ['JO']*1 + ['KT']*1 + ['KD']*1 + ['SW']*1)
#Windl = np.array(['ME']*1 + ['SB']*1 + ['TE']*1 + ['PA']*1 + ['SE']*1 + ['PE']*1 + ['JO']*1 + ['KT']*1 + ['KD']*1 + ['SW']*1)
Interl = np.array(['TH']*1 + ['IN']*1 + ['PH']*1) if node=='APG_Full' else np.array([]) # Add external interconnections if ASEAN Power Grid scenario
resolution = 1

###### DATA IMPORTS ######
MLoad = np.genfromtxt('Data/electricity{}.csv'.format(percapita), delimiter=',', skip_header=1, usecols=range(4, 4+len(Nodel))) # EOLoad(t, j), MW
TSPV = np.genfromtxt('Data/pv.csv', delimiter=',', skip_header=1, usecols=range(4, 4+len(PVl))) # TSPV(t, i), MW
#TSWind = np.genfromtxt('Data/wind.csv', delimiter=',', skip_header=1, usecols=range(4, 4+len(Windl))) # TSWind(t, i), MW

assets = np.genfromtxt('Data/assets.csv', dtype=None, delimiter=',', encoding=None)[1:, 3:].astype(np.float)
CHydro, CBio = [assets[:, x] * pow(10, -3) for x in range(assets.shape[1])] # CHydro(j), MW to GW
constraints = np.genfromtxt('Data/constraints.csv', dtype=None, delimiter=',', encoding=None)[1:, 3:].astype(np.float)
EHydro, EBio = [constraints[:, x] for x in range(assets.shape[1])] # GWh per year
CBaseload = np.array([0, 1, 0.26, 0.01, 0, 0.01, 0, 0.01, 0, 0.78, 0, 0, 0]) * EHydro / 8760 # 24/7, GW # Run-of-river percentage
CPeak = CHydro + CBio - CBaseload # GW

baseload = np.ones(MLoad.shape[0]) * CBaseload.sum() * 1000 # GW to MW

###### CONSTRAINTS ######
# Energy constraints
Hydromax = EHydro.sum() * pow(10,3) # GWh to MWh per year
Biomax = EBio.sum() * pow(10,3) # GWh to MWh per year

# Transmission constraints
externalImports = 0.05 if node=='APG_Full' else 0
CDC9max, CDC10max, CDC11max = 3 * [externalImports * MLoad.sum() / MLoad.shape[0] / 1000] # 5%: External interconnections: THKD, INSE, PHSB, MW to GW

###### TRANSMISSION LOSSES ######
if scenario=='HVDC':
    # HVDC backbone scenario
    dc_flags = np.array([True,True,True,True,True,True,True,True,True,True,True,True])
    
elif scenario=='HVAC':
    # HVAC backbone scenario
    dc_flags = np.array([False,False,False,False,False,False,False,False,True,True,True,True])
    
TLoss = []
TDistances = [135, 165, 90, 170, 175, 675, 135, 135, 935, 200, 260, 450] # ['KDPE', 'TEPA', 'SEME', 'MEJO', 'PESE', 'SBSW', 'KTTE', 'PASE', 'JOSW', 'THKD', 'INSE', 'PHSB']
for i in range(0,len(dc_flags)):
    TLoss.append(TDistances[i]*0.03) if dc_flags[i] else TLoss.append(TDistances[i]*0.07)
TLoss = np.array(TLoss)* pow(10, -3)

###### STORAGE SYSTEM CONSTANTS ######
efficiencyPH = 0.8
efficiencyB = 0.9

###### COST FACTORS ######
factor = np.genfromtxt('Data/factor.csv', delimiter=',', usecols=1)

###### SIMULATION PERIOD ######
firstyear, finalyear, timestep = (2012, 2021, 1)

###### SCENARIO ADJUSTMENTS #######
# Node values
if 'APG_Full' == node:
    coverage = Nodel

else:
    if 'APG_PMY_Only' == node:
        coverage = np.array(['JO', 'KD', 'KT', 'ME', 'PA', 'PE', 'SE', 'TE'])
    elif 'APG_BMY_Only' == node:
        coverage = np.array(['SB', 'SW'])
    elif 'APG_MY_Isolated' == node:
        coverage = np.array(['JO', 'KD', 'KT', 'ME', 'PA', 'PE', 'SB', 'SW', 'SE', 'TE'])
    else:
        coverage = np.array([node])

    MLoad = MLoad[:, np.where(np.in1d(Nodel, coverage)==True)[0]]
    TSPV = TSPV[:, np.where(np.in1d(Nodel, coverage)==True)[0]]
    #TSWind = TSWind[:, np.where(np.in1d(Nodel, coverage)==True)[0]]

    CBaseload = CBaseload[np.where(np.in1d(Nodel, coverage)==True)[0]]
    CHydro = CHydro[np.where(np.in1d(Nodel, coverage)==True)[0]]
    CBio = CBio[np.where(np.in1d(Nodel, coverage)==True)[0]]
    CPeak = CHydro + CBio - CBaseload # GW

    EHydro, EBio = [x[np.where(np.in1d(Nodel, coverage)==True)[0]] for x in (EHydro, EBio)]

    Hydromax = EHydro.sum() * pow(10,3) # GWh to MWh per year
    Biomax = EBio.sum() * pow(10,3) # GWh to MWh per year

    baseload = np.ones(MLoad.shape[0]) * CBaseload.sum() * 1000 # GW to MW

    Nodel, PVl, Interl = [x[np.where(np.in1d(x, coverage)==True)[0]] for x in (Nodel, PVl, Interl)]
#    Nodel, PVl, Windl, Interl = [x[np.where(np.in1d(x, coverage)==True)[0]] for x in (Nodel, PVl, Windl, Interl)]

# Scenario values
if scenario == 'HVAC':
    factor = np.genfromtxt('Data/factor_hvac.csv', delimiter=',', usecols=1)

###### DECISION VARIABLE LIST INDEXES ######
intervals, nodes = MLoad.shape
years = int(resolution * intervals / 8760)
pzones = TSPV.shape[1] # Solar PV and wind sites
# wzones = TSWind.shape[1]
# pidx, widx, phidx, bidx = (pzones, pzones + wzones, pzones + wzones + nodes, pzones + wzones + 2*nodes) # Index of solar PV (sites), wind (sites), pumped hydro power (service areas), and battery power (service areas)
pidx, phidx, bidx = (pzones, pzones + nodes, pzones + 2*nodes) # Index of solar PV (sites), wind (sites), pumped hydro power (service areas), and battery power (service areas)
inters = len(Interl) # Number of external interconnections
iidx = bidx + 2 + inters # Index of external interconnections, noting pumped hydro energy (network) and battery energy (network) decision variables after the index of battery power
gidx = iidx + nodes # Index of hydrogen (service areas)

###### NETWORK CONSTRAINTS ######
energy = (MLoad).sum() * pow(10, -9) * resolution / years # PWh p.a.
contingency_ph = list(0.25 * (MLoad).max(axis=0) * pow(10, -3)) # MW to GW
contingency_b = list(0.1 * (MLoad).max(axis=0) * pow(10, -3)) # MW to GW
#manage = 0 # weeks
#allowance = MLoad.sum(axis=1).max() * 0.05 * manage * 168 * efficiencyPH # MWh
allowance = 0 # Allowable annual deficit, MWh

GBaseload = np.tile(CBaseload, (intervals, 1)) * pow(10, 3) # GW to MW
Gasmax = energy * 2 * pow(10,9) # MWh

class Solution:
    """A candidate solution of decision variables CPV(i), CWind(i), CPHP(j), S-CPHS(j)"""

    def __init__(self, x):
        self.x = x
        self.MLoad = MLoad
        self.intervals, self.nodes = (intervals, nodes)
        self.resolution = resolution
        self.baseload = baseload

        self.CPV = list(x[: pidx]) # CPV(i), GW
#        self.CWind = list(x[pidx: widx]) # CWind(i), GW
        self.GPV = TSPV * np.tile(self.CPV, (intervals, 1)) * pow(10, 3) # GPV(i, t), GW to MW
#        self.GWind = TSWind * np.tile(self.CWind, (intervals, 1)) * pow(10, 3) # GWind(i, t), GW to MW

#        self.CPHP = list(x[widx: phidx]) # CPHP(j), GW
        self.CPHP = list(x[pidx: phidx]) # CPHP(j), GW
        self.CBP = list(x[phidx: bidx])
        self.CPHS = x[bidx] # S-CPHS(j), GWh
        self.CBS = x[bidx+1] 
        self.efficiencyPH = efficiencyPH
        self.efficiencyB = efficiencyB

        self.CInter = list(x[bidx+2: iidx]) if node == 'APG_Full' else len(Interl)*[0] #CInter(j), GW
        self.GInter = np.tile(self.CInter, (intervals, 1)) * pow(10,3) # GInter(j, t), GW to MW

        self.CGas = list(x[iidx: ]) # GW

        self.Nodel, self.PVl, self.Interl = (Nodel, PVl, Interl)
#        self.Windl = Windl
        self.node = node
        self.scenario = scenario
        self.allowance = allowance
        self.coverage = coverage
        self.TLoss = TLoss

        self.CBaseload, self.CPeak = (CBaseload, CPeak)
        self.CHydro = CHydro # GW
        self.CBio = CBio # GW

    def __repr__(self):
        """S = Solution(list(np.ones(64))) >> print(S)"""
        return 'Solution({})'.format(self.x)