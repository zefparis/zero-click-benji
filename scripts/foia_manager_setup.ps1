<#
.SYNOPSIS
    Installs Python 3 dependencies using pip.
.DESCRIPTION
    This script checks for Python 3, updates pip, and installs the required dependencies
    listed in requirements.txt. It handles potential authentication prompts.
.NOTES
    Requires Python 3 to be installed and in the system's PATH.
#>

# Set error action preference to stop on any error
$ErrorActionPreference = "Stop"

# Function to check if a command exists
function Test-CommandExists {
    param (
        [string]$Command
    )
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

# Check if Python 3 is installed
if (-not (Test-CommandExists "python3")) {
    Write-Error "Python 3 is not installed or not in your PATH. Please install Python 3."
    exit 1
}

Write-Host "Python 3 found."

# Check if pip is installed
if (-not (Test-CommandExists "pip3")) {
    Write-Error "pip3 is not installed. Please install pip for Python 3."
    exit 1
}

Write-Host "pip3 found."

# Update pip
Write-Host "Updating pip..."
try {
    python3 -m pip install --upgrade pip
}
catch {
    Write-Error "Failed to update pip: $($_.Exception.Message)"
    exit 1
}
Write-Host "pip updated successfully."

# Install dependencies from requirements.txt
Write-Host "Installing dependencies from requirements.txt..."
try {
    python3 -m pip install -r requirements.txt
}
catch {
    Write-Error "Failed to install dependencies: $($_.Exception.Message)"
    exit 1
}

Write-Host "Dependencies installed successfully."
Write-Host "Script completed."