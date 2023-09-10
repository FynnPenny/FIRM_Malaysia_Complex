# -*- coding: utf-8 -*-
"""
Created on Mon Dec  7 14:17:37 2020
@author: cheng + tim
"""

from Input import *
from Simulation import Reliability
import numpy as np
import datetime as dt

def fill_deficit(deficit,hydro,bio,gas,hydro_limit,bio_limit,gas_limit,hydro_annual,bio_annual,gas_annual,hflag,bflag,gflag,eff,step):
    idx = np.where(deficit > 0)[0]
    for idd, i in np.ndenumerate(idx):
        d = deficit[i]
        t = i
        count = 0
        #print("--------------------")
        #print(idd, " of ", len(idx))
        try:
            while d > 0 and t >= 0 and count < step:
                #print("t = ",t)
                year = t // 8760
                start = year * 8760
                end = (year+1) * 8760
                if t == i - 1:
                    ######## ADD BATTERY EFFICIENCY? #############
                    d = d / eff
                if hflag:
                    remaining = hydro_annual - sum(hydro[start:end])
                    assert remaining >= 0
                    hydro_c = min(hydro[t] + d, hydro_limit, hydro[t] + remaining)
                    d = d - (hydro_c - hydro[t])
                    hydro[t] = hydro_c
                    if remaining == 0:
                        print("Year", year, " annual limit met")
                        t = start - 1
                    else:
                        idxx = np.where(hydro < hydro_limit)[0]
                        t = sorted([i for i in idxx if i < t])[-1]
                if bflag:
                    if d > 0:
                        remaining = bio_annual - sum(bio[start:end])
                        assert remaining >= 0
                        bio_c = min(bio[t] + d, bio_limit, bio[t] + remaining)
                        d = d - (bio_c - bio[t])
                        bio[t] = bio_c
                        if remaining == 0:
                            t = start - 1
                        else:
                            idxx = np.where(bio < bio_limit)[0]
                            t = sorted([i for i in idxx if i < t])[-1]
                if gflag:
                    if d > 0:
                        remaining = gas_annual - sum(gas[start:end])
                        assert remaining >= 0
                        gas_c = min(gas[t] + d, gas_limit, gas[t] + remaining)
                        d = d - (gas_c - gas[t])
                        gas[t] = gas_c
                        if remaining == 0:
                            t = start - 1
                        else:
                            idxx = np.where(gas < gas_limit)[0]
                            t = sorted([i for i in idxx if i < t])[-1]
                count += 1
        except:
            continue
    return hydro,bio,gas

def save(h,b,g,suffix):
    np.savetxt('Results/Dispatch_Hydro' + suffix, h, fmt='%f', delimiter=',', newline='\n', header='Hydro')
    np.savetxt('Results/Dispatch_Bio' + suffix, b, fmt='%f', delimiter=',', newline='\n', header='Bio')
    np.savetxt('Results/Dispatch_Gas' + suffix, g, fmt='%f', delimiter=',', newline='\n', header='Gas')
    
def maxx(x):
    return np.reshape(x, (-1, 8760)).sum(axis=-1).max()/1e6

def mean(x):
    return x.sum()/years/1e6

def Analysis(optimisation_x,suffix):
    starttime = dt.datetime.now()
    print('Deficit fill starts at', starttime)

    S = Solution(optimisation_x)
    
    Deficit_energy1, Deficit_power1, Deficit1, DischargePH1, DischargeB1 = Reliability(S, hydro=baseload, bio=np.zeros(intervals), gas=np.zeros(intervals)) # Sj-EDE(t, j), MW
    Max_deficit1 = np.reshape(Deficit1, (-1, 8760)).sum(axis=-1) # MWh per year
    PFlexible_Gas = Deficit_power1.max() * pow(10, -3) # GW
    
    Deficit_energy2, Deficit_power2, Deficit2, DischargePH2, DischargeB2 = Reliability(S, hydro=np.ones(intervals) * CHydro.sum() * pow(10, 3), bio=np.zeros(intervals), gas=np.zeros(intervals))
    Max_deficit2 = np.reshape(Deficit2, (-1, 8760)).sum(axis=-1) # MWh per year
    PBio_Gas = Deficit_power2.max() * pow(10, -3) # GW

    Deficit_energy3, Deficit_power3, Deficit3, DischargePH3, DischargeB3 = Reliability(S, hydro=np.ones(intervals) * CHydro.sum() * pow(10, 3), bio=np.ones(intervals) * CBio.sum() * pow(10, 3), gas=np.zeros(intervals))
    Max_deficit3 = np.reshape(Deficit3, (-1, 8760)).sum(axis=-1) # MWh per year
    PGas = Deficit_power3.max() * pow(10, -3) # GW
    
    GHydro = (Max_deficit1 - Max_deficit2).max() / 0.8
    GBio = (Max_deficit2 - Max_deficit3).max() / 0.8
    GGas = Max_deficit3.max() / 0.8

    print("GGas_max:", GGas/1e6)
    print("GBio_max:", GBio/1e6)
    print("GHydro_max:",GHydro/1e6)
    
    GGas2 = Deficit3.sum() / years / 0.8
    GBio2 = Deficit2.sum() / years / 0.8 - GGas2
    GHydro2 = Deficit1.sum() / years / 0.8 - GBio2 - GGas2
    
    print("GGas_mean:", GGas2/1e6)
    print("GBio_mean:", GBio2/1e6)
    print("GHydro_mean:",GHydro2/1e6)

    hlimit = S.CHydro.sum() * pow(10, 3) # MW
    blimit = S.CBio.sum() * pow(10,3) # MW

    if (GGas == 0) and (GBio == 0):
        print("HYDRO ONLY")
        print("------------------------------")
        hydro = baseload
        bio = np.zeros(intervals)
        gas = np.zeros(intervals)
        Deficit_energy, Deficit_power, Deficit, DischargePH, DischargeB = Reliability(S, hydro=hydro, bio=bio, gas=gas)
        h,b,g = fill_deficit(Deficit,hydro,bio,gas,hlimit,blimit,sum(S.CGas)*1e3,Hydromax,Biomax,Gasmax,True,False,False,0.8,168)
        Deficit_energy, Deficit_power, Deficit, DischargePH, DischargeB = Reliability(S, hydro=h, bio=b, gas=g)
        print("Hydro generation:", maxx(h))
        print("Remaining deficit:", Deficit.sum()/1e6)
        step = 1
        while Deficit.sum() > allowance*years and step < 50:
            h,b,g = fill_deficit(Deficit,h,b,g,hlimit,blimit,sum(S.CGas)*1e3,Hydromax,Biomax,Gasmax,True,False,False,0.8,168)
            Deficit_energy, Deficit_power, Deficit, DischargePH, DischargeB = Reliability(S, hydro=h, bio=b, gas=g)
            step += 1
        print("Hydro generation max:", maxx(h))
        print("Hydro generation mean:", mean(h))
        print("Remaining deficit final:", Deficit.sum()/1e6)
    
    elif GGas == 0:
        print("HYDRO + BIO ONLY")
        print("------------------------------")
        hydro = np.ones(intervals) * hlimit
        bio = np.zeros(intervals)
        gas = np.zeros(intervals)
        Deficit_energy, Deficit_power, Deficit, DischargePH, DischargeB = Reliability(S, hydro=hydro, bio=bio, gas=gas)
        h,b,g = fill_deficit(Deficit,hydro,bio,gas,hlimit,blimit,sum(S.CGas)*1e3,Hydromax,Biomax,Gasmax,False,True,False,0.8,168)
        Deficit_energy, Deficit_power, Deficit, DischargePH, DischargeB = Reliability(S, hydro=h, bio=b, gas=g)
        np.savetxt("Debug/Deficit.csv",Deficit)
        print("Bio generation:", maxx(b))
        print("Remaining deficit:", Deficit.sum()/1e6)
        step = 1
        while Deficit.sum() > allowance*years and step < 50:
            h,b,g = fill_deficit(Deficit,h,b,g,hlimit,blimit,sum(S.CGas)*1e3,Hydromax,Biomax,Gasmax,False,True,False,0.8,168)
            Deficit_energy, Deficit_power, Deficit, DischargePH, DischargeB = Reliability(S, hydro=h, bio=b, gas=g)
            step += 1
        print("Bio generation max:", maxx(b))
        print("Bio generation mean:", mean(b))
        print("Remaining deficit final:", Deficit.sum()/1e6)
        if Deficit.sum() < allowance*years:
            hydro = baseload
            Deficit_energy, Deficit_power, Deficit, DischargePH, DischargeB = Reliability(S, hydro=hydro, bio=b, gas=g)
            h,b,g = fill_deficit(Deficit,hydro,b,g,hlimit,blimit,sum(S.CGas)*1e3,Hydromax,Biomax,Gasmax,True,False,False,0.8,168)
            Deficit_energy, Deficit_power, Deficit, DischargePH, DischargeB = Reliability(S, hydro=h, bio=b, gas=g)
            print("Hydro generation:", maxx(h))
            print("Remaining deficit:", Deficit.sum()/1e6)
            step = 1
            while Deficit.sum() > allowance*years and step < 50:
                h,b,g = fill_deficit(Deficit,hydro,b,g,hlimit,blimit,sum(S.CGas)*1e3,Hydromax,Biomax,Gasmax,True,False,False,0.8,168)
                Deficit_energy, Deficit_power, Deficit, DischargePH, DischargeB = Reliability(S, hydro=h, bio=b, gas=g)
                step += 1
            print("Hydro generation max:", maxx(h))
            print("Hydro generation mean:", mean(h))
            print("Remaining deficit final:", Deficit.sum()/1e6)
        
    else:
        print("HYDRO + BIO + GAS")
        print("------------------------------")
        hydro = np.ones(intervals) * hlimit
        bio = np.ones(intervals) * blimit
        gas = np.zeros(intervals)
        Deficit_energy, Deficit_power, Deficit, DischargePH, DischargeB = Reliability(S, hydro=hydro, bio=bio, gas=gas)
        h,b,g = fill_deficit(Deficit,hydro,bio,gas,hlimit,blimit,sum(S.CGas)*1e3,Hydromax,Biomax,Gasmax,False,False,True,0.8,168)
        Deficit_energy, Deficit_power, Deficit, DischargePH, DischargeB = Reliability(S, hydro=h, bio=b, gas=g)
        print("Gas generation:", maxx(g))
        print("Remaining deficit:", Deficit.sum()/1e6)
        step = 1
        while Deficit.sum() > allowance*years and step < 50:
            h,b,g = fill_deficit(Deficit,h,b,g,hlimit,blimit,sum(S.CGas)*1e3,Hydromax,Biomax,Gasmax,False,False,True,0.8,168)
            Deficit_energy, Deficit_power, Deficit, DischargePH, DischargeB = Reliability(S, hydro=h, bio=b, gas=g)
            step += 1
        print("Gas generation max:", maxx(g))
        print("Gas generation mean:", mean(g))
        print("Remaining deficit final:", Deficit.sum()/1e6)
        if Deficit.sum() < allowance*years:
            bio = np.zeros(intervals)
            Deficit_energy, Deficit_power, Deficit, DischargePH, DischargeB = Reliability(S, hydro=h, bio=bio, gas=g)
            h,b,g = fill_deficit(Deficit,hydro,bio,g,hlimit,blimit,sum(S.CGas)*1e3,Hydromax,Biomax,Gasmax,False,True,False,0.8,168)
            Deficit_energy, Deficit_power, Deficit, DischargePH, DischargeB = Reliability(S, hydro=h, bio=b, gas=g)
            print("Bio generation:", maxx(b))
            print("Remaining deficit:", Deficit.sum()/1e6)
            step = 1
            while Deficit.sum() > allowance*years and step < 50:
                h,b,g = fill_deficit(Deficit,hydro,b,g,hlimit,blimit,sum(S.CGas)*1e3,Hydromax,Biomax,Gasmax,False,True,False,0.8,168)
                Deficit_energy, Deficit_power, Deficit, DischargePH, DischargeB = Reliability(S, hydro=h, bio=b, gas=g)
                step += 1
            print("Bio generation max:", maxx(b))
            print("Bio generation mean:", mean(b))
            print("Remaining deficit final:", Deficit.sum()/1e6)
        if Deficit.sum() < allowance*years:
            hydro = baseload
            Deficit_energy, Deficit_power, Deficit, DischargePH, DischargeB = Reliability(S, hydro=hydro, bio=b, gas=g)
            h,b,g = fill_deficit(Deficit,hydro,b,g,hlimit,blimit,sum(S.CGas)*1e3,Hydromax,Biomax,Gasmax,True,False,False,0.8,168)
            Deficit_energy, Deficit_power, Deficit, DischargePH, DischargeB = Reliability(S, hydro=h, bio=b, gas=g)
            print("Hydro generation:", maxx(h))
            print("Remaining deficit:", Deficit.sum()/1e6)
            step = 1
            while Deficit.sum() > allowance*years and step < 50:
                h,b,g = fill_deficit(Deficit,hydro,b,g,hlimit,blimit,sum(S.CGas)*1e3,Hydromax,Biomax,Gasmax,True,False,False,0.8,168)
                Deficit_energy, Deficit_power, Deficit, DischargePH, DischargeB = Reliability(S, hydro=h, bio=b, gas=g)
                step += 1
            print("Hydro generation max:", maxx(h))
            print("Hydro generation mean:", mean(h))
            print("Remaining deficit final:", Deficit.sum()/1e6)

    save(h,b,g,suffix)

    endtime = dt.datetime.now()
    print('Deficit fill took', endtime - starttime)

    from Statistics import Information
    Information(optimisation_x,h,b,g)

    return True

if __name__=='__main__':
    suffix = "_APG_MY_Isolated_HVAC_5.csv"
    optimisation_x = np.genfromtxt('Results/Optimisation_resultx{}'.format(suffix).format(node,scenario,percapita), delimiter=',')
    Analysis(optimisation_x,'.csv')