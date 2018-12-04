# -*- coding: utf-8 -*-
## @namespace paper_classes_2
# Created on Mon Jul 17 16:43:49 2017
# Author
# Alejandro Pena-Bello
# alejandro.penabello@unige.ch
# Battery class definition
#Based on Parra & Patel, 2016
#Prices from ETH, UNIGE, PSI
#change rate from EUR to USD 1.18 as of August 2017
#We can include years of usage as a variable to modify efficiency and include ageing
#Price in USD/kWh in Pena-Bello et al. 2017 it changes according to the techno.

import numpy as np

#:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::#
#                                  CLASSES
#:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::#

class fullprint:
    #This is for printing the whole array when needed
    #it is used as follows:
    #with fullprint():
        #print(array)
    'context manager for printing full numpy arrays'

    def __init__(self, **kwargs):
        if 'threshold' not in kwargs:
            kwargs['threshold'] = np.nan
        self.opt = kwargs

    def __enter__(self):
        self._opt = np.get_printoptions()
        np.set_printoptions(**self.opt)

    def __exit__(self, type, value, traceback):
        np.set_printoptions(**self._opt)
class Hardware_Prices:

    def __init__(self,Inverter_power):
        #Prices are in USD/kW
        self.Price_PV=1500
        self.Price_inverter=880+304*Inverter_power
        self.PV_cal_life=25
        self.Inverter_cal_life=25
        self.Interest_rate=0.04

class Battery:

    def __init__(self,Capacity,choicetype,**kwargs):
        #Battery Price reduction in 15 years
        future_factor=.5
        self.Technology=choicetype
        self.Capacity=Capacity
        EUR_USD=1.18

        try:
            if choicetype=='NMC':#Tesla
                defaults = {'Efficiency': 0.918,
                'P_max_dis': -0.4*Capacity,
                'P_max_char': 0.4*Capacity,
                'SOC_max': 1*Capacity,
                'SOC_min': 0*Capacity,
                'Price_battery': 407*Capacity,
                'Battery_cal_life': 15,
                'Battery_cycle_life': 5000,
                'PCS_costs': 441*EUR_USD,
                'BOP_costs': 0,
                'OandM_costs': 0,
                'Fix_costs': 0,
                'EoL': 0.7}
                for key, val in defaults.items():
                    setattr(self, key, val)
                self.__dict__.update(kwargs)
###############################################################################
                self.Battery_future_Price=self.Price_battery*future_factor
###############################################################################
            elif choicetype=='NCA': #TRINA BESS
                defaults = {'Efficiency': 0.925,
                'P_max_dis': -1*Capacity,
                'P_max_char': 1*Capacity,
                'SOC_max': 1*Capacity,
                'SOC_min': 0*Capacity,
                'Price_battery': 645*Capacity,
                'Battery_cal_life': 20,
                'Battery_cycle_life': 8000,
                'PCS_costs': 286.65*EUR_USD,
                'BOP_costs': 0,
                'OandM_costs': 0,
                'Fix_costs': 0,
                'EoL': 0.7}
                for key, val in defaults.items():
                    setattr(self, key, val)
                self.__dict__.update(kwargs)
###############################################################################
                self.Battery_future_Price=self.Price_battery*future_factor
###############################################################################
            elif choicetype=='LFP':#Sony Fortelion
                defaults = {'Efficiency': 0.94,
                'P_max_dis': -2*Capacity,
                'P_max_char': 2*Capacity,
                'SOC_max': 1*Capacity,
                'SOC_min': 0*Capacity,
                'Price_battery': 980*Capacity,#USD,
                'Battery_cal_life': 20,
                'Battery_cycle_life': 6000, #Battery_cycle_life @ 80%DOD
                'PCS_costs': 607*EUR_USD,
                'BOP_costs': 0,
                'OandM_costs': 0,
                'Fix_costs': 0,
                'EoL': 0.7}
                for key, val in defaults.items():
                    setattr(self, key, val)
                self.__dict__.update(kwargs)
###############################################################################
                self.Battery_future_Price=self.Price_battery*future_factor
###############################################################################
            elif choicetype=='LTO':#Leclanché
                defaults = {'Efficiency': 0.967,
                'P_max_dis': -4*Capacity,
                'P_max_char': 4*Capacity,
                'SOC_max': 1*Capacity,
                'SOC_min': 0*Capacity,
                'Price_battery': 1630*Capacity,
                'Battery_cal_life': 25,
                'Battery_cycle_life': 15000,
                'PCS_costs': 287*EUR_USD,
                'BOP_costs': 0,
                'OandM_costs': 0,
                'Fix_costs': 0,
                'EoL': 0.7}
                for key, val in defaults.items():
                    setattr(self, key, val)
                self.__dict__.update(kwargs)
###############################################################################
                self.Battery_future_Price=self.Price_battery*future_factor
###############################################################################
            elif choicetype=='ALA':#Ecoult
                defaults = {'Efficiency': 0.91,
                'P_max_dis': -1*Capacity,
                'P_max_char': 1*Capacity,
                'SOC_max': 0.9*Capacity,
                'SOC_min': 0.2*Capacity,
                'Price_battery': 752*Capacity,
                'Battery_cal_life': 15,
                'Battery_cycle_life': 4500,
                'PCS_costs': 766,
                'BOP_costs': 0,
                'OandM_costs': 22*EUR_USD,
                'Fix_costs': 0,
                'EoL': 0.7}
                for key, val in defaults.items():
                    setattr(self, key, val)
                self.__dict__.update(kwargs)
###############################################################################
                self.Battery_future_Price=self.Price_battery*future_factor
###############################################################################
            elif choicetype=='VRLA':#Sonnenschein
                defaults = {'Efficiency': 0.85,
                'P_max_dis': -0.1*Capacity,
                'P_max_char': 0.1*Capacity,
                'SOC_max': 1*Capacity,
                'SOC_min': 0.5*Capacity,
                'Price_battery': 333*Capacity,
                'Battery_cal_life': 10,
                'Battery_cycle_life': 1500,
                'PCS_costs': 466*EUR_USD,
                'BOP_costs': 0,
                'OandM_costs': 0,
                'Fix_costs': 0,
                'EoL': 0.7}
                for key, val in defaults.items():
                    setattr(self, key, val)
                self.__dict__.update(kwargs)

###############################################################################
                self.Battery_future_Price=self.Price_battery*future_factor
            elif choicetype=='test':
                defaults = {'Efficiency': 0.95,
                'P_max_dis': -1*Capacity,
                'P_max_char': 1*Capacity,
                'SOC_max': 1*Capacity,
                'SOC_min': 0*Capacity,
                'Price_battery': 450*Capacity,
                'Battery_cal_life': 15,
                'Battery_cycle_life': 5000,
                'PCS_costs': 466*EUR_USD,
                'BOP_costs': 0,
                'OandM_costs': 0,
                'Fix_costs': 0,
                'EoL': 0.7}
                for key, val in defaults.items():
                    setattr(self, key, val)
                self.__dict__.update(kwargs)

###############################################################################
                self.Battery_future_Price=self.Price_battery*future_factor
            else:
                raise ValueError
        except ValueError:
            print("Oops that battery technology is not yet supported")
