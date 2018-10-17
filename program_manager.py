# Import generic packages
import time

# Import multi-threading libraries
from multiprocessing    import Queue
from threading          import Thread, Event

# Program packages
import front_end_manager
import connectivity_tfx, connectivity_qcx, connectivity_bfx
import strategy_manager

# Session settings

class program_master(Thread):

    def __init__(self):

        # Class name
        self.__name = 'master'
        print(self.__name + ' thread - Initializing ... ', end='')

        # Class internal variables
        self.__sleep_timer = 0.5

        # Class internal events
        self.stopped = Event()

        # Thread pointers
        self._gui_thread = None
        self._bfx_thread = None
        self._qcx_thread = None

        # Incoming Queues
        self._inbound_gui_q = Queue()
        self._inbound_tfx_q = Queue()
        self._inbound_qcx_q = Queue()

        # Outgoing Queues
        self._outbound_gui_q = Queue()

        # Data grid variables
        self.settings_grid = {}
        self.settings_grid['TARGET_ARB_COINS'] = ['BTC', 'ETH', 'BCH', 'LTC', '-']
        self.settings_grid['MULTI_FIAT'] = {
            'qcx_ws': ['BTC']
        }
        self.settings_grid['FEES'] = {
            'qcx_ws': {
                'coin_make': 0.002, 'coin_take': 0.002, 'coin_draw': 0, 'coin_fund': 0,
                'fiat_make': 0.005, 'fiat_take': 0.005, 'fiat_draw': 0, 'fiat_fund': 0
                },
            'bfx_ws': {
                'coin_make': 0.002, 'coin_take': 0.002, 'coin_draw': 0, 'coin_fund': 0,
                'fiat_make': 0.002, 'fiat_take': 0.002, 'fiat_draw': 0, 'fiat_fund': 0
            }
        }

        self.status_grid = {'master': 'Inactive', 'tfx_ws': 'Offline', 'qcx_ws': 'Offline', 'bfx_ws': 'Offline'}
        self.selection_grid = {'target_coin': '-', 'target_notional': 0.0, 'target_coin_multi_fiat': None}
        self.orderbook_grid = {'bfx_ws': {}, 'qcx_ws': {}}
        # Values that the strategy manager manipulates
        self.balance_fiat_grid = {
            'starting_cad': ('CAD', 0.0), 'starting_usd': ('USD', 0.0), 'ending_cad': ('CAD', 0.0),
            'bfx_fiat_amount': ('USD', 0.0), 'qcx_fiat_amount': ('CAD', 0.0)
        }
        self.balance_coin_grid = {
            'bfx_coin_amount': (None, 0.0),'qcx_coin_amount': (None, 0.0)
        }
        self.fees_grid = {
            'bfx_ws': {'trading': 0.0, 'deposit': 0.0, 'withdraw': 0.0},
            'qcx_ws': {'trading': 0.0, 'deposit': 0.0, 'withdraw': 0.0}
        }
        # Values that the GUI consumes
        self.data_grid = {
            'fx_pair': '', 'fx_rate': 0.0, 'qcx_cad': 0.0, 'qcx_usd': 0.0, 'qcx_usd_to_cad': 0.0,
            'qcx_implied_fx_rate': 0.0, 'qcx_internal_fx_coin_spread': 0.0, 'qcx_internal_fx_spread': 0,
            'coin_quantity': 0.0, 'bfx_usd': 0.0, 'bfx_cad': 0.0, 'arb_spread': 0.0, 'arb_return': 0.0
        }

        # Class command handlers
        self.command_handlers = {
            'stop_all': self.stop_all
        }

        # All thread command handlers
        self.thread_command_handlers = {}
        self.thread_command_handlers[self.__name] = self.command_handlers

        # Initialization complete. Instantiate thread
        super(program_master, self).__init__()
        print('Done.')

    def run(self):

        # Update status in thread status
        print(self.__name + ' thread - Started! Initializing child threads.')

        # Start Gui Thread
        self._gui_thread = front_end_manager.gui_manager(self, self._inbound_gui_q, self._outbound_gui_q
        )
        self._gui_thread.start()
        self.thread_command_handlers['gui'] = self._gui_thread.command_handlers

        # Wait for the gui thread to properly initialize
        time.sleep(1)
        self.update_thread_status(self.__name, 'Active')

        # Start True FX Thread
        self._tfx_thread = connectivity_tfx.tfx_webservice(self, self._inbound_tfx_q)
        self._tfx_thread.subscribe_fx_pair('USDCAD')
        self._tfx_thread.start()

        # Start QuadrigaCX Thread
        self._qcx_thread = connectivity_qcx.qcx_webservice(self, self._inbound_qcx_q)
        self._qcx_thread.start()

        # Start BitFinex Thread
        self._bfx_thread = connectivity_bfx.bfx_webservice(self)
        self._bfx_thread.start()

        # Initialize strategy_class
        self._strategy_core = strategy_manager.strategy_core(self)

        # Wait for all the threads to properly load with data
        time.sleep(2)

        # Main Loop
        while not self.stopped.is_set():

            if not self._inbound_gui_q.empty():
                src_name, tgt_name, command, payload = self._inbound_gui_q.get()
                self.run_cmd(src_name, tgt_name, command, payload)

            # Compute all calculations
            self.reset_strategy_grids()
            self._strategy_core.run_strategy()

            time.sleep(self.__sleep_timer)

        if self.stopped.is_set():

            print(self.__name + ' thread - Main Program shutting down, killing child threads.')
            self._tfx_thread.stop()
            self._qcx_thread.stop()
            self._bfx_thread.stop()
            self._gui_thread.stop()
            time.sleep(0.5)
            print(self.__name + ' thread - Exiting.')
            return

    def update_thread_status(self, thread_name, status):

        self.status_grid[thread_name] = status
        self._gui_thread.update_status_grid()

    def update_thread_selection(self, selection_name, selection):
        if self.selection_grid[selection_name] == selection:
            print('"' + selection + '" for "' + selection_name + '" has already been selected!')
        else:
            # TODO: Reset all the data grids that are sensitive to selection criteria

            self.selection_grid[selection_name] = selection
            if selection_name == 'target_coin':
                if selection in self.settings_grid['MULTI_FIAT']['qcx_ws']:
                    self.selection_grid['target_coin_multi_fiat'] = True
                else:
                    self.selection_grid['target_coin_multi_fiat'] = False

    def reset_strategy_grids(self):

        for element in self.balance_fiat_grid:
            self.balance_fiat_grid[element] = (self.balance_fiat_grid[element][0], 0.0)
        for element in self.balance_fiat_grid:
            self.balance_coin_grid[element] = (None, 0.0)
        for element in self.fees_grid:
            self.fees_grid[element] = {'trading': 0.0, 'deposit': 0.0, 'withdraw': 0.0}



    def run_cmd(self, src_name, tgt_name, cmd_name, payload):
        if not tgt_name in self.thread_command_handlers:
            print(self.__name + ' thread - No thread exists for: ' + tgt_name + ' to run command: ' + cmd_name + '.')
        elif not cmd_name in self.thread_command_handlers[tgt_name]:
            print(self.__name + ' thread - No command exists for ' + cmd_name + ' for thread ' + tgt_name + '.')
        else:
            self.thread_command_handlers[tgt_name][cmd_name](src_name, tgt_name, cmd_name, payload)

    def stop_all(self, src_name, tgt_name, cmd_name, payload):
        print(src_name + ' thread - Triggered main program stop command.')
        self.stopped.set()


