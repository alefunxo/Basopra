# -*- coding: utf-8 -*-
## @namespace main_paper
# Created on Wed Feb 28 09:47:22 2018
# Author
# Alejandro Pena-Bello
# alejandro.penabello@unige.ch
# Main script used for the paper Optimization of PV-coupled battery systems for combining applications: impact of battery technology and location (Pena-Bello et al 2019 to be published).
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
from pathlib import Path
import csv

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
def load_param():
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
	df=pd.read_csv('../Input/Input_data.csv',sep=';|,',decimal='.',engine='python',index_col=[0],usecols=[0])
	dict_input=df.variable.to_dict()
	try:
		filename=Path("../Input/df_US.csv")
		df=pd.read_csv(filename,sep=';|,',decimal='.',engine='python',index_col=[0])
	except:
		print ("Unexpected error")
	if int(365*24/float(dict_input['Time_resolution']))!=df.shape[0]:
	    print('The claimed data resolution (in Input_data.csv) and the real data resolution (in df_input) do not correspond')
	else:
	    if float(dict_input['Time_resolution'])in [0.25,0.5,1]:
	        freq=str(int(60*float(dict_input['Time_resolution'])))
	        ind=pd.date_range(start=pd.datetime(int(dict_input['year_data']), 1, 1), periods=df.shape[0], freq=freq+'T',tz='US/Central')

	        df.index=ind

	PV_nominal_power=float(dict_input['PV_nom'])
	Inverter_power=round(PV_nominal_power/float(dict_input['Inverter_load_ratio']),1)#ILR=1.2
	Curtailment=float(dict_input['Curtailment'])
	Inverter_Efficiency=float(dict_input['Inverter_efficiency'])
	Converter_Efficiency_Batt=float(dict_input['Converter_efficiency'])
	#define time resolution dt is 1/4 hours i.e. 15 min
	dt=float(dict_input['Time_resolution'])
	nyears=int(dict_input['number_of_years'])
	days=int(dict_input['number_of_days'])
	Capacity_tariff=float(dict_input['Capacity_tariff'])*12/365
	if (nyears>1) & (days!=365):
		days=365
	if days>365:
		days=365
	if nyears==0:
		nyears=1#minimum is 1
	ndays=days*nyears
	#define Applications, capacities and technologies to optimize
	App_comb=np.array([bool(dict_input['Avoidance_PV_curtailment']),True,bool(dict_input['Demand_load_shifting']),bool(dict_input['Demand_peak_shaving'])])
	Technology=dict_input['Technology']
	Capacity=float(dict_input['Capacity'])#support any capacity value
	param={'aging':aging,'Inv_power':Inverter_power,
	'Curtailment':Curtailment,'Inverter_eff':Inverter_Efficiency,
	'Converter_Efficiency_Batt':Converter_Efficiency_Batt,
	'delta_t':dt,'nyears':nyears,'days':days,'ndays':ndays,
	'App_comb':App_comb,'Tech':Technology,'cases':True,
	'Capacity':Capacity,'Capacity_tariff':Capacity_tariff,'PV_nom':PV_nominal_power}
	return param,df

@fn_timer
def main():
	'''
	Main function of the main script.
	'''
	print('&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&')
	print('Welcome to the  BAttery Schedule OPtimizer for Residential Application (BASOPRA).')
	print('This model allows the user to optimize the battery schedule of a customer, based on the PV generation, electricity demand and electricity tariffs. It is designed for residential applications (i.e., PV self-consumption, avoidance of PV curtailment, demand load shifting and demand peak shaving), but the input data can be of residential customers, C&I or aggregated for communities.')

	from Core_LP import single_opt2
	print('##############')
	filename1=Path('../Output/aggregated_results_ext.csv')
	if 'aggregated_results_ext.csv' not in os.listdir('../Output/'):
		print('Create a file for aggregated results')
		with open(filename1, 'w', newline='') as f:
			columns=['E_PV_batt', 'E_PV_curt', 'E_PV_grid', 'E_PV_load', 'E_char', 'E_cons',
       'E_dis', 'E_grid_batt', 'E_grid_load', 'E_loss_Batt', 'E_loss_conv',
       'E_loss_inv', 'E_loss_inv_PV', 'E_loss_inv_batt', 'E_loss_inv_grid',
       'E_demand', 'E_PV', 'App_comb', 'SOC_mean', 'SOC_max', 'SOC_min',
       'DoD_mean', 'DoD_max', 'DoD_min', 'last_cap', 'cap_fading', 'last_SOH',
       'P_max_year_batt', 'P_max_year_nbatt', 'Capacity', 'Tech', 'PV_nom',
       'name', 'results_PVbatt', 'results_PV', 'results', 'EFC_nolifetime',
       'LS', 'TSC', 'DSC', 'ISC', 'CU', 'PS_year', 'BS', 'cycle_to_total',
       'cases']
			writer = csv.writer(f, delimiter=';')
			writer.writerow(columns)
	param,data_input=load_param()
	name=data_input.columns[0]
	data_input.columns=['E_demand','E_PV','Price_flat','Price_DT','Price_flat_mod','Price_DT_mod','Export_price']
	print(param)
	print(data_input.head())
	try:
		if param['nyears']>1:
			data_input=pd.DataFrame(pd.np.tile(pd.np.array(data_input).T,param['nyears']).T,columns=data_input.columns)
		print('#############pool################')
		[df_out,Cap_arr,SOH,Cycle_aging_factor,P_max,results,         cycle_cal_arr]=single_opt2(param,data_input,name)
		print('out of optimization')
		#print(df_out.sum())
	except IOError as e:
		print ("I/O error({0}): {1}".format(e.errno, e.strerror))

	except ValueError:
		print ("Could not convert data to an integer.")

	except:
		print ("Unexpected error:", sys.exc_info()[0])
		print ("Unexpected error2:", sys.stderr)
	print('&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&')
if __name__== '__main__':
	main()
