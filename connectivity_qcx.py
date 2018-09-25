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
        self.loop_timer = 2

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

            # print(self.parent.selection_grid['target_coin'], self.parent.selection_grid['target_notional'])

            self.request_orderbook('cad')

            time.sleep(self.loop_timer)

        return

    def request_orderbook(self, base_currency):

        # Check to see if a target_coin and target_notional has been selected
        if self.parent.selection_grid['target_coin'] == '-' or self.parent.selection_grid['target_notional'] == 0.0:
            return

        target_coin = self.parent.selection_grid['target_coin'].lower()
        target_notional = self.parent.selection_grid['target_notional']
        target_side = self.parent.settings_grid['EXCHANGE_SIDE'][self.__name]

        if target_side == 'sell':
            target_side = 'bids'
        else:
            target_side = 'asks'

        request_url = config.qcx_url + 'order_book'

        pair = target_coin + '_' + base_currency.lower()
        request_parameters = {'book': pair}
        resp = requests.get(request_url, params=request_parameters)

        if resp.status_code != 200:
            print(resp.status_code)
            return
        else:
            raw_resp = json.loads(resp.content.decode('utf-8'))

        if target_side == 'asks':
            order_book = raw_resp['asks']
        else:
            order_book = raw_resp['bids']

        print('Average Cost of Coins: ' + str(self.average_cost_from_book(target_notional, order_book)))

    def average_cost_from_book(self, target_notional, order_book):

        total_coin = 0.0
        total_notional = 0.0

        for level in order_book:
            price = float(level[0])
            coins = float(level[1])
            level_notional = price * coins
            if total_notional + level_notional >= target_notional:
                total_coin += (target_notional - total_notional) / price
                total_notional += target_notional - total_notional
                break
            else:
                total_notional += level_notional
                total_coin += coins

        return total_notional / total_coin

    def stop(self):

        print(self.__name + ' thread - Shutting down.')
        self.parent.update_thread_status(self.__name, 'Offline')
        self._stopped.set()

def request_orderbook():

    request_url = config.qcx_url + 'order_book'

    request_parameters = {'book': 'btc_cad'}
    resp = requests.get(request_url, params=request_parameters)

    side = 'bids'
    notional = 50000

    if resp.status_code != 200:
        return False
    else:
        raw_resp = json.loads(resp.content.decode('utf-8'))

    total_coin = 0
    total_notional = 0

    if side =='asks':
        order_book = raw_resp['asks']
    else:
        order_book = raw_resp['bids']

    for ask in order_book:
        price = float(ask[0])
        coins = float(ask[1])
        level_notional = price * coins
        if total_notional + level_notional >= notional:
            total_notional += notional
            total_coin += notional / price
            break
        else:
            total_notional += level_notional
            total_coin += coins
            notional -= level_notional

    for asks in raw_resp['bids']:
        print(asks)