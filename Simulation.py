# To simulate energy supply-demand balance based on long-term, high-resolution chronological data
# Copyright (c) 2019, 2020 Bin Lu, The Australian National University
# Licensed under the MIT Licence
# Correspondence: bin.lu@anu.edu.au

import numpy as np

def Reliability(solution, hydro, bio, gas, start=None, end=None):
    """Deficit = Simulation.Reliability(S, hydro=...)"""

    ###### CALCULATE NETLOAD FOR EACH INTERVAL ######
    Netload = (solution.MLoad.sum(axis=1) \
               - solution.GPV.sum(axis=1) \
                - solution.GWind.sum(axis=1) \
                - solution.GInter.sum(axis=1))[start:end] \
                - hydro - bio - gas # Sj-ENLoad(j, t), MW
    length = len(Netload)
    
    solution.hydro = hydro # MW
    solution.bio = bio
    solution.gas = gas

    ###### CREATE STORAGE SYSTEM VARIABLES ######
    Pcapacity_PH = sum(solution.CPHP) * pow(10, 3) # S-CPHP(j), GW to MW
    Pcapacity_B = sum(solution.CBP) * pow(10,3)
    Scapacity_PH = solution.CPHS * pow(10, 3) # S-CPHS(j), GWh to MWh
    Scapacity_B = solution.CBS * pow(10,3)
    efficiencyPH, efficiencyB, resolution = (solution.efficiencyPH, solution.efficiencyB, solution.resolution)

    DischargePH, ChargePH, StoragePH, DischargeB, ChargeB, StorageB = map(np.zeros, [length] * 6)
    Deficit_energy, Deficit_power = map(np.zeros, [length] * 2)

    for t in range(length):
        ###### INITIALISE INTERVAL ######
        Netloadt = Netload[t]
        Storage_PH_t1 = StoragePH[t-1] if t>0 else 0.5 * Scapacity_PH
        Storage_B_t1 = StorageB[t-1] if t>0 else 0.5 * Scapacity_B

        ##### UPDATE STORAGE SYSTEMS ######
        Discharge_PH_t = min(max(0, Netloadt), Pcapacity_PH, Storage_PH_t1 / resolution)
        Charge_PH_t = min(-1 * min(0, Netloadt), Pcapacity_PH, (Scapacity_PH - Storage_PH_t1) / efficiencyPH / resolution)
        Storage_PH_t = Storage_PH_t1 - Discharge_PH_t * resolution + Charge_PH_t * resolution * efficiencyPH

        DischargePH[t] = Discharge_PH_t
        ChargePH[t] = Charge_PH_t
        StoragePH[t] = Storage_PH_t

        diff1 = Netloadt - Discharge_PH_t + Charge_PH_t
        
        Discharge_B_t = min(max(0, diff1), Pcapacity_B, Storage_B_t1 / resolution)
        Charge_B_t = min(-1 * min(0, diff1), Pcapacity_B, (Scapacity_B - Storage_B_t1) / efficiencyB / resolution)
        Storage_B_t = Storage_B_t1 - Discharge_B_t * resolution + Charge_B_t * resolution * efficiencyB

        DischargeB[t] = Discharge_B_t
        ChargeB[t] = Charge_B_t
        StorageB[t] = Storage_B_t

        diff2 = Netloadt - Discharge_PH_t - Discharge_B_t + Charge_PH_t + Charge_B_t
        
        ###### DETERMINE DEFICITS ######
        if diff2 <= 0:
            Deficit_energy[t] = 0
            Deficit_power[t] = 0
        elif ((Discharge_PH_t == Pcapacity_PH) and (Discharge_B_t == Pcapacity_B)):
            Deficit_energy[t] = 0
            Deficit_power[t] = diff2
        elif ((Discharge_PH_t == Storage_PH_t1 / resolution) and (Discharge_B_t == Storage_B_t1 / resolution)):
            Deficit_energy[t] = diff2
            Deficit_power[t] = 0
        elif ((Discharge_PH_t == Pcapacity_PH) and (Discharge_B_t == Storage_B_t1 / resolution)):
            Deficit_energy[t] = diff2 # B energy deficit
            Deficit_power[t] = diff1 - diff2 # PH power deficit 
        elif ((Discharge_PH_t == Storage_PH_t1 / resolution) and (Discharge_B_t == Pcapacity_B)):
            Deficit_energy[t] = diff1 - diff2 # PH energy deficit
            Deficit_power[t] = diff2 # B power deficit        

    Deficit = Deficit_energy + Deficit_power
    Spillage = -1 * np.minimum(Netload + ChargePH + ChargeB - DischargePH - DischargeB, 0)

    ###### ERROR CHECKING ######
    assert 0 <= int(np.amax(StoragePH)) <= Scapacity_PH, 'Storage below zero or exceeds max storage capacity'
    assert 0 <= int(np.amax(StorageB)) <= Scapacity_B, 'StorageB below zero or exceeds max storage capacity'
    assert np.amin(Deficit) > -0.1, 'DeficitD below zero'
    assert np.amin(Spillage) >= 0, 'Spillage below zero'

    ###### UPDATE SOLUTION OBJECT ######
    solution.DischargePH, solution.ChargePH, solution.StoragePH = (DischargePH, ChargePH, StoragePH)
    solution.DischargeB, solution.ChargeB, solution.StorageB = (DischargeB, ChargeB, StorageB)
    solution.Deficit_energy, solution.Deficit_power, solution.Deficit, solution.Spillage = (Deficit_energy, Deficit_power, Deficit, Spillage)

    return Deficit_energy, Deficit_power, Deficit, DischargePH, DischargeB

if __name__ == '__main__':
    from Input import *
    from Network import Transmission 

    #suffix = "_APG_PMY_Only_HVAC_5_TRUE_TRUE.csv"\
    suffix = '{}_{}_{}_{}_{}_{}.csv'.format(node,transmissionScenario,percapita,batteryScenario,gasScenario,maxit)
    Optimisation_x = np.genfromtxt('Results/Optimisation_resultx{}'.format(suffix), delimiter=',')
    
    # Initialise the optimisation
    S = Solution(Optimisation_x)

    CGas = np.nan_to_num(np.array(S.CGas))
    
    # Simulation with only baseload
    Deficit_energy1, Deficit_power1, Deficit1, DischargePH1, DischargeB1 = Reliability(S, hydro=baseload, bio=np.zeros(intervals), gas=np.zeros(intervals)) # Sj-EDE(t, j), MW
    Max_deficit1 = np.reshape(Deficit1, (-1, 8760)).sum(axis=-1) # MWh per year
    PFlexible_Gas = Deficit1.max() * pow(10, -3) # GW

    # Simulation with only baseload and hydro (cheapest)
    Deficit_energy2, Deficit_power2, Deficit2, DischargePH2, DischargeB2 = Reliability(S, hydro=np.ones(intervals) * CHydro.sum() * pow(10,3), bio=np.zeros(intervals), gas=np.zeros(intervals))
    Max_deficit2 = np.reshape(Deficit2, (-1, 8760)).sum(axis=-1) # MWh per year
    PBio_Gas = Deficit2.max() * pow(10, -3) # GW

    # Simulation with only baseload, hydro and bio (next cheapest)
    Deficit_energy3, Deficit_power3, Deficit3, DischargePH3, DischargeB3 = Reliability(S, hydro=np.ones(intervals) * CHydro.sum() * pow(10,3), bio = np.ones(intervals) * CBio.sum() * pow(10, 3), gas=np.zeros(intervals))
    Max_deficit3 = np.reshape(Deficit3, (-1, 8760)).sum(axis=-1) # MWh per year
    PGas = Deficit3.max() * pow(10, -3) # GW
    
    # Assume all storage provided by PHES (lowest efficiency i.e. worst cast). Look at maximum generation years for energy penalty function
    GHydro = resolution * (Max_deficit1 - Max_deficit2).max() / efficiencyPH + 8760*CBaseload.sum() * pow(10,3)
    GBio = resolution * (Max_deficit2 - Max_deficit3).max() / efficiencyPH
    GGas = resolution * (Max_deficit3).max() / efficiencyPH

    print("Sim3 Max Annual Flexible: ", GHydro, GBio, GGas)
    
    # Power and energy penalty functions
    PenEnergy = (max(0, GHydro - Hydromax) + max(0, GBio - Biomax) + max(0, GGas - Gasmax))*pow(10,3)
    PenPower = (max(0,PFlexible_Gas - (CPeak.sum() + CGas.sum())) + max(0, PBio_Gas - (CBio.sum() + CGas.sum())) + max(0, PGas - CGas.sum()))*pow(10,3)

    print("Powers: ",PFlexible_Gas,PBio_Gas,PGas)
    
    # Simulation with baseload, all existing capacity, and all hydrogen
    Deficit_energy, Deficit_power, Deficit, DischargePH, DischargeB = Reliability(S, hydro=np.ones(intervals) * CHydro.sum() * pow(10,3), bio = np.ones(intervals) * CBio.sum() * pow(10, 3), gas=np.ones(intervals) * CGas.sum() * pow(10, 3))
    
    # Deficit penalty function
    PenDeficit = max(0, Deficit.sum() * resolution - S.allowance)*pow(10,3)

    # Existing capacity generation profiles    
    gas = np.clip(Deficit3, 0, CGas.sum() * pow(10, 3))
    bio = np.clip(Deficit2 - Deficit3, 0, CBio.sum() * pow(10, 3))
    hydro = np.clip(Deficit1 - Deficit2, 0, CHydro.sum() * pow(10, 3)) + baseload

    print("GAS: ", CGas.sum()*pow(10,3),max(Deficit3))
    print("BIO: ", CBio.sum()*pow(10,3),max(Deficit2 - Deficit3))
    print("HYDRO: ", CHydro.sum()*pow(10,3),max(Deficit1 - Deficit2))

    # Simulation using the existing capacity generation profiles - required for storage average annual discharge
    Deficit_energy, Deficit_power, Deficit, DischargePH, DischargeB = Reliability(S, hydro=hydro, bio=bio, gas=gas)

    # Discharged energy from storage systems
    GPHES = DischargePH.sum() * resolution / years * pow(10,-6) # TWh per year
    GBattery = DischargeB.sum() * resolution / years * pow(10,-6)

    # Transmission capacity calculations
    TDC = Transmission(S) if 'APG' in node else np.zeros((intervals, len(TLoss))) # TDC: TDC(t, k), MW 
    CDC = np.amax(abs(TDC), axis=0) * pow(10, -3) # CDC(k), MW to GW

    # Transmission penalty function
    PenDC = max(0, CDC[9] - CDC9max) * pow(10, 3) # GW to MW
    PenDC += max(0, CDC[10] - CDC10max) * pow(10, 3) # GW to MW
    PenDC += max(0, CDC[11] - CDC11max) * pow(10, 3) # GW to MW
    PenDC *= pow(10, 3) # Blow up penalty function

    # Average annual electricity generated by existing capacity
    GGas = resolution * gas.sum() / years / efficiencyPH
    GHydro = resolution * hydro.sum() / years / efficiencyPH
    GBio = resolution * bio.sum() / years / efficiencyPH

    GGas_max = np.reshape(gas, (-1, 8760)).sum(axis=-1).max()
    GHydro_max = np.reshape(hydro, (-1, 8760)).sum(axis=-1).max()
    GBio_max = np.reshape(bio, (-1, 8760)).sum(axis=-1).max()
    
    # Average annual electricity imported through external interconnections
    GInter = sum(sum(S.GInter)) * resolution / years if len(S.GInter) > 0 else 0

    # Levelised cost of electricity calculation
    cost = factor * np.array([sum(S.CPV), GInter * pow(10,-6), sum(S.CPHP), S.CPHS, sum(S.CBP), S.CBS] + list(CDC) + [sum(S.CPV), GHydro * pow(10, -6), GBio * pow(10,-6), CGas.sum(), GGas * pow(10, -6), GPHES, GBattery, 0, 0]) # $b p.a.
    cost = cost.sum()
    loss = np.sum(abs(TDC), axis=0) * TLoss
    loss = loss.sum() * pow(10, -9) * resolution / years # PWh p.a.
    LCOE = cost / abs(energy - loss)

    print("Average Annual Flexible: ", GHydro, GBio, GGas)
    print("Max Annual Flexible: ", GHydro_max, GBio_max, GGas_max)
    print("Max allowable Flexible: ", Hydromax, Biomax, Gasmax)
    print("Interconnection: ", GInter)
    print("Penalties: ", PenDC, PenDeficit, PenEnergy, PenPower)
    print("Deficit: ", Deficit.sum(), S.allowance)
    print("LCOE: ", LCOE)

    # Import cost factors
    if transmissionScenario == 'HVDC':
        factor = np.genfromtxt('Data/factor.csv', dtype=None, delimiter=',', encoding=None)
    elif transmissionScenario == 'HVAC':
        factor = np.genfromtxt('Data/factor_hvac.csv', dtype=None, delimiter=',', encoding=None)
        
    factor = dict(factor)
    print("Cost Factors")
    # Calculate the annual costs for each technology
    CostPV = factor['PV'] * sum(S.CPV) # A$b p.a.
    CostWind = factor['Wind'] * sum(S.CWind) # A$b p.a.
    CostHydro = factor['Hydro'] * GHydro * pow(10,-6)# A$b p.a.
    CostBio = factor['Bio'] * GBio * pow(10,-6)# A$b p.a.
    CostGas = factor['GasCap'] * sum(CGas) + factor['GasFuel'] * GGas * pow(10,-6) # A$b p.a.
    CostPH = factor['PHP'] * sum(S.CPHP) + factor['PHS'] * S.CPHS + factor['PHES-VOM'] * DischargePH.sum() * resolution / years * pow(10,-6) # A$b p.a.
    CostInter = factor['Inter'] * GInter # A$b p.a.
    CostBattery = factor['BP'] * sum(S.CBP) + factor['BS'] * S.CBS + factor['B-VOM'] * DischargeB.sum() * resolution / years * pow(10,-6) # A$b p.a.
    if node>=21:
        CostPH -= factor['LegPH']

    CostT = np.array([factor['FQ'],factor['NQ'],factor['NS'],factor['NV'],factor['AS'],factor['SW'],factor['TV']])
    CostDC, CostAC, CDC, CAC = [],[],[],[]
    
    CostDC, CostAC, CDC, CAC = [np.array(x) for x in [CostDC, CostAC, CDC, CAC]]
    
    CostDC = (CostDC * CDC).sum() if len(CDC) > 0 else 0 # A$b p.a.
    CostAC = (CostAC * CAC).sum() if len(CAC) > 0 else 0 # A$b p.a.

#    if node>=21:
#        CostDC -= factor['LegINTC']

    CostAC += factor['ACPV'] * sum(S.CPV) # + factor['ACWind'] * CWind # A$b p.a.
    
    # Calculate the average annual energy demand
    Energy = (MLoad).sum() * pow(10, -9) * resolution / years # PWh p.a.
    Loss = np.sum(abs(TDC), axis=0) * TLoss
    Loss = Loss.sum() * pow(10, -9) * resolution / years # PWh p.a.

    # Calculate the levelised cost of elcetricity at a network level
    LCOE = (CostPV + CostInter + CostBattery + CostGas + CostHydro + CostBio + CostPH + CostDC + CostAC) / (Energy - Loss) # + CostWind / (Energy - Loss)
    LCOEPV = CostPV / (Energy - Loss)
    LCOEWind = CostWind / (Energy - Loss)
    LCOEInter = CostInter / (Energy - Loss)
    LCOEHydro = CostHydro / (Energy - Loss)
    LCOEBio = CostBio / (Energy - Loss)
    LCOEGas = CostGas / (Energy - Loss)
    LCOEPH = CostPH / (Energy - Loss)
    LCOEBattery = CostBattery / (Energy - Loss)
    LCOEDC = CostDC / (Energy - Loss)
    LCOEAC = CostAC / (Energy - Loss)
    
    # Calculate the levelised cost of generation
    GPV = S.GPV.sum() * pow(10, -6) * resolution / years
    GWind = S.GWind.sum() * pow(10, -6) * resolution / years
    LCOG = (CostPV + CostWind + CostHydro + CostBio) * pow(10, 3) / (GPV + GWind + GHydro + GBio)
#    LCOG = (CostPV + CostHydro + CostBio + CostGas + CostInter) * pow(10, 3) / (GPV + GHydro* pow(10,-6) + GBio* pow(10,-6) + GGas* pow(10,-6) + GInter* pow(10,-6))
    LCOGP = CostPV * pow(10, 3) / GPV if GPV!=0 else 0
    LCOGW = CostWind * pow(10, 3) / GWind if GWind!=0 else 0
    LCOGH = CostHydro * pow(10, 3) / (GHydro* pow(10,-6)) if GHydro!=0 else 0
    LCOGB = CostBio * pow(10, 3) / (GBio* pow(10,-6)) if GBio!=0 else 0
    LCOGG = CostGas * pow(10, 3) / (GGas* pow(10,-6)) if GGas != 0 else 0
    LCOGI = CostInter * pow(10, 3) / (GInter* pow(10,-6)) if GInter != 0 else 0

    # Calculate the levelised cost of balancing
    LCOB = LCOE - LCOG
    LCOBS_P = CostPH / (Energy - Loss)
    LCOBS_B = CostBattery / (Energy - Loss)
    LCOBT = (CostDC + CostAC) / (Energy - Loss)
    LCOBL = LCOB - LCOBS_P - LCOBS_B - LCOBT

    print('Levelised costs of electricity:')
    print('\u2022 LCOE:', LCOE)
    print('\u2022 LCOG:', LCOG)
    print('\u2022 LCOB:', LCOB)
    print('\u2022 LCOG-PV:', LCOGP)
    print('\u2022 LCOG-Wind:', LCOGW)
    print('\u2022 LCOG-Hydro:', LCOGH)
    print('\u2022 LCOG-Bio:', LCOGB)
    print('\u2022 LCOG-External_Imports:', LCOGI)
    print('\u2022 LCOG-Gas:', LCOGG)
    print('\u2022 LCOB-PHES_Storage:', LCOBS_P)
    print('\u2022 LCOB-Battery_Storage:', LCOBS_B)
    print('\u2022 LCOB-Transmission:', LCOBT)
    print('\u2022 LCOB-Spillage & loss:', LCOBL)