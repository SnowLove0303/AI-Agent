<#
.SYNOPSIS
    Launcher for MSDS Efficiency Workflow using standard Python 3.12+
#>
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ArgsList
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$workflowScript = Join-Path $scriptDir "scripts\run_efficiency_workflow.py"

$pyLauncher = Get-Command "py" -ErrorAction SilentlyContinue
if ($pyLauncher) {
    & py -3.12 $workflowScript @ArgsList
} else {
    & python $workflowScript @ArgsList
}
