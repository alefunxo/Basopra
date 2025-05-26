Description
Daily battery schedule optimizer (i.e. 24 h optimization framework), assuming perfect day-ahead forecast of the electricity demand load and solar PV generation in order to determine the maximum economic potential regardless of the forecast strategy used. Include the use of different applications which residential batteries can perform from a consumer perspective. Applications such as avoidance of PV curtailment, demand load-shifting and demand peak shaving are considered along with the base application, PV self-consumption. Different battery technologies and sizes can be analyzed as well as different tariff structures.
Aging is treated as an exogenous parameter, calculated on daily basis and is not subject of optimization. Data with 15-minute, 30-minute and 1-hour temporal resolution may be used for simulations. The model objective function have two components, the energy-based and the power-based component, as the tariff structure depends on the applications considered, a boolean parameter activate the power-based factor of the bill when is necessary.


Citation
If you make use of this software for your work we would appreciate if you would cite this paper from the journal "Renewable & Sustainable Energy Reviews":
@article{pena-bello2019,
  title={Optimized PV-coupled battery systems for combining applications: Impact of battery technology and geography},
  author={Pena-Bello, Alejandro and Barbour, Edward and Gonzalez, Marta C. and Patel, Martin K. and Parra, David},
  journal={Renewable & Sustainable Energy Reviews},
  volume={ 112},
  pages={ 978-990},
  year={2019},
  doi={https://doi.org/10.1016/j.rser.2019.06.003}
}


In order to run the program you will need to clone it, type in your console:

git clone https://github.com/alefunxo/Basopra.git

then go to the repertory BASOPRA and run the setup:

cd Basopra
conda env create -f environment_droplet.yml
conda activate basopra_1

pyomo 5.5.1 proved to work fine with python 3.6, 3.7 and 3.9, please use this version.

Once the setup has been succesfully run, you can run the Main script, for this, change the repertory to the subdirectory BASOPRA and run python3 Main.py:

cd BASOPRA
python3 Main.py

Please have in mind that you will need CPLEX (or gurobi, glpk...) to run the optimization. If you have problems with CPLEX or other optimization software but you are sure you have it, go to Core_LP.py and be sure that the executable path is the correct one for your system, it is in the line opt = SolverFactory('PATH_TO_YOUR_OPTIMIZATION_SOFTWARE') (i.e., lines 181 and 184 of Core_LP.py).

---------------------------HOW TO USE---------------------
If you have clone BASOPRA from github.com you will see three folders inside Basopra (BASOPRA, Input and Doc). BASOPRA contains the code, Doc the documentation. Finally, Input contains 5 files, df_1h.csv (example of dataframe with one-hour resolution), df_30m.csv (example of dataframe with 30-minute resolution), df_15m.csv (example of dataframe with 15-minute resolution), df_US_Batt.csv (US data used for the optimization in Pena-Bello et al. (2019) and Input_data.csv. Input_data.csv contains the parameters by default of the optimization, such as inverter load ratio, inverter and converter efficiency, number of days to be simulated, etc. Please modify this file to customize your optimization. 

Time_resolution in Input_data.csv will determine the input file for the optimization, if Time_resolution is 1 then df_1h.csv will be used, if Time_resolution is 0.5 then df_30m.csv will be the input data. Please modify the input data in these files using your own data (we are working on a nice interface, but for the moment this is the only way to do it).

In order to run BASOPRA go to the BASOPRA directory (where the code is) and from the console run python3 Main.py (or python Main.py depending on how your system is configured). The results will be in csv format in a Output folder (which will be created automatically).

In case of doubts, bugs or problems please contact us by e-mail: contact.basopra@gmail.com or using github.com

📜 License Change Notice
Important: As of 26/05/2025, this project has been relicensed under the Apache License 2.0.

Previously, the code was licensed under the GNU General Public License (GPL). Since I am the sole author of all original source code in this repository, and no external GPL-licensed code has been included or derived from, I have chosen to relicense the project under the Apache License 2.0 to support broader use and integration.

Please refer to the LICENSE file for the current terms.

