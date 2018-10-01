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

            self.calculate_data_grid()

            time.sleep(self.loop_timer)

        return

    def calculate_data_grid(self):

        if self.parent.data_grid['coin_quantity'] == 0.0 or self.parent.data_grid['fx_rate'] == 0.0:
            self.loop_timer = 0.01
            return
        else:
            self.loop_timer = 5

        order_book = self.request_orderbook()

        coin_quantity, usd_price = self.average_cost_from_book_quantity(order_book,
                                                                        self.parent.data_grid['coin_quantity'])

        self.parent.data_grid['bfx_usd'] = usd_price
        self.parent.data_grid['bfx_cad'] = usd_price * self.parent.data_grid['fx_rate']

    def request_orderbook(self):

        target_coin = self.parent.selection_grid['target_coin'].lower()
        target_side = self.parent.settings_grid['EXCHANGE_SIDE'][self.__name]

        if target_side == 'sell':
            target_side = 'bids'
        else:
            target_side = 'asks'

        request_url = config.bfx_url + 'book/' + target_coin + 'usd'
        resp = requests.get(request_url)

        if resp.status_code != 200:
            print(resp.status_code)
            return
        else:
            raw_resp = json.loads(resp.content.decode('utf-8'))

        try:
            if target_side == 'asks':
                order_book = raw_resp['asks']
            else:
                order_book = raw_resp['bids']
            return order_book
        except:
            print(raw_resp)

    def average_cost_from_book_quantity(self, order_book, quantity):

        target_quantity = quantity

        total_coin = 0.0
        total_notional = 0.0

        for level in order_book:
            price = float(level['price'])
            coins = float(level['amount'])
            if coins + total_coin >= target_quantity:
                total_notional += (target_quantity - total_coin) * price
                total_coin = target_quantity
                break
            else:
                total_notional += price * coins
                total_coin += coins

        return total_coin, total_notional / total_coin

    def stop(self):

        print(self.__name + ' thread - Shutting down.')
        self.parent.update_thread_status(self.__name, 'Offline')
        self._stopped.set()