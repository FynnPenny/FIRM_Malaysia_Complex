# Load profiles and generation mix data (LPGM) & energy generation, storage and transmission information (GGTA)
# based on x/capacities from Optimisation and flexible from Dispatch
# Copyright (c) 2019, 2020 Bin Lu, The Australian National University
# Licensed under the MIT Licence
# Correspondence: bin.lu@anu.edu.au

from Input import *
from Simulation import Reliability
from Network import Transmission

import numpy as np
import datetime as dt

def Debug(solution):
    """Debugging"""

    Load, PV, Inter = (solution.MLoad.sum(axis=1), solution.GPV.sum(axis=1), solution.GInter.sum(axis=1))
    Wind = solution.GWind.sum(axis=1)
    Hydro, Bio, Gas = (solution.MHydro.sum(axis=1), solution.MBio.sum(axis=1), solution.MGas.sum(axis=1))

    DischargePH, ChargePH, StoragePH = (solution.DischargePH, solution.ChargePH, solution.StoragePH)
    DischargeB, ChargeB, StorageB = (solution.DischargeB, solution.ChargeB, solution.StorageB)
    Deficit_energy, Deficit_power, Deficit, Spillage = (solution.Deficit_energy, solution.Deficit_power, solution.Deficit, solution.Spillage)

    PHS, BS = solution.CPHS * pow(10, 3), solution.CBS * pow(10, 3) # GWh to MWh
    efficiencyPH, efficiencyB = solution.efficiencyPH, solution.efficiencyB

    for i in range(intervals):
        # Energy supply-demand balance
        # assert abs(Load[i] + ChargePH[i] + ChargeB[i] + Spillage[i]
        #            - PV[i] - Inter[i] - Wind[i] - Baseload[i] - Peak[i] - DischargePH[i] + DischargeB[i] - Deficit[i]) <= 1
        # assert abs(Load[i] + ChargePH[i] + ChargeB[i] + Spillage[i]
        #            - PV[i] - Inter[i] - Hydro[i] - Bio[i] - DischargePH[i] - DischargeB[i] - Deficit[i] - Gas[i]) <= 1
        # print("something here")
        # print(Load[i] + ChargePH[i] + ChargeB[i] + Spillage[i]
        #         - PV[i] - Inter[i] - Wind[i] - Hydro[i] - Bio[i] - DischargePH[i] - DischargeB[i] - Deficit[i] - Gas[i])
        # print([Load[i] , ChargePH[i] , ChargeB[i] , Spillage[i]
        #         , PV[i] , Inter[i] , Wind[i] , Hydro[i] , Bio[i] , DischargePH[i] , DischargeB[i] , Deficit[i] , Gas[i]])
        # print("something done")

        try: assert abs(Load[i] + ChargePH[i] + ChargeB[i] + Spillage[i]
                - PV[i] - Inter[i] - Wind[i] - Hydro[i] - Bio[i] - DischargePH[i] - DischargeB[i] - Deficit[i] - Gas[i]) <= 1 \
                , "Energy Imbalance > 1"
        except AssertionError as errmsg:
            print(errmsg)
            print("Scenario used: {}".format(solution.node))
            print("Energy Imbalance: {}".format(Load[i] + ChargePH[i] + ChargeB[i] + Spillage[i]
                - PV[i] - Inter[i] - Wind[i] - Hydro[i] - Bio[i] - DischargePH[i] - DischargeB[i] - Deficit[i] - Gas[i]))

        # Discharge, Charge and Storage
        if i==0:
            assert abs(StoragePH[i] - 0.5 * PHS + DischargePH[i] * resolution - ChargePH[i] * resolution * efficiencyPH) <= 1
            assert abs(StorageB[i] - 0.5 * BS + DischargeB[i] * resolution - ChargeB[i] * resolution * efficiencyB) <= 1
        else:
            assert abs(StoragePH[i] - StoragePH[i - 1] + DischargePH[i] * resolution - ChargePH[i] * resolution * efficiencyPH) <= 1
            assert abs(StorageB[i] - StorageB[i - 1] + DischargeB[i] * resolution - ChargeB[i] * resolution * efficiencyB) <= 1

        # Capacity: PV, wind, Discharge, Charge and Storage
        try:
            assert np.amax(PV) <= sum(solution.CPV) * pow(10, 3), print(np.amax(PV) - sum(solution.CPV) * pow(10, 3))
            assert np.amax(Wind) <= sum(solution.CWind) * pow(10, 3), print(np.amax(Wind) - sum(solution.CWind) * pow(10, 3))
            assert np.amax(Inter) <= sum(solution.CInter) * pow(10,3)
            assert np.amax(Gas) <= sum(solution.CGas) * pow(10,3)

            assert np.amax(DischargePH) <= sum(solution.CPHP) * pow(10, 3), print(np.amax(DischargePH) - sum(solution.CPHP) * pow(10, 3))
            assert np.amax(ChargePH) <= sum(solution.CPHP) * pow(10, 3), print(np.amax(ChargePH) - sum(solution.CPHP) * pow(10, 3))
            assert np.amax(StoragePH) <= solution.CPHS * pow(10, 3), print(np.amax(StoragePH) - solution.CPHS * pow(10, 3))
            assert np.amax(DischargeB) <= sum(solution.CBP) * pow(10, 3), print(np.amax(DischargeB) - sum(solution.CBP) * pow(10, 3))
            assert np.amax(ChargeB) <= sum(solution.CBP) * pow(10, 3), print(np.amax(ChargeB) - sum(solution.CBP) * pow(10, 3))
            assert np.amax(StorageB) <= solution.CBS * pow(10, 3), print(np.amax(StorageB) - solution.CBS * pow(10, 3))
        except AssertionError:
            pass

    print('Debugging: everything is ok')

    return True

def LPGM(solution,suffix):
    """Load profiles and generation mix data"""

    Debug(solution)

    # C = np.stack([(solution.MLoad).sum(axis=1), (solution.MGas).sum(axis=1),
    #               solution.MHydro.sum(axis=1), solution.MInter.sum(axis=1), solution.MBio.sum(axis=1), solution.GPV.sum(axis=1), #solution.GWind.sum(axis=1),
    #               solution.DischargePH, solution.DischargeB, solution.Deficit, -1 * solution.Spillage, -1 * solution.ChargePH, -1 * solution.ChargeB,
    #               solution.StoragePH, solution.StorageB,
    #               solution.FQ, solution.NQ, solution.NS, solution.NV, solution.AS, solution.SW, solution.TV])

    C = np.stack([(solution.MLoad).sum(axis=1), (solution.MGas).sum(axis=1),
                  solution.MHydro.sum(axis=1), solution.MInter.sum(axis=1), solution.MBio.sum(axis=1), solution.GPV.sum(axis=1), solution.GWind.sum(axis=1),
                  solution.DischargePH, solution.DischargeB, solution.Deficit, -1 * solution.Spillage, -1 * solution.ChargePH, -1 * solution.ChargeB,
                  solution.StoragePH, solution.StorageB,
                  solution.FQ, solution.NQ, solution.NS, solution.NV, solution.AS, solution.SW, solution.TV])
    
    C = np.around(C.transpose())

    datentime = np.array([(dt.datetime(firstyear, 1, 1, 0, 0) + x * dt.timedelta(minutes=60 * resolution)).strftime('%Y %H:%M') for x in range(intervals)])
    C = np.insert(C.astype('str'), 0, datentime, axis=1)

    header = 'Date & time,Operational demand,Hydrogen (MW),' \
             'Hydropower (MW),External IC Imports (MW), Biomass (MW),Solar photovoltaics (MW),Wind (MW),'\
             'PHES-Discharge (MW),Battery-Discharge (MW),Energy deficit (MW),Energy spillage (MW),PHES-Charge (MW),Battery-Charge (MW),' \
             'PHES-Storage (MWh),Battery-Storage (MWh),' \
             'FQ,NQ,NS,NV,AS,SW,TV'

    np.savetxt('Results/LPGM{}_Network.csv'.format(suffix), C, fmt='%s', delimiter=',', header=header, comments='')

    # if 'APG' in node:
    if node > 17:
        header = 'Date & time,Operational demand,Hydrogen (MW),' \
                 'Hydropower (MW),External IC Imports (MW), Biomass (MW),Solar photovoltaics (MW),Wind (MW)'\
                 'PHES-Discharge (MW),Battery-Discharge (MW),Energy deficit (MW),Energy spillage (MW),'\
                 'Transmission,PHES-Charge (MW),Battery-Charge (MW),' \
                 'PHES-Storage,Battery-Storage'

        Topology = solution.Topology[np.where(np.in1d(Nodel, coverage) == True)[0]]

        for j in range(nodes):
            C = np.stack([(solution.MLoad)[:, j], (solution.MGas)[:, j],
                          solution.MHydro[:, j], solution.MInter[:, j], solution.MBio[:, j], solution.MPV[:, j], solution.MWind[:, j],
                          solution.MDischargePH[:, j], solution.MDischargeB[:, j], solution.MDeficit[:, j], -1 * solution.MSpillage[:, j], Topology[j], 
                          -1 * solution.MChargePH[:, j], -1 * solution.MChargeB[:, j],
                          solution.MStoragePH[:, j], solution.MStorageB[:, j]])
            C = np.around(C.transpose())

            C = np.insert(C.astype('str'), 0, datentime, axis=1)
            np.savetxt('Results/LPGM{}_{}.csv'.format(suffix, solution.Nodel[j]), C, fmt='%s', delimiter=',', header=header, comments='')

    print('Load profiles and generation mix is produced.')

    return True

def GGTA(solution, suffix):
    """GW, GWh, TWh p.a. and A$/MWh information"""
    # Import cost factors
    # if transmissionScenario == 'HVDC':
    #     factor = np.genfromtxt('Data/factor.csv', dtype=None, delimiter=',', encoding=None)
    # elif transmissionScenario == 'HVAC':
    #     factor = np.genfromtxt('Data/factor_hvac.csv', dtype=None, delimiter=',', encoding=None)

    factor = np.genfromtxt('Data/Australia/factor.csv', dtype=None, delimiter=',', encoding=None)
        
    factor = dict(factor)

    # Import capacities [GW, GWh] from the least-cost solution
    CPV, CInter, CPHP, CBP, CPHS, CBS = (sum(solution.CPV), sum(solution.CInter), sum(solution.CPHP), sum(solution.CBP), solution.CPHS, solution.CBS) # GW, GWh
    CWind = sum(solution.CWind)
    CapHydro, CapBio = CHydro.sum(), CBio.sum() # GW
    CapGas = (solution.MGas.sum(axis=1)).max() * pow(10,-3) # GW

    # Import generation energy [GWh] from the least-cost solution
    GPV, GHydro, GGas, GInter, GBio = map(lambda x: x * pow(10, -6) * resolution / years, (solution.GPV.sum(), solution.MHydro.sum(), solution.MGas.sum(), solution.MInter.sum(), solution.MBio.sum())) # TWh p.a.
    DischargePH, DischargeB = (solution.DischargePH.sum(), solution.DischargeB.sum())
    GWind = solution.GWind.sum()
    CFPV = GPV / CPV / 8.76
    CFWind = GWind / CWind / 8.76
    
    # Calculate the annual costs for each technology
    CostPV = factor['PV'] * CPV # A$b p.a.
    CostWind = factor['Wind'] * CWind # A$b p.a.
    CostHydro = factor['Hydro'] * GHydro # A$b p.a.
    CostBio = factor['Bio'] * GBio # A$b p.a.
    CostGas = factor['GasCap'] * CapGas + factor['GasFuel'] * GGas # A$b p.a.
    CostPH = factor['PHP'] * CPHP + factor['PHS'] * CPHS + factor['PHES-VOM'] * DischargePH * resolution / years * pow(10,-6) # A$b p.a.
    CostInter = factor['Inter'] * GInter # A$b p.a.
    CostBattery = factor['BP'] * CBP + factor['BS'] * CBS + factor['B-VOM'] * DischargeB * resolution / years * pow(10,-6) # A$b p.a.
#    if scenario>=21:
#        CostPH -= factor['LegPH']

    # CostT = np.array([factor['KDPE'], factor['TEPA'], factor['SEME'], factor['MEJO'], factor['PESE'], factor['SBSW'], factor['KTTE'], factor['PASE'], factor['JOSW'], factor['THKD'], factor['INSE'], factor['PHSB']])
    # TODO make sure these are correct
    CostT = np.array([factor['FQ'],factor['NQ'],factor['NS'],factor['NV'],factor['AS'],factor['SW'],factor['TV']])
    CostDC, CostAC, CDC, CAC = [],[],[],[]

    for i in range(0,len(CostT)):
        CostDC.append(CostT[i]) if dc_flags[i] else CostAC.append(CostT[i])
        CDC.append(solution.CDC[i]) if dc_flags[i] else CAC.append(solution.CDC[i])
    CostDC, CostAC, CDC, CAC = [np.array(x) for x in [CostDC, CostAC, CDC, CAC]]
    
    CostDC = (CostDC * CDC).sum() if len(CDC) > 0 else 0 # A$b p.a.
    CostAC = (CostAC * CAC).sum() if len(CAC) > 0 else 0 # A$b p.a.

#    if scenario>=21:
#        CostDC -= factor['LegINTC']

    CostAC += factor['ACPV'] * CPV + factor['ACWind'] * CWind # A$b p.a.
    

    # Calculate the average annual energy demand
    Energy = (MLoad).sum() * pow(10, -9) * resolution / years # PWh p.a.
    Loss = np.sum(abs(solution.TDC), axis=0) * TLoss
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
#    LCOG = (CostPV + CostWind + CostHydro + CostBio) * pow(10, 3) / (GPV + GWind + GHydro + GBio)
#    LCOG = (CostPV + CostHydro + CostBio + CostGas + CostInter) * pow(10, 3) / (GPV + GHydro + GBio + GGas + GInter)
    LCOG = (CostPV + CostWind + CostHydro + CostBio + CostGas + CostInter) * pow(10, 3) / (GPV + GWind + GHydro + GBio + GGas + GInter)
    LCOGP = CostPV * pow(10, 3) / GPV if GPV!=0 else 0
    LCOGW = CostWind * pow(10, 3) / GWind if GWind!=0 else 0
    LCOGH = CostHydro * pow(10, 3) / GHydro if GHydro!=0 else 0
    LCOGB = CostBio * pow(10, 3) / GBio if GBio!=0 else 0
    LCOGG = CostGas * pow(10, 3) / GGas if GGas != 0 else 0
    LCOGI = CostInter * pow(10, 3) / GInter if GInter != 0 else 0

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
    print('\u2022 LCOG-PV:', LCOGP, '(%s)' % CFPV)
    print('\u2022 LCOG-Wind:', LCOGW, '(%s)' % CFWind)
    print('\u2022 LCOG-Hydro:', LCOGH)
    print('\u2022 LCOG-Bio:', LCOGB)
    print('\u2022 LCOG-External_Imports:', LCOGI)
    print('\u2022 LCOG-Gas:', LCOGG)
    print('\u2022 LCOB-PHES_Storage:', LCOBS_P)
    print('\u2022 LCOB-Battery_Storage:', LCOBS_B)
    print('\u2022 LCOB-Transmission:', LCOBT)
    print('\u2022 LCOB-Spillage & loss:', LCOBL)

    #size = 28 + len(list(solution.CDC))
    size = 31 + len(list(solution.CDC))
    D = np.zeros((1, size))
    header = 'Annual demand (PWh) , Annual Energy Losses (PWh), \
                PV Capacity (GW) , PV Avg Annual Gen (GWh) , Wind Capacity (GW) , Wind Avg Annual Gen (GWh), \
                Hydro Capacity (GW) , Hydro Avg Annual Gen (GWh) , Bio Capacity (GW) , Bio Avg Annual Gen (GWh),\
                Gas Capacity (GW) , Gas Avg Annual Gen (GWh) , Inter Capacity (GW) , Inter Avg Annual Gen (GWh), \
                PHES-PowerCap (GW) , Battery-PowerCap (GW) , PHES-EnergyCap (GWh) , Battery-EnergyCap (GWh) , \
                FQ , NQ , NS , NV , AS , SW , TV ,  \
                LCOE , LCOG , LCOB , LCOG_PV , LCOG_Wind , LCOG_Hydro , LCOG_Bio , LCOG_Gas , LCOG_Inter , LCOBS_PHES , LCOBS_Battery , LCOBT ,  LCOBL'
    D[0, :] = [Energy * pow(10, 3), Loss * pow(10, 3), CPV, GPV, CWind, GWind, CapHydro, GHydro, CapBio, GBio, CapGas, GGas, CInter, GInter] \
              + [CPHP, CBP, CPHS, CBS] \
              + list(solution.CDC) \
              + [LCOE, LCOG, LCOB, LCOGP, LCOGW, LCOGH, LCOGB, LCOGG, LCOGI, LCOBS_P, LCOBS_B, LCOBT, LCOBL]


    #header = header.replace('\n', ',')
    np.savetxt('Results/GGTA{}.csv'.format(suffix), D, header=header, fmt='%f', delimiter=',')
    print('Energy generation, storage and transmission information is produced.')

    return True

def Information(x, hydro , bio, gas, suffix):
    """Dispatch: Statistics.Information(x, Flex)"""

    start = dt.datetime.now()
    print("Statistics start at", start)

    S = Solution(x)
    Deficit_energy, Deficit_power, Deficit, DischargePH, DischargeB = Reliability(S, hydro=hydro, bio=bio, gas=gas)

    try:
        assert Deficit.sum() * resolution < 0.1, 'Energy generation and demand are not balanced.'
    except AssertionError:
        pass
    
    # assert np.reshape(hydro, (-1, 8760)).sum(axis=-1).max() <= Hydromax, f"Hydro generation exceeds requirement {np.reshape(hydro, (-1, 8760)).sum(axis=-1).max()} {Hydromax}"
    # assert np.reshape(bio, (-1, 8760)).sum(axis=-1).max() <= Biomax, f"Bio generation exceeds requirement {np.reshape(bio, (-1, 8760)).sum(axis=-1).max()} {Biomax}"
    # assert np.reshape(gas, (-1, 8760)).sum(axis=-1).max() <= Gasmax, f"Gas generation exceeds requirement {np.reshape(gas, (-1, 8760)).sum(axis=-1).max()} {Gasmax}"

    assert yearfunc(hydro,np.sum).max() <= Hydromax, f"Hydro generation exceeds requirement {yearfunc(hydro,np.sum).max()} {Hydromax}"
    assert yearfunc(bio, np.sum).max() <= Biomax, f"Bio generation exceeds requirement {yearfunc(hydro,np.sum).max()} {Biomax}"
    assert yearfunc(gas, np.sum).max() <= Gasmax, f"Gas generation exceeds requirement {yearfunc(hydro,np.sum).max()} {Gasmax}"


    #S.TDC = Transmission(S, output=True) if 'APG' in node else np.zeros((intervals, len(TLoss))) # TDC(t, k), MW
    S.TDC = Transmission(S, output=True)
    S.CDC = np.amax(abs(S.TDC), axis=0) * pow(10, -3) # CDC(k), MW to GW
    # S.KDPE, S.TEPA, S.SEME, S.MEJO, S.PESE, S.SBSW, S.KTTE, S.PASE, S.JOSW, S.THKD, S.INSE, S.PHSB = map(lambda k: S.TDC[:, k], range(S.TDC.shape[1]))
    S.FQ, S.NQ, S.NS, S.NV, S.AS, S.SW, S.TV = map(lambda k: S.TDC[:, k], range(S.TDC.shape[1]))

    CGas = np.nan_to_num(np.array(S.CGas))

    # if 'APG' not in node:
    if 0:
        S.MPV = S.GPV
        S.MWind = S.GWind if S.GWind.shape[1]>0 else np.zeros((intervals, 1))
        S.MInter = S.GInter
        S.MDischargePH = np.tile(S.DischargePH, (nodes, 1)).transpose()
        S.MDischargeB = np.tile(S.DischargeB, (nodes, 1)).transpose()
        S.MDeficit = np.tile(S.Deficit, (nodes, 1)).transpose()
        S.MChargePH = np.tile(S.ChargePH, (nodes, 1)).transpose()
        S.MChargeB = np.tile(S.ChargeB, (nodes, 1)).transpose()
        S.MStoragePH = np.tile(S.StoragePH, (nodes, 1)).transpose()
        S.MStorageB = np.tile(S.StorageB, (nodes, 1)).transpose()
        S.MSpillage = np.tile(S.Spillage, (nodes, 1)).transpose()

    S.MHydro = np.clip(S.MHydro, None, CHydro * pow(10, 3)) # GHydro(t, j), GW to MW
    S.MBio = np.clip(S.MBio, None, CBio * pow(10, 3))
    S.MGas = np.clip(S.MGas, None, CGas * pow(10, 3))

    S.MPHS = S.CPHS * np.array(S.CPHP) * pow(10, 3) / sum(S.CPHP) # GW to MW
    S.MBS = S.CBS * np.array(S.CBP) * pow(10, 3) / sum(S.CBP) # GW to MW

    # # S.KDPE, S.TEPA, S.SEME, S.MEJO, S.PESE, S.SBSW, S.KTTE, S.PASE, S.JOSW, S.THKD, S.INSE, S.PHSB
    # S.Topology = np.array([-1 * (S.SEME + S.MEJO),      # ME
    #               S.PHSB + S.SBSW,                      # SB
    #               S.KTTE + S.TEPA,                      # TE
    #               -1 * (S.TEPA + S.KTTE),               # PA
    #               S.PESE + S.PASE + S.SEME - S.INSE,    # SE
    #               -1 * (S.KDPE + S.PESE),               # PE
    #               S.JOSW + S.MEJO,                      # JO
    #               -1 * S.KTTE,                          # KT
    #               S.THKD + S.KDPE,                      # KD
    #               -1 * (S.JOSW + S.SBSW),               # SW
    #               -1 * S.THKD,                          # TH
    #               S.INSE,                               # IN
    #               -1 * S.PHSB])                         # PH

    # S.FQ, S.NQ, S.NS, S.NV, S.AS, S.SW, S.TV
      #['FNQ','NSW', 'NT', 'QLD', 'SA', 'TAS', 'VIC', 'WA']
    S.Topology = np.array([
                        -1*S.FQ,                        #FNQ
                        -1*(S.NS + S.NQ + S.NV),        #NSW
                        -1*S.AS,                        #NT
                         S.NQ + S.FQ,                   #QLD
                         S.NS + S.AS - S.SW,            #SA
                        -1*S.TV,                        #TAS 
                         S.NV + S.TV,                   #VIC
                         S.SW                           #WA 
    ])

    # S.Topology = np.array([]) # TODO Figure out topology

    LPGM(S,suffix)
    GGTA(S,suffix)

    end = dt.datetime.now()
    print("Statistics took", end - start)

    return True

if __name__ == '__main__':
    suffix = "_5_TRUE_TRUE_1"
    Optimisation_x = np.genfromtxt('Results/Optimisation_resultx{}.csv'.format(suffix), delimiter=',')
    hydro = np.genfromtxt('Results/Dispatch_Hydro{}.csv'.format(suffix), delimiter=',', skip_header=1)
    bio = np.genfromtxt('Results/Dispatch_Bio{}.csv'.format(suffix), delimiter=',', skip_header=1)
    gas = np.genfromtxt('Results/Dispatch_Gas{}.csv'.format(suffix), delimiter=',', skip_header=1)
    Information(Optimisation_x, hydro, bio, gas, suffix)