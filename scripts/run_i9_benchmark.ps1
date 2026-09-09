param(
    [string]$Python = ""
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$OutputRelative = "paper_results/runtime_i9_0.1.3"
$OutputDirectory = Join-Path $ProjectRoot $OutputRelative

if ([string]::IsNullOrWhiteSpace($Python)) {
    $VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
    if (Test-Path -LiteralPath $VenvPython) {
        $Python = $VenvPython
    }
    else {
        $Python = "python"
    }
}

if (Test-Path -LiteralPath $OutputDirectory) {
    throw "Refusing to overwrite existing benchmark output: $OutputDirectory"
}

$Cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
$CpuName = $Cpu.Name.Trim()
if ($CpuName -notmatch "i9-12900K") {
    throw "This request is for the i9-12900K reference machine; detected: $CpuName"
}

Push-Location $ProjectRoot
try {
    & $Python -c "from importlib.metadata import version; assert version('slabx') == '1.0.6'; assert version('slabx-lh2') == '0.1.3'"
    if ($LASTEXITCODE -ne 0) { throw "Required package versions are not installed." }

    & $Python scripts/benchmark_runtime.py `
        --repeats 100 `
        --batch-repeats 30 `
        --cold-repeats 20 `
        --warmup 10 `
        --batch35 30 `
        --parallel 0 `
        --out $OutputRelative
    if ($LASTEXITCODE -ne 0) { throw "Benchmark execution failed." }

    $RawPath = Join-Path $OutputDirectory "runtime_raw.csv"
    $SummaryPath = Join-Path $OutputDirectory "runtime_summary.csv"
    $RawRows = @(Import-Csv -LiteralPath $RawPath)
    $SummaryRows = @(Import-Csv -LiteralPath $SummaryPath)
    $Expected = [ordered]@{
        "ffi_test4|warm_e2e_single" = 100
        "ffi_test6|warm_e2e_single" = 100
        "nasa_test6|warm_e2e_single" = 100
        "ffi6|warm_e2e_ffi6_batch" = 30
        "all35|warm_e2e_35_sequential" = 30
        "ffi_test4|cold_start_single" = 20
    }
    $Validation = @()
    $Overall = "PASS"
    $RawErrors = @($RawRows | Where-Object {
        -not [string]::IsNullOrWhiteSpace([string]$_.error)
    })
    if ($RawErrors.Count -ne 0) {
        throw "Benchmark raw data contains $($RawErrors.Count) error row(s)."
    }
    foreach ($Entry in $Expected.GetEnumerator()) {
        $Parts = $Entry.Key.Split("|")
        $CaseId = $Parts[0]
        $Metric = $Parts[1]
        $Selected = @($RawRows | Where-Object {
            $_.case_id -eq $CaseId -and $_.metric -eq $Metric
        })
        if ($Selected.Count -ne [int]$Entry.Value) {
            throw "$($Entry.Key): expected n=$($Entry.Value), found n=$($Selected.Count)."
        }
        $Summary = @($SummaryRows | Where-Object {
            $_.case_id -eq $CaseId -and $_.metric -eq $Metric
        })
        if ($Summary.Count -ne 1) {
            throw "$($Entry.Key): expected one summary row, found $($Summary.Count)."
        }
        if ([int]$Summary[0].failures -ne 0) {
            throw "$($Entry.Key): summary reports $($Summary[0].failures) failure(s)."
        }
        $P50 = [double]$Summary[0].p50_ms
        $P99 = [double]$Summary[0].p99_ms
        if ($P50 -le 0.0) {
            throw "$($Entry.Key): non-positive p50 ($P50)."
        }
        $Ratio = $P99 / $P50
        $Flag = if ($Ratio -le 1.30) { "PASS" } else { "WARN" }
        if ($Flag -eq "WARN") { $Overall = "WARN" }
        $Validation += ("{0} n={1} failures=0 p99/p50={2:F3} {3}" -f `
            $Entry.Key, $Selected.Count, $Ratio, $Flag)
    }
    $Validation = @("overall=$Overall") + $Validation
    Set-Content -LiteralPath (Join-Path $OutputDirectory "validation.txt") `
        -Value $Validation -Encoding utf8

    $Os = Get-CimInstance Win32_OperatingSystem
    $PythonVersion = (& $Python --version 2>&1 | Out-String).Trim()
    $PythonExecutable = (& $Python -c "import sys; print(sys.executable)" | Out-String).Trim()
    $PackageVersions = (& $Python -c "from importlib.metadata import version; [print(n + '=' + version(n)) for n in ('slabx', 'slabx-lh2', 'numpy', 'CoolProp')]" | Out-String).Trim()
    $Environment = @(
        "timestamp_utc=$([DateTime]::UtcNow.ToString('o'))"
        "cpu=$CpuName"
        "cpu_physical_cores=$($Cpu.NumberOfCores)"
        "cpu_logical_processors=$($Cpu.NumberOfLogicalProcessors)"
        "os=$($Os.Caption) $($Os.Version)"
        "python=$PythonVersion"
        "python_executable=$PythonExecutable"
        $PackageVersions
        "command=benchmark_runtime.py --repeats 100 --batch-repeats 30 --cold-repeats 20 --warmup 10 --batch35 30 --parallel 0"
        "validation=$Overall (see validation.txt)"
    )
    Set-Content -LiteralPath (Join-Path $OutputDirectory "environment.txt") -Value $Environment -Encoding utf8

    $HashLines = Get-ChildItem -LiteralPath $OutputDirectory -File |
        Where-Object { $_.Name -ne "SHA256SUMS.txt" } |
        Sort-Object Name |
        ForEach-Object {
            $Hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName).Hash.ToLowerInvariant()
            "$Hash  $($_.Name)"
        }
    Set-Content -LiteralPath (Join-Path $OutputDirectory "SHA256SUMS.txt") -Value $HashLines -Encoding ascii
}
finally {
    Pop-Location
}

Write-Host "Benchmark package created: $OutputDirectory"
Write-Host "Validation: $Overall"
