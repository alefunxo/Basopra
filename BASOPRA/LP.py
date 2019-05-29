# -*- coding: utf-8 -*-
## @namespace LP
# Created on Wed Nov  1 15:44:25 2017
# Author
# Alejandro Pena-Bello
# alejandro.penabello@unige.ch
# In this script the optimization is set up.
# This LP algorithm allows the user to optimize the daily electricity bill
# The system here presented is a DC-coupled system with a charge controller and
# a bi-directional inverter as presented in [1]
# It includes efficiency losses.
# It includes 4 applications and their combination with PVSC as base app.
# avoidance of PV curtailment, Demand peak shaving and demand load shifting.
# Demand peak shaving is done in the same basis than the optimization, i.e.
# if it is a daily optimization, the peak shaving is done every day, if it is
# yearly, then the peak of the year is shaved and so on.
# According to the Data it can be expanded to one month or n years optimization
# An Integrated Inverter is used, in this script the Converter and inverter
# efficiency are the same and are an input from the user.
# The delta_t allows the user to set the time step delta_t=fraction of hour, e.g.
# delta_t=0.25 is a 15 min time step
# [1] Installed Cost Benchmarks and Deployment Barriers for Residential Solar+
# Photovoltaics with Energy Storage: Q1 2016
# Kristen Ardani,Eric O'Shaughnessy,Ran Fu,Chris McClurg,Joshua Huneycutt,
# and Robert Margolis
#  -----     --------------    -------          -----
# | PV |--->| MPPT+Ch.Ctrl|-->|Bi-Inv|---------|Grid|
#  ----      -------------     ------     |    -----
                  # |            |        |
                  # | -----------         |
                  # |                   -----
                  # |                  |Load|
               # -------               -----
              # | Batt |
              # -------




import pyomo.environ as en

#Model
def Concrete_model(Data):
    m = en.ConcreteModel()

    #Sets

    m.Time=en.Set(initialize=Data['Set_declare'][1:],ordered=True)
    m.tm=en.Set(initialize=Data['Set_declare'],ordered=True)

    #Parameters
    m.dt=en.Param(initialize=Data['delta_t'])

    m.PVAC=en.Param(initialize=Data['App_comb'][0])
    m.PVSC=en.Param(initialize=Data['App_comb'][1])
    m.DLS=en.Param(initialize=Data['App_comb'][2])
    m.DPS=en.Param(initialize=Data['App_comb'][3])

    m.retail_price=en.Param(m.Time,initialize=Data['retail_price'])
    m.E_PV=en.Param(m.Time,initialize=Data['E_PV'])
    m.E_demand=en.Param(m.Time,initialize=Data['E_demand'])

    m.export_price=en.Param(m.Time,initialize=Data['Export_price'])
    m.capacity_tariff=en.Param(default=Data['Capacity_tariff'])
    m.Inverter_power=en.Param(initialize=Data['Inv_power'])
    m.Inverter_eff=en.Param(initialize=Data['Inverter_eff'])
    m.Converter_eff=en.Param(initialize=Data['Converter_Efficiency_Batt'])

    m.Max_injection=en.Param(initialize=Data['Max_inj'])
    m.SOC_init=en.Param(initialize=Data['Batt'].SOC_min)
    m.SOC_min=en.Param(initialize=Data['Batt'].SOC_min)
    m.SOC_max=en.Param(initialize=Data['SOC_max'])
    m.Efficiency=en.Param(initialize=Data['Batt'].Efficiency)
    m.Batt_dis_max=en.Param(initialize=-Data['Batt'].P_max_dis)
    m.Batt_char_max=en.Param(initialize=Data['Batt'].P_max_char)



    #Variables
    m.Bool_inj=en.Var(m.Time,within=en.Boolean)
    m.Bool_cons=en.Var(m.Time,within=en.Boolean,initialize=0)
    m.Bool_char=en.Var(m.Time,within=en.Boolean)

    m.Bool_dis=en.Var(m.Time,within=en.Boolean,initialize=0)
    m.E_PV_grid=en.Var(m.Time,bounds=(0,None),initialize=0)
    m.E_PV_load=en.Var(m.Time,bounds=(0,None),initialize=0)
    m.E_PV_batt=en.Var(m.Time,bounds=(0,None),initialize=0)
    m.E_PV_curt=en.Var(m.Time,bounds=(0,None),initialize=0)
    m.E_grid_load=en.Var(m.Time,bounds=(0,None),initialize=0)
    m.E_grid_batt=en.Var(m.Time,bounds=(0,m.Batt_char_max*m.dt),
                       initialize=0)#because the power is in C terms thus, per hour

    m.E_loss_Batt=en.Var(m.Time,bounds=(0,None),initialize=0)

    m.E_cons=en.Var(m.Time,bounds=(0,None),initialize=0)

    m.E_char=en.Var(m.Time,bounds=(0,m.dt*m.Batt_char_max))#because the power is in C terms thus, per hour
    m.E_dis=en.Var(m.Time,bounds=(0,m.dt*m.Batt_dis_max))#because the power is in C terms thus, per hour
    m.P_max_day=en.Var(initialize=0)
    m.SOC=en.Var(m.tm,bounds=(m.SOC_min,m.SOC_max),initialize=m.SOC_min)

    m.E_loss_conv=en.Var(m.Time,bounds=(0,None),initialize=0)
    m.E_loss_inv=en.Var(m.Time,bounds=(0,None),initialize=0)
    m.E_loss_inv_PV=en.Var(m.Time,bounds=(0,None),initialize=0)
    m.E_loss_inv_batt=en.Var(m.Time,bounds=(0,None),initialize=0)
    m.E_loss_inv_grid=en.Var(m.Time,bounds=(0,None),initialize=0)
    #Objective Function

    m.total_cost = en.Objective(rule=Obj_fcn,sense=en.minimize)

    #Constraints
    m.cons_r=en.Constraint(m.Time,rule=Cons_rule)

    m.cons_ch1=en.Constraint(m.Time,rule=Bool_cons_rule_1)
    m.cons_ch2=en.Constraint(m.Time,rule=Bool_cons_rule_2)
    m.cons_ch3=en.Constraint(m.Time,rule=Bool_cons_rule_3)
    m.cons_ch4=en.Constraint(m.Time,rule=Bool_cons_rule_4)

    m.Batt_char_dis=en.Constraint(m.Time,rule=Batt_char_dis)
    m.Batt_ch1=en.Constraint(m.Time,rule=Bool_char_rule_1)
    m.Batt_ch2=en.Constraint(m.Time,rule=Bool_char_rule_2)
    m.Batt_cd3=en.Constraint(m.Time,rule=Bool_char_rule_3)
    m.Batt_cd4=en.Constraint(m.Time,rule=Bool_char_rule_4)
    m.Batt_SOC=en.Constraint(m.tm,rule=def_storage_state_rule)
    m.Balance_batt=en.Constraint(m.Time,rule=Balance_Batt_rule)
    m.Balance_PV=en.Constraint(m.Time,rule=Balance_PV_rule)
    m.Balance_load=en.Constraint(m.Time,rule=Balance_load_rule)
    m.E_char_r=en.Constraint(m.Time,rule=E_char_rule)
    m.E_dis_r=en.Constraint(m.Time,rule=E_dis_rule)

    m.Curtailment_r=en.Constraint(m.Time,rule=Curtailment_rule)
    m.Sold=en.Constraint(m.Time,rule=Sold_rule)
    m.Inverter=en.Constraint(m.Time,rule=Inverter_rule)
    m.Converter=en.Constraint(m.Time,rule=Converter_rule)
    m.Inverter_grid=en.Constraint(m.Time,rule=Inverter_grid_rule)
    m.Grid_cons=en.Constraint(m.Time,rule=Grid_cons_rule)
    m.P_max=en.Constraint(m.Time,rule=P_max_rule)
    m.PVSC_const=en.Constraint(m.Time,rule=PVSC_rule)
    m.Batt_losses=en.Constraint(m.Time,rule=Batt_losses_rule)
    m.Conv_losses=en.Constraint(m.Time,rule=Conv_losses_rule)
    m.Inv_losses=en.Constraint(m.Time,rule=Inv_losses_rule)

    m.Inv_losses_PV=en.Constraint(m.Time,rule=Inv_losses_PV_rule)
    m.Inv_losses_batt=en.Constraint(m.Time,rule=Inv_losses_Batt_rule)
    m.Inv_losses_grid=en.Constraint(m.Time,rule=Inv_losses_Grid_rule)
    #m.Batt_max_char=en.Constraint(m.Time,rule=Batt_max_char_rule)
    #m.Batt_max_dis=en.Constraint(m.Time,rule=Batt_max_dis_rule)
    #m.SOC_r=en.Constraint(m.Time,rule=SOC_rule)

    return m

#Instance

#Energy
#Battery constraints

def Bool_char_rule_1(m,i):
    '''
    Description
    -------
    Forbids the battery to charge and discharge at the same time 1/5
    '''
    bigM=500000
    return((m.E_dis[i])>=-bigM*(m.Bool_dis[i]))

def Bool_char_rule_2(m,i):
    '''
    Description
    -------
    Forbids the battery to charge and discharge at the same time 2/5
    '''
    bigM=500000
    return((m.E_dis[i])<=0+bigM*(1-m.Bool_char[i]))

def Bool_char_rule_3(m,i):
    '''
    Description
    -------
    Forbids the battery to charge and discharge at the same time 3/5
    '''
    bigM=500000
    return((m.E_char[i])>=-bigM*(m.Bool_char[i]))

def Bool_char_rule_4(m,i):
    '''
    Description
    -------
    Forbids the battery to charge and discharge at the same time 4/5
    '''
    bigM=500000
    return((m.E_char[i])<=0+bigM*(1-m.Bool_dis[i]))

def Batt_char_dis(m,i):
    '''
    Description
    -------
    Forbids the battery to charge and discharge at the same time 5/5
    '''
    return (m.Bool_char[i]+m.Bool_dis[i],1)

def Balance_Batt_rule(m,i):
    '''
    Description
    -------
    Balance of the battery charge, discharge and efficiency losses.
    '''
    return (sum(m.E_char[i]for i in m.Time)
            -sum(m.E_dis[i]+m.E_loss_Batt[i] for i in m.Time)==0)

def E_char_rule(m,i):
    '''
    Description
    -------
    Balance of energy charged into the battery from PV and grid.
    '''
    return(m.E_char[i],m.E_PV_batt[i]+m.E_grid_batt[i])

def E_dis_rule(m,i):
    '''
    Description
    -------
    Sets the maximum energy available to be discharged as the SOC - the minimum SOC.
    '''
    return(m.E_dis[i]<=m.SOC[i-1]-m.SOC_min)

#Energy balance constraints

def Bool_cons_rule_1(m,i):
    '''
    Description
    -------
    Forbids the system to inject and export energy at the same time 1/5
    '''
    bigM=500000
    return((m.E_cons[i])>=-bigM*(m.Bool_cons[i]))

def Bool_cons_rule_2(m,i):
    '''
    Description
    -------
    Forbids the system to inject and export energy at the same time 2/5
    '''
    bigM=500000
    return((m.E_cons[i])<=0+bigM*(1-m.Bool_inj[i]))

def Bool_cons_rule_3(m,i):
    '''
    Description
    -------
    Forbids the system to inject and export energy at the same time 3/5
    '''
    bigM=500000
    return((m.E_PV_grid[i])>=-bigM*(m.Bool_inj[i]))

def Bool_cons_rule_4(m,i):
    '''
    Description
    -------
    Forbids the system to inject and export energy at the same time 4/5
    '''
    bigM=500000
    return((m.E_PV_grid[i])<=0+bigM*(1-m.Bool_cons[i]))

def Cons_rule(m,i):
    '''
    Description
    -------
    Forbids the system to inject and export energy at the same time 5/5
    '''
    return (m.Bool_inj[i]+m.Bool_cons[i],1)

def Grid_cons_rule(m,i):
    '''
    Description
    -------
    Balance of grid consumption, includes the electricity consumed by the battery, the loads, and losses in the inverter (when charging the battery from the grid),
    '''
    return(m.E_cons[i],m.E_grid_batt[i]+m.E_grid_load[i]+m.E_loss_inv_grid[i])

def Balance_PV_rule(m,i):
    '''
    Description
    -------
    Balance of PV consumption, includes the electricity provided to the battery, the loads, losses in the inverter and the converter. Includes as well curtailed PV.
    '''
    return (m.E_PV[i],m.E_PV_load[i]+m.E_PV_batt[i]+m.E_PV_grid[i]
            +m.E_loss_conv[i]+m.E_loss_inv_PV[i]+m.E_PV_curt[i])

def Sold_rule(m,i):
    '''
    Description
    -------
    The total PV generation must be greater than the PV electricity injected into the grid and the PV curtailed.
    '''
    return m.E_PV_grid[i]+m.E_PV_curt[i]<=m.E_PV[i]

#include the bi-directional inverter energy standby consumption as a function
#of the inverter power
def Balance_load_rule(m,i):
    '''
    Description
    -------
    Balance of electricity demand, includes the electricity provided by the PV, the battery and the grid.
    TODO
    -------
    include the bi-directional inverter energy standby consumption as a function
    of the inverter power
    '''
    return (m.E_demand[i],m.E_PV_load[i]+m.E_dis[i]*(m.Inverter_eff)
            +m.E_grid_load[i])#-m.Inverter_power*0.5/100)

def def_storage_state_rule(m, t):
    '''
    Description
    -------
    State of charge definition as the previous SOC plus charged electricity minus losses minus discharged electricity. Stablishes as well the initial SOC at SOC_min
    '''
    if t==-1:
        return(m.SOC[t],m.SOC_min)
    else:
        return (m.SOC[t] ==m.SOC[t-1]+m.E_char[t]-m.E_dis[t]-m.E_loss_Batt[t])

#Efficiency losses constraints

def Conv_losses_rule(m,i):
    '''
    Description
    -------
    Converter losses definition. 1-Converter_efficiency times the electricity that pass through the converter. Since E_PV_load, and E_PV_grid are the energy flows after the inverter, they need to be divided by the inverter efficiency to get the real converter losses.
    '''
    return(m.E_loss_conv[i],((m.E_PV_load[i]+m.E_PV_grid[i])/(m.Inverter_eff)+m.E_PV_batt[i])*(1-m.Converter_eff))

def Inv_losses_PV_rule(m,i):
    '''
    Description
    -------
    PV inverter losses definition. 1-Inverter_efficiency times the electricity that pass through the Inverter (takes into account only PV related electricity). Since E_PV_load and E_PV_grid are the energy flows after the inverter, they need to be divided by the inverter efficiency to get the real inverter losses.
    '''
    return(m.E_loss_inv_PV[i],(m.E_PV_grid[i]
           +m.E_PV_load[i])*(1-m.Inverter_eff)/(m.Inverter_eff))

def Inv_losses_Batt_rule(m,i):
    '''
    Description
    -------
    Battery inverter losses definition. 1-Inverter_efficiency times the electricity that pass through the Inverter (takes into account only battery related electricity). E_dis is the energy discharged from the battery, thus no need to divide by the inverter efficiency.
    '''
    return(m.E_loss_inv_batt[i],(m.E_dis[i])*(1-m.Inverter_eff))#E_dis is the flow from the battery (before the inverter)

def Inv_losses_Grid_rule(m,i):
    '''
    Description
    -------
    PV inverter losses definition. 1-Inverter_efficiency times the electricity that pass through the Inverter (takes into account only grid related electricity, i.e. for charging the battery). E_grid_batt does not need to be divided by the inverter efficiency since it is at the consumption side of the system.
    '''
    return(m.E_loss_inv_grid[i],(m.E_grid_batt[i])*(1-m.Inverter_eff))

def Inv_losses_rule(m,i):
    '''
    Description
    -------
    Inverter losses definition. Summation of the PV, battery and grid related losses.
    '''
    return(m.E_loss_inv[i],m.E_loss_inv_grid[i]
           +m.E_loss_inv_batt[i]+m.E_loss_inv_PV[i])

def Batt_losses_rule(m,i):
    '''
    Description
    -------
    Battery losses definition. 1-Battery_efficiency times the electricity that pass through the battery (roundtrip efficiency).
    '''
    return(m.E_loss_Batt[i],(m.E_grid_batt[i]*(m.Inverter_eff)+m.E_PV_batt[i]*(m.Converter_eff))*(1-m.Efficiency))

#Batt

def Inverter_rule(m,i):
    '''
    Description
    -------
    Inverter power definition. All electricity flows through the inverter must be lower than the inverter nominal power (including losses).
    '''
    return(m.E_PV_grid[i]/m.dt+m.E_dis[i]/m.dt+m.E_PV_load[i]/m.dt
           +m.E_loss_inv[i]/m.dt<=m.Inverter_power)

def Converter_rule(m,i):
    '''
    Description
    -------
    Converter power definition. All electricity flows through the Converter must be lower than the inverter nominal power (including losses).
    '''
    return(m.E_PV_grid[i]/m.dt+m.E_PV_batt[i]/m.dt+m.E_PV_load[i]/m.dt
           +m.E_loss_conv[i]/m.dt<=m.Inverter_power)

def Inverter_grid_rule(m,i):
    '''
    Description
    -------
    Inverter power definition. All electricity flows through the inverter must be lower than the inverter nominal power (including losses). This rule is used for grid charging only.
    '''
    return(m.E_grid_batt[i]/m.dt+m.E_loss_inv_grid[i]/m.dt<=m.Inverter_power)

def P_max_rule(m,i):
    '''
    Description
    -------
    Calculates the maximum power drained from the grid each day.
    TODO
    -------
    include the same rule for PV injection as well
    #def P_max_rule_grid(m,i):
    return (m.E_PV_grid[i]<=m.P_max_day*m.dt)
    '''
    return(m.E_cons[i]/m.dt<=m.P_max_day)


#App

def Curtailment_rule(m,i):
    '''
    Description
    -------
    Restrains the maximum PV injection into the grid (in kW) if avoidance of PV curtailment is activated. In the other case it skips the rule since PV curtailed is not necessarily zero, it depends as well on the inverter size.
    '''
    if m.PVAC==0:
        return en.Constraint.Skip
    else:
        #Max_injection in kW
        return m.E_PV_grid[i]/m.dt<=m.Max_injection

def PVSC_rule(m,i):
    '''
    Description
    -------
    Sets the flows from grid to the battery to zero if demand load shifting is not activated. In the other case it skips the rule.
    '''
    if m.DLS==1:
        return en.Constraint.Skip
    else:
        return(m.E_grid_batt[i]==0)

#Objective

def Obj_fcn(m):
    '''
    Description
    -------
    The bill is calculated in two parts, the energy related part is the retail price times the energy consumed from the grid minus the export price times the PV injection. If there is demand peak shaving (a capacity tariff is applied) the maximum power taken from the grid (in kW) is multiplied by the DAILY capacity tariff ($/kW per day).
    '''
    return(sum((m.retail_price[i]*m.E_cons[i])
    -(m.export_price[i]*m.E_PV_grid[i]) for i in m.Time))*m.PVSC+(m.P_max_day*m.capacity_tariff)*m.DPS
