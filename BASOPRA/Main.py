# -*- coding: utf-8 -*-
## @namespace main_paper
# Created on Wed Feb 28 09:47:22 2018
# Author
# Alejandro Pena-Bello
# alejandro.penabello@unige.ch
# Main script used for the paper Optimization of PV-coupled battery systems for combining applications: impact of battery technology and location (Pena-Bello et al 2018 to be published).
# The study focuses on residential PV-coupled battery systems. We study the different applications which residential batteries can perform from a consumer perspective. Applications such as avoidance of PV curtailment, demand load-shifting and demand peak shaving are considered along  with the base application, PV self-consumption. Moreover, six different battery technologies currently available in the market are considered as well as three sizes (3 kWh, 7 kWh and 14 kWh). We analyze the impact of the type of demand profile and type of tariff structure by comparing results across dwellings in Switzerland and in the U.S.
# The battery schedule is optimized for every day (i.e. 24 h optimization framework), we assume perfect day-ahead forecast of the electricity demand load and solar PV generation in order to determine the maximum economic potential regardless of the forecast strategy used. Aging was treated as an exogenous parameter, calculated on daily basis and was not subject of optimization. Data with 15-minute temporal resolution were used for simulations. The model objective function have two components, the energy-based and the power-based component, as the tariff structure depends on the applications considered, a boolean parameter activate the power-based factor of the bill when is necessary.
# Every optimization was run for one year and then the results were linearly-extrapolated to reach the battery end of life. Therefore, the analysis is done with same prices for all years across battery lifetime. We assume 30\% of capacity depletion as the end of life.
# The script works in Linux and Windows
# This script works was tested with pyomo version 5.4.3
# INPUTS
# ------
# OUTPUTS
# -------
# TODO
# ----
# User Interface, including path to save the results and choose countries, load curves, etc.
# Simplify by merging select_data and load_data and probably load_param.
# Requirements
# ------------
#  Pandas, numpy, sys, glob, os, csv, pickle, functools, argparse, itertools, time, math, pyomo and multiprocessing


import os
import pandas as pd
import argparse
import numpy as np
import itertools
import sys
import glob
import multiprocessing as mp
import time
from functools import wraps
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

@fn_timer
def select_data(country):
    '''
    This function selects the dwellings we are going to work with,
    specified by their names. The list of names is a result of clustering
	(which has been done previously, see Grouping_via_average_day.py).
    Since every run of the clustering script gives a different set of dwelings
    we opt to maintain them as a fix list instead of call the clustering for
    each instance.

    According to the country selected, DatetimeIndex is selected, load curves,
	generation profiles and tariff structures are loaded. Output is a
	dictionary that includes name, dataframe & PV quartile.

    Parameters
    ----------
    country : input txt

    Examples
    --------
    'CH' & 'US'


    Returns
    -------
    selected_dwellings : dict

    '''
    if sys.platform=='win32':
       init_path='C:/Users/alejandro/'
    else:
        init_path='/home/alefunxo/'
    if country=='CH':
        print('CH data is confidential')
    if country=='US':
        test=True
        file=list(glob.glob('../Input/df_US.csv'))
        df=pd.read_csv(file[0],index_col=[0],parse_dates=[0],infer_datetime_format=True,sep=';')#Attention to this line, depending on os the separator may be ','
        df.index=df.index.tz_localize('UTC').tz_convert('US/Central')
        dwellings=['164','79','466', '1', '539', '161', '122', '325', '327', '538','403', '204']
        dwellings=[i+'_US' for i in dwellings]
        PVvec={'PV25':3.2,'PV75':6.4,'PV50':5}
        #PVvec={'PV50':5}
        if test:
            PVvec={'PV50':5}
            dwellings=['164']
            dwellings=[i+'_US' for i in dwellings]
        combis=pd.DataFrame(np.array([i+'_'+j for i in dwellings for j in PVvec]))
        selected_dwellings=[]
        for combo in combis.index:
        	id_dwell=combis.loc[combo][0][:-8]
        	PV_quart=combis.loc[combo][0][-4:]
        	data_input=pd.concat([df.loc[:,id_dwell],
        						 df.loc[:,'E_PV']*PVvec[PV_quart],
        						 df.loc[:,'Price_flat'],df.loc[:,'Price_DT'],
        						 df.loc[:,'Export_price']],axis=1)
        	d={'name':combis.loc[combo][0],'df':data_input,
        		'PV_nom':PVvec[PV_quart], 'Capacity_tariff':10.14*12/365}
        	selected_dwellings.append(d)
    print('############selecting data##############')

    return selected_dwellings
@fn_timer
def load_param(PV_nominal_power,data_input):
	'''
	Description
	-----------
    Load all parameters into a dictionary, if aging is present (True) or not
    (False), percentage of curtailment, Inverter and Converter efficiency, time
    resolution (0.25), number of years or days if only some days want to be
    optimized, applications, capacities and technologies to optimize.

    Applications are defined as a Boolean vector, where a True activates the
    corresponding application. PVSC is assumed to be always used. The order
    is as follows: [PVCT, PVSC, DLS, DPS]
	i.e PV avoidance of curtailment, PV self-consumption,
	Demand load shifting and demand peak shaving.
    [0,1,0,0]-0
    [0,1,0,1]-1
    [0,1,1,0]-2
    [0,1,1,1]-3
    [1,1,0,0]-4
    [1,1,0,1]-5
    [1,1,1,0]-6
    [1,1,1,1]-7


    Parameters
    ----------
    PV_nominal_power : int

    Returns
    ------
    param: dict
    '''
	test=True
	aging=True
	Inverter_power=round(PV_nominal_power/1.2,1)#ILR=1.2
	Curtailment=0.5#50% of the PV nominal power
	Inverter_Efficiency=0.95
	Converter_Efficiency_Batt=0.98
	#define time resolution dt is 1/4 hours i.e. 15 min
	dt=0.25
	nyears=1
	days=1#in order to do some tests this parameter allows the user to change the number of days to simulate (1-365)
	if (nyears>1) & (days!=365):
		days=365
	ndays=days*nyears
	#define Applications, capacities and technologies to optimize
	App_comb_scenarios=np.array([i for i in itertools.product([False,True],repeat=3)])
	App_comb_scenarios=np.insert(App_comb_scenarios,True,1,axis=1)
	Technologies=['NCA','NMC','LFP','LTO','ALA','VRLA']
	Capacities=np.array([3,7,14])#support any capacity value

	if test:
		Technologies=['LFP']
		Capacities=np.array([7])#support any capacity value
		App_comb_scenarios=App_comb_scenarios[-1:]
	print(App_comb_scenarios)

	param={'aging':aging,'Inv_power':Inverter_power,
    'Curtailment':Curtailment,'Inverter_eff':Inverter_Efficiency,
    'Converter_Efficiency_Batt':Converter_Efficiency_Batt,
    'delta_t':dt,'nyears':nyears,'days':days,'ndays':ndays,
    'App_comb_scenarios':App_comb_scenarios,'Technologies':Technologies,
    'Capacities':Capacities}
	return param

@fn_timer
def pooling(selected_dwellings):
    '''
    Description
    -----------
    Calls other functions, load the data and Core_LP.
    Parameters
    ----------
    selected_dwellings : dict

    Returns
    ------
    bool
        True if successful, False otherwise.
    '''
    print('##############')
    print('pooling')
    from Core_LP import single_opt

    data_input=selected_dwellings['df'].copy()
    data_input.columns=['E_demand','E_PV','Price_flat'
                        ,'Price_DT','Export_price']
    param=load_param(selected_dwellings['PV_nom'],data_input)
    print(data_input.sum())
    try:
        if param['nyears']>1:
            data_input=pd.DataFrame(pd.np.tile(pd.np.array(data_input).T,
                                   param['nyears']).T,columns=data_input.columns)
        print('#############pool################')
        [df_out,Cap_arr,SOH,Cycle_aging_factor,P_max,results,
         cycle_cal_arr]=single_opt(param, data_input,
                         selected_dwellings['Capacity_tariff'],
                         selected_dwellings['PV_nom'],
                         str(selected_dwellings['name']))
        print(df_out.sum())
    except:
        print('An unexpected error occurred:')
        raise

    return
@fn_timer
def main():
    '''
    Main function of the main script. Allows the user to select the country
	(CH or US). For the moment is done automatically if working in windows
	the country is US. It opens a pool of 4 processes to process in parallel, if several dwellings are assessed.
    '''
    print('&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&')
    print('Welcome to basopra')
    print('Here you will able to get the optimization of a single family house in the U.S. using a 7 kWh LFP-based battery')
    selected_dwellings=select_data('US')
    mp.freeze_support()
    pool=mp.Pool(processes=4)
    pool.map(pooling,selected_dwellings)
    pool.close()
    pool.join()
    print('&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&')
if __name__== '__main__':
    main()
