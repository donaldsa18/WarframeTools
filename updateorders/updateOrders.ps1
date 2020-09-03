$ingamename = "InsertUsernameHere"
$region = "en"
$platform = "pc"

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$json = Invoke-RestMethod -Method GET -Uri "https://api.warframe.market/v1/profile/$($ingamename)/orders"

$inventoryCsv = Import-Csv ../inventory/inventory_gen.csv

$inventory = @{}

ForEach($item in $inventoryCsv) {
	$inventory[$item.Have] = [int]$item.Quantity
}

Function FindPrice {
	param([String]$itemName)
	$json = Invoke-RestMethod -Method GET -Uri "https://api.warframe.market/v1/items/$($itemName)/orders"
	$selling = $json.payload.orders | where {$_.user.status -match "ingame" -and $_.order_type -match "sell" -and $_.region -match $region -and $_.platform -match $platform -and $_.user.ingame_name -ne $ingamename}
	
	if($selling.length -eq 0) {
		$selling = $json.payload.orders | where {$_.order_type -match "sell"}
	}
	if($selling.length -eq 0) {
		$selling = $json.payload.orders | where {$_.order_type -match "buy"}
		if($selling.length -eq 0) {
			$price = -1
		}
		else {
			$price = ($selling.platinum | Measure-Object -Maximum).Maximum
		}
	}
	else {
		$price = ($selling.platinum | Measure-Object -Minimum).Minimum - 1
	}
	return $price
}

$listed = New-Object System.Collections.Generic.List[System.Object]
$minPrice = 1000000

if($json.payload.sell_orders.length -eq 0) {
	Write-Output "All orders hidden"
}


ForEach($order in $json.payload.sell_orders) {
	#Compare with inventory quantity
	$item = $order.item.en.item_name
	if($inventory.ContainsKey($item)) {
		$quantity = $inventory[$item]
		if($quantity -ne $order.quantity) {
			Write-Output "Quantity mismatch: $($item) has $($quantity) in inventory but $($order.quantity) on warframe.market"
		}
	}
	else {
	
		Write-Output "Quantity mismatch: $($item) not in inventory but $($order.quantity) are listed on warframe.market"
	}
	
	#Check prices again
	$price = FindPrice($order.item.url_name)
	if($order.platinum -ne $price) {
		if($order.platinum -lt $price*0.95) {
			Write-Output "Price too low: $($item) is listed for $($order.platinum)p but the next price is $($price+1)p"
		}
		if($order.platinum -gt $price) {
			Write-Output "Price too high: $($item) is listed for $($order.platinum)p but the cheapest one is $($price+1)p"
		}
	}
	
	$listed.Add($item)
	if($minPrice -gt $order.platinum) {
		$minPrice = $order.platinum
	}
}
$prices = @{}

$allprice = Import-Csv ../warframemarket/allprice.csv
ForEach($row in $allprice) {
	$prices[$row.Item] = [int]$row.Plat
}

ForEach($item in $inventoryCsv.Have) {
	if(-not $listed.Contains($item)) {
		if($prices[$item] -gt $minPrice) {
			$url_name = $item.ToLower().Replace('&','and').Replace(' ','_')
			$price = FindPrice($url_name)
			if($price -gt $minPrice) {
				Write-Output "Unlisted: $($item)x$($inventory[$item]) is not listed for $($price) but the cheapest item sold is $($minPrice)"
			}
			
		}
	}
}