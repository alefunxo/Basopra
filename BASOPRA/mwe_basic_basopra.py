import pyomo.environ as en
from pyomo.opt import SolverFactory
import paper_classes as pp
import LP
import matplotlib.pyplot as plt
import numpy as np

def generate_swiss_profiles_15min():
    """
    Returns realistic 15-min PV and demand profiles for a typical spring day in Switzerland.
    Values are in kWh per timestep (delta_t = 0.25 h).
    """

    t = np.arange(96)                 # 96 timesteps (15 min)
    hours = t * 0.25                 # convert to hours

    # --- PV profile (bell-shaped, peak ~ noon) ---
    # Sunrise ~6h, sunset ~18h (spring/autumn approximation)
    pv_peak_power = 4.0  # kW peak for a typical residential system

    pv = np.zeros_like(hours)
    for i, h in enumerate(hours):
        if 6 <= h <= 18:
            # smooth sinusoidal shape
            pv[i] = pv_peak_power * np.sin(np.pi * (h - 6) / 12)

    # Convert kW → kWh per timestep
    pv = pv * 0.25

    # --- Demand profile (Swiss residential typical shape) ---
    # Base load + morning + evening peaks (stronger evening)
    base_load = 0.3  # kW

    demand_power = (
        base_load
        + 0.6 * np.exp(-0.5 * ((hours - 7.5) / 1.5) ** 2)   # morning peak
        + 1.2 * np.exp(-0.5 * ((hours - 19) / 2.0) ** 2)    # evening peak
    )

    # Slight midday dip (people away)
    demand_power -= 0.2 * np.exp(-0.5 * ((hours - 13) / 2.5) ** 2)

    # Ensure non-negative
    demand_power = np.maximum(demand_power, 0.2)

    # Convert kW → kWh per timestep
    demand = demand_power * 0.25

    # Convert to dictionaries
    E_PV = {int(ti): float(pv[ti]*0) for ti in t}
    E_demand = {int(ti): float(demand[ti])*5 for ti in t}

    return E_PV, E_demand


def plot_dispatch_results(model, Data):
    """
    Plot optimization results in 3 subplots with a cleaner design:
    - Top: exchanges + PV production + demand
    - Middle: battery SOC
    - Bottom: prices

    Conventions:
    - Grid import is plotted negative
    - Battery charge is plotted negative
    - Battery discharge is plotted positive
    """

    # ---------- Time vectors ----------
    t_ops = [t for t in sorted(model.Time) if t >= 0]
    t_soc = [t for t in sorted(model.SOC.index_set())]

    # ---------- Input series ----------
    retail_price = [Data['retail_price'][t] for t in t_ops]
    pv_prod = [Data['E_PV'][t] for t in t_ops]
    demand = [Data['E_demand'][t] for t in t_ops]

    # ---------- Model results ----------
    grid_import = [-en.value(model.E_cons[t]) for t in t_ops]
    pv_export = [en.value(model.E_PV_grid[t]*-1) for t in t_ops]
    soc_vals = [en.value(model.SOC[t]) for t in t_soc]

    batt_charge = [-en.value(model.E_char[t]) for t in t_ops] if hasattr(model, 'E_char') else None
    batt_discharge = [en.value(model.E_dis[t]) for t in t_ops] if hasattr(model, 'E_dis') else None

    # ---------- Figure ----------
    fig = plt.figure(figsize=(14, 9), facecolor="white")
    gs = fig.add_gridspec(3, 1, height_ratios=[2.2, 1.2, 1.0], hspace=0.12)

    ax0 = fig.add_subplot(gs[0])
    ax1 = fig.add_subplot(gs[1], sharex=ax0)
    ax2 = fig.add_subplot(gs[2], sharex=ax0)

    # ---------- Common axis styling ----------
    for ax in (ax0, ax1, ax2):
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(True, axis='y', alpha=0.25, linewidth=0.8)
        ax.grid(False, axis='x')
        ax.tick_params(axis='both', labelsize=10)

    # ---------- Top panel: exchanges ----------
    ax0.axhline(0, color='black', linewidth=1.0, alpha=0.7)

    # Filled areas
    ax0.fill_between(t_ops, 0, grid_import, step='mid', alpha=0.35, label='Grid import')
    ax0.fill_between(t_ops, 0, pv_prod, step='mid', alpha=0.28, label='PV production')
    ax0.fill_between(t_ops, 0, pv_export, step='mid', alpha=0.25, label='PV export')

    if batt_charge is not None:
        ax0.fill_between(t_ops, 0, batt_charge, step='mid', alpha=0.25, label='Battery charge')
    if batt_discharge is not None:
        ax0.fill_between(t_ops, 0, batt_discharge, step='mid', alpha=0.25, label='Battery discharge')

    # Demand as a clean line on top
    ax0.plot(t_ops, demand, linewidth=2.2, label='Demand')

    ax0.set_ylabel('Energy [kWh]', fontsize=11)
    #ax0.set_title('Household energy flows', fontsize=14, pad=10)
    ax0.legend(
        ncol=3,
        frameon=False,
        fontsize=10,
        loc='upper center',
        bbox_to_anchor=(0.5, 1.08)
    )

    # ---------- Middle panel: SOC ----------
    ax1.plot(t_soc, soc_vals, linewidth=2.5, label='SOC')
    ax1.fill_between(t_soc, 0, soc_vals, alpha=0.18)

    if 'SOC_min' in Data:
        ax1.axhline(Data['SOC_min'], linestyle='--', linewidth=1.0, alpha=0.7)
    if 'SOC_max' in Data:
        ax1.axhline(Data['SOC_max'], linestyle='--', linewidth=1.0, alpha=0.7)

    ax1.set_ylabel('SOC [-]', fontsize=11)
    ax1.set_ylim(bottom=0)

    # ---------- Bottom panel: prices ----------
    ax2.step(t_ops, retail_price, where='mid', linewidth=2.2, label='Retail price')
    if 'Export_price' in Data:
        export_price = [Data['Export_price'][t] for t in t_ops]
        ax2.step(t_ops, export_price, where='mid', linewidth=1.8, linestyle='--', label='Export price')

    ax2.set_ylabel('Price [CHF/kWh]', fontsize=11)
    ax2.set_xlabel('Time of day [h]', fontsize=11)
    ax2.legend(frameon=False, fontsize=10, loc='upper right')

    # ---------- X ticks as hours ----------
    xticks = list(range(0, max(t_ops) + 1, 4))
    ax2.set_xticks(xticks)
    ax2.set_xticklabels([f'{int(x * Data["delta_t"]):02d}:00' for x in xticks])

    # ---------- Global title ----------
    fig.suptitle('Daily dispatch overview', fontsize=16, y=0.98)

    plt.tight_layout()
    plt.show()

##############################################################

# Create instances with minimal values
batt = pp.Battery_tech(Capacity=10,Technology='NMC')
batt.Efficiency = 0.9
batt.P_max_dis = -10  # kW
batt.P_max_char = 10  # kW



price = np.array([
    0.2389, 0.2361, 0.2358, 0.2342, 0.2326, 0.2412, 0.2365, 0.2319,
    0.2249, 0.2202, 0.2148, 0.2101, 0.2070, 0.2062, 0.2062, 0.2054,
    0.2062, 0.2085, 0.2109, 0.2132, 0.2187, 0.2234, 0.2304, 0.2389,
    0.2498, 0.2552, 0.2606, 0.2994, 0.2986, 0.2916, 0.2846, 0.2675,
    0.2512, 0.2372, 0.2256, 0.2124, 0.1945, 0.1813, 0.1736, 0.1643,
    0.1550, 0.1473, 0.1403, 0.1341, 0.1302, 0.1263, 0.1248, 0.1232,
    0.0715, 0.0653, 0.0645, 0.0645, 0.0645, 0.0645, 0.0645, 0.0645,
    0.0684, 0.0723, 0.0770, 0.0817, 0.0895, 0.0980, 0.1073, 0.1174,
    0.1283, 0.1438, 0.1531, 0.1679, 0.2241, 0.2373, 0.2513, 0.2661,
    0.2762, 0.2863, 0.2941, 0.2995, 0.3034, 0.3057, 0.3057, 0.3018,
    0.2964, 0.2933, 0.2902, 0.2886, 0.2855, 0.2809, 0.2762, 0.2716,
    0.2669, 0.2622, 0.2576, 0.2521, 0.2156, 0.2187, 0.2210, 0.2233
])

# Create a time set from -1 to 23 (with -1 as the initial condition)
time_set = list(range(-1, 96))
# Generate profiles
E_PV, E_demand = generate_swiss_profiles_15min()
# Build the Data dictionary with minimal parameters for a full day.
# In this example heating is active but without thermal storage and DHW.
Data = {
    'Set_declare': time_set,
    'delta_t': 0.25,
    'dayofyear': 1,  # within 120-274
    'App_comb': [1, 1, 1, 1],  # [PVAC, PVSC, DLS, DPS]
    #'retail_price': {t: 0.2201 for t in range(96)},#Flat
    #'retail_price': {t: 0.2679 if 8*4 <= t <= 20*4 else 0.2359 for t in range(96)},#DT 

    'retail_price': {t: float(price[t]) for t in range(96)}, # Dynamic
    'E_PV': E_PV,
    'E_demand': E_demand,
    'Export_price': {t: 0.06 for t in range(96)},
    'Capacity_tariff': 10.75,
    'Inv_power': batt.Capacity*0.7,

    'Inverter_eff': 0.95,
    'Converter_Efficiency_Batt': 0.98,

    'Max_inj': 10,

    'Batt': batt,
    'SOC_max':batt.SOC_max,
    'SOC_min':batt.SOC_min
}

# Import the Concrete_model function from your script.
# It is assumed that the provided script with Concrete_model and all constraints is in scope.
model = LP.Concrete_model(Data)

# Create and run the solver (using GLPK as an example)
solver = SolverFactory('gurobi')
result = solver.solve(model, tee=True)
result.write(num=1)

plot_dispatch_results(model, Data)
# Display a few results: objective value, grid consumption, PV injection, and battery SOC.
print("Objective value:", en.value(model.total_cost))
for t in sorted(model.Time):
    grid_cons = en.value(model.E_cons[t])
    pv_inj = en.value(model.E_PV_grid[t])
    # Battery SOC is defined over m.tm (which includes the initial time -1)
    soc = en.value(model.SOC[t]) if t in model.SOC else None
    print(f"15-min {t}: Grid consumption = {grid_cons:.3f} kWh, PV injection = {pv_inj:.3f} kWh, Battery SOC = {soc:.3f}")

