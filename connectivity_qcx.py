# Import general libraries
import time
import json, requests

# Import multi-threading libraries
from threading import Thread, Event

# Import configuration
import connectivity_qcx_config as config

class qcx_webservice(Thread):

    def __init__(self, parent, outbound_queue):

        self.__name = 'qcx_ws'
        print(self.__name + ' thread - Initializing ... ', end='')

        # Class variables
        self.parent = parent
        self.loop_timer = 5           # There are around 15 requests before the requests get rejected

        # Class queues
        self.outbound_queue = outbound_queue

        # Class event flags
        self._stopped = Event()

        print('Done.')
        super(qcx_webservice, self).__init__()

    def run(self):

        print(self.__name + ' thread - Started.')
        self.parent.update_thread_status(self.__name, 'Online')

        # Main loop
        while not self._stopped.is_set():

            if self.parent.selection_grid['target_coin'] == '-':
                continue

            to_coin = self.parent.selection_grid['target_coin']

            # Grab CAD book
            orderbook, pair = self.request_orderbook(to_coin, 'cad')
            self.parent.orderbook_grid[self.__name][pair] = self.standardize_orderbook(orderbook)

            # Grab USD book
            orderbook, pair = self.request_orderbook(to_coin, 'usd')
            self.parent.orderbook_grid[self.__name][pair] = self.standardize_orderbook(orderbook)

            time.sleep(self.loop_timer)

        return

    def request_orderbook(self, to_currency, from_currency):

        request_url = config.qcx_url + 'order_book'

        pair = to_currency.lower() + '_' + from_currency.lower()
        request_parameters = {'book': pair}
        resp = requests.get(request_url, params=request_parameters)

        if resp.status_code != 200:
            print(resp.status_code)
            return
        else:
            order_book = json.loads(resp.content.decode('utf-8'))

        return order_book, to_currency.lower() + from_currency.lower()

    def standardize_orderbook(self, orderbook):

        bids_book = {}
        asks_book = {}

        for level in orderbook['bids']:
            bids_book[float(level[0])] = float(level[1])
        for level in orderbook['asks']:
            asks_book[float(level[0])] = float(level[1])

        orderbook = {'asks': asks_book, 'bids': bids_book}

        return orderbook

    def stop(self):

        print(self.__name + ' thread - Shutting down.')
        self.parent.update_thread_status(self.__name, 'Offline')
        self._stopped.set()