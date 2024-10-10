# Modelling input and assumptions
# Copyright (c) 2019, 2020 Bin Lu, The Australian National University
# Licensed under the MIT Licence
# Correspondence: bin.lu@anu.edu.au

import numpy as np
from Optimisation import transmissionScenario, node, percapita, batteryScenario, gasScenario, leapYearData, verbose, gasCapLim, gasGenLim, quick, factorScenario, maxit
######### DEBUG ##########
""" transmissionScenario = 'HVAC'
node = 'APG_MY_Isolated'
percapita = 5
batteryScenario = True
gasScenario = True """
#########################

###### NODAL LISTS ######
Nodel       = np.array(['FNQ','NSW', 'NT', 'QLD', 'SA', 'TAS', 'VIC', 'WA'])
PVl         = np.array(['NSW']*7 + ['FNQ']*1 + ['QLD']*2 + ['FNQ']*3 + ['SA' ]*6 + ['TAS']*0 + ['VIC']*1 + ['WA' ]*1 + ['NT' ]*1)
Windl       = np.array(['NSW']*8 + ['FNQ']*1 + ['QLD']*2 + ['FNQ']*2 + ['SA' ]*8 + ['TAS']*4 + ['VIC']*4 + ['WA' ]*3 + ['NT' ]*1) # TODO FNQ here in different spots, why?
pv_ub_np    = np.array([50.  ]*7 + [50.  ]*1 + [50.  ]*2 + [50.  ]*3 + [50.  ]*6 + [50.  ]*0 + [50.  ]*1 + [50.  ]*1 + [50.  ]*1)
wind_ub_np  = np.array([50.  ]*8 + [50.  ]*1 + [50.  ]*2 + [50.  ]*2 + [50.  ]*8 + [50.  ]*4 + [50.  ]*4 + [50.  ]*3 + [50.  ]*1)
phes_ub_np  = np.array([1. ]   + [20. ]   + [1. ]   + [20. ]   + [20. ]   + [20. ]   + [20. ]   + [20. ]   + [20. ] + [0.] + [0.] + [0.]) # why are there three extra nodes???
# gas_ub_np   = np.array([30.]   + [30. ]   + [30.]   + [30. ]   + [30. ]   + [30. ]   + [30. ]   + [30. ]   + [30. ] + [0.] + [0.] + [0.])
Interl      = np.array([]) # No external interconnections for Australia
resolution = 0.5

###### DATA IMPORTS ######
MLoad = np.genfromtxt('Data/Australia/electricity.csv', delimiter=',', skip_header=1, usecols=range(4, 4+len(Nodel))) # EOLoad(t, j), MW

# for i in ['evan', 'erigid', 'earticulated', 'enonfreight', 'ebus', 'emotorcycle', 'erail', 'eair', 'ewater', 'ecooking', 'emanufacturing', 'emining']:
#     MLoad += np.genfromtxt('Data/Demand{}.csv'.format(i), delimiter=',', skip_header=1, usecols=range(4, 4+len(Nodel)))

TSPV = np.genfromtxt('Data/Australia/pv.csv', delimiter=',', skip_header=1, usecols=range(4, 4+len(PVl))) # TSPV(t, i), MW
TSWind = np.genfromtxt('Data/Australia/wind.csv', delimiter=',', skip_header=1, usecols=range(4, 4+len(Windl))) # TSWind(t, i), MW
if quick:
    MLoad  = MLoad[0:int(24*366/resolution),:] # Use first year of data only
    TSPV   = TSPV[0:int(24*366/resolution),:] # Use first year of data only
    TSWind = TSWind[0:int(24*366/resolution),:] # Use first year of data only
    
assets = np.genfromtxt('Data/Australia/noassets.csv', dtype=None, delimiter=',', encoding=None)[1:, 3:].astype(float)
CHydro, CBio = [assets[:, x] * pow(10, -3) for x in range(assets.shape[1])] # CHydro(j), MW to GW
# TODO: Does Aus model need energy constraints on hydrobio? Need actual numbers if so
constraints = np.genfromtxt('Data/Australia/constraints.csv', dtype=None, delimiter=',', encoding=None)[1:, 3:].astype(float)
EHydro, EBio = [constraints[:, x] for x in range(assets.shape[1])] # GWh per year

if verbose > 1: print("Data Loaded")

# CBaseloadR = np.array([0, 0, 0, 0, 0, 1.0, 0, 0]) * EHydro / 8760 # 24/7, GW # Run-of-river percentage
# CBaseloadF = np.array([0, 0, 0, 0, 0,  0,  0, 0]) * 100 / 8760 # 24/7, GW # Run-of-river percentage
# CBaseload  = CBaseloadR # + CBaseloadF
# CPeak = CHydro + CBio - CBaseload # GW

CBaseload = np.array([0, 0, 0, 0, 0, 0, 0, 0]) # 24/7, GW
# CBaseload = np.array([0, 0, 0, 0, 0, 1.0, 0, 0]) # 24/7, GW
CPeak = CHydro + CBio - CBaseload # GW

baseload = np.ones(MLoad.shape[0]) * CBaseload.sum() * 1000 # GW to MW

###### CONSTRAINTS ######
# Energy constraints
Hydromax = EHydro.sum() * pow(10,3) # GWh to MWh per year
Biomax   = EBio.sum() * pow(10,3) # GWh to MWh per year

# Transmission constraints
externalImports = 0 # Have ignored for Australia
CDC6max = 3 * 0.63 # GW from FIRM Aus
gasEmit = 0.1735 # gas emissions t/MWh
# CDC9max, CDC10max, CDC11max = 3 * [externalImports * MLoad.sum() / MLoad.shape[0] / 1000] # 5%: External interconnections: THKD, INSE, PHSB, MW to GW

###### TRANSMISSION LOSSES ######
if transmissionScenario=='HVDC':
    # HVDC backbone scenario
    # dc_flags = np.array([True,True,True,True,True,True,True,True,True,True,True,True]) # Old
    dc_flags = np.array([True,True,True,True,True,True,True]) # Australia
    
elif transmissionScenario=='HVAC': # TODO: Transition to Aus
    # HVAC backbone scenario
    # dc_flags = np.array([False,False,False,False,False,False,False,False,True,True,True,True]) # Old
    dc_flags = np.array([False,False,False,False,False,False,False]) # Australia
    
TLoss = []
TDistances = [1500, 1000, 1000, 800, 1200, 2400, 400] # ['FQ','NQ','NS','NV','AS','SW','TV']]

for i in range(0,len(dc_flags)):
    TLoss.append(TDistances[i]*0.03) if dc_flags[i] else TLoss.append(TDistances[i]*0.07)
TLoss = np.array(TLoss)* pow(10, -3)

###### STORAGE SYSTEM CONSTANTS ######
efficiencyPH = 0.8
efficiencyB = 0.9

###### COST FACTORS ######
if factorScenario == 0:
    factor = np.genfromtxt('Data/Australia/factors original.csv',delimiter=',', usecols=1)
else:
    factor = np.genfromtxt('Data/Australia/factors test{}.csv'.format(factorScenario),delimiter=',', usecols=1)

###### SIMULATION PERIOD ######
firstyear, finalyear, timestep = (2020,2020,1) if quick else (2020,2029,1)
if leapYearData:
    leaps = np.array((np.arange(firstyear,finalyear+1,timestep) % 4) == 0)
else:
    leaps = np.zeros_like(np.arange(firstyear,finalyear+1,timestep)).astype(bool)

def yearfunc(data,npfunc): # applies a function 
    i = 0
    j = 0
    outs = np.zeros(len(leaps)).astype(float)
    n = int(365 * 24 / resolution)
    n_leap = int(366 * 24 / resolution)

    for leap in leaps:
        if leap:
            outs[j] = npfunc(data[i:i+n_leap])
            i += n_leap
            j += 1
        else:
            outs[j] = npfunc(data[i:i+n])
            i += n
            j += 1

    return outs

# firstyear, finalyear, timestep = (2012, 2021, 1) # Required for the depracated dispatch module 

###### SCENARIO ADJUSTMENTS #######
# Node values
# if 'APG_Full' == node:
#     coverage = Nodel

if node<=17: 
    coverage = Nodel[node % 10]

elif 20 < node <=29 : # TODO Add scenario descriptions
    coverage = [np.array(['NSW', 'QLD', 'SA', 'TAS', 'VIC']), # NEM only
        np.array(['NSW', 'QLD', 'SA', 'TAS', 'VIC', 'WA']), # NEM + WA
        np.array(['NSW', 'NT', 'QLD', 'SA', 'TAS', 'VIC']), # NEM + NT
        np.array(['NSW', 'NT', 'QLD', 'SA', 'TAS', 'VIC', 'WA']), # NEM + NT + WA
        np.array(['FNQ', 'NSW', 'QLD', 'SA', 'TAS', 'VIC']), # NEM + FNQ
        np.array(['FNQ', 'NSW', 'QLD', 'SA', 'TAS', 'VIC', 'WA']), # NEM + FNQ + WA
        np.array(['FNQ', 'NSW', 'NT', 'QLD', 'SA', 'TAS', 'VIC']), # NEM + FNQ + NT
        np.array(['FNQ', 'NSW', 'NT', 'QLD', 'SA', 'TAS', 'VIC', 'WA'])][node % 10 - 1] # All regions

elif node >= 30:
    coverage = np.array(['FNQ', 'NSW', 'NT', 'QLD', 'SA', 'TAS', 'VIC', 'WA'])

else:
    coverage = np.array([node])

if verbose > 1: print(coverage)

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

Nodel, PVl, Windl, Interl = [x[np.where(np.in1d(x, coverage)==True)[0]] for x in (Nodel, PVl, Windl, Interl)]

# Scenario values
factor = np.genfromtxt('Data/Australia/factor.csv', delimiter=',', usecols=1)

###### DECISION VARIABLE LIST INDEXES ######
intervals, nodes = MLoad.shape
years = int(resolution * intervals / 8760)
pzones = TSPV.shape[1] # Solar PV and wind sites
wzones = TSWind.shape[1]
pidx, widx, phidx, bidx = (pzones, pzones + wzones, pzones + wzones + nodes, pzones + wzones + 2*nodes) # Index of solar PV (sites), wind (sites), pumped hydro power (service areas), and battery power (service areas)
inters = len(Interl) # Number of external interconnections
iidx = bidx + 2 + inters # Index of external interconnections, noting pumped hydro energy (network) and battery energy (network) decision variables after the index of battery power
gidx = iidx + nodes # Index of hydrogen (service areas)

###### NETWORK CONSTRAINTS ######
energy = (MLoad).sum() * pow(10, -9) * resolution / years # PWh p.a.
contingency_ph = list(0.25 * (MLoad).max(axis=0) * pow(10, -3)) # MW to GW
contingency_b = list(0.1 * (MLoad).max(axis=0) * pow(10, -3)) # MW to GW

# manage = 0 # weeks TODO What is this for?? What are these things supposed to be doing??

# allowance = MLoad.sum(axis=1).max() * 0.05 * manage * 168 * efficiencyPH # MWh
allowance = 0.00002*yearfunc(MLoad,np.max).min() # Allowable annual deficit of 0.002%, MWh 

GBaseload = np.tile(CBaseload, (intervals, 1)) * pow(10, 3) # GW to MW

if gasGenLim is not None:
    Gasmax = energy * (gasGenLim/10000) * pow(10,9) # MWh
else:
    Gasmax = energy * 2 * pow(10,9) # MWh

###### DECISION VARIABLE UPPER BOUNDS ######
pv_ub = [x for x in pv_ub_np]
wind_ub = [x for x in wind_ub_np]
phes_ub = [x for x in phes_ub_np]
battery_ub = [20.] * (nodes - inters) + inters * [0] if batteryScenario == True else nodes * [0]
phes_s_ub = [10000.]
battery_s_ub = [100.] if batteryScenario == True else [0]
inter_ub = [500.] * inters if node == 'APG_Full' else inters * [0] # Ignored for Aus
gas_ub = [30.] * (nodes - inters) + inters * [0] if gasScenario == True else nodes * [0]

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