$region = "en"
$platform = "pc"

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$json = Invoke-RestMethod -Method GET -Uri "https://api.warframe.market/v1/items"

$items = $json.payload.items

If(Test-Path ./allprice.csv) {
	Remove-Item ./allprice.csv
}
Add-Content -Path ./allprice.csv -Value '"Item","Plat","Status"'

ForEach ($item in $items) {
	$json = Invoke-RestMethod -Method GET -Uri "https://api.warframe.market/v1/items/$($item.url_name)/orders"
	$orders = $json.payload.orders | where {$_.region -match $region -and $_.platform -match $platform}
	$selling = $orders | where {$_.user.status -match "ingame" -and $_.order_type -match "sell"}
	$status = "Online"
	
	if($selling.length -eq 0) {
		$selling = $orders | where {$_.order_type -match "sell"}
		$status = "Offline"
	}
	if($selling.length -eq 0) {
		$selling = $orders | where {$_.order_type -match "buy"}
		if($selling.length -eq 0) {
			$price = -1
			$status = "Unlisted"
		}
		else {
			$price = ($selling.platinum | Measure-Object -Maximum).Maximum
			$status = "Buying"
		}
	}
	else {
		$price = ($selling.platinum | Measure-Object -Minimum).Minimum - 1
	}
	
	$newLine = "$($item.item_name),$($price),$($status)"
	Add-Content -Path ./allprice.csv -Value $newLine
	Write-Output $newLine
}
Import-Csv ./allprice.csv | sort {[int]$_.Plat} -Descending | Export-Csv sortedallprice.csv -NoTypeInformation

