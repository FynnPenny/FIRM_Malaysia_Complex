# A transmission network model to calculate inter-regional power flows
# Copyright (c) 2019, 2020 Bin Lu, The Australian National University
# Licensed under the MIT Licence
# Correspondence: bin.lu@anu.edu.au

import numpy as np

def Transmission(solution, output=False):
    """TDC = Network.Transmission(S)"""

    Nodel, PVl, Windl, Interl = (solution.Nodel, solution.PVl, solution.Windl, solution.Interl)
    intervals, nodes = (solution.intervals, solution.nodes)

    MPV, MWind, MInter = map(np.zeros, [(nodes, intervals)] * 3)
    for i, j in enumerate(Nodel):
        MPV[i, :] = solution.GPV[:, np.where(PVl==j)[0]].sum(axis=1)
        MWind[i, :] = solution.GWind[:, np.where(Windl==j)[0]].sum(axis=1)
        if solution.node=='APG':
            MInter[i, :] = solution.GInter[:, np.where(Interl==j)[0]].sum(axis=1)
    MPV, MWind, MInter = (MPV.transpose(), MWind.transpose(), MInter.transpose()) # Sij-GPV(t, i), Sij-GWind(t, i), MW

    ###### TO FIX: DOUBLE CHECK THIS
    MBaseload = solution.GBaseload # MW
    CPeak = solution.CPeak # GW
    pkfactor = np.tile(CPeak, (intervals, 1)) / CPeak.sum()
    MPeak = np.tile(solution.flexible, (nodes, 1)).transpose() * pkfactor # MW

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

    MPW = MPV + MWind
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
              - MPV - MWind - MInter - MBaseload - MPeak - MGas - MDischargePH - MDischargeB - MDeficit # EIM(t, j), MW

    # Imorts into external nodes
    THKD = MImport[:, np.where(Nodel=='TH')[0][0]]
    PHSB = MImport[:, np.where(Nodel=='PH')[0][0]]
    INSE = -1 * MImport[:, np.where(Nodel=='IN')[0][0]]

    # Imports into outer internal nodes
    KTTE = MImport[:, np.where(Nodel=='KT')[0][0]]

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

    if output:
        MStoragePH = np.tile(solution.StoragePH, (nodes, 1)).transpose() * pcfactor # SPH(t, j), MWh
        MStorageB = np.tile(solution.StoragePH, (nodes, 1)).transpose() * bfactor # SPH(t, j), MWh
        solution.MPV, solution.MWind, solution.Inter, solution.MBaseload, solution.MPeak, solution.MGas = (MPV, MWind, MInter, MBaseload, MPeak, MGas)
        solution.MDischargePH, solution.MChargePH, solution.MStoragePH = (MDischargePH, MChargePH, MStoragePH)
        solution.MDischargeB, solution.MChargeB, solution.MStorageB = (MDischargeB, MChargeB, MStorageB)
        solution.MDeficit, solution.MSpillage = (MDeficit, MSpillage)

    return TDC