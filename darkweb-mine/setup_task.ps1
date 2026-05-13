$taskName = "EmpireMinerAutoScan"
$scriptPath = "C:\Users\jiezishu001\darkweb-mine\main.py"

Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

$action = New-ScheduledTaskAction -Execute "python" -Argument "$scriptPath --once"
$trigger = New-ScheduledTaskTrigger -Once -At "00:00" -RepetitionInterval (New-TimeSpan -Hours 3) -RepetitionDuration (New-TimeSpan -Days 3650)
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -MultipleInstances IgnoreNew

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Description "EmpireMiner" -Force
Start-ScheduledTask -TaskName $taskName

Write-Output "Empire Miner task installed OK"
Write-Output "Check: Get-ScheduledTask -TaskName '$taskName'"
