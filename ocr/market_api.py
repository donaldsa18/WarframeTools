import requests


class MarketReader:
    def __init__(self, gui=None, ocr=None):
        self.api_str = "https://api.warframe.market/v1/items"
        self.region = "en"
        self.platform = "pc"
        self.gui = gui
        self.ocr = ocr
        self.prime_items = None
        self.exit_now = False

    def get_prime_items(self):
        if self.prime_items is None:
            response = requests.get(self.api_str)
            json_response = response.json()
            items = json_response['payload']['items']
            self.prime_items = [x for x in items if "Prime " in x['item_name'] and not x['item_name'].endswith("Set")]
            if self.gui is None:
                print("Found {} primes".format(len(self.prime_items)))
            else:
                self.gui.update_primes_info(len(self.prime_items), self.prime_items[-1]['item_name'])
            if self.exit_now:
                return

    def update_ducats(self):
        self.get_prime_items()
        i = 0
        ducats = {}
        for prime in self.prime_items:
            response = requests.get("{}/{}".format(self.api_str,prime['url_name']))
            json_response = response.json()
            item = [x for x in json_response['payload']['item']['items_in_set'] if x['url_name'] == prime['url_name']][0]
            ducat = 0
            if 'ducat' in item:
                ducat = item['ducats']
            ducats[prime['item_name']] = ducat
            i = i + 1
            if self.gui is None:
                print("{}/{}: {},{}".format(i, len(self.prime_items), prime['item_name'], ducat))
            elif i % int(len(self.prime_items) / 100) == 0:
                self.set_ducats_progress(i)
            if self.exit_now:
                return

        if self.ocr is not None:
            self.ocr.ducats = ducats
            self.ocr.ducats["Forma Blueprint"] = 0
        if self.gui is not None:
            self.gui.finished_update_progress()
            self.gui.update_ducats_time()

    def set_prices_progress(self, val):
        self.gui.update_prices_progress.setValue(val)

    def set_ducats_progress(self, val):
        self.gui.update_ducats_progress.setValue(val)

    def update_prices(self):
        self.get_prime_items()
        primes = []
        #print(str(self.prime_items[0]))
        i = 0
        headers = {'Platform': self.platform, 'Region': self.region}
        for prime_item in self.prime_items:
            response = requests.get("{}/{}/orders".format(self.api_str, prime_item['url_name']), headers=headers)
            json_response = response.json()

            orders = json_response['payload']['orders']
            #orders = [x for x in all_orders if x['region'] == self.region and x['platform'] == self.platform]
            #print(str(orders[0]))
            selling = [x for x in orders if x["user"]["status"] == "ingame" and x["order_type"] == "sell"]
            status = "Online"
            price = 0
            if len(selling) == 0:
                selling = [x for x in orders if x["order_type"] == "sell"]
                status = "Offline"
            if len(selling) == 0:
                selling = [x for x in orders if x["order_type"] == "buy"]
                if len(selling) == 0:
                    status = "Unlisted"
                else:
                    price = max([x["platinum"] for x in selling])
                    status = "Buying"
            else:
                price = min([x["platinum"] for x in selling])-1
            price = int(price)
            primes.append((prime_item['item_name'], price, status))
            i = i + 1
            if self.gui is None:
                print("{}/{}: {},{},{}".format(i, len(self.prime_items), prime_item['item_name'], price, status))
            elif i % int(len(self.prime_items)/100) == 0:
                self.set_prices_progress(i)
            if self.exit_now:
                return

        if self.ocr is not None:
            self.ocr.prices = {prime[0]: self.safe_cast(prime[1], int, 0) for prime in primes}
            self.ocr.prices["Forma Blueprint"] = 0
        if self.gui is not None:
            self.gui.finished_update_progress()
            self.gui.update_prices_time()

    def safe_cast(self, val, to_type, default=None):
        try:
            return to_type(val)
        except (ValueError, TypeError):
            return default


if __name__ == "__main__":
    reader = MarketReader()
    reader.update_ducats()
