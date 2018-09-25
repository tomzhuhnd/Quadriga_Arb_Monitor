# Import general libraries
import time
import json, requests

# Import multi-threading libraries
from threading import Thread, Event

# Import configuration
import connectivity_tfx_config as config

class tfx_webservice(Thread):

    def __init__(self, parent, outbound_queue):

        self.__name = 'tfx_ws'
        print(self.__name + ' thread - Initializing ... ', end='')

        # Class variables
        self.parent = parent
        self.sub_pair = ''
        self.loop_timer = 3

        # Class queues
        self.outbound_queue = outbound_queue

        # Class event flags
        self._stopped = Event()

        print('Done.')
        super(tfx_webservice, self).__init__()

    def run(self):

        print(self.__name + ' thread - Started.')
        self.parent.update_thread_status(self.__name, 'Online')

        # Main loop
        while not self._stopped.is_set():

            if self.sub_pair is not None:
                pair_fx = self.request_fx()
                self.parent.data_grid['fx_rate'] = pair_fx

            time.sleep(self.loop_timer)

    def stop(self):

        print(self.__name + ' thread - Shutting down.')
        self.parent.update_thread_status(self.__name, 'Offline')
        self._stopped.set()

    def subscribe_fx_pair(self, pair):
        if pair in config.tfx_available_currencies:
            self.sub_pair = pair
            self.parent.data_grid['fx_pair'] = pair
        else:
            print(self.__name + ' thread - Warning! Subscription failed, pair not available.')

    def unsubscribe_fx_pair(self):
        self.sub_pair = ''
        self.parent.data_grid['fx_pair'] = ''
        self.parent.data_grid['fx_rate'] = 0.0

    def request_fx(self):

        resp = requests.get(config.tfx_url)

        if resp.status_code != 200:
            return False
        else:
            raw_resp = resp.content.decode('utf-8')

        raw_resp = raw_resp.split('\n')

        fx_quotes = {}

        for raw_quote in raw_resp:
            quote = raw_quote.split(',')
            if len(quote) > 1:
                bid = float(quote[2] + quote[3])
                ask = float(quote[4] + quote[5])
                fx_quotes[quote[0][0:3] + quote[0][4:7]] = round((bid + ask) / 2, 6)

        fx_dict = {}

        for pair in fx_quotes:
            fx_dict[pair] = fx_quotes[pair]
            fx_dict[pair[3:6] + pair[0:3]] = round(1 / fx_quotes[pair], 6)

        return fx_dict[self.sub_pair]