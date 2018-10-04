# Import general libraries
import time
import json, requests

# Import multi-threading libraries
from threading import Thread, Event

# Import configuration
import connectivity_bfx_config as config

class bfx_webservice(Thread):

    def __init__(self, parent):

        self.__name = 'bfx_ws'
        print(self.__name + ' thread - Initializing ... ', end='')

        # Class variables
        self.parent = parent
        self.loop_timer = 5

        # Class events
        self._stopped = Event()

        print('Done.')
        super(bfx_webservice, self).__init__()

    def run(self):

        print(self.__name + ' thread - Started.')
        self.parent.update_thread_status(self.__name, 'Online')

        # Main loop
        while not self._stopped.is_set():

            if self.parent.selection_grid['target_coin'] == '-':
                continue

            # Grab coin/usd orderbook
            orderbook, pair = self.request_orderbook(self.parent.selection_grid['target_coin'], 'usd')
            self.parent.orderbook_grid[self.__name][pair] = self.standardize_orderbook(orderbook)

            time.sleep(self.loop_timer)

        return

    def request_orderbook(self, to_currency, from_currency):

        target_pair = to_currency.lower() + from_currency.lower()

        request_url = config.bfx_url + 'book/' + target_pair
        resp = requests.get(request_url)

        if resp.status_code != 200:
            print(resp.status_code)
            return
        else:
            orderbook = json.loads(resp.content.decode('utf-8'))

        return orderbook, target_pair

    def standardize_orderbook(self, orderbook):

        bids_book = {}
        asks_book = {}

        for level in orderbook['bids']:
            bids_book[float(level['price'])] = float(level['amount'])
        for level in orderbook['asks']:
            asks_book[float(level['price'])] = float(level['amount'])

        orderbook = {'asks': asks_book, 'bids': bids_book}

        return orderbook


    def stop(self):

        print(self.__name + ' thread - Shutting down.')
        self.parent.update_thread_status(self.__name, 'Offline')
        self._stopped.set()