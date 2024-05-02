# Modelling input and assumptions
# Copyright (c) 2019, 2020 Bin Lu, The Australian National University
# Licensed under the MIT Licence
# Correspondence: bin.lu@anu.edu.au

import numpy as np
from Optimisation import transmissionScenario, node, percapita, batteryScenario, gasScenario
######### DEBUG ##########
""" transmissionScenario = 'HVAC'
node = 'APG_MY_Isolated'
percapita = 5
batteryScenario = True
gasScenario = True """
#########################

###### NODAL LISTS ######
# Nodel       = np.array(['FNQ', 'NSW', 'NT', 'QLD', 'SA', 'TAS', 'VIC', 'WA'])
# PVl         = np.array(['NSW']*7 + ['FNQ']*1 + ['QLD']*2 + ['FNQ']*3 + ['SA']*6 + ['TAS']*0 + ['VIC']*1 + ['WA']*1 + ['NT']*1)
# Windl       = np.array(['NSW']*8 + ['FNQ']*1 + ['QLD']*2 + ['FNQ']*2 + ['SA']*8 + ['TAS']*4 + ['VIC']*4 + ['WA']*3 + ['NT']*1)
# pv_ub_np    = np.array([365. ]*7 + [887. ]*1 + [257. ]*2 + [1071.]*3 + [260.]*6 + [284. ]*0 + [1070.]*1 + [163.]*1 + [103.]*1)
# wind_ub_np  = np.array([365. ]*8 + [887. ]*1 + [257. ]*2 + [1071.]*2 + [260.]*8 + [284. ]*4 + [1070.]*4 + [163.]*3 + [103.]*1)
# phes_ub_np  = np.array([55.  ]   + [1200.]   + [368. ]   + [552. ]   + [13. ]   + [1268.]   + [2.   ]   + [942.]   + [255.]+ [0.] + [0.] + [0.]) # why are there three extra nodes???
# Interl      = np.array([]) No external interconnections for Australia
# resolution = 1

Nodel = np.array(['ME', 'SB', 'TE', 'PA', 'SE', 'PE', 'JO', 'KT', 'KD', 'SW', 'TH', 'IN', 'PH'])
PVl =   np.array(['ME']*1 + ['SB']*2 + ['TE']*1 + ['PA']*1 + ['SE']*1 + ['PE']*2 + ['JO']*1 + ['KT']*1 + ['KD']*2 + ['SW']*3)
pv_ub_np = np.array([365.] + [887., 887.] + [257.] + [1071.] + [260.] + [284., 284.] + [1070.] + [163.] + [103.,103.] + [627., 627., 627.])
wind_ub_np = np.array([365.] + [887., 887.] + [257.] + [1071.] + [260.] + [284., 284.] + [1070.] + [163.] + [103.,103.] + [627., 627., 627.])
phes_ub_np = np.array([55.] + [1200.] + [368.] + [552.] + [13.] + [1268.] + [2.] + [942.] + [255.] + [2000.] + [0.] + [0.] + [0.])
Windl = np.array(['ME']*1 + ['SB']*1 + ['TE']*1 + ['PA']*1 + ['SE']*1 + ['PE']*1 + ['JO']*1 + ['KT']*1 + ['KD']*1 + ['SW']*1)
Interl = np.array(['TH']*1 + ['IN']*1 + ['PH']*1) if node=='APG_Full' else np.array([]) # Add external interconnections if ASEAN Power Grid scenario
resolution = 1


###### DATA IMPORTS ######
MLoad = np.genfromtxt('Data/electricity{}.csv'.format(percapita), delimiter=',', skip_header=1, usecols=range(4, 4+len(Nodel))) # EOLoad(t, j), MW

# for i in ['evan', 'erigid', 'earticulated', 'enonfreight', 'ebus', 'emotorcycle', 'erail', 'eair', 'ewater', 'ecooking', 'emanufacturing', 'emining']:
#     MLoad += np.genfromtxt('Data/Demand{}.csv'.format(i), delimiter=',', skip_header=1, usecols=range(4, 4+len(Nodel)))

TSPV = np.genfromtxt('Data/pv.csv', delimiter=',', skip_header=1, usecols=range(4, 4+len(PVl))) # TSPV(t, i), MW
TSWind = np.genfromtxt('Data/wind.csv', delimiter=',', skip_header=1, usecols=range(4, 4+len(Windl))) # TSWind(t, i), MW


assets = np.genfromtxt('Data/assets.csv', dtype=None, delimiter=',', encoding=None)[1:, 3:].astype(float)
CHydro, CBio = [assets[:, x] * pow(10, -3) for x in range(assets.shape[1])] # CHydro(j), MW to GW
constraints = np.genfromtxt('Data/constraints.csv', dtype=None, delimiter=',', encoding=None)[1:, 3:].astype(float)
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
if transmissionScenario=='HVDC':
    # HVDC backbone scenario
    dc_flags = np.array([True,True,True,True,True,True,True,True,True,True,True,True])
    
elif transmissionScenario=='HVAC':
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
if transmissionScenario=='HVDC':
    factor = np.genfromtxt('Data/factor.csv', delimiter=',', usecols=1)
else:
    factor = np.genfromtxt('Data/factor_hvac.csv', delimiter=',', usecols=1)

###### SIMULATION PERIOD ######
# firstyear, finalyear, timestep = (2020,2029,1)
firstyear, finalyear, timestep = (2012, 2021, 1) # Required for the depracated dispatch module 

###### SCENARIO ADJUSTMENTS #######
# Node values
if 'APG_Full' == node:
    coverage = Nodel

elif 0: # TODO: Changes need to be made for aus scenarios
    if node<=17: 
        coverage = Nodel[node % 10]

    if 20 < node <=29 : # TODO Add scenario descriptions
        coverage = [np.array(['NSW', 'QLD', 'SA', 'TAS', 'VIC']), # description1
            np.array(['NSW', 'QLD', 'SA', 'TAS', 'VIC', 'WA']),
            np.array(['NSW', 'NT', 'QLD', 'SA', 'TAS', 'VIC']),
            np.array(['NSW', 'NT', 'QLD', 'SA', 'TAS', 'VIC', 'WA']),
            np.array(['FNQ', 'NSW', 'QLD', 'SA', 'TAS', 'VIC']),
            np.array(['FNQ', 'NSW', 'QLD', 'SA', 'TAS', 'VIC', 'WA']),
            np.array(['FNQ', 'NSW', 'NT', 'QLD', 'SA', 'TAS', 'VIC']),
            np.array(['FNQ', 'NSW', 'NT', 'QLD', 'SA', 'TAS', 'VIC', 'WA'])][node % 10 - 1]
    
    if node >= 30:
        coverage = np.array(['FNQ', 'NSW', 'NT', 'QLD', 'SA', 'TAS', 'VIC', 'WA'])

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
TSPV = TSPV[:, np.where(np.in1d(PVl, coverage)==True)[0]]
TSWind = TSWind[:, np.where(np.in1d(Windl, coverage)==True)[0]]

CBaseload = CBaseload[np.where(np.in1d(Nodel, coverage)==True)[0]]
CHydro = CHydro[np.where(np.in1d(Nodel, coverage)==True)[0]]
CBio = CBio[np.where(np.in1d(Nodel, coverage)==True)[0]]
CPeak = CHydro + CBio - CBaseload # GW

EHydro, EBio = [x[np.where(np.in1d(Nodel, coverage)==True)[0]] for x in (EHydro, EBio)]

Hydromax = EHydro.sum() * pow(10,3) # GWh to MWh per year
Biomax = EBio.sum() * pow(10,3) # GWh to MWh per year

baseload = np.ones(MLoad.shape[0]) * CBaseload.sum() * 1000 # GW to MW

pv_ub_np = pv_ub_np[np.where(np.in1d(PVl, coverage)==True)[0]]
wind_ub_np = wind_ub_np[np.where(np.in1d(Windl, coverage)==True)[0]]
phes_ub_np = phes_ub_np[np.where(np.in1d(Nodel, coverage)==True)[0]]

#    Nodel, PVl, Interl = [x[np.where(np.in1d(x, coverage)==True)[0]] for x in (Nodel, PVl, Interl)]

Nodel, PVl, Windl, Interl = [x[np.where(np.in1d(x, coverage)==True)[0]] for x in (Nodel, PVl, Windl, Interl)]

# Scenario values
if transmissionScenario == 'HVAC':
    factor = np.genfromtxt('Data/factor_hvac.csv', delimiter=',', usecols=1)

###### DECISION VARIABLE LIST INDEXES ######
intervals, nodes = MLoad.shape
years = int(resolution * intervals / 8760)
pzones = TSPV.shape[1] # Solar PV and wind sites
wzones = TSWind.shape[1]
pidx, widx, phidx, bidx = (pzones, pzones + wzones, pzones + wzones + nodes, pzones + wzones + 2*nodes) # Index of solar PV (sites), wind (sites), pumped hydro power (service areas), and battery power (service areas)
#pidx, phidx, bidx = (pzones, pzones + nodes, pzones + 2*nodes) # Index of solar PV (sites), wind (sites), pumped hydro power (service areas), and battery power (service areas)
inters = len(Interl) # Number of external interconnections
iidx = bidx + 2 + inters # Index of external interconnections, noting pumped hydro energy (network) and battery energy (network) decision variables after the index of battery power
gidx = iidx + nodes # Index of hydrogen (service areas)

###### NETWORK CONSTRAINTS ######
energy = (MLoad).sum() * pow(10, -9) * resolution / years # PWh p.a.
contingency_ph = list(0.25 * (MLoad).max(axis=0) * pow(10, -3)) # MW to GW
contingency_b = list(0.1 * (MLoad).max(axis=0) * pow(10, -3)) # MW to GW
#manage = 0 # weeks
#allowance = MLoad.sum(axis=1).max() * 0.05 * manage * 168 * efficiencyPH # MWh
allowance = min(0.00002*np.reshape(MLoad.sum(axis=1), (-1, 8760)).sum(axis=-1)) # Allowable annual deficit of 0.002%, MWh

GBaseload = np.tile(CBaseload, (intervals, 1)) * pow(10, 3) # GW to MW
Gasmax = energy * 2 * pow(10,9) # MWh

###### DECISION VARIABLE UPPER BOUNDS ######
pv_ub = [x for x in pv_ub_np]
wind_ub = [x for x in wind_ub_np]
phes_ub = [x for x in phes_ub_np]
battery_ub = [1000.] * (nodes - inters) + inters * [0] if batteryScenario == True else nodes * [0]
phes_s_ub = [10000.]
battery_s_ub = [10000.] if batteryScenario == True else [0]
inter_ub = [500.] * inters if node == 'APG_Full' else inters * [0]
gas_ub = [50.] * (nodes - inters) + inters * [0] if gasScenario == True else nodes * [0]

class Solution:
    """A candidate solution of decision variables CPV(i), CWind(i), CPHP(j), S-CPHS(j)"""

    def __init__(self, x):
        self.x = x
        self.MLoad = MLoad
        self.intervals, self.nodes = (intervals, nodes)
        self.resolution = resolution
        self.baseload = baseload

        self.CPV = list(x[: pidx]) # CPV(i), GW
        self.CWind = list(x[pidx: widx]) # CWind(i), GW
        self.GPV = TSPV * np.tile(self.CPV, (intervals, 1)) * pow(10, 3) # GPV(i, t), GW to MW
        self.GWind = TSWind * np.tile(self.CWind, (intervals, 1)) * pow(10, 3) # GWind(i, t), GW to MW

        self.CPHP = list(x[widx: phidx]) # CPHP(j), GW
#        self.CPHP = list(x[pidx: phidx]) # CPHP(j), GW
        self.CBP = list(x[phidx: bidx])
        self.CPHS = x[bidx] # S-CPHS(j), GWh
        self.CBS = x[bidx+1] 
        self.efficiencyPH = efficiencyPH
        self.efficiencyB = efficiencyB

        self.CInter = list(x[bidx+2: iidx]) if node == 'APG_Full' else len(Interl)*[0] #CInter(j), GW
        self.GInter = np.tile(self.CInter, (intervals, 1)) * pow(10,3) # GInter(j, t), GW to MW

        self.CGas = list(x[iidx:gidx]) # GW

        self.Nodel, self.PVl, self.Interl = (Nodel, PVl, Interl)
        self.Windl = Windl
        self.node = node
        self.transmissionScenario = transmissionScenario
        self.allowance = allowance
        self.coverage = coverage
        self.TLoss = TLoss

        self.CBaseload, self.CPeak = (CBaseload, CPeak)
        self.CHydro = CHydro # GW
        self.CBio = CBio # GW

    def __repr__(self):
        """S = Solution(list(np.ones(64))) >> print(S)"""
        return 'Solution({})'.format(self.x)