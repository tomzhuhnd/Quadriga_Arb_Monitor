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

        # Class queues
        self.outbound_queue = outbound_queue

        # Class event flags
        self._stopped = Event()

        print('Done.')
        super(qcx_webservice, self).__init__()

    def run(self):

        print(self.__name + ' thread - Starting.')

        # Main loop
        while not self._stopped.is_set():
            print()

    def request_orderbook(self):
        pass

def request_orderbook():

    request_url = config.qcx_url + 'order_book'
    request_parameters = {'book': 'btc_cad'}
    resp = requests.get(request_url, params=request_parameters)

    if resp.status_code != 200:
        return False
    else:
        raw_resp = resp.content.decode('utf-8')

    print(raw_resp)

request_orderbook()