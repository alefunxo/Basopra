#!/usr/bin/python3
# -*- coding: utf-8 -*-
## @namespace Core_LP
# Created on Tue Oct 31 11:11:33 2017
# Author
# Alejandro Pena-Bello
# alejandro.penabello@unige.ch
# script used for the paper Optimization of PV-coupled battery systems for combining applications: impact of battery technology and location (Pena-Bello et al 2018 to be published).
# This script prepares the input for the LP algorithm and get the output in a dataframe, finally it saves the output.
# Description
# -----------
# INPUTS
# ------
# OUTPUTS
# -------
# TODO
# ----
# User Interface, including path to save the results and choose countries, load curves, etc.
# Requirements
# ------------
# Pandas, numpy, pyomo, pickle, math, sys,glob, time

import pandas as pd
import paper_classes as pc
from pyomo.opt import SolverFactory, SolverStatus, TerminationCondition
from pyomo.core import Var
import time
import numpy as np
import LP as optim
import math
import pickle
import sys
import glob
from functools import wraps
import csv
import os
import tempfile
import post_proc as pp
import threading
from pathlib import Path

def fn_timer(function):
    @wraps(function)
    def function_timer(*args, **kwargs):
        t0 = time.time()
        result = function(*args, **kwargs)
        t1 = time.time()
        print ("Total time running %s: %s seconds" %
               (function.__name__, str(t1-t0))
               )
        return result
    return function_timer

def Get_output(instance):
    '''
    Gets the model output and transforms it into a pandas dataframe
	with the desired names.
    Parameters
    ----------
    instance : instance of pyomo
    Returns
    -------
    df : DataFrame
    P_max_ : vector of daily maximum power
    '''
    #to write in a csv goes faster than actualize a df

    np.random.seed()
    filename='out'+str(np.random.randint(1, 10, 10))[1:-1].replace(" ", "")+'.csv'
    with open(filename, 'a') as f:
        writer = csv.writer(f, delimiter=';')
        for v in instance.component_objects(Var, active=True):
          varobject = getattr(instance, str(v))
          for index in varobject:
              if str(v) =='P_max_day':
                  P_max_=(v[index].value)
              else:
                  writer.writerow([index, varobject[index].value, v])
    df=pd.read_csv(filename,sep=';',names=['val','var'])
    os.remove(filename)
    df=df.pivot_table(values='val', columns='var',index=df.index)
    df=df.drop(-1)
    return [df,P_max_]
@fn_timer
def Optimize(Capacity,Tech,App_comb,data_input,
            param):

    """
    This function calls the LP and controls the aging. The aging is then
    calculated in daily basis and the capacity updated. When the battery
    reaches the EoL the loop breaks. 'days' allows to optimize multiple days at once.

    Parameters
    ----------
    Capacity : float
    Tech : string
    App_comb : array
    data_input: DataFrame
    param: dict

    Returns
    -------
    df : DataFrame
    aux_Cap_arr : array
    SOH_arr : array
    Cycle_aging_factor : array
    P_max_arr : array
    results_arr : array
    cycle_cal_arr : array
    DoD_arr : array
    """
    print(App_comb)
    print(Tech)
    print(Capacity)
    days=1
    dt=param['delta_t']
    end_d=int(param['ndays']*24/dt)
    window=int(24*days/dt)
    print(end_d)

    print('%%%%%%%%% Optimizing %%%%%%%%%%%%%%%')
    if param['cases']==False:
        Batt=pc.Battery_tech(Capacity=Capacity,Technology=Tech)
    else:
        Batt=pc.Battery_case(Capacity=Capacity,Technology=Tech,case=param['cases'])

    aux_Cap_arr=np.zeros(param['ndays'])
    SOC_max_arr=np.zeros(param['ndays'])
    SOH_arr=np.zeros(param['ndays'])
    P_max_arr=np.zeros(param['ndays'])
    cycle_cal_arr=np.zeros(param['ndays'])
    results_arr=[]
    DoD_arr=np.zeros(param['ndays'])
    aux_Cap=Batt.Capacity
    SOC_max_=Batt.SOC_max
    SOH_aux=1

    for i in range(int(param['ndays']/days)):
        print(i, end='')
        toy=0
        if i==0:
            aux_Cap_aged=Batt.Capacity
            aux_SOC_max=Batt.SOC_max
            SOH=1
        else:
            aux_Cap_aged=aux_Cap
            aux_SOC_max=SOC_max_
            SOH=SOH_aux
        data_input_=data_input[data_input.index.dayofyear==data_input.index.dayofyear[0]+i]
        if App_comb[2]==True:
            if App_comb[3]==True:
                retail_price_dict=dict(enumerate(data_input_.Price_DT_mod))
            else:
                retail_price_dict=dict(enumerate(data_input_.Price_DT))
        else:
            if App_comb[3]==True:
                retail_price_dict=dict(enumerate(data_input_.Price_flat_mod))
            else:
                retail_price_dict=dict(enumerate(data_input_.Price_flat))

        Export_price_dict=dict(enumerate(data_input_.Export_price))
        E_demand_dict=dict(enumerate(data_input_.E_demand))
        E_PV_dict=dict(enumerate(data_input_.E_PV))
        Set_declare=np.arange(-1,data_input_.shape[0])

        param.update({'SOC_max':aux_SOC_max,
    		'Batt':Batt,
    		'Export_price':Export_price_dict,
    		'Set_declare':Set_declare,
    		'E_demand':E_demand_dict,'E_PV':E_PV_dict,
    		'retail_price':retail_price_dict,
    		'App_comb':dict(enumerate(App_comb))})
            #Max_inj is in kW

        param['Max_inj']=param['Curtailment']*param['PV_nom']


        instance = optim.Concrete_model(param)
        if sys.platform=='win32':
            opt = SolverFactory('cplex')

        else:
            opt = SolverFactory('cplex',executable='/opt/ibm/ILOG/'
                            'CPLEX_Studio1271/cplex/bin/x86-64_linux/cplex')

        results = opt.solve(instance)#,tee=True)
        #results.write(num=1)

        if (results.solver.status == SolverStatus.ok) and (results.solver.termination_condition == TerminationCondition.optimal):

        # Do something when the solution is optimal and feasible
            [df_1,P_max]=Get_output(instance)

            if param['aging']:
                [SOC_max_,aux_Cap,SOH_aux,Cycle_aging_factor,cycle_cal,DoD]=aging_day(
                df_1.E_char,SOH,Batt.SOC_min,Batt,aux_Cap_aged)
                DoD_arr[i]=DoD
                cycle_cal_arr[i]=cycle_cal
                P_max_arr[i]=P_max
                aux_Cap_arr[i]=aux_Cap
                SOC_max_arr[i]=SOC_max_
                SOH_arr[i]=SOH_aux
            else:
                DoD_arr[i]=df_1.E_dis.sum()/Batt.Capacity
                cycle_cal_arr[i]=0
                P_max_arr[i]=P_max
                aux_Cap_arr[i]=aux_Cap
                SOC_max_arr[i]=SOC_max_
                SOH_arr[i]=SOH_aux
                Cycle_aging_factor=0
            results_arr.append(instance.total_cost())
            if i==0:#initialize
                df=pd.DataFrame(df_1)
            elif i==param['ndays']-1:#if we go until the end of the days
                df=df.append(df_1,ignore_index=True)
                if SOH<=0:
                    break
                if param['ndays']/365>Batt.Battery_cal_life:
                    break
            else:#if SOH or ndays are greater than the limit
                df=df.append(df_1,ignore_index=True)
                if SOH<=0:
                    df=df.append(df_1,ignore_index=True)
                    end_d=df.shape[0]
                    break
                if i/365>Batt.Battery_cal_life:
                    df=df.append(df_1,ignore_index=True)
                    break
        elif (results.solver.termination_condition == TerminationCondition.infeasible):

            # Do something when model is infeasible
            print('Termination condition',results.solver.termination_condition)
            return (None,None,None,None,None,None,None,None,results)
        else:
            # Something else is wrong
            print ('Solver Status: ',  results.solver.status)
            return (None,None,None,None,None,None,None,None,results)
    end_d=df.shape[0]
    df=pd.concat([df,data_input.loc[data_input.index[:end_d],['E_demand','E_PV','Export_price']].reset_index()],axis=1)
    if App_comb[2]==True:
        if App_comb[3]==True:
            df['price']=data_input.Price_DT_mod.reset_index(drop=True)[:end_d].values
        else:
            df['price']=data_input.Price_DT.reset_index(drop=True)[:end_d].values
    else:
        if App_comb[3]==True:
            df['price']=data_input.Price_flat_mod.reset_index(drop=True)[:end_d].values
        else:
            df['price']=data_input.Price_flat.reset_index(drop=True)[:end_d].values
    df['Inv_P']=((df.E_PV_load+df.E_dis+df.E_PV_grid+df.E_loss_inv)/dt)
    df['Conv_P']=((df.E_PV_load+df.E_PV_batt+df.E_PV_grid
                  +df.E_loss_conv)/dt)

    df.set_index('index',inplace=True)
    return (df,aux_Cap_arr,SOH_arr,Cycle_aging_factor,P_max_arr,results_arr,cycle_cal_arr,DoD_arr,results)
def get_cycle_aging(DoD,Technology):
    '''
    The cycle aging factors are defined for each technology according
	to the DoD using an exponential function close to the Woehler curve.
    Parameters
    ----------
    DoD : float
    Technology : string

    Returns
    -------
    Cycle_aging_factor : float
    '''
    if Technology=='LTO':#Xalt 60Ah LTO Model F920-0006
        Cycle_aging_factor=1/(math.exp((math.log(DoD)-math.log(771.51))/-0.604)-45300)#R2=.9977
    elif Technology=='LFP':#https://doi.org/10.1016/j.apenergy.2013.09.003
        Cycle_aging_factor=1/(math.exp((math.log(DoD)-math.log(70.869))/-0.54)+1961.37135)#R2=.917
    elif Technology=='NCA':#Saft Evolion
        #Cycle_aging_factor=1/(math.exp((math.log(DoD)-math.log(1216.7))/-0.869)-289.736058)#R2=.9675 SAFT
        Cycle_aging_factor=1/(math.exp((math.log(DoD)-math.log(1216.7))/-0.869)+4449.67011)#TRINA BESS
    elif Technology=='NMC':#Tesla Truong et al. 2016
        Cycle_aging_factor=1/(math.exp((math.log(DoD)-math.log(1E8))/-2.168))
    elif Technology=='ALA':#Sacred sun FCP-1000 lead carbon
        Cycle_aging_factor=1/(math.exp((math.log(DoD)-math.log(37403))/-1.306)+330.656417)#R2=.9983
    elif Technology=='VRLA':#Sonnenschein
        Cycle_aging_factor=1/(math.exp((math.log(DoD)-math.log(667.61))/-.988))#R2=0.99995
    elif Technology=='test':
        Cycle_aging_factor=1/(math.exp((math.log(DoD)-math.log(238.86))/-0.875)+4482.74484)#R2=.961
    return Cycle_aging_factor

def aging_day(daily_ESB,SOH,SOC_min,Batt,aux_Cap):
    """"
    A linear relationship between the capacity loss with the maximum battery
    life (years) was chosen. The values of calendric lifetime provide a
    reference value for storage degradation to 70% SOH at 20 °C temperature,
    when no charge throughput is applied [1].

    The temperature is assumed to be controlled and its effect on the battery
    aging minimized. As for the cyclic aging, we use a similar approach as the
    presented by Magnor et al. assuming different Woehler curves for different
    battery technologies [2]. The Woehler curves are provided in the
    specifications for some technologies (e.g. NCA), when the curve is not
    provided, we use other manufacturer curve, which use the same technology
    and adapt it to the referenced number of cycles of the real manufacturer.
    The cyclic agingis then the number of cycles per day at the given DoD,
    divided by the maximum number of cycles at a given DoD.

    [1] H. C. Hesse, R. Martins, P. Musilek, M. Naumann, C. N. Truong, and A.
    Jossen, “Economic Optimization of Component Sizing for Residential
    Battery Storage Systems,” Energies, vol. 10, no. 7, p. 835, Jun. 2017.

    [2]D. U. Sauer, P. Merk, M. Ecker, J. B. Gerschler, and D. Magnor, “Concept
    of a Battery Aging Model for Lithium-Ion Batteries Considering the Lifetime
    Dependency on the Operation Strategy,” 24th Eur. Photovolt. Sol. Energy
    Conf. 21-25 Sept. 2009 Hambg. Ger., pp. 3128–3134, Nov. 2009.

    cycle_cal indicates which aging dominates in the day if 1 cycle is dominating.
    Parameters
    ----------
    daily_ESB : array
    SOH : float
    SOC_min : float
    Batt : class
    aux_Cap : float

    Returns
    -------
    SOC_max : float
    aux_Cap : float
    SOH : float
    Cycle_aging_factor : float
    cycle_cal : int
    DoD : float
    """
    #aging is daily
    Cal_aging_factor=1/(Batt.Battery_cal_life*24*365)
    aux_DOD=(Batt.SOC_max-Batt.SOC_min)/Batt.Capacity
    DoD=daily_ESB.sum()/Batt.Capacity
    if DoD==0:
        Cycle_aging_factor=get_cycle_aging(DoD+0.00001,Batt.Technology)
    elif DoD<=1:
        Cycle_aging_factor=get_cycle_aging(DoD,Batt.Technology)
    else:
        aux_DoD=DoD-int(DoD)
        Cycle_aging_factor=get_cycle_aging(aux_DoD,Batt.Technology)
        for i in range(int(DoD)):
            Cycle_aging_factor+=get_cycle_aging(1,Batt.Technology)
    #Linearize SOH in [0,1]
    #SOH=0 if EoL (70% CNom)
    SOH=1/.3*aux_Cap/Batt.Capacity-7/3
    aging=max(Cycle_aging_factor,Cal_aging_factor*24)
    aux_Cap=Batt.Capacity*(1-0.3*(1-SOH+aging))
    if Cycle_aging_factor>(Cal_aging_factor*24):
        cycle_cal=1
    else:
        cycle_cal=0
    SOC_max=Batt.SOC_min+aux_Cap*(aux_DOD)
    return [SOC_max,aux_Cap,SOH,Cycle_aging_factor,cycle_cal,DoD]

def single_opt2(param, data_input, name):
    """"
    Iterates over capacities, technologies and applications and calls the module to save the results.
    Parameters
    ----------
    param: dict
    data_input: DataFrame
    name: string

    Returns
    -------
    df : DataFrame
    Cap_arr : array
    SOH : float
    Cycle_aging_factor : float
    P_max : float
    results : float
    cycle_cal_arr :array
    """
    print('@@@@@@@@@@@@@@@@@@@@@@@@@@')
    print('single_opt2')

    aux_app_comb=param['App_comb']#afterwards is modified to send to LP
    print('Printing cases')
    print(param['cases'])
    param.update({'cases':param['cases']})
    print('enter optimize1')
    [df,Cap_arr,SOH,Cycle_aging_factor,P_max,results, cycle_cal_arr,DoD_arr,aux]=Optimize(param['Capacity'],param['Tech'],param['App_comb'],data_input,param)
    print('out of optimize1')
    param.update({'App_comb':aux_app_comb})
    save_results(name,df,param['Tech'], aux_app_comb,param['Capacity'],Cap_arr,SOH,Cycle_aging_factor,P_max,results,cycle_cal_arr,param['PV_nom'],DoD_arr,param['cases'],0)
    aggregate_results(name,df,aux_app_comb,param,Cap_arr,SOH,Cycle_aging_factor,P_max,results,cycle_cal_arr,DoD_arr,0)
    return  [df,Cap_arr,SOH,Cycle_aging_factor,P_max,results,cycle_cal_arr]

def aggregate_results(name,df,aux_app_comb,param,Cap_arr,SOH,Cycle_aging_factor,P_max,results,cycle_cal_arr,DoD_arr,status):
    '''
    Takes the results from the whole year optimization and gets the aggregated results.
    Parameters
    ----------
    name : string
    df : DataFrame
    Cap_arr : array
    SOH : float
    Cycle_aging_factor : float
    P_max :float
    results : array
    cycle_cal_arr : array
    DoD_arr : array
    Returns
    -------
    bool
        True if successful, False otherwise.
    '''
    #attention E_batt_load

    try:
        print("OUIIIIIIIIIIIIII")
        Capacity_aux=param['Capacity']
        if Capacity_aux%1>0:

            Capacity_aux=str(param['Capacity']).replace('.','_')

        df=df.loc[:,['E_PV_batt', 'E_PV_curt', 'E_PV_grid', 'E_PV_load',
        'E_char', 'E_cons', 'E_dis',
       'E_grid_batt', 'E_grid_load', 'E_loss_Batt',
       'E_loss_conv', 'E_loss_inv', 'E_loss_inv_PV', 'E_loss_inv_batt',
       'E_loss_inv_grid', 'SOC', 'E_demand', 'E_PV', 'Export_price',
       'price', 'Inv_P', 'Conv_P']]
        dict_res={'df':df,'Tech':param['Tech'], 'App_comb': param['App_comb'], 'Capacity':Capacity_aux,
        'Cap_arr':Cap_arr,'SOH':SOH,'DoD':DoD_arr,
        'Cycle1_aging0_factor':Cycle_aging_factor,'P_max':P_max,'name':name,
        'results':results,'cycle_cal_arr':cycle_cal_arr,'PV_nom':param['PV_nom'],'cases':param['cases'],'status':status}

        col = ["%i" % x for x in param['App_comb']]
        name_comb=col[0]+col[1]+col[2]+col[3]

        [agg_results]=pp.get_main_results(dict_res,param)

        print(agg_results.head())
        filename=Path('../Output/aggregated_results_ext.csv')

        write_csv(filename,agg_results.values)
        print(agg_results.keys())
        flag=0
    except IOError as e:
        flag=1
        print('Had some issues with the aggregated results')
        print ("I/O error({0}): {1}".format(e.errno, e.strerror))

    except ValueError:
        flag=1
        print('Had some issues with the aggregated results')
        print ("Could not convert data to an integer.")

    except:
        flag=1
        print('Had some issues with the aggregated results')
        print ("Unexpected error:", sys.exc_info()[0])
        print ("Unexpected error2:", sys.stderr)

    finally:


        if flag==1:
            print('in any case save the results')
            save_results(name,df,param['Tech'], param['App_comb'], param['Capacity'],Cap_arr,SOH,
                         Cycle_aging_factor,P_max,results,cycle_cal_arr,
                         param['PV_nom'],DoD_arr,param['cases'],status)
def write_csv(filename,val):#Should be saved in a DB
    print('write_csv')
    with open(filename, 'a', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(val)

def save_results(name,df,Tech, App_comb, Capacity,Cap_arr,SOH,
                 Cycle_aging_factor,P_max,results,cycle_cal_arr,
                 PV_nominal_power,DoD_arr,cases,status):
    '''
    Save the results in pickle format using the corresponding timezone.
	The file is saved in the same directory the program is saved.
	The name is structured as follows: df_name_tech_App_Cap.pickle
    Parameters
    ----------
    name : string
    df : DataFrame
    Tech : string
    App_comb : array
    Capacity : float
    Cap_arr : array
    SOH : float
    Cycle_aging_factor : float
    P_max :float
    results : array
    cycle_cal_arr : array
    PV_nominal_power : float
    DoD_arr : array
    Returns
    -------
    bool
        True if successful, False otherwise.
    '''
    try:
        print('saving')
        Capacity_aux=Capacity
        if Capacity%1>0:
            Capacity_aux=str(Capacity).replace('.','_')
        else:
            Capacity_aux=int(Capacity)
        df=df.loc[:,['E_PV_batt', 'E_PV_curt', 'E_PV_grid', 'E_PV_load',
           'E_char', 'E_cons', 'E_dis',
           'E_grid_batt', 'E_grid_load', 'E_loss_Batt',
           'E_loss_conv', 'E_loss_inv', 'E_loss_inv_PV', 'E_loss_inv_batt',
           'E_loss_inv_grid', 'SOC', 'E_demand', 'E_PV', 'Export_price',
           'price', 'Inv_P', 'Conv_P']]

        col = ["%i" % x for x in App_comb]
        name_comb=col[0]+col[1]+col[2]+col[3]

        if sys.platform=='win32':
            filename_save=('../Output/df_%(name)s_%(Tech)s_%(App_comb)s_%(Cap)s_%(cases)s_online.csv'%{'name':name,'Tech':Tech,'App_comb':name_comb,'Cap':Capacity,'cases':cases})

        else:
        		filename_save=('../Output/df_%(name)s_%(Tech)s_%(App_comb)s_%(Cap)s_%(cases)s_marzia.csv'%{'name':name,'Tech':Tech,'App_comb':name_comb,'Cap':Capacity,'cases':cases})
        #pickle.dump(dict_save,open(filename_save,"wb"))
        df.round(4).to_csv(filename_save)
        print(App_comb)
        print(name_comb)
        print ('%%%%%%%%%%%% File Saved as %%%%%%%%%%%%%%%%%')
        print(filename_save)



    except:
        print('Save Failed')
    return()
