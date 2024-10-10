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

        # if solution.node=='APG_Full':
        #     MInter[i, :] = solution.GInter[:, np.where(Interl==j)[0]].sum(axis=1)

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
              - MPV - MWind - MInter - MHydro - MBio - MGas - MDischargePH - MDischargeB - MDeficit #; EIM(t, j), MW
    
    coverage = solution.coverage 
    
    if np.size(coverage) > 1:
        # Imports into outer internal nodes
        FQ = -1 *   MImport[:, np.where(Nodel=='FNQ')[0][0]] if 'FNQ' in coverage else np.zeros(intervals)
        AS = -1 *   MImport[:, np.where(Nodel=='NT ')[0][0]] if 'NT ' in coverage else np.zeros(intervals)
        SW =        MImport[:, np.where(Nodel=='WA ')[0][0]] if 'WA ' in coverage else np.zeros(intervals)
        TV = -1 *   MImport[:, np.where(Nodel=='TAS')[0][0]]
        # Imports into inner internal nodes
        NQ =        MImport[:, np.where(Nodel=='QLD')[0][0]] - FQ
        NV =        MImport[:, np.where(Nodel=='VIC')[0][0]] - TV
        # Check the final node
        NS = -1 *   MImport[:, np.where(Nodel=='NSW')[0][0]] - NQ - NV
        NS1 =       MImport[:, np.where(Nodel=='SA' )[0][0]] - AS + SW
       
        # max_diff = abs(NS - NS1).max()
        # total_diff = np.array([FQ, NQ, NV, TV, NS, SW, AS]).sum(1)
        # assert max_diff<=0.1, f"Difference {max_diff} exceeds threshold 0.1. Total diff: {total_diff}"

        TDC = np.array([FQ, NQ, NV, TV, NS, SW, AS]).transpose() # TDC(t, k), MW

    else:
        TDC = np.zeros((intervals, len(solution.TLoss)))

    if output:
        MStoragePH = np.tile(solution.StoragePH, (nodes, 1)).transpose() * pcfactor # SPH(t, j), MWh
        MStorageB  = np.tile(solution.StoragePH, (nodes, 1)).transpose() * bfactor  # SPH(t, j), MWh
        solution.MPV, solution.MInter, solution.MHydro, solution.MBio, solution.MGas = (MPV, MInter, MHydro, MBio, MGas)
        solution.MWind = MWind
        solution.MDischargePH, solution.MChargePH, solution.MStoragePH = (MDischargePH, MChargePH, MStoragePH)
        solution.MDischargeB, solution.MChargeB, solution.MStorageB = (MDischargeB, MChargeB, MStorageB)
        solution.MDeficit, solution.MSpillage = (MDeficit, MSpillage)

    return TDC