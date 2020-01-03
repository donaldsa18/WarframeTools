[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$apiStr = "https://api.warframe.market/v1/items"

$json = Invoke-RestMethod -Method GET -Uri $apiStr

$csvPath = './ducats.csv'
$numItemsPath = './numItems.txt'
$numItemsReturned = $json.payload.items.length.ToString()
If(Test-Path $numItemsPath) {
	$numItems = Get-Content $numItemsPath
	If($numItems -eq $numItemsReturned) {
		Write-Host "Ducats csv is up to date"
		Exit
	}
}


If(Test-Path $csvPath) {
	Remove-Item $csvPath
}
Add-Content -Path $csvPath -Value '"Item","Ducats"'

$items = $json.payload.items
$primes = $items | where {$_.item_name.Contains("Prime ") -and $_.item_name -notmatch "Set$"}
ForEach($prime in $primes) {
	$json = Invoke-RestMethod -Method GET -Uri "$($apiStr)/$($prime.url_name)"
	$ducat = ($json.payload.item.items_in_set | where {$_.url_name -match $prime.url_name}).ducats
	Add-Content -Path $csvPath -Value "$($prime.item_name),$($ducat)"
	Write-Host "$($prime.item_name)=$($ducat)"
}
Import-Csv $csvPath | where {$_.Item -match "Prime"} | ForEach {$_.Item -split " "} | Select -unique | Sort-Object | Out-File primes.txt
$numItemsReturned | Out-File -FilePath $numItemsPath