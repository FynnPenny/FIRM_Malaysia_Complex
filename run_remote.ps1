# Remote desktop details
$remoteHost = "re100_ug@10.46.20.32"
$remotePath = "/media/fileshare/re100_ug/FIRM_Australia_Complex/FIRM_Malaysia_Complex-1/"
$sshKeyPath = "$env:USERPROFILE\.ssh\id_rsa"

# Array of parameter sets
$paramSets = @(
    "-n 11 -s 1000 -q 1 -i 5 -v 0",
    "-n 11 -s 1000 -q 1 -i 6 -v 0"
    # Add more parameter sets as needed
)

# Function to check CPU usage on remote desktop
function Get-RemoteCPUUsage {
    $cpuUsage = ssh -i $sshKeyPath $remoteHost "top -bn1 | grep 'Cpu(s)' | awk '{print `$2 + `$4}'"
    return [math]::Round([double]$cpuUsage, 2)
}

# Check initial CPU usage
$initialCPUUsage = Get-RemoteCPUUsage
Write-Host "Current CPU usage on remote desktop: $initialCPUUsage%"

# Wait for user input
$userInput = Read-Host "Press Enter to continue or 'q' to quit"
if ($userInput -eq 'q') {
    Write-Host "Script terminated by user."
    exit
}

# Loop through each parameter set
foreach ($params in $paramSets) {
    # Command to run on the remote machine
    $remoteCommand = "python3 Optimisation.py $params"
    
    Write-Host "`n========================================"
    Write-Host "Starting optimization with parameters: $params"
    Write-Host "========================================"
    
    # Use SSH to execute the command on the remote desktop
    $output = ssh -i $sshKeyPath $remoteHost "cd $remotePath && PYTHONIOENCODING=utf-8 LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 $remoteCommand" 2>&1

    Write-Host "Output from remote execution:"
    $output | Out-String -Stream | ForEach-Object {
       Write-Host $_
   }
    
    Write-Host "========================================"
    Write-Host "Finished optimization with parameters: $params"
    Write-Host "========================================`n"
}

Write-Host "All optimization runs completed."
