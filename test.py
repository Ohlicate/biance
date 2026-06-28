params = {
	"quantity": '1118.2'
}

Bitcoin = {
	'Sell_sz': 0
}

Bitcoin['Sell_sz'] += float(params['quantity'])
print(Bitcoin['Sell_sz'])
