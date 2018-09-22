# Import generic packages
import time

# Import multi-threading capacity
from multiprocessing import Queue
from threading import Thread, Event

# Import GUI packages
import tkinter      as tk
import tkinter.font as tkFont
import tkinter.ttk  as ttk

font_collection = {}

class gui_manager(Thread):

    def __init__(self, outbound_queue, inbound_queue):

        # Class name
        self.__name = 'gui'
        print(self.__name + ' thread - initializing ... ', end='')

        # Class variables


        # Class queues
        self.inbound_q  = inbound_queue
        self.outbound_q = outbound_queue

        # Class events
        self._stopped = Event()

        # Class command handlers
        self.command_handlers = {

        }

        print('done.')
        super(gui_manager, self).__init__()

    def run(self):

        print(self.__name + ' thread - starting.')

        # Generate tkinter master window
        self.gui_root = tk.Tk()

        # Font Dictionary
        font_collection['button1'] = tkFont.Font(family='arial', size=10, weight='bold')
        font_collection['header1'] = tkFont.Font(family='arial', size=10, weight='bold')
        font_collection['body1']   = tkFont.Font(family='arial', size=10)

        # Instantiate window classes
        self.main_window = main_window(self.gui_root, self.inbound_q, self.outbound_q)

        self.gui_root.after(0, self.run_gui)
        self.gui_root.mainloop()

    def run_gui(self):

        # Gui main loop
        if not self._stopped.is_set():
            if not self.inbound_q.empty():
                src_name, tgt_name, command, payload = self.inbound_q.get()
                if command not in self.command_handlers:
                    print(self.__name + ' thread - No handler for ' + command)
                else:
                    self.command_handlers[command](src_name, tgt_name, command, payload)

            self.gui_root.update()
            self.gui_root.after(0, self.run_gui)
        else:
            # Todo: set all tkinter varaibles to None on exit
            self.gui_root.destroy()
            self.gui_root.quit()

    def stop(self):
        # Set Stop event
        print(self.__name + ' thread - Shutting down.')
        self._stopped.set()

class main_window:

    def __init__(self, gui_root, inbound_q, outbound_q):

        # Class internal variables
        self.__name = 'gui'
        self.gui_root = gui_root
        self.gui_root.title('Program')
        self.frame = tk.Frame(self.gui_root)
        self.inbound_q = inbound_q
        self.outbound_q = outbound_q


        # Window grid objects
        self._tk_grid_obj = {
            0: {0: None},
            1: {0: None}
        }
        # Window grid variables
        self._tk_var_obj = {
            0: {0: 'Stop Main Program'},
            1: {0: 'Coin to Arb: '}
        }

        # ========================================== GRID OBJECTS ========================================== #
        # ============================================== ROW 0 ============================================= #
        self._tk_grid_obj[0][0] = tk.Button(
            self.gui_root,
            text=self._tk_var_obj[0][0],
            command=self.button_stop_main
        )
        self._tk_grid_obj[0][0].grid(row=0, column=0, padx=5, pady=5,
                                     sticky=('N', 'W', 'E', 'S'))

        # ============================================== ROW 1 ============================================= #
        self._tk_grid_obj[1][0] = tk.Message(
            self.gui_root, width=200,
            text=self._tk_var_obj[1][0], font=font_collection['header1']
        )
        self._tk_grid_obj[1][0].grid(row=1, column=0, padx=5, pady=5, sticky=('N', 'W', 'E', 'S'))


    # ========================================== Button Commands ========================================== #
    def button_stop_main(self):
        self.outbound_q.put((self.__name, 'master', 'stop_all', None))
