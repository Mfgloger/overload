import logging
import shelve
import Tkinter as tk
import ttk
import tkFileDialog
import tkMessageBox

from gui_utils import ToolTip, BusyManager
from logging_setup import format_traceback, LogglyAdapter
from setup_dirs import USER_DATA, MY_DOCS
from reports import compile_batch_info, prep_results_data


module_logger = LogglyAdapter(logging.getLogger('overload'), None)


class ResultsView(tk.Frame):
    """
    GUI for viewing GetBib results
    """

    def __init__(self, parent):
        self.parent = parent
        self.base = tk.Toplevel(self.parent, background='white')
        # self.base.minsize(width=800, height=500)
        self.base.iconbitmap('./icons/report.ico')
        self.base.title('GetBib Report')

        self.base.columnconfigure(0, minsize=10)
        self.base.columnconfigure(1, minsize=1100)
        self.base.columnconfigure(3, minsize=200)
        self.base.columnconfigure(5, minsize=10)
        self.base.rowconfigure(0, minsize=10)
        self.base.rowconfigure(7, minsize=600)

        self.dfs = None

        self.yscrollbar = tk.Scrollbar(self.base, orient=tk.VERTICAL)
        self.yscrollbar.grid(
            row=1, column=2, rowspan=9, sticky='nse')
        self.xscrollbar = tk.Scrollbar(self.base, orient=tk.HORIZONTAL)
        self.xscrollbar.grid(
            row=10, column=1, columnspan=2, sticky='swe')

        self.reportTxt = tk.Text(
            self.base,
            borderwidth=0,
            wrap=tk.NONE,
            yscrollcommand=self.yscrollbar.set,
            xscrollcommand=self.xscrollbar.set)
        self.reportTxt.grid(
            row=1, column=1, rowspan=9, sticky='snew')
        self.reportTxt.tag_config('blue', foreground='blue', underline=1)
        self.reportTxt.tag_config('red', foreground='red')

        self.yscrollbar.config(command=self.reportTxt.yview)
        self.xscrollbar.config(command=self.reportTxt.xview)

        ttk.Button(
            self.base,
            text='save ready',
            width=12,
            cursor='hand2',
            command=lambda: self.save('ready')).grid(
            row=1, column=3, sticky='snew', padx=30, pady=20)
        ttk.Button(
            self.base,
            text='save full',
            width=12,
            cursor='hand2',
            command=lambda: self.save('full')).grid(
            row=2, column=3, sticky='snew', padx=30, pady=10)
        ttk.Button(
            self.base,
            text='save mixed',
            width=12,
            cursor='hand2',
            command=lambda: self.save('mixed')).grid(
            row=3, column=3, sticky='snew', padx=30, pady=10)
        ttk.Button(
            self.base,
            text='save dups',
            width=12,
            cursor='hand2',
            command=lambda: self.save('dups')).grid(
            row=4, column=3, sticky='snew', padx=30, pady=10)
        ttk.Button(
            self.base,
            text='save missing',
            width=12,
            cursor='hand2',
            command=lambda: self.save('missing')).grid(
            row=5, column=3, sticky='snew', padx=30, pady=10)

        self.generate_report()

    def save(self, category):
        if category == 'ready':
            d = self.cdf['target_sierraId']
        elif category == 'full':
            d = self.fdf
        elif category == 'mixed':
            d = self.mdf
        elif category == 'dups':
            d = self.ddf
        elif category == 'missing':
            d = self.ndf

        user_data = shelve.open(USER_DATA)
        paths = user_data['paths']
        if 'pvr_last_open_dir' in paths:
            last_open_dir = paths['pvr_last_open_dir']
        else:
            last_open_dir = MY_DOCS
        user_data.close()

        if d.shape[0] > 0:
            dst_fh = tkFileDialog.asksaveasfilename(
                parent=self.base,
                title='Save as',
                initialfile='bibNos.txt',
                initialdir=last_open_dir)
            if dst_fh:
                d.to_csv(dst_fh, index=False)

    def generate_report(self):
        summary = compile_batch_info()
        self.reportTxt.insert(tk.END, summary)

        self.cdf, self.fdf, self.mdf, self.ddf, self.ndf = prep_results_data()

        self.reportTxt.insert(tk.END, '\n{}\n'.format('=' * 125))
        self.reportTxt.insert(tk.END, '{}\n'.format('=' * 125))
        self.reportTxt.insert(tk.END, 'READY FOR PROCESSING TITLES:\n')
        self.reportTxt.insert(tk.END, self.cdf.to_string())
        self.reportTxt.insert(tk.END, '\n{}\n'.format('=' * 125))
        self.reportTxt.insert(tk.END, 'REJECTED FULL BIB TITLES:\n')
        self.reportTxt.insert(tk.END, self.fdf.to_string())
        self.reportTxt.insert(tk.END, '\n{}\n'.format('=' * 125))
        self.reportTxt.insert(tk.END, 'REJECTED MIXED BIB TITLES:\n')
        self.reportTxt.insert(tk.END, self.mdf.to_string())
        self.reportTxt.insert(tk.END, '\n{}\n'.format('=' * 125))
        self.reportTxt.insert(tk.END, 'REJECTED DUPLICATE BIB TITLES:\n')
        self.reportTxt.insert(tk.END, self.ddf.to_string())
        self.reportTxt.insert(tk.END, '\n{}\n'.format('=' * 125))
        self.reportTxt.insert(tk.END, 'REJECTED NOT IN SIERRA BIB TITLES:\n')
        self.reportTxt.insert(tk.END, self.ndf.to_string())
