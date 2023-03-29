# A transmission network model to calculate inter-regional power flows
# Copyright (c) 2019, 2020 Bin Lu, The Australian National University
# Licensed under the MIT Licence
# Correspondence: bin.lu@anu.edu.au

import numpy as np

def Transmission(solution, output=False):
    """TDC = Network.Transmission(S)"""

    Nodel, PVl, Interl = (solution.Nodel, solution.PVl, solution.Interl)
#    Windl = solution.Windl
    intervals, nodes = (solution.intervals, solution.nodes)

    MPV, MInter = map(np.zeros, [(nodes, intervals)] * 2)
#    MWind = map(np.zeros, [(nodes, intervals)] * 1)
    for i, j in enumerate(Nodel):
        MPV[i, :] = solution.GPV[:, np.where(PVl==j)[0]].sum(axis=1)
#        MWind[i, :] = solution.GWind[:, np.where(Windl==j)[0]].sum(axis=1)
        if solution.node=='APG':
            MInter[i, :] = solution.GInter[:, np.where(Interl==j)[0]].sum(axis=1)
    MPV, MInter = (MPV.transpose(), MInter.transpose()) # Sij-GPV(t, i), Sij-GWind(t, i), MW
#    MWind = MWind.transpose()
  
    baseload = solution.baseload
    existing = solution.existing
    flexible = existing - baseload

    CBaseload = solution.CBaseload
    basefactor = np.tile(CBaseload, (intervals, 1)) / CBaseload.sum()
    MBaseload = np.tile(baseload, (nodes, 1)).transpose() * basefactor
    
    CPeak = solution.CPeak # GW
    pkfactor = np.tile(CPeak, (intervals, 1)) / CPeak.sum()
    MPeak = np.tile(flexible, (nodes, 1)).transpose() * pkfactor # MW

    CGas = np.nan_to_num(np.array(solution.CGas)) # GW
    gas = solution.gas # MW
    if CGas.sum() == 0:
        gfactor = np.tile(CGas, (intervals, 1))
    else:
        gfactor = np.tile(CGas, (intervals, 1)) / CGas.sum()
    MGas = np.tile(gas, (nodes, 1)).transpose() * gfactor
    
    MLoad = solution.MLoad # EOLoad(t, j), MW

    defactor = MLoad / MLoad.sum(axis=1)[:, None]
    MDeficit = np.tile(solution.Deficit, (nodes, 1)).transpose() * defactor # MDeficit: EDE(j, t)

    MPW = MPV + MInter # + MWind
    spfactor = np.divide(MPW, MPW.sum(axis=1)[:, None], where=MPW.sum(axis=1)[:, None]!=0)
    MSpillage = np.tile(solution.Spillage, (nodes, 1)).transpose() * spfactor # MSpillage: ESP(j, t)

    CPHP = solution.CPHP
    pcfactor = np.tile(CPHP, (intervals, 1)) / sum(CPHP) if sum(CPHP) != 0 else 0
    MDischargePH = np.tile(solution.DischargePH, (nodes, 1)).transpose() * pcfactor # MDischarge: DPH(j, t)
    MChargePH = np.tile(solution.ChargePH, (nodes, 1)).transpose() * pcfactor # MCharge: CHPH(j, t)

    CBP = solution.CBP
    bfactor = np.tile(CBP, (intervals, 1)) / sum(CBP) if sum(CBP) != 0 else 0
    MDischargeB = np.tile(solution.DischargeB, (nodes, 1)).transpose() * bfactor # MDischarge: DPH(j, t)
    MChargeB = np.tile(solution.ChargeB, (nodes, 1)).transpose() * bfactor # MCharge: CHPH(j, t)

    MImport = MLoad + MChargePH + MChargeB + MSpillage \
              - MPV - MInter - MBaseload - MPeak - MGas - MDischargePH - MDischargeB - MDeficit # - MWind; EIM(t, j), MW
    
    """ i = 19
    print("---- TRANSMISSION ----")
    print("x: ", solution.x)
    print("CPV: ", solution.CPV)
    print("CPHP: ", solution.CPHP)
    print("CBP: ", solution.CBP)
    print("CPHS: ", solution.CPHS)
    print("CBS: ", solution.CBS)
    print("CInter: ", solution.CInter)
    print("CGas: ", solution.CGas)
    print("---------------------")
    print("MImport: ", MImport[i].sum())
    print("MLoad", MLoad[i].sum())
    print("MChargePH", MChargePH[i].sum())
    print("MChargeB", MChargeB[i].sum())
    print("MSpillage", MSpillage[i].sum())
    print("MPV", MPV[i].sum())
    print("MInter", MInter[i].sum())
    print("MBaseload", MBaseload[i].sum())
    print("MPeak", MPeak[i].sum())
    print("MGas", MGas[i].sum())
    print("MDischargePH", MDischargePH[i].sum())
    print("MDischargeB", MDischargeB[i].sum())
    print("MDeficit", MDeficit[i].sum())
    print("---------------------")
    print("existing: ", MPeak[i].sum() + MBaseload[i].sum())
    print("gas: ", MGas[i].sum())
    print("NetLoad", MLoad[i].sum() - MPeak[i].sum() - MBaseload[i].sum() - MGas[i].sum() - MPV[i].sum() - MInter[i].sum())
    print("Positive Balancing: ", MChargePH[i].sum() + MChargeB[i].sum() + MSpillage[i].sum())
    print("Negative Balancing: ", MDischargePH[i].sum() + MDischargeB[i].sum() + MDeficit[i].sum())
    print("spfactor: ", spfactor[i]) """

    # Imorts into external nodes
    THKD = -1 * MImport[:, np.where(Nodel=='TH')[0][0]]
    PHSB = -1 * MImport[:, np.where(Nodel=='PH')[0][0]]
    INSE = MImport[:, np.where(Nodel=='IN')[0][0]]

    # Imports into outer internal nodes
    KTTE = -1 * MImport[:, np.where(Nodel=='KT')[0][0]]

    # Imports into inner internal nodes
    KDPE = MImport[:, np.where(Nodel=='KD')[0][0]] - THKD
    SBSW = MImport[:, np.where(Nodel=='SB')[0][0]] - PHSB
    TEPA = MImport[:, np.where(Nodel=='TE')[0][0]] - KTTE

    JOSW = -1 * MImport[:, np.where(Nodel=='SW')[0][0]] - SBSW
    PASE = -1 * MImport[:, np.where(Nodel=='PA')[0][0]] - TEPA
    PESE = -1 * MImport[:, np.where(Nodel=='PE')[0][0]] - KDPE
    
    MEJO = MImport[:, np.where(Nodel=='JO')[0][0]] - JOSW
    SEME = -1 * MImport[:, np.where(Nodel=='ME')[0][0]] - MEJO

    # Check the final node
    SEME1 = MImport[:, np.where(Nodel=='SE')[0][0]] + INSE - PASE - PESE
    assert abs(SEME - SEME1).max() <= 0.1, print(abs(SEME - SEME1).max())

    TDC = np.array([KDPE, TEPA, SEME, MEJO, PESE, SBSW, KTTE, PASE, KDPE, JOSW, THKD, INSE, PHSB]).transpose() # TDC(t, k), MW

    #DEBUG ########################################
    TDC1 = np.array([KDPE, TEPA, SEME, SEME1, MEJO, PESE, SBSW, KTTE, PASE, KDPE, JOSW, THKD, INSE, PHSB]).transpose() # TDC(t, k), MW
    """ print("SEME Difference: ", abs(SEME - SEME1).max())
    print("SEME Difference0: ", abs(SEME[i] - SEME1[i]))
    print("\nImports: \n", MImport[i], "\n",\
          "\nPositive: \n", MLoad[i], "\n", MChargePH[i], "\n", MChargeB[i], "\n", MSpillage[i], "\n",\
          "\nNegative: \n", MPV[i], "\n", MInter[i], "\n", MBaseload[i], "\n", MPeak[i], "\n", MGas[i], "\n", MDischargePH[i], "\n", MDischargeB[i], "\n", MDeficit[i], "\n")
    np.savetxt("Debug/TDC1.csv", TDC1, delimiter=",")
 """
    if output:
        MStoragePH = np.tile(solution.StoragePH, (nodes, 1)).transpose() * pcfactor # SPH(t, j), MWh
        MStorageB = np.tile(solution.StoragePH, (nodes, 1)).transpose() * bfactor # SPH(t, j), MWh
        solution.MPV, solution.Inter, solution.MBaseload, solution.MPeak, solution.MGas = (MPV, MInter, MBaseload, MPeak, MGas)
#        solution.MWind = MWind        
        solution.MDischargePH, solution.MChargePH, solution.MStoragePH = (MDischargePH, MChargePH, MStoragePH)
        solution.MDischargeB, solution.MChargeB, solution.MStorageB = (MDischargeB, MChargeB, MStorageB)
        solution.MDeficit, solution.MSpillage = (MDeficit, MSpillage)

    return TDC