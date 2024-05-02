# A transmission network model to calculate inter-regional power flows
# Copyright (c) 2019, 2020 Bin Lu, The Australian National University
# Licensed under the MIT Licence
# Correspondence: bin.lu@anu.edu.au

import numpy as np

def Transmission(solution, output=False):
    """TDC = Network.Transmission(S)"""

    Nodel, PVl, Interl = (solution.Nodel, solution.PVl, solution.Interl)
    Windl = solution.Windl
    intervals, nodes = (solution.intervals, solution.nodes)

    MPV    = np.zeros((nodes,intervals))
    MInter = np.zeros((nodes,intervals))
    MWind  = np.zeros((nodes,intervals))
    for i, j in enumerate(Nodel):
        MPV  [i, :] = solution.GPV  [:, np.where(PVl  ==j)[0]].sum(axis=1)
        MWind[i, :] = solution.GWind[:, np.where(Windl==j)[0]].sum(axis=1)

        if solution.node=='APG_Full':
            MInter[i, :] = solution.GInter[:, np.where(Interl==j)[0]].sum(axis=1)

    MPV, MInter = (MPV.transpose(), MInter.transpose()) # Sij-GPV(t, i), Sij-GWind(t, i), MW
    MWind = MWind.transpose()
  
    CHydro = solution.CHydro
    hfactor = np.tile(CHydro,(intervals, 1)) / CHydro.sum() if CHydro.sum() > 0 else np.tile(CHydro,(intervals, 1))
    MHydro = np.tile(solution.hydro, (nodes, 1)).transpose() * hfactor

    CBio = solution.CBio
    bfactor = np.tile(CBio,(intervals, 1)) / CBio.sum() if CBio.sum() > 0 else np.tile(CBio,(intervals, 1))
    MBio = np.tile(solution.bio, (nodes, 1)).transpose() * bfactor

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

    M_minFactors = np.full((intervals, nodes), pow(10,-9)) # Matrix of 10^(-9) required to distribute spillage between nodes when no solar generation
    MPW = MPV + M_minFactors + MWind
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
              - MPV - MInter - MHydro - MBio - MGas - MDischargePH - MDischargeB - MDeficit # - MWind; EIM(t, j), MW
    
    coverage = solution.coverage
    if len(coverage) > 1:
        # Imports into external nodes
        THKD = -1 * MImport[:, np.where(Nodel=='TH')[0][0]] if 'TH' in coverage else np.zeros(intervals)
        PHSB = -1 * MImport[:, np.where(Nodel=='PH')[0][0]] if 'PH' in coverage else np.zeros(intervals)
        INSE = MImport[:, np.where(Nodel=='IN')[0][0]] if 'IN' in coverage else np.zeros(intervals)

        # Imports into outer internal nodes
        KTTE = -1 * MImport[:, np.where(Nodel=='KT')[0][0]] if 'KT' in coverage else np.zeros(intervals)

        # Imports into inner internal nodes
        KDPE = MImport[:, np.where(Nodel=='KD')[0][0]] - THKD if 'KD' in coverage else np.zeros(intervals)
        SBSW = MImport[:, np.where(Nodel=='SB')[0][0]] - PHSB if 'SB' in coverage else np.zeros(intervals)
        TEPA = MImport[:, np.where(Nodel=='TE')[0][0]] - KTTE if 'TE' in coverage else np.zeros(intervals)

        JOSW = -1 * MImport[:, np.where(Nodel=='SW')[0][0]] - SBSW if 'SW' in coverage else np.zeros(intervals)
        PASE = -1 * MImport[:, np.where(Nodel=='PA')[0][0]] - TEPA if 'PA' in coverage else np.zeros(intervals)
        PESE = -1 * MImport[:, np.where(Nodel=='PE')[0][0]] - KDPE if 'PE' in coverage else np.zeros(intervals)
        
        MEJO = MImport[:, np.where(Nodel=='JO')[0][0]] - JOSW if 'JO' in coverage else np.zeros(intervals)
        SEME = -1 * MImport[:, np.where(Nodel=='ME')[0][0]] - MEJO if 'ME' in coverage else np.zeros(intervals)

        # Check the final node
        SEME1 = MImport[:, np.where(Nodel=='SE')[0][0]] + INSE - PASE - PESE if 'SE' in coverage else np.zeros(intervals)
        SBSW1 = -1 * MImport[:, np.where(Nodel=='SW')[0][0]] - JOSW if 'SW' in coverage else np.zeros(intervals)

        assert abs(SEME - SEME1).max() <= 0.1, print('SEME Error', abs(SEME - SEME1).max())
        assert abs(SBSW - SBSW1).max() <= 0.1, print('SBSW Error', abs(SBSW - SBSW1).max())

        TDC = np.array([KDPE, TEPA, SEME, MEJO, PESE, SBSW, KTTE, PASE, JOSW, THKD, INSE, PHSB]).transpose() # TDC(t, k), MW   
    
    else:
        TDC = np.zeros((intervals, len(solution.TLoss)))

    if output:
        MStoragePH = np.tile(solution.StoragePH, (nodes, 1)).transpose() * pcfactor # SPH(t, j), MWh
        MStorageB = np.tile(solution.StoragePH, (nodes, 1)).transpose() * bfactor # SPH(t, j), MWh
        solution.MPV, solution.MInter, solution.MHydro, solution.MBio, solution.MGas = (MPV, MInter, MHydro, MBio, MGas)
        solution.MWind = MWind        
        solution.MDischargePH, solution.MChargePH, solution.MStoragePH = (MDischargePH, MChargePH, MStoragePH)
        solution.MDischargeB, solution.MChargeB, solution.MStorageB = (MDischargeB, MChargeB, MStorageB)
        solution.MDeficit, solution.MSpillage = (MDeficit, MSpillage)

    return TDC