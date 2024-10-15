# PowerShell script to run Optimisation.py with different parameters

# Define an array of parameter sets
$parameterSets = @(
    @{n=11; s=500; q=1; i=3}
)

# Loop through each parameter set
foreach ($params in $parameterSets) {
    # Construct the command
    $command = "python src/Optimisation.py"
    foreach ($key in $params.Keys) {
        $command += " -$key $($params[$key])"
    }
    
    # Display the command being run
    Write-Host "Running: $command"
    
    # Execute the command
    Invoke-Expression $command
    
    # Optional: Add a pause between runs
    Start-Sleep -Seconds 5
}

Write-Host "All runs completed."
