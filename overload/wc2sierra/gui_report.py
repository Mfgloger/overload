import logging
import shelve
import Tkinter as tk
import ttk
import tkFileDialog
import tkMessageBox


from errors import OverloadError
from gui_utils import ToolTip, BusyManager
from logging_setup import format_traceback, LogglyAdapter
from manager import retrieve_downloaded_bibs
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

        # worlcat records display frame
        self.dispFrm = ttk.LabelFrame(self.top, text='Worldcat records')
        self.dispFrm.grid(
            row=1, column=0, columnspan=4, sticky='snew', padx=5, pady=10)

        self.xscrollbar = tk.Scrollbar(self.dispFrm, orient=tk.HORIZONTAL)
        self.xscrollbar.grid(
            row=0, column=1, columnspan=10, sticky='nwe')
        self.yscrollbar = tk.Scrollbar(self.dispFrm, orient=tk.VERTICAL)
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
        self.populate_preview()

    def previous_batch(self):
        pass

    def next_batch(self):
        pass

    def confirm(self):
        pass

    def populate_preview(self):
        data = retrieve_downloaded_bibs()
        row = 0
        self.tracker = {}
        for d in data:
            self.create_resource(d, row)
            row += 1

    def create_resource(self, data, row):
        unitFrm = tk.Frame(self.preview_frame)
        unitFrm.grid(row=row, column=0, sticky='snew')

        selCbn = ttk.Checkbutton(
            unitFrm)
        selCbn.grid(
            row=0, column=0, sticky='snw')

        sierraTxt = tk.Text(
            unitFrm,
            height=5,
            width=1000,
            wrap='word')
        sierraTxt.grid(
            row=0, column=1, sticky='snew')

        self.pupulate_sierra_data(sierraTxt, data[1])

        worldcatTxt = tk.Text(
            unitFrm,
            wrap='word')
        worldcatTxt.grid(
            row=1, column=1, sticky='snew')

        self.pupulate_worldcat_data(worldcatTxt, data[2])

        return dict(check=selCbn, wchid=data[0])

    def pupulate_sierra_data(self, widget, data):
        l1 = '{}\n'.format(data['title'])
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
            print(type(data))
            print(data)
            l1 = u'{} / {}\n'.format(
                data['title'],
                data['author'])
            l2 = u'\tclassification: {} | {}\n'.format(
                data['lccn'], data['dewey'])
            l3 = u'\t{} , {}\n'.format(
                data['publisher'], data['pub_year'])
            l4 = u'\t{}\n'.format(
                ' | '.join(data['physical_desc']))
            l5 = u'\t{}'.format(
                ' | '.join(data['subjects']))

            widget.insert(1.0, l1)
            widget.insert(2.0, l2)
            widget.insert(3.0, l3)
            widget.insert(4.0, l4)
            widget.insert(5.0, l5)

            widget.tag_add('header', '1.0', '1.end')
            widget.tag_config('header', font=("tahoma", "11", "bold"))
            widget.tag_add('location', '3.11', '3.end')
            widget.tag_config('location', font=(
                "tahoma", "11", "bold"), foreground='tomato2')

        else:
            l1 = 'NO GOOD MATCHES FOUND IN WORLDCAT'
            widget.insert(1.0, l1)

        widget['state'] = 'disable'

    def selection_observer(self, *args):
        if self.sel_var.get() == 1:
            self.sel_lbl.set('unselect all')
        elif self.sel_var.get() == 0:
            self.sel_lbl.set('select all')

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
