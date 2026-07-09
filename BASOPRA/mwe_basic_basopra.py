import math
import pyomo.environ as en
from pyomo.opt import SolverFactory, SolverStatus, TerminationCondition
import paper_classes as pp
import LP
from Core_LP import aging_day
import matplotlib.pyplot as plt
import numpy as np

def generate_swiss_profiles_15min(n_days=1):
    """
    Returns realistic 15-min PV and demand profiles for n_days of a typical
    spring week in Switzerland. Values are in kWh per timestep (delta_t = 0.25 h).
    Day-to-day variability (cloudier/sunnier days, higher/lower demand days) is
    added so a multi-day horizon is not just the same day repeated verbatim.
    """
    steps_per_day = 96
    t = np.arange(steps_per_day)      # 96 timesteps (15 min)
    hours = t * 0.25                 # convert to hours

    # --- PV profile (bell-shaped, peak ~ noon) ---
    # Sunrise ~6h, sunset ~18h (spring/autumn approximation)
    pv_peak_power = 4.0  # kW peak for a typical residential system

    pv_day = np.zeros_like(hours)
    for i, h in enumerate(hours):
        if 6 <= h <= 18:
            # smooth sinusoidal shape
            pv_day[i] = pv_peak_power * np.sin(np.pi * (h - 6) / 12)

    # Convert kW → kWh per timestep
    pv_day = pv_day * 0.25

    # --- Demand profile (Swiss residential typical shape) ---
    # Base load + morning + evening peaks (stronger evening)
    base_load = 0.3  # kW

    demand_power_day = (
        base_load
        + 0.6 * np.exp(-0.5 * ((hours - 7.5) / 1.5) ** 2)   # morning peak
        + 1.2 * np.exp(-0.5 * ((hours - 19) / 2.0) ** 2)    # evening peak
    )

    # Slight midday dip (people away)
    demand_power_day -= 0.2 * np.exp(-0.5 * ((hours - 13) / 2.5) ** 2)

    # Ensure non-negative
    demand_power_day = np.maximum(demand_power_day, 0.2)

    # Convert kW → kWh per timestep
    demand_day = demand_power_day * 0.25

    rng = np.random.default_rng(0)
    pv_all = []
    demand_all = []
    for _ in range(n_days):
        cloud_factor = rng.uniform(0.7, 1.0)    # some days cloudier than others
        load_factor = rng.uniform(0.85, 1.15)   # some days higher/lower demand
        pv_all.append(pv_day * cloud_factor)
        demand_all.append(demand_day * load_factor)
    pv = np.concatenate(pv_all)
    demand = np.concatenate(demand_all)

    # PV is kept multiplied by 0 (as in the original single-day MWE) so the
    # demo isolates demand-shifting/peak-shaving from the grid; set the '*0'
    # factor to 1 below if you want PV in the mix.
    E_PV = pv
    E_demand = demand*5

    return E_PV, E_demand


def plot_dispatch_results(series, delta_t, window_days):
    """
    Plot the full stitched multi-window dispatch trajectory in 3 subplots:
    - Top: exchanges + PV production + demand
    - Middle: battery SOC
    - Bottom: prices

    Conventions:
    - Grid import is plotted negative
    - Battery charge is plotted negative
    - Battery discharge is plotted positive

    'series' holds plain python/numpy arrays already stitched across every
    solved window (see the simulation loop below) - this function has no
    knowledge of pyomo or of how many windows were solved.
    """
    t_ops = series['t_ops']
    t_soc = series['t_soc']
    steps_per_day = int(24/delta_t)
    total_days = int(np.ceil(len(t_ops)/steps_per_day))

    retail_price = series['retail_price']
    pv_prod = series['pv_prod']
    demand = series['demand']
    grid_import = series['grid_import']
    pv_export = series['pv_export']
    soc_vals = series['soc']
    batt_charge = series['batt_charge']
    batt_discharge = series['batt_discharge']
    export_price = series['export_price']

    # ---------- Figure ----------
    fig = plt.figure(figsize=(14, 9), facecolor="white")
    gs = fig.add_gridspec(3, 1, height_ratios=[2.2, 1.2, 1.0], hspace=0.12)

    ax0 = fig.add_subplot(gs[0])
    ax1 = fig.add_subplot(gs[1], sharex=ax0)
    ax2 = fig.add_subplot(gs[2], sharex=ax0)

    # ---------- Common axis styling ----------
    day_boundaries = [d*steps_per_day for d in range(1, total_days)]
    window_boundaries = [w*steps_per_day for w in range(window_days, total_days, window_days)]
    for ax in (ax0, ax1, ax2):
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(True, axis='y', alpha=0.25, linewidth=0.8)
        ax.grid(False, axis='x')
        ax.tick_params(axis='both', labelsize=10)
        for xb in day_boundaries:
            ax.axvline(xb, color='black', linewidth=0.8, alpha=0.15, linestyle='-')
        for xb in window_boundaries:
            # thicker marker at every point where a NEW LP window was solved,
            # i.e. where the rolling-window loop hands aging state forward
            ax.axvline(xb, color='crimson', linewidth=1.4, alpha=0.5, linestyle='--')

    # ---------- Top panel: exchanges ----------
    ax0.axhline(0, color='black', linewidth=1.0, alpha=0.7)

    ax0.fill_between(t_ops, 0, grid_import, step='mid', alpha=0.35, label='Grid import')
    ax0.fill_between(t_ops, 0, pv_prod, step='mid', alpha=0.28, label='PV production')
    ax0.fill_between(t_ops, 0, pv_export, step='mid', alpha=0.25, label='PV export')
    ax0.fill_between(t_ops, 0, batt_charge, step='mid', alpha=0.25, label='Battery charge')
    ax0.fill_between(t_ops, 0, batt_discharge, step='mid', alpha=0.25, label='Battery discharge')

    ax0.plot(t_ops, demand, linewidth=2.2, label='Demand')

    ax0.set_ylabel('Energy [kWh]', fontsize=11)
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
    ax1.set_ylabel('SOC [-]', fontsize=11)
    ax1.set_ylim(bottom=0)

    # ---------- Bottom panel: prices ----------
    ax2.step(t_ops, retail_price, where='mid', linewidth=2.2, label='Retail price')
    ax2.step(t_ops, export_price, where='mid', linewidth=1.8, linestyle='--', label='Export price')

    ax2.set_ylabel('Price [CHF/kWh]', fontsize=11)
    ax2.set_xlabel('Time [day, hour]', fontsize=11)
    ax2.legend(frameon=False, fontsize=10, loc='upper right')

    # ---------- X ticks ----------
    if total_days == 1:
        xticks = list(range(0, max(t_ops) + 1, 4))
        ax2.set_xticks(xticks)
        ax2.set_xticklabels([f'{int(x * delta_t):02d}:00' for x in xticks])
    else:
        tick_step = steps_per_day // 2   # one tick every 12h
        xticks = list(range(0, max(t_ops) + 1, tick_step))
        ax2.set_xticks(xticks)
        ax2.set_xticklabels([
            f'D{x // steps_per_day + 1} {int((x % steps_per_day) * delta_t):02d}:00'
            for x in xticks
        ], rotation=45, ha='right')

    title = 'Daily dispatch overview' if total_days == 1 else (
        f'{total_days}-day dispatch overview '
        f'({window_days}-day rolling optimization windows, dashed red = new window solved)'
    )
    fig.suptitle(title, fontsize=15, y=0.98)

    plt.tight_layout()
    plt.show()

##############################################################

# Create instances with minimal values
batt = pp.Battery_tech(Capacity=100,Technology='NMC')
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

# WINDOW_DAYS: size of each single LP solve (matches Core_LP's 'days', e.g. 7
#              for the weekly optimization window).
# TOTAL_DAYS:  total number of days to simulate (matches Core_LP's
#              param['ndays']). The rolling loop below solves
#              ceil(TOTAL_DAYS/WINDOW_DAYS) independent LP windows in
#              sequence, carrying aging (SOH/capacity/SOC_max) from the end of
#              one window into the start of the next - exactly like
#              Core_LP.Optimize(). Set TOTAL_DAYS == WINDOW_DAYS to reproduce
#              a single-window solve (e.g. the original 1-day MWE).
WINDOW_DAYS = 7
TOTAL_DAYS = 21
STEPS_PER_DAY = 96
dt = 0.25

E_PV_all, E_demand_all = generate_swiss_profiles_15min(n_days=TOTAL_DAYS)
retail_price_all = np.tile(price, TOTAL_DAYS)
export_price_all = np.full(STEPS_PER_DAY*TOTAL_DAYS, 0.06)

n_windows = math.ceil(TOTAL_DAYS/WINDOW_DAYS)

aux_Cap_aged = batt.Capacity
aux_SOC_max = batt.SOC_max
SOH = 1

soc_full = [batt.SOC_min]
grid_cons_full = []
pv_inj_full = []
E_char_full = []
E_dis_full = []
day_summary = []   # per-day aging trace: (day, SOH, capacity, DoD)

for i in range(n_windows):
    d0 = i*WINDOW_DAYS
    d1 = min(d0+WINDOW_DAYS, TOTAL_DAYS)
    n_days_window = d1-d0
    steps0 = d0*STEPS_PER_DAY
    steps1 = d1*STEPS_PER_DAY
    window_len = steps1-steps0

    Data = {
        'Set_declare': list(range(-1, window_len)),
        'delta_t': dt,
        'dayofyear': 1+d0,
        'App_comb': [1, 1, 1, 1],  # [PVAC, PVSC, DLS, DPS]
        'retail_price': {k: float(retail_price_all[steps0+k]) for k in range(window_len)},
        'E_PV': {k: float(E_PV_all[steps0+k]) for k in range(window_len)},
        'E_demand': {k: float(E_demand_all[steps0+k]) for k in range(window_len)},
        'Export_price': {k: float(export_price_all[steps0+k]) for k in range(window_len)},
        'Capacity_tariff': 10.75,
        'Inv_power': batt.Capacity*0.7,
        'Inverter_eff': 0.95,
        'Converter_Efficiency_Batt': 0.98,
        'Max_inj': 10,
        'Batt': batt,
        'SOC_max': aux_SOC_max,
        'SOC_min': batt.SOC_min,
    }

    model = LP.Concrete_model(Data)
    solver = SolverFactory('gurobi')
    result = solver.solve(model)

    if not ((result.solver.status == SolverStatus.ok) and
            (result.solver.termination_condition == TerminationCondition.optimal)):
        print(f"Window {i+1}/{n_windows} (days {d0+1}-{d1}) failed to solve: "
              f"{result.solver.termination_condition}")
        break

    t_ops = sorted(t for t in model.Time)
    grid_cons_win = [en.value(model.E_cons[t]) for t in t_ops]
    pv_inj_win = [en.value(model.E_PV_grid[t]) for t in t_ops]
    E_char_win = np.array([en.value(model.E_char[t]) for t in t_ops])
    E_dis_win = np.array([en.value(model.E_dis[t]) for t in t_ops])
    soc_win = [en.value(model.SOC[t]) for t in t_ops]

    grid_cons_full.extend(grid_cons_win)
    pv_inj_full.extend(pv_inj_win)
    E_char_full.extend(E_char_win.tolist())
    E_dis_full.extend(E_dis_win.tolist())
    soc_full.extend(soc_win)

    # Aging is tracked per REAL calendar day inside the window (the LP itself
    # solves the whole window against a single fixed SOC_max/capacity), then
    # the last day's outcome is carried forward as the starting point for the
    # next window - this mirrors Core_LP.Optimize() exactly.
    for day_offset in range(n_days_window):
        day_slice = slice(day_offset*STEPS_PER_DAY, (day_offset+1)*STEPS_PER_DAY)
        SOC_max_, aux_Cap_aged, SOH, Cycle_aging_factor, cycle_cal, DoD = aging_day(
            E_char_win[day_slice], SOH, batt.SOC_min, batt, aux_Cap_aged)
        aux_SOC_max = SOC_max_
        day_summary.append({'day': d0+day_offset+1, 'SOH': SOH,
                             'capacity': aux_Cap_aged, 'DoD': DoD})

    print(f"Window {i+1}/{n_windows} (days {d0+1}-{d1}): objective={en.value(model.total_cost):.3f}  "
          f"-> end-of-window SOH={SOH:.4f}, capacity={aux_Cap_aged:.3f} kWh")

n_solved = len(grid_cons_full)
t_ops_full = list(range(n_solved))
t_soc_full = list(range(-1, n_solved))

series = {
    't_ops': t_ops_full,
    't_soc': t_soc_full,
    'retail_price': retail_price_all[:n_solved],
    'export_price': export_price_all[:n_solved],
    'pv_prod': E_PV_all[:n_solved],
    'demand': E_demand_all[:n_solved],
    'grid_import': [-v for v in grid_cons_full],
    'pv_export': [-v for v in pv_inj_full],
    'soc': soc_full,
    'batt_charge': [-v for v in E_char_full],
    'batt_discharge': E_dis_full,
}

plot_dispatch_results(series, dt, WINDOW_DAYS)

print("\nPer-day aging summary:")
print(f"{'Day':>4} {'SOH':>8} {'Capacity[kWh]':>15} {'DoD':>8}")
for row in day_summary:
    print(f"{row['day']:>4} {row['SOH']:>8.4f} {row['capacity']:>15.3f} {row['DoD']:>8.3f}")
