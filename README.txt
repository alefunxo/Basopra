Description
Daily battery schedule optimizer (i.e. 24 h optimization framework), assuming perfect day-ahead forecast of the electricity demand load and solar PV generation in order to determine the maximum economic potential regardless of the forecast strategy used. Include the use of different applications which residential batteries can perform from a consumer perspective. Applications such as avoidance of PV curtailment, demand load-shifting and demand peak shaving are considered along with the base application, PV self-consumption. Different battery technologies and sizes can be analyzed as well as different tariff structures.
Aging is treated as an exogenous parameter, calculated on daily basis and is not subject of optimization. Data with 15-minute, 30-minute and 1-hour temporal resolution may be used for simulations. The model objective function have two components, the energy-based and the power-based component, as the tariff structure depends on the applications considered, a boolean parameter activate the power-based factor of the bill when is necessary.


Citation
If you make use of this software for your work we would appreciate if you would cite this paper from the journal "Renewable & Sustainable Energy Reviews":
@article{pena-bello2018,
  title={ Optimized PV-coupled battery systems for combining applications: impact of battery technology and location},
  author={Pena-Bello, Alejandro and Barbour, Edward and Gonzalez, Marta C. and Patel, Martin K. and Parra, David},
  journal={Renewable & Sustainable Energy Reviews},
  volume={ tbd },
  number={ tbd },
  pages={ tbd },
  year={2019}
}


In order to run the program you will need to clone it, type in your console:

git clone https://github.com/alefunxo/Basopra.git

then go to the repertory BASOPRA and run the setup:

cd BASOPRA
python setup.py install

Once the setup has been succesfully run, you can run the Main script, for this, change the repertory to the subdirectory BASOPRA and run python3 Main.py:

cd BASOPRA
python3 Main.py

In the folder Output you will find the resulting file (*.csv) which includes the results of the optimization in the same resolution of the input data as well as a csv file with the aggregated results.

Please have in mind that you will need CPLEX (or gurobi, glpk...) to run the optimization. If you have problems with CPLEX or other optimization software but you are sure you have it, go to Core_LP.py and be sure that the executable path is the correct one for your system, it is in the line opt = SolverFactory('PATH_TO_YOUR_OPTIMIZATION_SOFTWARE').

