import logging
import shelve
import Tkinter as tk
import ttk
import tkFileDialog
import tkMessageBox


from errors import OverloadError
from gui_utils import ToolTip, BusyManager
from logging_setup import format_traceback, LogglyAdapter
from manager import (retrieve_bibs_batch, count_total, persist_choice,
                     create_marc_file)
from setup_dirs import USER_DATA, MY_DOCS


mlogger = LogglyAdapter(logging.getLogger('overload'), None)


class W2SReport(tk.Frame):
    """
    GUI for verification and selection of records retrieved
    using Worldcat2Sierra module
    """

    def __init__(self, parent, dst_fh):
        self.parent = parent
        self.dst_fh = dst_fh
        tk.Frame.__init__(self, self.parent, background='white')
        self.top = tk.Toplevel(self, background='white')
        self.cur_manager = BusyManager(self)
        self.top.iconbitmap('./icons/report.ico')
        self.top.title('W2S Report & Selection')

        # variables
        self.sel_lbl = tk.StringVar()
        self.sel_lbl.set('select all')
        self.sel_var = tk.IntVar()
        self.sel_var.trace('w', self.selection_observer)
        self.hold_var = tk.IntVar()

        self.disp_batch = tk.StringVar()
        self.batch = 20
        self.disp_start = 0
        self.disp_end = self.batch
        self.total_count = 0
        self.selected_count = 0

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

        # worlcat records display frame
        self.dispFrm = ttk.LabelFrame(self.top, text='Worldcat records')
        self.dispFrm.grid(
            row=1, column=0, columnspan=4, sticky='snew', padx=5, pady=10)

        self.xscrollbar = ttk.Scrollbar(self.dispFrm, orient=tk.HORIZONTAL)
        self.xscrollbar.grid(
            row=0, column=1, columnspan=10, sticky='nwe')
        self.yscrollbar = ttk.Scrollbar(self.dispFrm, orient=tk.VERTICAL)
        self.yscrollbar.grid(
            row=1, column=0, rowspan=20, sticky='nse')
        self.preview_base = tk.Canvas(
            self.dispFrm, bg='gray',
            height=600,
            width=1000,
            xscrollcommand=self.xscrollbar.set,
            yscrollcommand=self.yscrollbar.set)
        self.preview_base.grid(
            row=1, column=1, rowspan=20, columnspan=10, sticky='nwe')
        self.preview_base.bind_all("<MouseWheel>", self.on_mousewheel)
        self.preview()

        # populate preview_frame with Sierra & Worldcat data
        self.display_totals()
        self.populate_preview(self.meta_ids[:self.disp_end])
        # update count display
        self.disp_batch.set('{} out of {} displayed'.format(
            len(self.meta_ids[:self.disp_end]), self.count_total))

    def save_choices(self):
        for k, v in self.tracker.items():
            if v['check'].get():
                persist_choice([v['wcsmid']], True)
            else:
                persist_choice([v['wcsmid']], False)

    def previous_batch(self):
        self.save_choices()
        if self.disp_start > 0:
            self.preview_frame.destroy()
            self.preview()
            self.disp_end = self.disp_start
            self.start = self.disp_end - self.batch
            self.populate_preview(
                self.meta_ids[self.disp_start:self.disp_end])

    def next_batch(self):
        self.save_choices()
        if self.disp_end <= len(self.meta_ids):
            self.preview_frame.destroy()
            self.preview()
            self.disp_start = self.disp_end
            self.disp_end = self.disp_end + self.batch
            self.populate_preview(
                self.meta_ids[self.disp_start: self.disp_end])

    def confirm(self):
        self.save_choices()

        create_marc_file(self.dst_fh, self.hold_var.get())

        if self.hold_var.get():
            msg = 'Records have been saved to a file.\n' \
                  'OCLC Holdings have been set.'
        else:
            msg = 'Records have been saved to a file.\n' \
                  'No OCLC holdings have been set.'
        tkMessageBox.showinfo(
            'Info', msg,
            parent=self.top)

    def display_totals(self):
        self.count_total, self.meta_ids = count_total()

    def populate_preview(self, meta_ids):
        data = retrieve_bibs_batch(meta_ids)
        row = 0
        self.tracker = {}
        for d in data:
            wid, wdict = self.create_resource(d, row)
            self.tracker[wid] = wdict
            row += 1

    def create_resource(self, data, row):
        unitFrm = tk.Frame(self.preview_frame)
        unitFrm.grid(row=row, column=0, columnspan=10, sticky='snew')
        unitFrm.configure(background='white')
        unitFrm.columnconfigure(0, minsize=40)

        var = tk.IntVar()
        var.set(data[1]['choice'])

        selCbn = ttk.Checkbutton(
            unitFrm,
            var=var)
        selCbn.grid(
            row=0, column=0, sticky='snew', padx=5)

        sierraTxt = tk.Text(
            unitFrm,
            height=5,
            width=118,
            wrap='word',
            borderwidth=0)
        sierraTxt.grid(
            row=0, column=1, columnspan=10, sticky='snew', pady=5)

        self.pupulate_sierra_data(sierraTxt, data[1])

        scrollbar = ttk.Scrollbar(unitFrm)
        scrollbar.grid(
            row=1, column=11, sticky='snw', pady=5)
        worldcatTxt = tk.Text(
            unitFrm,
            wrap='word',
            width=118,
            borderwidth=0,
            yscrollcommand=scrollbar.set)
        worldcatTxt.grid(
            row=1, column=1, columnspan=10, sticky='snew', pady=5)
        scrollbar.config(command=worldcatTxt.yview)

        self.pupulate_worldcat_data(worldcatTxt, data[2])

        ttk.Separator(unitFrm, orient=tk.HORIZONTAL).grid(
            row=2, column=0, columnspan=10, sticky='sew', padx=10, pady=10)

        return (selCbn.winfo_name(), dict(check=var, wcsmid=data[0]))

    def pupulate_sierra_data(self, widget, data):
        l1 = '  {}\n'.format(data['title'])
        l2 = '\tbib #: {}, ord #: {}\n'.format(
            data['sierraId'], data['oid'])
        l3 = '\tlocations: {}\n'.format(data['locs'])
        l4 = '\tnotes: {} | {} | {}\n'.format(
            data['venNote'],
            data['note'],
            data['intNote'])
        widget.insert(1.0, l1)
        widget.insert(2.0, l2)
        widget.insert(3.0, l3)
        widget.insert(4.0, l4)

        widget.tag_add('header', '1.0', '1.end')
        widget.tag_config('header', font=("tahoma", "11", "bold"))
        widget.tag_add('location', '3.11', '3.end')
        widget.tag_config('location', font=(
            "tahoma", "11", "bold"), foreground='tomato2')
        widget['state'] = 'disable'

    def pupulate_worldcat_data(self, widget, data):
        if data:
            widget.insert(1.0, data)
        else:
            l1 = 'NO GOOD MATCHES FOUND IN WORLDCAT'
            widget.insert(1.0, l1)
            widget.configure(height=2)

        widget['state'] = 'disable'

    def selection_observer(self, *args):
        if self.sel_var.get() == 1:
            self.sel_lbl.set('unselect all')
            for key, value in self.tracker.items():
                value['check'].set(1)
            persist_choice(self.meta_ids, True)
        elif self.sel_var.get() == 0:
            self.sel_lbl.set('select all')
            for key, value in self.tracker.items():
                value['check'].set(0)
            presist_choice(self.meta_ids, False)

    def preview(self):
        self.preview_frame = tk.Frame(
            self.preview_base)
        self.xscrollbar.config(command=self.preview_base.xview)
        self.yscrollbar.config(command=self.preview_base.yview)
        self.preview_base.create_window(
            (0, 0), window=self.preview_frame, anchor="nw",
            tags="self.preview_frame")
        self.preview_frame.bind("<Configure>", self.onFrameConfigure)

    def onFrameConfigure(self, event):
        self.preview_base.config(scrollregion=self.preview_base.bbox('all'))

    def on_mousewheel(self, event):
        self.preview_base.yview_scroll(
            int(-1 * (event.delta / 120)), "units")
