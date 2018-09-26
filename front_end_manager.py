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

    def __init__(self, master_thread, outbound_queue, inbound_queue):

        # Class name
        self.__name = 'gui'
        print(self.__name + ' thread - Initializing ... ', end='')

        # Master thread
        self.master_thread = master_thread

        # Class variables
        self.settings_grid = self.master_thread.settings_grid
        self.status_grid = self.master_thread.status_grid
        self.selection_grid = self.master_thread.selection_grid
        self.data_grid = self.master_thread.data_grid
        self.loop_timer = 0.5

        # Class queues
        self.inbound_q  = inbound_queue
        self.outbound_q = outbound_queue

        # Class events
        self._stopped = Event()

        # Class command handlers
        self.command_handlers = {

        }

        print('Done.')
        super(gui_manager, self).__init__()

    def run(self):

        print(self.__name + ' thread - Started.')

        # Generate tkinter master window
        self.gui_root = tk.Tk()

        # Font Dictionary
        font_collection['button1'] = tkFont.Font(family='arial', size=10, weight='bold')
        font_collection['header1'] = tkFont.Font(family='arial', size=10, weight='bold')
        font_collection['body1']   = tkFont.Font(family='arial', size=10)

        # Instantiate window classes
        self.main_window = main_window(self.gui_root, self.inbound_q, self.outbound_q, self)

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
            self.main_window.update_data_grid()
            time.sleep(self.loop_timer)

            self.gui_root.after(0, self.run_gui)
        else:
            # Todo: set all tkinter varaibles to None on exit
            self.gui_root.destroy()
            self.gui_root.quit()

    def stop(self):
        # Set Stop event
        print(self.__name + ' thread - Shutting down.')
        self._stopped.set()

    def update_status_grid(self):
        self.main_window.update_status_grid()


class main_window:

    def __init__(self, gui_root, inbound_q, outbound_q, parent):

        # Class internal variables
        self.__name = 'gui'
        self.gui_root = gui_root
        self.parent = parent
        self.gui_root.title('Program')
        self.frame = tk.Frame(self.gui_root)
        self.inbound_q = inbound_q
        self.outbound_q = outbound_q

        # Status grid mappings to GUI dynamic variables
        self.status_map = {
            'master': (2, 0), 'tfx_ws': (2, 1), 'qcx_ws': (2, 2)
        }

        # Data grid mappings to GUI dynamic variables
        self.data_map = {
            'fx_pair': (3, 3), 'fx_rate': (3, 5)
        }

        # Window grid objects
        self._tk_grid_obj = {
            0: {0: None},
            1: {0: None, 1: None, 2: None},
            2: {0: None, 1: None, 2: None},
            3: {0: None, 1: None, 2: None, 3: None, 4: None, 5: None},
            4: {0: None, 1: None, 2: None,          4: None, 5: None},
            5: {0: None, 1: None, 2: None,          4: None},
            6: {0: None, 1: None, 2: None,          4: None},
            7: {0: None}                                                        # Spacing
        }
        # Window grid variables
        self._tk_var_obj = {
            0: {0: 'Stop Main Program'},
            1: {0: 'Master Thread', 1: 'TrueFX Thread', 2: 'Quadriga Thread'},
            2: {0: tk.StringVar(),  1: tk.StringVar(),  2: tk.StringVar()},
            3: {0: 'Coin to Arb:', 1: tk.StringVar(), 2: 'FX Pair:', 3: tk.StringVar(),
                4: 'FX Rate:', 5: tk.DoubleVar()},
            4: {0: 'Notional Target (CAD):', 1: tk.DoubleVar(), 2: 'Set Notional Target',
                4: 'Target (CAD):', 5: tk.StringVar()},
            5: {0: 'Quadriga CAD Price', 1: 'Quadriga USD Price', 2: 'BitFinex CAD Price', 4: 'BitFinex USD Price'},
            6: {0: tk.DoubleVar(), 1: tk.DoubleVar(), 2: tk.DoubleVar(), 4: tk.DoubleVar()},
            7: {0: 'Estimated Spread:'}
        }

        # Window width settings
        self._column_width = {0: 250, 1: 250, 2: 150, 3: 150, 4: 150, 5: 150}

        # ========================================== GRID OBJECTS ========================================== #
        # ============================================== ROW 0 ============================================= #
        self._tk_grid_obj[0][0] = tk.Button(
            self.gui_root,
            text=self._tk_var_obj[0][0], font=font_collection['header1'], background='light grey',
            command=self.__button_stop_main
        )
        self._tk_grid_obj[0][0].grid(row=0, column=0, padx=5, pady=5, sticky=('N', 'W', 'E', 'S'), columnspan=2)

        # ============================================== ROW 1 ============================================= #

        self._tk_grid_obj[1][0] = tk.Message(
            self.gui_root, width=self._column_width[0],
            text=self._tk_var_obj[1][0], font=font_collection['header1'], relief='ridge'
        )
        self._tk_grid_obj[1][0].grid(row=1, column=0, padx=5, sticky=('N', 'W', 'E', 'S'), columnspan=1)

        self._tk_grid_obj[1][1] = tk.Message(
            self.gui_root, width=self._column_width[1],
            text=self._tk_var_obj[1][1], font=font_collection['header1'], relief='ridge'
        )
        self._tk_grid_obj[1][1].grid(row=1, column=1, padx=5, sticky=('N', 'W', 'E', 'S'), columnspan=1)

        self._tk_grid_obj[1][2] = tk.Message(
            self.gui_root, width=self._column_width[2],
            text=self._tk_var_obj[1][2], font=font_collection['header1'], relief='ridge'
        )
        self._tk_grid_obj[1][2].grid(row=1, column=2, padx=5, sticky=('N', 'W', 'E', 'S'), columnspan=2)

        # ============================================== ROW 2 ============================================= #

        self._tk_grid_obj[2][0] = tk.Message(
            self.gui_root, width=self._column_width[0],
            textvariable=self._tk_var_obj[2][0], font=font_collection['header1'], relief='ridge'
        )
        self._tk_grid_obj[2][0].grid(row=2, column=0, padx=5, sticky=('N', 'W', 'E', 'S'), columnspan=1)

        self._tk_grid_obj[2][1] = tk.Message(
            self.gui_root, width=self._column_width[1],
            textvariable=self._tk_var_obj[2][1], font=font_collection['header1'], relief='ridge'
        )
        self._tk_grid_obj[2][1].grid(row=2, column=1, padx=5, sticky=('N', 'W', 'E', 'S'), columnspan=1)

        self._tk_grid_obj[2][2] = tk.Message(
            self.gui_root, width=self._column_width[2],
            textvariable=self._tk_var_obj[2][2], font=font_collection['header1'], relief='ridge'
        )
        self._tk_grid_obj[2][2].grid(row=2, column=2, padx=5, sticky=('N', 'W', 'E', 'S'), columnspan=2)

        # ============================================== ROW 3 ============================================= #
        self._tk_grid_obj[3][0] = tk.Message(
            self.gui_root, width=self._column_width[0],
            text=self._tk_var_obj[3][0], font=font_collection['header1']
        )
        self._tk_grid_obj[3][0].grid(row=3, column=0, padx=5, pady=5, sticky=('N', 'W', 'E', 'S'),columnspan=1)

        self._tk_var_obj[3][1].set(self.parent.selection_grid['target_coin'])
        self._tk_var_obj[3][1].trace('w', self.__trace_option_menu_change_r3_c1)
        self._tk_grid_obj[3][1] = tk.OptionMenu(
            self.gui_root, self._tk_var_obj[3][1], *self.parent.settings_grid['TARGET_ARB_COINS']
        )
        self._tk_grid_obj[3][1].config(font=font_collection['body1'], width=10)
        self._tk_grid_obj[3][1].grid(row=3, column=1, padx=5, pady=5, sticky=('N', 'W', 'E', 'S'), columnspan=1)

        self._tk_grid_obj[3][2] = tk.Message(
            self.gui_root, width=self._column_width[2],
            text=self._tk_var_obj[3][2], font=font_collection['header1']
        )
        self._tk_grid_obj[3][2].grid(row=3, column=2, padx=5, pady=5, sticky=('N', 'W', 'E', 'S'), columnspan=1)

        self._tk_var_obj[3][3].set('')
        self._tk_grid_obj[3][3] = tk.Message(
            self.gui_root, width=self._column_width[3],
            textvariable=self._tk_var_obj[3][3], font=font_collection['body1']
        )
        self._tk_grid_obj[3][3].grid(row=3, column=3, padx=5, pady=5, sticky=('N', 'W', 'E', 'S'), columnspan=1)

        self._tk_grid_obj[3][4] = tk.Message(
            self.gui_root, width=self._column_width[4],
            text=self._tk_var_obj[3][4], font=font_collection['header1']
        )
        self._tk_grid_obj[3][4].grid(row=3, column=4, padx=5, pady=5, sticky=('N', 'W', 'E', 'S'), columnspan=1)

        self._tk_var_obj[3][5].set('')
        self._tk_grid_obj[3][5] = tk.Message(
            self.gui_root, width=self._column_width[5],
            textvariable=self._tk_var_obj[3][5], font=font_collection['body1']
        )
        self._tk_grid_obj[3][5].grid(row=3, column=5, padx=5, pady=5, sticky=('N', 'W', 'E', 'S'), columnspan=1)

        # ============================================== ROW 4 ============================================= #
        self._tk_grid_obj[4][0] = tk.Message(
            self.gui_root, width=self._column_width[0],
            text=self._tk_var_obj[4][0], font=font_collection['header1']
        )
        self._tk_grid_obj[4][0].grid(row=4, column=0, padx=5, pady=5, sticky=('N', 'W', 'E', 'S'), columnspan=1)

        self._tk_grid_obj[4][1] = tk.Entry(
            self.gui_root,
            textvariable=self._tk_var_obj[4][1], font=font_collection['body1'], justify='right'
        )
        self._tk_grid_obj[4][1].grid(row=4, column=1, padx=5, pady=5, sticky=('N', 'W', 'E', 'S'), columnspan=1)

        self._tk_grid_obj[4][2] = tk.Button(
            self.gui_root,
            text=self._tk_var_obj[4][2], font=font_collection['header1'], background='light grey',
            command=self.__button_set_notional
        )
        self._tk_grid_obj[4][2].grid(row=4, column=2, padx=5, pady=5, sticky=('N', 'W', 'E', 'S'), columnspan=2)

        self._tk_grid_obj[4][4] = tk.Message(
            self.gui_root, width=self._column_width[4],
            text=self._tk_var_obj[4][4], font=font_collection['header1']
        )
        self._tk_grid_obj[4][4].grid(row=4, column=4, padx=5, pady=5, sticky=('N', 'W', 'E', 'S'), columnspan=1)

        self._tk_grid_obj[4][5] = tk.Message(
            self.gui_root, width=self._column_width[5],
            textvariable=self._tk_var_obj[4][5], font=font_collection['body1'], justify='right'
        )
        self._tk_grid_obj[4][5].grid(row=4, column=5, padx=5, pady=5, sticky=('N', 'W', 'E', 'S'), columnspan=1)

        # ============================================== ROW 5 ============================================= #
        self._tk_grid_obj[5][0] = tk.Message(
            self.gui_root, width=self._column_width[0],
            text=self._tk_var_obj[5][0], font=font_collection['header1'], relief='ridge'
        )
        self._tk_grid_obj[5][0].grid(row=5, column=0, padx=5, sticky=('N', 'W', 'E', 'S'), columnspan=1)

        # ============================================== ROW 6 ============================================= #
        self._tk_grid_obj[6][0] = tk.Message(
            self.gui_root, width=self._column_width[0],
            textvariable=self._tk_var_obj[6][0], font=font_collection['header1'], relief='ridge'
        )
        self._tk_grid_obj[6][0].grid(row=6, column=0, padx=5, sticky=('N', 'W', 'E', 'S'), columnspan=1)

        # ============================================== ROW 7 ============================================= #
        self._tk_grid_obj[7][0] = tk.Message(
            self.gui_root, width=self._column_width[0],
            text=self._tk_var_obj[7][0], font=font_collection['header1']
        )
        self._tk_grid_obj[7][0].grid(row=7, column=0, padx=5, pady=5, sticky=('N', 'W', 'E', 'S'), columnspan=1)

    # ========================================== Button Commands ========================================== #
    def __button_stop_main(self):
        self.outbound_q.put((self.__name, 'master', 'stop_all', None))

    def __button_set_notional(self):
        try:
            selected_notional = self._tk_var_obj[4][1].get()
            if selected_notional > 0:
                self.parent.master_thread.update_thread_selection('target_notional', selected_notional)
                self._tk_var_obj[4][5].set('$ {0:.2f}'.format(selected_notional))
            else:
                self._tk_var_obj[4][1].set(0.0)
        except Exception as e:
            print(self.__name + ' thread - Exception! Notional Entry is not float type!')
            self._tk_var_obj[4][1].set(0.0)

    # ========================================== Trace Callback commands========================================== #
    def __trace_option_menu_change_r3_c1(self, *args):
        selected_coin = self._tk_var_obj[3][1].get()
        self.parent.master_thread.update_thread_selection('target_coin', selected_coin)

    # ========================================== External facing commands========================================== #

    def update_status_grid(self):

        for name in self.parent.status_grid:
            if name in self.status_map:
                position = self.status_map[name]
                status = self.parent.status_grid[name]
                self._tk_var_obj[position[0]][position[1]].set(self.parent.status_grid[name])
                if status in ['Active', 'Online']:
                    self._tk_grid_obj[position[0]][position[1]].config(background='lime green')
                elif status in ['Inactive', 'Offline']:
                    self._tk_grid_obj[position[0]][position[1]].config(background='red2')
            else:
                print(self.__name + ' thread - Warning! No tkinter grid variable for status: "' + str(name) + '".')

    def update_data_grid(self):

        # for item in self.parent.data_grid:
        for item in self.parent.data_grid:
            if item in self.data_map:
                position = self.data_map[item]
                self._tk_var_obj[position[0]][position[1]].set(self.parent.data_grid[item])
            else:
                print(self.__name + ' thread - Warning! No tkinter grid variable for data object: "' + str(item) + '".')

