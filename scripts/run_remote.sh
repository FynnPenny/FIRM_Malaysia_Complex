#!/bin/bash

# Remote desktop details
REMOTE_HOST="re100_ug@10.46.20.32"
REMOTE_PATH="/media/fileshare/re100_ug/FIRM_Australia_Complex/Results_Storage/Results_Export/"

# Array of parameter sets
declare -a PARAM_SETS=(
    "-n 11 -s 1000 -q 1 -i 100"
    # Add more parameter sets as needed
)

# Loop through each parameter set
for PARAMS in "${PARAM_SETS[@]}"
do
    # Command to run on the remote machine
    REMOTE_COMMAND="python src/Optimisation.py $PARAMS"
    
    echo "Running with parameters: $PARAMS"
    
    # Use SSH to execute the command on the remote desktop
    ssh $REMOTE_HOST "cd $REMOTE_PATH && $REMOTE_COMMAND"
    
    echo "Finished run with parameters: $PARAMS"
    echo "-----------------------------------"
done

echo "All runs completed."
