import requests
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
from threading import Lock

class MarketReader:
    def __init__(self, gui=None, ocr=None):
        self.api_str = "https://api.warframe.market/v1/items"
        self.region = "en"
        self.platform = "pc"
        self.gui = gui
        self.ocr = ocr
        self.prime_items = None
        self.exit_now = False
        self.ducats = {}
        self.headers = {'Platform': self.platform, 'Region': self.region}
        self.primes = []
        self.threads = 4

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

    def update_ducats_sub(self, url_name, item_name):
        if self.exit_now:
            return
        response = requests.get("{}/{}".format(self.api_str, url_name))
        if self.exit_now:
            return
        json_response = response.json()
        item = [x for x in json_response['payload']['item']['items_in_set'] if x['url_name'] == url_name][0]
        ducat = 0
        if 'ducat' in item:
            ducat = item['ducats']
        self.ducats[item_name] = ducat
        if self.gui is None:
            print("{}/{}: {},{}".format(len(self.ducats), len(self.prime_items), item_name, ducat))
        elif len(self.ducats) % int(len(self.prime_items) / 100) == 0:
            self.set_ducats_progress()

    def update_ducats(self):
        self.get_prime_items()
        self.ducats = {}
        with ThreadPoolExecutor(max_workers=self.threads) as ex:
            for prime in self.prime_items:
                ex.submit(self.update_ducats_sub, prime['url_name'], prime['item_name'])
            ex.shutdown(wait=True)

        if self.ocr is not None:
            self.ocr.ducats = self.ducats
            self.ocr.ducats["Forma Blueprint"] = 0
        if self.gui is not None:
            self.gui.finished_update_progress()
            self.gui.update_ducats_time()

    def set_prices_progress(self):
        self.gui.update_prices_progress.setValue(len(self.primes))

    def set_ducats_progress(self):
        self.gui.update_ducats_progress.setValue(len(self.ducats))

    def update_prices_sub(self, url_name, item_name):
        if self.exit_now:
            return
        response = requests.get("{}/{}/orders".format(self.api_str, url_name), headers=self.headers)
        if self.exit_now:
            return
        json_response = response.json()

        orders = json_response['payload']['orders']
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
            price = min([x["platinum"] for x in selling]) - 1
        price = int(price)
        self.primes.append((item_name, price, status))
        if self.gui is None:
            print("{}/{}: {},{},{}".format(len(self.primes), len(self.prime_items), item_name, price, status))
        elif len(self.primes) % int(len(self.prime_items) / 100) == 0:
            self.set_prices_progress()

    def update_prices(self):
        self.get_prime_items()
        self.primes = []
        with ThreadPoolExecutor(max_workers=self.threads) as ex:
            for prime in self.prime_items:
                ex.submit(self.update_prices_sub, prime['url_name'], prime['item_name'])
            ex.shutdown(wait=True)

        if self.ocr is not None:
            self.ocr.prices = {prime[0]: self.safe_cast(prime[1], int, 0) for prime in self.primes}
            self.ocr.prices["Forma Blueprint"] = 0
        if self.gui is not None:
            self.gui.finished_update_progress()
            self.gui.update_prices_time()

    def set_num_threads(self,val):
        self.threads = val

    def safe_cast(self, val, to_type, default=None):
        try:
            return to_type(val)
        except (ValueError, TypeError):
            return default


if __name__ == "__main__":
    reader = MarketReader()
    reader.update_ducats()
