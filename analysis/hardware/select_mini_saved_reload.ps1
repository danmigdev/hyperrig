param([Parameter(Mandatory=$true)][string]$ReportPath)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$source=@'
import sys,json
from pathlib import Path
sys.path.insert(0,'.')
from tools.mini_host_journal import read_shared_json
p=Path(sys.argv[1]).resolve()
assert p.is_relative_to(Path('build').resolve())
r=read_shared_json(p)
assert r['result']=='running' and r['phase']=='awaiting_exact_UIA_selection'
print(json.dumps({k:r[k] for k in ['browser_process_id','origin','selection_path']}))
'@
$r=($source | & C:\Python312\python.exe -B -X utf8 - $ReportPath) | ConvertFrom-Json
if($LASTEXITCODE -ne 0){throw 'Active report read failed'}
$process=Get-Process -Id $r.browser_process_id
$root=[System.Windows.Automation.AutomationElement]::FromHandle($process.MainWindowHandle)
if($root.Current.ProcessId -ne $r.browser_process_id){throw 'Wrong browser owner'}
function Exact-Matches($node,$name,$type){
 $a=New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::NameProperty,$name)
 $b=New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty,$type)
 $c=New-Object System.Windows.Automation.AndCondition($a,$b)
 return ,$node.FindAll([System.Windows.Automation.TreeScope]::Descendants,$c)
}
$deadline=[DateTime]::UtcNow.AddSeconds(12)
$row=$null
while([DateTime]::UtcNow -lt $deadline){
 $panes=Exact-Matches $root ($r.origin+' wants to connect to a serial port') ([System.Windows.Automation.ControlType]::Pane)
 if($panes.Count -gt 1){throw 'Ambiguous chooser'}
 if($panes.Count -eq 1){
  $pane=$panes.Item(0)
  $rows=Exact-Matches $pane 'Tank-M HyperRig (COM3)' ([System.Windows.Automation.ControlType]::DataItem)
  if($rows.Count -gt 1){throw 'Ambiguous MINI row'}
  if($rows.Count -eq 1){$row=$rows.Item(0);break}
 }
 Start-Sleep -Milliseconds 150
}
if($null -eq $row){throw 'Exact MINI row not found; no selection performed'}
if($row.Current.ProcessId -ne $r.browser_process_id){throw 'Wrong row owner'}
$selection=$row.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern)
$selection.Select()
if(-not $selection.Current.IsSelected){throw 'Selection did not occur'}
$buttons=Exact-Matches $pane 'Connect' ([System.Windows.Automation.ControlType]::Button)
if($buttons.Count -ne 1 -or -not $buttons.Item(0).Current.IsEnabled){throw 'Unique enabled Connect required'}
$target=[IO.Path]::GetFullPath((Join-Path (Get-Location) $r.selection_path))
if(Test-Path -LiteralPath $target){throw 'Selection record already exists'}
$buttons.Item(0).GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke()
$proof=[ordered]@{
 observed_utc=[DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ss.ffffffZ')
 browser_pid=$r.browser_process_id
 origin=$r.origin
 selected_row='Tank-M HyperRig (COM3)'
 exact_unique_row_verified=$true
 no_other_device_selected=$true
 method='Windows UIAutomation SelectionItem and Invoke'
}
[IO.File]::WriteAllText($target+'.tmp',($proof|ConvertTo-Json),[Text.UTF8Encoding]::new($false))
Move-Item -LiteralPath ($target+'.tmp') -Destination $target
$proof|ConvertTo-Json
