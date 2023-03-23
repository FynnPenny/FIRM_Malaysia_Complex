# To simulate energy supply-demand balance based on long-term, high-resolution chronological data
# Copyright (c) 2019, 2020 Bin Lu, The Australian National University
# Licensed under the MIT Licence
# Correspondence: bin.lu@anu.edu.au

import numpy as np

def Reliability(solution, flexible, gas, start=None, end=None):
    """Deficit = Simulation.Reliability(S, hydro=...)"""

    Netload = (solution.MLoad.sum(axis=1) - solution.GPV.sum(axis=1) - solution.GWind.sum(axis=1) - solution.GBaseload.sum(axis=1))[start:end] \
              - flexible - gas # Sj-ENLoad(j, t), MW
    length = len(Netload)
    
    solution.flexible = flexible # MW
    solution.gas = gas

    Pcapacity_PH = sum(solution.CPHP) * pow(10, 3) # S-CPHP(j), GW to MW
    Pcapacity_B = sum(solution.CBP) * pow(10,3)
    Scapacity_PH = solution.CPHS * pow(10, 3) # S-CPHS(j), GWh to MWh
    Scapacity_B = solution.CBS * pow(10,3)
    efficiencyPH, efficiencyB, resolution = (solution.efficiencyPH, solution.efficiencyB, solution.resolution)

    DischargePH, ChargePH, StoragePH, DischargeB, ChargeB, StorageB = map(np.zeros, [length] * 6)
    Deficit_energy, Deficit_power = map(np.zeros, [length] * 2)

    for t in range(length):

        Netloadt = Netload[t]
        StoragePH_t1 = Storage[t-1] if t>0 else 0.5 * Scapacity_PH
        StorageB_t1 = StorageB[t-1] if t>0 else 0.5 * Scapacity_B

        ##### THIS BLOCK DOES NOT MAKE SENSE CURRENTLY. BASED ON ENTIRE NET LOAD FOR BOTH STORAGE SYSTEMS - SHOULD BE APPORTIONED BETWEEN EACH
        ##### SHOULD TEST ONE STORAGE SYSTEM, THEN BALANCE REMAINING NET LOAD WITH THE OTHER
        ##### THEN OVERAL DEFICIT AT THE END SHOULD BE DETERMINED
        Discharge_PH_t = min(max(0, Netloadt), Pcapacity_PH, Storage_PH_t1 / resolution)
        Charge_PH_t = min(-1 * min(0, Netloadt), Pcapacity_PH, (Scapacity_PH - Storage_PH_t1) / efficiencyPH / resolution)
        Storage_PH_t = Storage_PH_t1 - Discharge_PH_t * resolution + Charge_PH_t * resolution * efficiencyPH
        
        Discharge_B_t = min(max(0, Netloadt), Pcapacity_B, Storage_B_t1 / resolution)
        Charge_B_t = min(-1 * min(0, Netloadt), Pcapacity_B, (Scapacity_B - Storage_B_t1) / efficiencyB / resolution)
        Storage_B_t = Storage_B_t1 - Discharge_B_t * resolution + Charge_B_t * resolution * efficiencyB

        Discharge_PH[t] = Discharge_PH_t
        Charge_PH[t] = Charge_PH_t
        StoragePH[t] = Storage_PH_t

        Discharge_B[t] = Discharge_B_t
        Charge_B[t] = Charge_B_t
        StorageB[t] = Storage_B_t

        diff = Netloadt - Discharge_PH_t - Discharge_B_t
        
        ##### TO FIX: SPLIT DEFICIT ENERGY AND POWER BASED ON WHICH SYSTEM EXPERIENCES A PARTICULAR DEFICIT
        if diff <= 0:
            Deficit_energy[t] = 0
            Deficit_power[t] = 0
        elif ((Discharge_PH_t == Pcapacity_PH) and (Discharge_B_t == Pcapacity_B)):
            Deficit_energy[t] = 0
            Deficit_power[t] = diff
        elif ((Discharge_PH_t == Storage_PH_t_1 / resolution) and (Discharge_B_t == Storage_B_t_1 / resolution)):
            Deficit_energy[t] = diff
            Deficit_power[t] = 0
        elif ((Discharge_PH_t == Pcapacity_PH) and (Discharge_B_t == Storage_B_t_1 / resolution)):
            Deficit_energy[t] = # B energy deficit
            Deficit_power[t] = # PH power deficit 
        elif ((Discharge_PH_t == Storage_PH_t_1 / resolution) and (Discharge_B_t == Pcapacity_B)):
            Deficit_energy[t] = # PH energy deficit
            Deficit_power[t] = # B power deficit
        elif ((Discharge_PH_t == Storage_PH_t_1 / resolution) and (Discharge_B_t == Pcapacity_B)):
            Deficit_energy[t] = # PH energy deficit
            Deficit_power[t] = 0
        elif ((Discharge_PH_t == Storage_PH_t_1 / resolution) and (Discharge_B_t == Pcapacity_B)):
            Deficit_energy[t] = 0
            Deficit_power[t] = # PH power deficit
        elif ((Discharge_PH_t == Storage_PH_t_1 / resolution) and (Discharge_B_t == Pcapacity_B)):
            Deficit_energy[t] = # B energy deficit
            Deficit_power[t] = 0
        elif ((Discharge_PH_t == Storage_PH_t_1 / resolution) and (Discharge_B_t == Pcapacity_B)):
            Deficit_energy[t] = 0
            Deficit_power[t] = # B power deficit
        

    Deficit = np.maximum(Netload - Discharge + P2V, 0)
    DeficitD = ConsumeD - DischargeD - P2V * efficiencyD
    Spillage = -1 * np.minimum(Netload + Charge + ChargeD, 0)

    assert 0 <= int(np.amax(Storage)) <= Scapacity, 'Storage below zero or exceeds max storage capacity'
    assert 0 <= int(np.amax(StorageD)) <= ScapacityD, 'StorageD below zero or exceeds max storage capacity'
    assert np.amin(Deficit) >= 0, 'Deficit below zero'
    assert np.amin(DeficitD) > -0.1, 'DeficitD below zero: {}'.format(np.amin(DeficitD))
    assert np.amin(Spillage) >= 0, 'Spillage below zero'

    solution.Discharge, solution.Charge, solution.Storage, solution.P2V = (Discharge, Charge, Storage, P2V)
    solution.DischargeD, solution.ChargeD, solution.StorageD = (DischargeD, ChargeD, StorageD)
    solution.Deficit, solution.DeficitD, solution.Spillage = (Deficit, DeficitD, Spillage)

    return Deficit, DeficitD