#!/bin/bash

python3 Optimisation.py -e 5 -n APG_PMY_Only -s HVAC -b True -H False -i 2000 -p 5
python3 Optimisation.py -e 10 -n APG_PMY_Only -s HVAC -b True -H False -i 2000 -p 5
python3 Optimisation.py -e 20 -n APG_PMY_Only -s HVAC -b True -H False -i 2000 -p 5
python3 Optimisation.py -e 5 -n APG_PMY_Only -s HVAC -b True -H True -i 2000 -p 5
python3 Optimisation.py -e 10 -n APG_PMY_Only -s HVAC -b True -H True -i 2000 -p 5
python3 Optimisation.py -e 20 -n APG_PMY_Only -s HVAC -b True -H True -i 2000 -p 5

python3 Optimisation.py -e 5 -n APG_BMY_Only -s HVAC -b True -H False -i 2000 -p 5
python3 Optimisation.py -e 10 -n APG_BMY_Only -s HVAC -b True -H False -i 2000 -p 5
python3 Optimisation.py -e 20 -n APG_BMY_Only -s HVAC -b True -H False -i 2000 -p 5
python3 Optimisation.py -e 5 -n APG_BMY_Only -s HVAC -b True -H True -i 2000 -p 5
python3 Optimisation.py -e 10 -n APG_BMY_Only -s HVAC -b True -H True -i 2000 -p 5
python3 Optimisation.py -e 20 -n APG_BMY_Only -s HVAC -b True -H True -i 2000 -p 5

python3 Optimisation.py -e 5 -n APG_MY_Isolated -s HVAC -b True -H False -i 2000 -p 5
python3 Optimisation.py -e 10 -n APG_MY_Isolated -s HVAC -b True -H False -i 2000 -p 5
python3 Optimisation.py -e 20 -n APG_MY_Isolated -s HVAC -b True -H False -i 2000 -p 5
python3 Optimisation.py -e 5 -n APG_MY_Isolated -s HVAC -b True -H True -i 2000 -p 5
python3 Optimisation.py -e 10 -n APG_MY_Isolated -s HVAC -b True -H True -i 2000 -p 5
python3 Optimisation.py -e 20 -n APG_MY_Isolated -s HVAC -b True -H True -i 2000 -p 5

python3 Optimisation.py -e 5 -n APG_Full -s HVAC -b True -H False -i 2000 -p 5
python3 Optimisation.py -e 10 -n APG_Full -s HVAC -b True -H False -i 2000 -p 5
python3 Optimisation.py -e 20 -n APG_Full -s HVAC -b True -H False -i 2000 -p 5
python3 Optimisation.py -e 5 -n APG_Full -s HVAC -b True -H True -i 2000 -p 5
python3 Optimisation.py -e 10 -n APG_Full -s HVAC -b True -H True -i 2000 -p 5
python3 Optimisation.py -e 20 -n APG_Full -s HVAC -b True -H True -i 2000 -p 5