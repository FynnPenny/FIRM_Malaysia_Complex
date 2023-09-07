# To simulate energy supply-demand balance based on long-term, high-resolution chronological data
# Copyright (c) 2019, 2020 Bin Lu, The Australian National University
# Licensed under the MIT Licence
# Correspondence: bin.lu@anu.edu.au

import numpy as np

def Reliability(solution, hydro, bio, gas, start=None, end=None):
    """Deficit = Simulation.Reliability(S, hydro=...)"""

    ###### CALCULATE NETLOAD FOR EACH INTERVAL ######
    Netload = (solution.MLoad.sum(axis=1) - solution.GPV.sum(axis=1) - solution.GInter.sum(axis=1))[start:end] \
        - hydro - bio - gas # - solution.GWind.sum(axis=1); Sj-ENLoad(j, t), MW
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

    suffix = "_SB_HVAC_5.csv"
    Optimisation_x = np.genfromtxt('Results/Optimisation_resultx{}'.format(suffix), delimiter=',')
    
    # Initialise the optimisation
    S = Solution(Optimisation_x)

    CGas = np.nan_to_num(np.array(S.CGas))
    
    # Simulation with only baseload
    Deficit_energy1, Deficit_power1, Deficit1, DischargePH1, DischargeB1 = Reliability(S, hydro=baseload, bio=np.zeros(intervals), gas=np.zeros(intervals)) # Sj-EDE(t, j), MW
    Max_deficit1 = np.reshape(Deficit1, (-1, 8760)).sum(axis=-1) # MWh per year
    PFlexible_Gas = Deficit_power1.max() * pow(10, -3) # GW

    # Simulation with only baseload and hydro (cheapest)
    Deficit_energy2, Deficit_power2, Deficit2, DischargePH2, DischargeB2 = Reliability(S, hydro=np.ones(intervals) * CHydro.sum() * pow(10,3), bio=np.zeros(intervals), gas=np.zeros(intervals))
    Max_deficit2 = np.reshape(Deficit2, (-1, 8760)).sum(axis=-1) # MWh per year
    PBio_Gas = Deficit_power2.max() * pow(10, -3) # GW

    # Simulation with only baseload, hydro and bio (next cheapest)
    Deficit_energy3, Deficit_power3, Deficit3, DischargePH3, DischargeB3 = Reliability(S, hydro=np.ones(intervals) * CHydro.sum() * pow(10,3), bio = np.ones(intervals) * CBio.sum() * pow(10, 3), gas=np.zeros(intervals))
    Max_deficit3 = np.reshape(Deficit3, (-1, 8760)).sum(axis=-1) # MWh per year
    PGas = Deficit_power3.max() * pow(10, -3) # GW
    
    # Assume all storage provided by PHES (lowest efficiency i.e. worst cast). Look at maximum generation years for energy penalty function
    GHydro = resolution * (Max_deficit1 - Max_deficit2).max() / efficiencyPH + 8760*CBaseload.sum() * pow(10,3)
    GBio = resolution * (Max_deficit2 - Max_deficit3).max() / efficiencyPH
    GGas = resolution * (Max_deficit3).max() / efficiencyPH

    print("Sim3 Max Annual Flexible: ", GHydro, GBio, GGas)
    print("Baseloads: ", CBaseload.sum() * pow(10,3), baseload)
    
    # Power and energy penalty functions
    PenEnergy = max(0, GHydro - Hydromax) + max(0, GBio - Biomax) + max(0, GGas - Gasmax)
    PenPower = max(0,PFlexible_Gas - (CPeak.sum() + CGas.sum())) + max(0, PGas - CGas.sum())
    
    # Simulation with baseload, all existing capacity, and all hydrogen
    Deficit_energy, Deficit_power, Deficit, DischargePH, DischargeB = Reliability(S, hydro=np.ones(intervals) * CHydro.sum() * pow(10,3), bio = np.ones(intervals) * CBio.sum() * pow(10, 3), gas=np.ones(intervals) * CGas.sum() * pow(10, 3))
    
    # Deficit penalty function
    PenDeficit = max(0, Deficit.sum() * resolution - S.allowance)

    # Existing capacity generation profiles    
    gas = np.clip(Deficit3, 0, CGas.sum() * pow(10, 3))
    bio = np.clip(Deficit2 - Deficit3, 0, CBio.sum() * pow(10, 3))
    hydro = np.clip(Deficit1 - Deficit2, 0, CHydro.sum() * pow(10, 3)) + baseload



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
    PenDC *= pow(10, 3) # GW to MW

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