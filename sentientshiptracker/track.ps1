
$dict = @{}
$dict.Add('505','Ruse War Field')
$dict.Add('510','Gian Point')
$dict.Add('550','Nsu Grid')
$dict.Add('551',"Ganalen's Grave")
$dict.Add('552','Rya')
$dict.Add('553','Flexa')
$dict.Add('554','H-2 Cloud')
$dict.Add('555','R-9 Cloud')

Add-Type -AssemblyName System.Windows.Forms 



While($true) {
	$json = Invoke-RestMethod -Method GET -Uri "http://content.warframe.com/dynamic/worldState.php"
	$date = Get-Date
	If($tmp -ne $json.Tmp) {
		$tmp = $json.Tmp
		$line = ""
		
		If($tmp.Length -eq 11) {
			$node = $tmp.Substring(7,3)
			If($dict.ContainsKey($node)) {
				$readableNode = $dict[$node]
				$line = "Sentient Ship appeared on $($readableNode)"
			}
		}
		If($tmp.Length -eq 2) {
			$line = "Sentient Ship disappeared"
		}
		$output = "$($date) $($line)"
		Write-Output "$($output)" | Out-File ./log.txt -append
		Write-Output "$($output)"
		$global:balloon = New-Object System.Windows.Forms.NotifyIcon
		$path = (Get-Process -id $pid).Path
		$balloon.Icon = [System.Drawing.Icon]::ExtractAssociatedIcon($path) 
		$balloon.BalloonTipIcon = [System.Windows.Forms.ToolTipIcon]::Warning 
		$balloon.BalloonTipText = $line
		$balloon.BalloonTipTitle = "Warframe Ship Tracker" 
		$balloon.Visible = $true
		$balloon.ShowBalloonTip(5000)
	}
	Start-Sleep 30
}
