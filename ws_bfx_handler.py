# Import default libraries
import time, datetime
import json, requests
import hmac, hashlib

# Import connectivity libraries
import websocket

# Import multi-threading libraries
from multiprocessing import Queue
from threading import Thread, Event, Timer

import ws_bfx_settings

# URLs
url_bfx = 'wss://api.bitfinex.com/ws/2'

# BFX Websocket class
class bfx_websocket(Thread):

    def __init__(self):

        # Class name
        self.__name = 'bfx_ws'
        print(self.__name + ' thread - initializing ... ', end='')

        # Internal status variables
        self._isActive = False

        # Internal class events
        self._connected = Event()
        self._disconnected = Event()
        self._pause = Event()

        # Channel mappings
        self._channel_ids = {}

        # Event handlers
        self._event_handlers = {
            'info': self.__handle_event_info,
            'auth': self.__handle_event_auth,
            'subscribed': self.__handle_event_subscribed
        }

        # Data handlers
        self._data_handlers = {
            'account': self.__process_data_account,
            'ticker':  self.__process_data_ticker,
            'trades':  self.__process_data_trades
        }

        # Data handlers
        self._data_account_handlers = {
            'ps':  self.__handle_data_account_ps,
            'ws':  self.__handle_data_account_ws,
            'os':  self.__handle_data_account_os,
            'fcs': self.__handle_data_account_fcs,
            'fls': self.__handle_data_account_fls,
            'fos': self.__handle_data_account_fos
        }

        # Data queues
        self.data_queue = Queue()

        # Data Grids
        self.account_orders = {}
        self.account_funding_positions = {}

        # Websocket specific variables
        self.ws_version = None
        self.ws_userid  = None

        # Establish as new independent thread
        Thread.__init__(self)
        self.daemon = True
        print('done.')

    def run(self):
        print(self.__name + ' thread - starting.')
        self._connect()

    def stop(self):

        # Disconnect event
        self._disconnected.set()
        try:
            # Check ws connection, close if its open
            if self.ws:
                self.ws.close()
            self._isActive = False
            # Give thread a second to process close operation
            self.join(timeout=1)
            return True
        except Exception as e:
            print(self.__name + ' thread - Error on stop! Error code: ' + str(e))
            return False

    # ===================================== Main Loop for websocket connection ===================================== #

    def _connect(self):
        # Start the websocket object
        websocket.enableTrace(False)
        self.ws = websocket.WebSocketApp(
            url_bfx,
            on_open=self._bfx_auth_open,
            on_close=self._on_close,
            on_error=self._on_error,
            on_message=self._on_message
        )
        # Run loop
        self.ws.run_forever()
        # self.ws.run_forever(ping_interval=60, ping_timeout=65)

        while not self._disconnected.is_set():
            print('test')
            self.ws.keep_running = True
            self.ws.run_forever()

        # ===================================== Connection functions ===================================== #

    def _bfx_auth_open(self, ws):

        # Create encoded payload for authentication
        nonce = str(int(time.time() * 1000000))
        auth_payload = 'AUTH' + nonce
        signature = hmac.new(self.__skey, auth_payload.encode(), hashlib.sha384).hexdigest()
        payload = {
            'apiKey': self.__key,
            'event': 'auth',
            'authPayload': auth_payload,
            'authNonce': nonce,
            'authSig': signature
        }

        # Send payload to establish authenticated connection to account
        print(self.__name + ' thread - Establishing authenticated connection to account.')
        try:
            self.ws.send(json.dumps(payload))
            self._connected.set()
        except websocket.WebSocketConnectionClosedException:
            print(self.__name + ' thread - Exception! Payload failed to send, websocket connection is closed!')
        except Exception as e:
            print(self.__name + ' thread - Exception! Exception type: ' + str(e))

    def _on_close(self, ws):
        self._connected.clear()
        self._disconnected.set()
        self.ws.close()
        print(self.__name + ' thread - Websocket connection has been closed.')

    def _on_error(self, ws, error):
        print(error)
        # Todo: Create an actual error handlers

    def _on_message(self, ws, message):

        # Decode incoming json message
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            print(self.__name + ' thread - Exception! Bad JSON Message received! Msg: ' + str(message))
            return
        except Exception as e:
            print(message)
            print(self.__name + ' thread - Exception! Exception type: ' + str(e))
            return

        if isinstance(data, dict):                                  # Message is a dictionary | Event type

            if self.store_raw:
                self.data_raw_log.info(self.__name + ' thread - Raw event: ' + str(data))

            if data['event'] in self._event_handlers:
                self._event_handlers[data['event']](data)
            else:
                print(self.__name + ' thread - Missing event handler for: "' + data['event'] + '". ', end='')
                print('Event Contents: ' + str(data))
                return
        else:                                                       # Message is a list       | Data type

            if data[1] == 'hb':                                     # Handle heart beats differently
                self.__handle_data_heartbeat(data)
            else:

                if self.store_raw:
                    self.data_raw_log.info(self.__name + ' thread - Raw data : ' + str(data))

                # Grab channel_name for data_handler identification
                try:
                    channel_pair = self._channel_ids[data[0]]
                except:
                    print(self.__name + ' thread - Warning[Exception]! Unmapped channel for: ' + str(data[0]) + '.')
                    print(data)
                    return
                # Pass data to data handler for processing
                try:
                    self._data_handlers[channel_pair[0]](data, channel_pair)
                except:
                    print(self.__name + ' thread - Warning[Exception]! Missing data handler for channel pair: "' +
                          str(channel_pair) + '".')
                    print(data)
                    return

    # ===================================== External Facing Functions ===================================== #

    def subscribe_to_channel(self, channel, pair):

        channel = channel.lower()

        # Check if channel is a proper channel subscription
        if channel in ws_bfx_settings.bfx_public_channels:
            if pair in ws_bfx_settings.bfx_trading_pairs:

                # Generate subscription payload
                if channel != 'book':
                    payload = {'event': 'subscribe', 'channel': channel, 'pair': pair}
                else:
                    payload = {'event': 'subscribe', 'channel': channel, 'pair': pair,
                               'prec': ws_bfx_settings.bfx_book_pair_precision[pair],
                               'length': ws_bfx_settings.bfx_book_pair_length[pair]
                               }

                output_string = self.__name + ' thread - Sending subscription request for CHANNEL: "' + channel
                output_string += '" | PAIR: "' + pair + '".'
                print(output_string)
                # Send subscribe payload through websocket
                try:
                    self.ws.send(json.dumps(payload))
                    self._connected.set()
                except websocket.WebSocketConnectionClosedException:
                    print(self.__name + ' thread - Exception! Payload failed to send, websocket connection is closed!')
                except Exception as e:
                    print(self.__name + ' thread - Exception! Exception type: ' + str(e))

            else:
                print(self.__name + ' thread - Warning! Received subscription request to unsupported pair.', end='')
                print(' Unsupported Pair: ' + pair)
        else:
            print(self.__name + ' thread - Warning! Received subscription request to unsupported channel.', end='')
            print(' Unsupported Channel: ' + channel)


    # ===================================== Event handlers ===================================== #

    def __handle_event_info(self, data):

        if 'version' in data:
            self.ws_version = data['version']
        if 'platform' in data:
            if 'status' in data['platform']:
                if data['platform']['status'] == 1:
                    print(self.__name + ' thread - BFX Websocket platform is currently active!')
                    # Todo: have an actual handler for when the platform goes down
                else:
                    print(self.__name + ' thread - BFX Webscoket platform is currently offline!')
                    # Todo: have an actual handler for when the platform goes down

    def __handle_event_auth(self, data):

        if 'status' in data and data['status'] == 'OK':             # Authenticated channel subscription successful
            self._channel_ids[('account', data['chanId'])] = data['chanId']
            self._channel_ids[data['chanId']] = ('account', data['chanId'])
            print(self.__name + ' thread - Authenticated account channel created. ChanId: ' + str(data['chanId']))
        else:
            print(self.__name + ' thread - BFX Websocket failed to establish authenticated channel subscription!')
            # Todo: Add handlers that will try to re-authenticate when the initial auth. fails

    def __handle_event_subscribed(self, data):

        self._channel_ids[data['chanId']] = (data['channel'], data['symbol'])
        self._channel_ids[(data['channel'], data['symbol'])] = data['chanId']
        print(self.__name + ' thread - Successful subscription to CHANNEL: "' + str(data['channel'])
              + '" | PAIR: "' + data['symbol'] + '" | ChanID: ' + str(data['chanId']) + '.')

    # ===================================== General Data Handlers ===================================== #

    def __handle_data_heartbeat(self, data):

        # TODO: Add proper heartbeat, ping/pong handler. Need a seperate thread for message monitoring
        if False:
            print(self.__name + ' thread - Heartbeat {currently ignored}.')

    # ===================================== Ticker Data handlers ===================================== #

    def __process_data_ticker(self, data, pair):

        print('Ticker data received')
        print(data)

    # ===================================== Trades Data handlers ===================================== #

    def __process_data_trades(self, data, pair):

        if pair[1][0] == 'f':

            print('Received funding data')

        elif pair[1][0] == 't':
            print('Received trading data')
        else:
            print(self.__name + ' thread - Warning! Unrecognized pair type: "' + str(pair) + '".')