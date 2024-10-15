#!/bin/bash
 
pid=$(grep ^Pid /proc/self/status)
corelist=$(grep Cpus_allowed_list: /proc/self/status | awk '{print $8}')
host=$(hostname | sed 's/.gadi.nci.org.au//g')
echo subtask $1 running in $pid using cores $corelist on compute node $host
 
# Load module, always specify version number.
module load python3/3.11.0
 
python3 Optimisation.py -e $1 -n $2 -s $3 -b $4 -H $5 -i $6 -p $7