class Hardware_Prices:
    '''
    Prices in Pena-Bello et al. 2017 maybe more (inverter) because is one for PV and Batt
    '''
    def __init__(self,Inverter_power):
        #Prices are in USD/kW
        self.Price_PV=1500
        self.Price_inverter=880+304*Inverter_power
        self.PV_cal_life=25
        self.Inverter_cal_life=25
        self.Interest_rate=0.04

class Battery(object):
    '''
    Battery object with a selected capacity.
    Change rate from EUR to USD 1.18 as of August 2017
    '''

    def __init__(self,Capacity,  **kwargs):
        super().__init__(**kwargs)
        self.Capacity = Capacity
        self.EUR_USD=1.18
class Battery_tech(Battery):
    '''
    Battery object with default values for different battery technologies.
    NMC (Tesla), NCA (Trina BESS), LFP (Fortelion), LTO (Leclanche),
    ALA (Fukurawa) and VRLA (Sonnenschein).
    Based on Parra & Patel, 2016 and Datasheets
    Price in USD/kWh in Pena-Bello et al. 2017 it changes according to the techno.
    TODO
    ------
    Years of usage as a variable to modify efficiency may be included as well as ageing

    '''
    def __init__(self, Technology,**kwargs):
        super().__init__(**kwargs)
        self.Technology = Technology
        if self.Technology=='NMC':#Tesla
                defaults = {'Efficiency': 0.918,
                'P_max_dis': -0.4*self.Capacity,
                'P_max_char': 0.4*self.Capacity,
                'SOC_max': 1*self.Capacity,
                'SOC_min': 0*self.Capacity,
                'Price_battery': 410*self.Capacity,
                'Battery_cal_life': 15,
                'Battery_cycle_life': 5000,
                'PCS_costs': 441*self.EUR_USD,
                'BOS_costs':2187*self.EUR_USD,
                'OandM_costs': 0,
                'Fix_costs': 0,
                'EoL': 0.7,
                'IRENA_future_Price':167*self.Capacity}

                for key, val in defaults.items():
                    setattr(self, key, val)
                self.__dict__.update(kwargs)
###############################################################################
        elif self.Technology=='NCA': #TRINA BESS
                defaults = {'Efficiency': 0.925,
                'P_max_dis': -1*self.Capacity,
                'P_max_char': 1*self.Capacity,
                'SOC_max': 1*self.Capacity,
                'SOC_min': 0*self.Capacity,
                'Price_battery': 650*self.Capacity,
                'Battery_cal_life': 20,
                'Battery_cycle_life': 8000,
                'PCS_costs': 286.65*self.EUR_USD,
                'BOS_costs':2241*self.EUR_USD,
                'OandM_costs': 0,
                'Fix_costs': 0,
                'EoL': 0.7,
                'IRENA_future_Price':145*self.Capacity}
                for key, val in defaults.items():
                    setattr(self, key, val)
                self.__dict__.update(kwargs)

###############################################################################
        elif self.Technology=='LFP':#Sony Fortelion
                defaults = {'Efficiency': 0.94,
                'P_max_dis': -2*self.Capacity,
                'P_max_char': 2*self.Capacity,
                'SOC_max': 1*self.Capacity,
                'SOC_min': 0*self.Capacity,
                'Price_battery': 980*self.Capacity,#USD,
                'Battery_cal_life': 20,
                'Battery_cycle_life': 6000, #Battery_cycle_life @ 80%DOD
                'PCS_costs': 607*self.EUR_USD,
                'BOS_costs':2061*self.EUR_USD,
                'OandM_costs': 0,
                'Fix_costs': 0,
                'EoL': 0.7,
                'IRENA_future_Price':224*self.Capacity}

                for key, val in defaults.items():
                    setattr(self, key, val)
                self.__dict__.update(kwargs)


###############################################################################
        elif self.Technology=='LTO':
                defaults = {'Efficiency': 0.967,
                'P_max_dis': -4*self.Capacity,
                'P_max_char': 4*self.Capacity,
                'SOC_max': 1*self.Capacity,
                'SOC_min': 0*self.Capacity,
                'Price_battery': 1630*self.Capacity,
                'Battery_cal_life': 25,
                'Battery_cycle_life': 15000,
                'PCS_costs': 287*self.EUR_USD,
                'BOS_costs':1622*self.EUR_USD,
                'OandM_costs': 0,
                'Fix_costs': 0,
                'EoL': 0.7,
                'IRENA_future_Price':480*self.Capacity}
                for key, val in defaults.items():
                    setattr(self, key, val)
                self.__dict__.update(kwargs)

###############################################################################
        elif self.Technology=='ALA':
                defaults = {'Efficiency': 0.91,
                'P_max_dis': -1*self.Capacity,
                'P_max_char': 1*self.Capacity,
                'SOC_max': 0.9*self.Capacity,
                'SOC_min': 0.2*self.Capacity,
                'Price_battery': 750*self.Capacity,
                'Battery_cal_life': 15,
                'Battery_cycle_life': 4500,
                'PCS_costs': 766,
                'BOS_costs':2030*self.EUR_USD,
                'OandM_costs': 22*self.EUR_USD,
                'Fix_costs': 0,
                'EoL': 0.7,
                'IRENA_future_Price':330*self.Capacity}
                for key, val in defaults.items():
                    setattr(self, key, val)
                self.__dict__.update(kwargs)
###############################################################################
        elif self.Technology=='VRLA':
                defaults = {'Efficiency': 0.85,
                'P_max_dis': -0.1*self.Capacity,
                'P_max_char': 0.1*self.Capacity,
                'SOC_max': 1*self.Capacity,
                'SOC_min': 0.5*self.Capacity,
                'Price_battery': 330*self.Capacity,
                'Battery_cal_life': 10,
                'Battery_cycle_life': 1500,
                'PCS_costs': 466*self.EUR_USD,
                'BOS_costs':1143*self.EUR_USD,
                'OandM_costs': 0,
                'Fix_costs': 0,
                'EoL': 0.7,
                'IRENA_future_Price':150*self.Capacity}
                for key, val in defaults.items():
                    setattr(self, key, val)
                self.__dict__.update(kwargs)

###############################################################################
        elif self.Technology=='test':
                defaults = {'Efficiency': 0.95,
                'P_max_dis': -1*self.Capacity,
                'P_max_char': 1*self.Capacity,
                'SOC_max': 1*self.Capacity,
                'SOC_min': 0*self.Capacity,
                'Price_battery': 450*self.Capacity,
                'Battery_cal_life': 15,
                'Battery_cycle_life': 5000,
                'PCS_costs': 466*self.EUR_USD,
                'BOP_costs': 0,
                'OandM_costs': 0,
                'Fix_costs': 0,
                'EoL': 0.7}
                for key, val in defaults.items():
                    setattr(self, key, val)
                self.__dict__.update(kwargs)

###############################################################################
        else:
                raise ValueError


class Battery_case(Battery_tech): #Based on Schmidt et al. (2019)
    '''
    Include the values of Schmidt et al. (2019) for comparison using
    NMC, NCA, LFP, LTO and VRLA technologies.

    TODO
    -----
    include ALA
    '''
    def __init__(self,case, **kwargs):
        super().__init__(**kwargs)
        self.case = case
        if self.Technology=='NMC':
            if self.case=='mean':
                defaults = {
                'Efficiency': 0.89,
                'Price_battery': 335*self.Capacity*self.EUR_USD,
                'Battery_cal_life': 15,
                'Battery_cycle_life': 4996,
                'SOC_max': 0.965*self.Capacity,
                'SOC_min': 0.035*self.Capacity}
                for key, val in defaults.items():
                    setattr(self, key, val)
                self.__dict__.update(kwargs)
            elif self.case=='min':
                defaults = {
                'Efficiency': 0.87,
                'Price_battery': 250*self.Capacity*self.EUR_USD,
                'Battery_cal_life': 5,
                'Battery_cycle_life': 2555,
                'SOC_max': 0.965*self.Capacity,
                'SOC_min': 0.035*self.Capacity}
                for key, val in defaults.items():
                    setattr(self, key, val)
                self.__dict__.update(kwargs)
            elif self.case=='max':
                defaults = {
                'Efficiency': 0.92,
                'Price_battery': 420*self.Capacity*self.EUR_USD,
                'Battery_cal_life': 20,
                'Battery_cycle_life': 8000,
                'SOC_max': 0.965*self.Capacity,
                'SOC_min': 0.035*self.Capacity}
                for key, val in defaults.items():
                    setattr(self, key, val)
                self.__dict__.update(kwargs)
        elif self.Technology=='NCA':
            if self.case=='mean':
                defaults = {
                'Efficiency': 0.89,
                'Price_battery': 281*self.Capacity*self.EUR_USD,
                'Battery_cal_life': 12,
                'Battery_cycle_life': 2498,
                'SOC_max': 0.965*self.Capacity,
                'SOC_min': 0.035*self.Capacity}
                for key, val in defaults.items():
                    setattr(self, key, val)
                self.__dict__.update(kwargs)
            elif self.case=='min':
                defaults = {
                'Efficiency': 0.87,
                'Price_battery': 210*self.Capacity*self.EUR_USD,
                'Battery_cal_life': 5,
                'Battery_cycle_life': 1278,
                'SOC_max': 0.965*self.Capacity,
                'SOC_min': 0.035*self.Capacity}
                for key, val in defaults.items():
                    setattr(self, key, val)
                self.__dict__.update(kwargs)
            elif self.case=='max':
                defaults = {
                'Efficiency': 0.92,
                'Price_battery': 352*self.Capacity*self.EUR_USD,
                'Battery_cal_life': 20,
                'Battery_cycle_life': 4000,
                'SOC_max': 0.965*self.Capacity,
                'SOC_min': 0.035*self.Capacity}
                for key, val in defaults.items():
                    setattr(self, key, val)
                self.__dict__.update(kwargs)
        elif self.Technology=='LFP':
            if self.case=='mean':
                defaults = {
                'Efficiency': 0.87,
                'Price_battery': 461*self.Capacity*self.EUR_USD,
                'Battery_cal_life': 12,
                'Battery_cycle_life': 6529,
                'SOC_max': 0.965*self.Capacity,
                'SOC_min': 0.035*self.Capacity}
                for key, val in defaults.items():
                    setattr(self, key, val)
                self.__dict__.update(kwargs)
            elif self.case=='min':
                defaults = {
                'Efficiency': 0.84,
                'Price_battery': 344*self.Capacity*self.EUR_USD,
                'Battery_cal_life': 5,
                'Battery_cycle_life': 2000,
                'SOC_max': 0.965*self.Capacity,
                'SOC_min': 0.035*self.Capacity}
                for key, val in defaults.items():
                    setattr(self, key, val)
                self.__dict__.update(kwargs)
            elif self.case=='max':
                defaults = {
                'Efficiency': 0.89,
                'Price_battery': 587*self.Capacity*self.EUR_USD,
                'Battery_cal_life': 20,
                'Battery_cycle_life': 10000,
                'SOC_max': 0.965*self.Capacity,
                'SOC_min': 0.035*self.Capacity}
                for key, val in defaults.items():
                    setattr(self, key, val)
                self.__dict__.update(kwargs)
        elif self.Technology=='LTO':
            if self.case=='mean':
                defaults = {
                'Efficiency': 0.91,
                'Price_battery': 900*self.Capacity*self.EUR_USD,
                'Battery_cal_life': 23,
                'Battery_cycle_life': 15000,
                'SOC_max': 1*self.Capacity,
                'SOC_min': 0*self.Capacity}
                for key, val in defaults.items():
                    setattr(self, key, val)
                self.__dict__.update(kwargs)
            elif self.case=='min':
                defaults = {
                'Efficiency': 0.88,
                'Price_battery': 800*self.Capacity*self.EUR_USD,
                'Battery_cal_life': 20,
                'Battery_cycle_life': 5000,
                'SOC_max': 1*self.Capacity,
                'SOC_min': 0*self.Capacity}
                for key, val in defaults.items():
                    setattr(self, key, val)
                self.__dict__.update(kwargs)
            elif self.case=='max':
                defaults = {
                'Efficiency': 0.95,
                'Price_battery': 1000*self.Capacity*self.EUR_USD,
                'Battery_cal_life': 25,
                'Battery_cycle_life': 20000,
                'SOC_max': 1*self.Capacity,
                'SOC_min': 0*self.Capacity}
                for key, val in defaults.items():
                    setattr(self, key, val)
                self.__dict__.update(kwargs)

        elif self.Technology=='ALA':
            if self.case=='mean':
                defaults = {
                'Efficiency': 0.918,
                'Price_battery': 410*self.Capacity*self.EUR_USD,
                'Battery_cal_life': 15,
                'Battery_cycle_life': 5000,
                'SOC_max': 0.9*self.Capacity,
                'SOC_min': 0.2*self.Capacity}
                for key, val in defaults.items():
                    setattr(self, key, val)
                self.__dict__.update(kwargs)
            elif self.case=='min':
                defaults = {
                'Efficiency': 0.87,
                'Price_battery': 50*self.Capacity*self.EUR_USD,
                'Battery_cal_life': 5,
                'Battery_cycle_life': 2555,
                'SOC_max': 0.9*self.Capacity,
                'SOC_min': 0.2*self.Capacity}
                for key, val in defaults.items():
                    setattr(self, key, val)
                self.__dict__.update(kwargs)
            elif self.case=='max':
                defaults = {
                'Efficiency': 0.92,
                'Price_battery': 420*self.Capacity*self.EUR_USD,
                'Battery_cal_life': 20,
                'Battery_cycle_life': 8000,
                'SOC_max': 0.9*self.Capacity,
                'SOC_min': 0.2*self.Capacity}
                for key, val in defaults.items():
                    setattr(self, key, val)
                self.__dict__.update(kwargs)

        elif self.Technology=='VRLA':
            if self.case=='mean':
                defaults = {
                'Efficiency': 0.75,
                'Price_battery': 263*self.Capacity*self.EUR_USD,
                'Battery_cal_life': 9,
                'Battery_cycle_life': 1500,
                'SOC_max': 0.95*self.Capacity,
                'SOC_min': 0.4*self.Capacity}
                for key, val in defaults.items():
                    setattr(self, key, val)
                self.__dict__.update(kwargs)
            elif self.case=='min':
                defaults = {
                'Efficiency': 0.73,
                'Price_battery': 105*self.Capacity*self.EUR_USD,
                'Battery_cal_life': 3,
                'Battery_cycle_life': 250,
                'SOC_max': 0.95*self.Capacity,
                'SOC_min': 0.4*self.Capacity}
                for key, val in defaults.items():
                    setattr(self, key, val)
                self.__dict__.update(kwargs)
            elif self.case=='max':
                defaults = {
                'Efficiency': 0.78,
                'Price_battery': 473*self.Capacity*self.EUR_USD,
                'Battery_cal_life': 15,
                'Battery_cycle_life': 2500,
                'SOC_max': 0.95*self.Capacity,
                'SOC_min': 0.4*self.Capacity}
                for key, val in defaults.items():
                    setattr(self, key, val)
                self.__dict__.update(kwargs)

###############################################################################
        else:
                raise ValueError
