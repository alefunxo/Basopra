Description
Daily battery schedule optimizer (i.e. 24 h optimization framework), assuming perfect day-ahead forecast of the electricity demand load and solar PV generation in order to determine the maximum economic potential regardless of the forecast strategy used. Include the use of different applications which residential batteries can perform from a consumer perspective. Applications such as avoidance of PV curtailment, demand load-shifting and demand peak shaving are considered along with the base application, PV self-consumption. Different battery technologies and sizes can be analyzed as well as different tariff structures.
Aging is treated as an exogenous parameter, calculated on daily basis and is not subject of optimization. Data with 15-minute temporal resolution are used for simulations. The model objective function have two components, the energy-based and the power-based component, as the tariff structure depends on the applications considered, a boolean parameter activate the power-based factor of the bill when is necessary.


Citation
If you make use of this software for your work we would appreciate it if you would cite the paper from the Journal of Open Source Software:
@article{pena-bello2018,
  title={ Optimization of PV-coupled battery systems for combining applications: impact of battery technology and location},
  author={Pena-Bello, Alejandro and Barbour, Edward and Gonzalez, Marta C. and Patel, Martin K. and Parra, David},
  journal={tbd},
  volume={ tbd },
  number={ tbd },
  pages={ tbd },
  year={2018}
}


In order to run the program you will need to clone it, type in your console:

git clone https://github.com/alefunxo/Basopra.git

then go to the repertory BASOPRA and run the setup:

cd BASOPRA
python setup.py install

Once the setup has been succesfully run, you can run the Main script, for this change
of repertory to the subdirectory BASOPRA and run Main.py:

cd BASOPRA
python Main.py

In the folder Output you will find the resulting file (*.pickle) which includes the whole information of the optimization in the form of a dictionary.
In the same folder you will find the file 'test_out.csv' where you will be able to see the last optimized day.

Please have in mind that you will need CPLEX to run the optimization. If you have problems with CPLEX but you are sure you have it go to Core_LP.py and be sure that the executable path is the correct one for your system.

