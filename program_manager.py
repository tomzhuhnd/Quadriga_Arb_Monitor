# Import generic packages
import time

# Import multi-threading libraries
from multiprocessing    import Queue
from threading          import Thread, Event

# Program packages
import front_end_manager

# Websocket packages
import ws_bfx_handler

class program_master(Thread):

    def __init__(self):

        # Class name
        self.__name = 'master'
        print(self.__name + ' thread - initializing ... ', end='')

        # Class internal variables
        self.__sleep_timer = 0.01

        # Class internal events
        self.stopped = Event()

        # Thread pointers
        self._gui_thread = None
        self._bfx_thread = None

        # Thread statuses
        self.thread_status = {}

        # Incoming Queues
        self._inbound_gui_q = Queue()

        # Outgoing Queues
        self._outbound_gui_q = Queue()

        # Data grid variables

        # Class command handlers
        self.command_handlers = {
            'stop_all': self.stop_all
        }

        # All thread command handlers
        self.thread_command_handlers = {}
        self.thread_command_handlers[self.__name] = self.command_handlers

        # Initialization complete. Instantiate thread
        super(program_master, self).__init__()
        print('done.')

    def run(self):

        # Update status in thread status
        self.thread_status['master'] = True         # Todo: add handler to push status to gui
        print(self.__name + ' thread - started! Initializing child threads ... ')

        # Start Gui Thread
        self._gui_thread = front_end_manager.gui_manager(
            self._inbound_gui_q,
            self._outbound_gui_q
        )
        self._gui_thread.start()
        self.thread_status['gui'] = True
        self.thread_command_handlers['gui'] = self._gui_thread.command_handlers

        # # Start bfx_ws Thread
        # self._bfx_thread = ws_bfx_handler.bfx_websocket()
        # self._bfx_thread.start()
        # self.thread_status['bfx_ws'] = True

        # # Wait for websocket to establish connections before sending subscription requests
        # time.sleep(1)
        # self._bfx_thread.subscribe_to_channel('trades', 'fBTC')

        # Main Loop
        while not self.stopped.is_set():

            if not self._inbound_gui_q.empty():
                src_name, tgt_name, command, payload = self._inbound_gui_q.get()
                self.run_cmd(src_name, tgt_name, command, payload)

            time.sleep(self.__sleep_timer)

        if self.stopped.is_set():

            print(self.__name + ' thread - Main Program shutting down, killing child threads.')
            self._gui_thread.stop()

            time.sleep(0.5)
            print(self.__name + ' thread - Exiting.')
            return

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


