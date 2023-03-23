# Modelling input and assumptions
# Copyright (c) 2019, 2020 Bin Lu, The Australian National University
# Licensed under the MIT Licence
# Correspondence: bin.lu@anu.edu.au

import numpy as np
from Optimisation import scenario

###### NODAL LISTS ######
Nodel = np.array(['JO', 'KD', 'KT', 'ME', 'PA', 'PE', 'SB', 'SW', 'SE', 'TE'])
PVl =   np.array(['JO']*1 + ['KD']*1 + ['KT']*1 + ['ME']*1 + ['PA']*1 + ['PE']*1 + ['SB']*1 + ['SW']*1 + ['SE']*1, ['TE']*1)
Windl = np.array(['JO']*1 + ['KD']*1 + ['KT']*1 + ['ME']*1 + ['PA']*1 + ['PE']*1 + ['SB']*1 + ['SW']*1 + ['SE']*1, ['TE']*1)
Interl = np.array(['KD']*1 + ['SB']*1 + ['SE']*1) if node=='APG' else np.array([]) # Add external interconnections if ASEAN Power Grid scenario
resolution = 1

###### DATA IMPORTS ######
MLoad = np.genfromtxt('Data/electricity{}.csv'.format(percapita), delimiter=',', skip_header=1) # EOLoad(t, j), MW
TSPV = np.genfromtxt('Data/pv.csv', delimiter=',', skip_header=1, usecols=range(4, 4+len(PVl))) # TSPV(t, i), MW
TSWind = np.genfromtxt('Data/wind.csv', delimiter=',', skip_header=1, usecols=range(4, 4+len(Windl))) # TSWind(t, i), MW

assets = np.genfromtxt('Data/assets.csv', dtype=None, delimiter=',', encoding=None)[1:, 3:].astype(np.float)
CHydro, CBio = [assets[:, x] * pow(10, -3) for x in range(assets.shape[1])] # CHydro(j), MW to GW
CBaseload = np.array([1.0, 0]) # 24/7, GW #FIX: UPDATE TO RUN-OF-RIVER PERCENTAGE
CPeak = CHydro + CBio - CBaseload # GW

###### CONSTRAINTS ######
# Energy constraints
constraints = np.genfromtxt('Data/constraints.csv', dtype=None, delimiter=',', encoding=None)[1:, 3:].astype(np.float)

# Transmission constraints
externalImports = 0.05 if node=='APG' else 0
CDC11max, CDC12max, CDC13max = 3 * [externalImports * MLoad.sum() / MLoad.shape[0] / 1000] # 5%: External interconnections: KDTH, SEIN, SBPH, MW to GW


###### TRANSMISSION LOSSES ######
if scenario=='HVDC':
    # HVDC backbone scenario
    DCloss = np.array([205, 165, 90, 170, 175, 675, 135, 135, 137, 935]) * 0.03 * pow(10, -3) # [KTPE, TEPA, SEME, MEJO, PESE, SBSW, KTTE, PASE, KDPE, JOSW]
elif scenario=='HVAC':
    # HVAC backbone scenario
    DCloss = np.array([i*0.07 for i in [205, 165, 90, 170, 175, 675, 135, 135, 137]] + 0.03*[935]) * 0.03 * pow(10, -3) # [KTPE, TEPA, SEME, MEJO, PESE, SBSW, KTTE, PASE, KDPE, JOSW]

###### STORAGE SYSTEM CONSTANTS ######
efficiencyPH = 0.8
efficiencyB = 0.9

###### COST FACTORS ######
factor = np.genfromtxt('Data/factor.csv', delimiter=',', usecols=1)

###### SIMULATION PERIOD ######
firstyear, finalyear, timestep = (2012, 2021, 1)

###### SCENARIO ADJUSTMENTS #######
if 'APG' not in node:
    MLoad = MLoad[:, np.where(Nodel==node)[0]]
    baseload = baseload[np.where(Nodel==node)[0]]
    TSPV = TSPV[:, np.where(PVl==node)[0]]
    TSWind = TSWind[:, np.where(Windl==node)[0]]
    CHydro = CHydro[np.where(Nodel==node)[0]]
    CBio = CBio[np.where(Nodel==node)[0]]

###### DECISION VARIABLE LIST INDEXES ######
intervals, nodes = MLoad.shape
years = int(resolution * intervals / 8760)
pzones, wzones = (TSPV.shape[1], TSWind.shape[1]) # Solar PV and wind sites
pidx, widx, phidx, bidx = (pzones, pzones + wzones, pzones + wzones + nodes, pzones + wzones + 2*nodes) # Index of solar PV (sites), wind (sites), pumped hydro power (service areas), and battery power (service areas)
inters = len(Interl) # Number of external interconnections
iidx = bidx + 2 + inters # Index of external interconnections, noting pumped hydro energy (network) and battery energy (network) decision variables after the index of battery power
gidx = iidx + nodes # Index of hydrogen (service areas)

###### NETWORK CONSTRAINTS ######
energy = (MLoad).sum() * pow(10, -9) * resolution / years # PWh p.a.
contingency = list(0.25 * (MLoad).max(axis=0) * pow(10, -3)) # MW to GW
manage = 0 # weeks
allowance = MLoad.sum(axis=1).max() * 0.05 * manage * 168 * efficiency # MWh

GBaseload = np.tile(CBaseload, (intervals, 1)) * pow(10, 3) # GW to MW
Existing_max = energy * 0.1 * pow(10, 9) # Max contribution from hydro and other renewables: 10% of annual electricity demand in MWh
Gasmax = energy * 2 * pow(10,9) # MWh

class Solution:
    """A candidate solution of decision variables CPV(i), CWind(i), CPHP(j), S-CPHS(j)"""

    def __init__(self, x):
        self.x = x
        self.MLoad = MLoad
        self.intervals, self.nodes = (intervals, nodes)
        self.resolution = resolution
        #self.baseload = baseload

        self.CPV = list(x[: pidx]) # CPV(i), GW
        self.CWind = list(x[pidx: widx]) # CWind(i), GW
        self.GPV = TSPV * np.tile(self.CPV, (intervals, 1)) * pow(10, 3) # GPV(i, t), GW to MW
        self.GWind = TSWind * np.tile(self.CWind, (intervals, 1)) * pow(10, 3) # GWind(i, t), GW to MW

        self.CPHP = list(x[widx: phidx]) # CPHP(j), GW
        self.CBP = list(x[phidx: bidx])
        self.CPHS = x[bidx] # S-CPHS(j), GWh
        self.CBS = x[bidx+1] 
        self.efficiencyPH = efficiencyPH
        self.efficiencyB = efficiencyB

        self.CInter = list(x[bidx+2: iidx]) if node == 'APG' else [0] #CInter(j), GW
        self.GInter = np.tile(self.CInter, (intervals, 1)) * pow(10,3) # GInter(j, t), GW to MW

        self.CGas = list(x[iidx: gidx]) # GW

        self.Nodel, self.PVl, self.Windl, self.Interl = (Nodel, PVl, Windl, Interl)
        self.node = node
        self.scenario = scenario
        self.allowance = allowance

        self.GBaseload, self.CPeak = (GBaseload, CPeak)
        self.CHydro = CHydro # GW, GWh
        self.CBio = CBio # GW, GWh

    def __repr__(self):
        """S = Solution(list(np.ones(64))) >> print(S)"""
        return 'Solution({})'.format(self.x)