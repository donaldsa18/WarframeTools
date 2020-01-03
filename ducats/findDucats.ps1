[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$json = Invoke-RestMethod -Method GET -Uri "https://api.warframe.market/v1/items"

$csvPath = './ducats.csv'

If(Test-Path $csvPath) {
	Remove-Item $csvPath
}
Add-Content -Path $csvPath -Value '"Item","Ducats"'

$items = $json.payload.items
$primes = $items | where {$_.item_name.Contains("Prime ") -and $_.item_name -notmatch "Set$"}
ForEach($prime in $primes) {
	$json = Invoke-RestMethod -Method GET -Uri "https://api.warframe.market/v1/items/$($prime.url_name)"
	$ducat = ($json.payload.item.items_in_set | where {$_.url_name -match $prime.url_name}).ducats
	Add-Content -Path $csvPath -Value "$($prime.item_name),$($ducat)"
}
Import-Csv $csvPath | where {$_.Item -match "Prime"} | ForEach {$_.Item -split " "} | Select -unique | Sort-Object | Out-File primes.txt