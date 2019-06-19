import logging
import shelve
import Tkinter as tk
import ttk
import tkFileDialog
import tkMessageBox


from errors import OverloadError
from gui_utils import ToolTip, BusyManager
from logging_setup import format_traceback, LogglyAdapter
from setup_dirs import USER_DATA, MY_DOCS
from manager import launch_process


mlogger = LogglyAdapter(logging.getLogger('overload'), None)


class W2SReport(tk.Frame):
    """
    GUI for verification and selection of records retrieved
    using Worldcat2Sierra module
    """

    def __init__(self, parent):
        self.parent = parent
        tk.Frame.__init__(self, self.parent, background='white')
        self.top = tk.Toplevel(self, background='white')
        self.cur_manager = BusyManager(self)
        self.top.iconbitmap('./icons/report.ico')
        self.top.title('W2S Report & Selection')

        # variables
        self.sel_lbl = tk.StringVar()
        self.sel_var = tk.IntVar()
        self.sel_var.trace('w', self.selection_observer)
        self.hold_var = tk.IntVar()
        self.disp_batch = tk.StringVar()
        self.disp_sel = tk.StringVar()

        self.disp_batch.set('20 out of 20 displayed')
        self.disp_sel.set('5 our of 20 selected')

        # navigation frame
        self.navFrm = ttk.Frame(self.top)
        self.navFrm.grid(
            row=0, column=0, padx=20, pady=20)
        self.navFrm.columnconfigure(2, minsize=200)
        self.navFrm.columnconfigure(4, minsize=40)

        self.leftBtn = ttk.Button(
            self.navFrm,
            text='<<',
            width=5,
            command=self.previous_batch)
        self.leftBtn.grid(
            row=0, column=0, sticky='nsw', padx=5, pady=20)

        self.rightBtn = ttk.Button(
            self.navFrm,
            text='>>',
            width=5,
            command=self.next_batch)
        self.rightBtn.grid(
            row=0, column=1, sticky='nse', padx=5, pady=20)

        self.batch_dispLbl = ttk.Label(
            self.navFrm,
            textvariable=self.disp_batch)
        self.batch_dispLbl.grid(
            row=1, column=0, columnspan=2, sticky='snw', padx=5)

        self.selCbn = ttk.Checkbutton(
            self.navFrm,
            textvariable=self.sel_lbl,
            variable=self.sel_var)
        self.selCbn.grid(
            row=0, column=2, sticky='snew')

        self.holdCbn = ttk.Checkbutton(
            self.navFrm,
            text='set OCLC holdings',
            variable=self.hold_var)
        self.holdCbn.grid(
            row=0, column=3, sticky='snw')

        self.sel_dispLbl = ttk.Label(
            self.navFrm,
            textvariable=self.disp_sel)
        self.sel_dispLbl.grid(
            row=1, column=2, columnspan=2, sticky='snw')

        self.confirmBtn = ttk.Button(
            self.navFrm,
            text='confirm',
            width=15,
            command=self.confirm)
        self.confirmBtn.grid(
            row=0, column=5, sticky='nsw', padx=20, pady=20)

        self.cancelBtn = ttk.Button(
            self.navFrm,
            text='cancel',
            width=15,
            command=self.top.destroy)
        self.cancelBtn.grid(
            row=0, column=6, sticky='nsw', padx=20, pady=20)

    def previous_batch(self):
        pass

    def next_batch(self):
        pass

    def confirm(self):
        pass


    def selection_observer(self, *args):
        if self.sel_var.get() == 1:
            self.sel_lbl.set('unselect all')
        elif self.sel_var.get() == 0:
            self.sel_lbl.set('select all')

