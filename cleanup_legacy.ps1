# Run this from the root of the existing Algo repository.
# Preserves old files locally under archive/ but removes them from Git tracking.
$ErrorActionPreference = "Stop"

New-Item -ItemType Directory -Force -Path ".\archive\legacy_placeholder_data" | Out-Null
New-Item -ItemType Directory -Force -Path ".\archive\legacy_placeholder_results" | Out-Null
New-Item -ItemType Directory -Force -Path ".\archive\legacy_code" | Out-Null

$preserve = @(
    @{ Source = ".\data\XAUUSD_H1.csv"; Destination = ".\archive\legacy_placeholder_data\XAUUSD_H1.csv" },
    @{ Source = ".\research\trend_system_report.txt"; Destination = ".\archive\legacy_placeholder_results\trend_system_report.txt" },
    @{ Source = ".\research\trend_equity_curve.png"; Destination = ".\archive\legacy_placeholder_results\trend_equity_curve.png" },
    @{ Source = ".\backtests\trend_system_vbt.py"; Destination = ".\archive\legacy_code\trend_system_vbt.py" },
    @{ Source = ".\data\data_loader_mt5.py"; Destination = ".\archive\legacy_code\data_loader_mt5.py" },
    @{ Source = ".\test_setup.py"; Destination = ".\archive\legacy_code\test_setup.py" }
)

foreach ($item in $preserve) {
    if (Test-Path $item.Source) {
        git rm --cached --ignore-unmatch -- $item.Source 2>$null | Out-Null
        $parent = Split-Path $item.Destination -Parent
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
        Move-Item -Force $item.Source $item.Destination
        Write-Host "Archived: $($item.Source)"
    }
}

# Remove tracked Python/test caches from Git and local disk.
git rm -r --cached --ignore-unmatch -- .pytest_cache __pycache__ 2>$null | Out-Null
Get-ChildItem -Path . -Directory -Recurse -Force -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -in @("__pycache__", ".pytest_cache") } |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# Remove the now-empty legacy directories if possible.
foreach ($dir in @(".\research", ".\backtests")) {
    if ((Test-Path $dir) -and -not (Get-ChildItem $dir -Force)) {
        Remove-Item $dir -Force
    }
}

Write-Host "Legacy files preserved under .\archive (ignored by Git)."
Write-Host "Review git status before committing."
