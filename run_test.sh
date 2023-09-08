#!/bin/bash
python3 Optimisation.py -e 5 -n SB -s HVAC -b True -H True -i 400 -p 2

python3 Optimisation.py -e 5 -n APG_PMY_Only -s HVAC -b True -H True -i 800 -p 2

python3 Optimisation.py -e 5 -n APG_BMY_Only -s HVAC -b True -H True -i 800 -p 2

python3 Optimisation.py -e 5 -n APG_MY_Isolated -s HVAC -b True -H True -i 800 -p 4

python3 Optimisation.py -e 5 -n APG_Full -s HVAC -b True -H True -i 800 -p 4