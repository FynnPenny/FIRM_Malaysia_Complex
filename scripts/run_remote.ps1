# Remote desktop details
$remoteHost = "re100_ug@10.46.20.32"
$remotePath = "/media/fileshare/re100_ug/FIRM_Australia_Complex/FIRM_Malaysia_Complex-1/"
$sshKeyPath = "$env:USERPROFILE\.ssh\id_rsa"

# Array of parameter sets
$paramSets = @(
    "-n 11 -s 0 -q 1 -i 3 -f 1 -v 0", # Test run - do not remove (~2 mins to run)
    "-n 11 -s 0 -q 1 -i 150 -f 1 -v 0",
    "-n 11 -s 0 -q 1 -i 150 -f 3 -v 0",
    "-n 11 -s 70 -q 1 -i 150 -f 1 -v 0",
    "-n 11 -s 70 -q 1 -i 150 -f 3 -v 0"
    # "-n 11 -s 150 -q 1 -i 150 -f 1 -v 0",
    # "-n 11 -s 150 -q 1 -i 150 -f 3 -v 0",
    # "-n 11 -s 420 -q 1 -i 150 -f 1 -v 0",
    # "-n 11 -s 420 -q 1 -i 150 -f 3 -v 0"
    # Add more parameter sets as needed
)

# Function definitions
function Get-RemoteCPUUsage {
    $cpuUsage = ssh -i $sshKeyPath $remoteHost "top -bn1 | grep 'Cpu(s)' | awk '{print `$2 + `$4}'"
    return [math]::Round([double]$cpuUsage, 2)
}

function Download-Results {
    $localPath = "C:\Users\fynns\Downloads\Results_Import"
    $remotePath = "/media/fileshare/re100_ug/FIRM_Australia_Complex/FIRM_Malaysia_Complex-1/Results/"
    
    Write-Host "Downloading results from remote desktop..."
    
    # Create the local directory if it doesn't exist
    if (-not (Test-Path -Path $localPath)) {
        New-Item -ItemType Directory -Force -Path $localPath
    }
    
    # Ask user if they want to download files
    $downloadConfirmation = Read-Host "Do you want to download all files? [Y/N]"
    
    if ($downloadConfirmation -eq "Y") {
        # Download all files
        $scpCommand = "scp -r -i $sshKeyPath ${remoteHost}:$remotePath $localPath"
        
        try {
            Invoke-Expression $scpCommand
            Write-Host "All results downloaded successfully to $localPath"
        }
        catch {
            Write-Host "Error downloading results: $_"
        }
    }
    else {
        Write-Host "No files downloaded."
    }
}

# Main execution
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

# Call the function to download results after all optimizations are complete
Download-Results
