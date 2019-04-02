import logging
import shelve
import Tkinter as tk
import ttk
import tkFileDialog
import tkMessageBox

from gui_utils import ToolTip, BusyManager
from logging_setup import format_traceback, LogglyAdapter
from setup_dirs import USER_DATA


module_logger = LogglyAdapter(logging.getLogger('overload'), None)


class UpgradeBibs(tk.Frame):
    """
    GUI for module upgrading records from Worldcat
    """

    def __init__(self, parent, controller, **app_data):
        self.parent = parent
        tk.Frame.__init__(self, parent, background='white')
        self.controller = controller
        self.activeW = app_data['activeW']
        self.activeW.trace('w', self.observer)

        self.cur_manager = BusyManager(self)

        # variables
        self.system = tk.StringVar()
        self.system.trace('w', self.system_observer)
        self.library = tk.StringVar()
        self.action = tk.StringVar()
        self.api = tk.StringVar()
        self.encode_level = tk.StringVar()
        self.rec_type = tk.StringVar()
        self.cat_rules = tk.StringVar()
        self.cat_source = tk.StringVar()
        self.source_fh = tk.StringVar()
        self.dst_dir = tk.StringVar()
        self.counter = tk.StringVar()
        self.nohits = tk.IntVar()
        self.found = tk.IntVar()

        # logos
        self.nyplLogo = tk.PhotoImage(file='./icons/nyplLogo.gif')
        self.bplLogo = tk.PhotoImage(file='./icons/bplLogo.gif')

        # layout of the main frame
        self.rowconfigure(0, minsize=30)
        self.rowconfigure(2, minsize=10)
        self.columnconfigure(0, minsize=5)
        self.columnconfigure(2, minsize=5)

        # layout of the base frame
        self.baseFrm = ttk.LabelFrame(
            self,
            text='Upgrade Bibs')
        self.baseFrm.grid(
            row=1, column=1, rowspan=6, sticky='snew')
        self.baseFrm.rowconfigure(0, minsize=10)
        self.baseFrm.rowconfigure(18, minsize=10)
        self.baseFrm.columnconfigure(0, minsize=10)
        self.baseFrm.columnconfigure(7, minsize=10)

        # layout of parameters
        self.paramsFrm = ttk.Frame(
            self.baseFrm,
            borderwidth=2,
            relief='ridge')
        self.paramsFrm.grid(
            row=1, column=1, columnspan=6, sticky='snew')
        self.paramsFrm.rowconfigure(0, minsize=10)
        self.paramsFrm.rowconfigure(5, minsize=10)
        self.paramsFrm.columnconfigure(0, minsize=10)
        self.paramsFrm.columnconfigure(3, minsize=20)
        self.paramsFrm.columnconfigure(6, minsize=10)

        # params drop down menu
        self.systemLbl = ttk.Label(
            self.paramsFrm,
            text='system:')
        self.systemLbl.grid(
            row=1, column=1, sticky='snew')
        self.systemCbx = ttk.Combobox(
            self.paramsFrm,
            textvariable=self.system,
            width=25)
        self.systemCbx.grid(
            row=1, column=2, sticky='nsw', padx=5, pady=5)

        self.libraryLbl = ttk.Label(
            self.paramsFrm,
            text='library:')
        self.libraryLbl.grid(
            row=2, column=1, sticky='snew')
        self.libraryCbx = ttk.Combobox(
            self.paramsFrm,
            textvariable=self.library,
            width=25)
        self.libraryCbx.grid(
            row=2, column=2, sticky='nsw', padx=5, pady=5)

        self.actionLbl = ttk.Label(
            self.paramsFrm,
            text='action:')
        self.actionLbl.grid(
            row=3, column=1, sticky='snew')
        self.actionCbx = ttk.Combobox(
            self.paramsFrm,
            textvariable=self.action,
            width=25)
        self.actionCbx.grid(
            row=3, column=2, sticky='nsw', padx=5, pady=5)

        self.apiLbl = ttk.Label(
            self.paramsFrm,
            text='worlcat credentials:')
        self.apiLbl.grid(
            row=4, column=1, sticky='snew')
        self.apiCbx = ttk.Combobox(
            self.paramsFrm,
            textvariable=self.api,
            width=25)
        self.apiCbx.grid(
            row=4, column=2, sticky='nsw', padx=5, pady=5)

        self.encode_levelLbl = ttk.Label(
            self.paramsFrm,
            text='record level:')
        self.encode_levelLbl.grid(
            row=1, column=3, sticky='snew')
        self.encode_levelCbx = ttk.Combobox(
            self.paramsFrm,
            textvariable=self.encode_level,
            width=25)
        self.encode_levelCbx.grid(
            row=1, column=4, sticky='nsw', padx=5, pady=5)

        self.rec_typeLbl = ttk.Label(
            self.paramsFrm,
            text='record type:')
        self.rec_typeLbl.grid(
            row=2, column=3, sticky='snew')
        self.rec_typeCbx = ttk.Combobox(
            self.paramsFrm,
            textvariable=self.rec_type,
            width=25)
        self.rec_typeCbx.grid(
            row=2, column=4, sticky='nsw', padx=5, pady=5)

        self.cat_rulesLbl = ttk.Label(
            self.paramsFrm,
            text='cataloging rules:')
        self.cat_rulesLbl.grid(
            row=3, column=3, sticky='snew')
        self.cat_rulesCbx = ttk.Combobox(
            self.paramsFrm,
            textvariable=self.cat_rules,
            width=25)
        self.cat_rulesCbx.grid(
            row=3, column=4, sticky='nsw', padx=5, pady=5)

        self.cat_sourceLbl = ttk.Label(
            self.paramsFrm,
            text='source:')
        self.cat_sourceLbl.grid(
            row=4, column=3, sticky='snew')
        self.cat_sourceCbx = ttk.Combobox(
            self.paramsFrm,
            textvariable=self.cat_source,
            width=25)
        self.cat_sourceCbx.grid(
            row=4, column=4, sticky='nsw', padx=5, pady=5)

        self.actionFrm = ttk.Frame(
            self.baseFrm,
            borderwidth=2,
            relief='ridge')
        self.actionFrm.grid(
            row=3, column=1, columnspan=6, sticky='snew')
        self.actionFrm.rowconfigure(0, minsize=10)
        self.actionFrm.rowconfigure(3, minsize=20)
        self.actionFrm.rowconfigure(5, minsize=20)
        self.actionFrm.rowconfigure(7, minsize=10)
        self.actionFrm.rowconfigure(8, minsize=30)
        self.actionFrm.rowconfigure(10, minsize=10)
        self.actionFrm.columnconfigure(0, minsize=10)
        self.actionFrm.columnconfigure(3, minsize=250)
        self.actionFrm.columnconfigure(2, minsize=20)
        self.actionFrm.columnconfigure(6, minsize=20)
        self.actionFrm.columnconfigure(8, minsize=10)

        # source row
        self.sourceLbl = ttk.Label(
            self.actionFrm,
            text='source file')
        self.sourceLbl.grid(
            row=1, column=1, sticky='snew')
        self.sourceEnt = ttk.Entry(
            self.actionFrm,
            textvariable=self.source_fh)
        self.sourceEnt.grid(
            row=1, column=2, columnspan=4, sticky='snew', pady=5)
        searchICO = tk.PhotoImage(file='./icons/search.gif')
        self.sourceBtn = ttk.Button(
            self.actionFrm, image=searchICO,
            cursor='hand2',
            command=self.find_source)
        self.sourceBtn.image = searchICO
        self.sourceBtn.grid(
            row=1, column=7, sticky='new', pady=4)

        # destination row
        self.dstLbl = ttk.Label(
            self.actionFrm,
            text='destination')
        self.dstLbl.grid(
            row=2, column=1, sticky='snew')
        self.dstEnt = ttk.Entry(
            self.actionFrm,
            textvariable=self.dst_dir)
        self.dstEnt.grid(
            row=2, column=2, columnspan=4, sticky='snew', pady=5)
        self.dstBtn = ttk.Button(
            self.actionFrm, image=searchICO,
            cursor='hand2',
            command=self.find_out_directory)
        self.dstBtn.image = searchICO
        self.dstBtn.grid(
            row=2, column=7, sticky='new', pady=4)

        # progess area
        self.progLbl = ttk.Label(
            self.actionFrm,
            text='progress')
        self.progLbl.grid(
            row=4, column=1, sticky='snew')
        self.progbar = ttk.Progressbar(
            self.actionFrm,
            mode='determinate',
            orient=tk.HORIZONTAL,)
        self.progbar.grid(
            row=4, column=2, columnspan=4, sticky='snew')
        self.counterLbl = ttk.Label(
            self.actionFrm,
            textvariable=self.counter)
        self.counterLbl.grid(
            row=4, column=7, sticky='snew')

        self.tallyLbl = ttk.Label(
            self.actionFrm,
            text='status')
        self.tallyLbl.grid(
            row=6, column=1, sticky='snew')
        self.foundLbl = ttk.Label(
            self.actionFrm,
            text='found:')
        self.foundLbl.grid(
            row=6, column=2, sticky='snew')
        self.foundcounterLbl = ttk.Label(
            self.actionFrm,
            textvariable=self.found)
        self.foundcounterLbl.grid(
            row=6, column=3, sticky='snw')
        self.nohitsLbl = ttk.Label(
            self.actionFrm,
            text='not found:')
        self.nohitsLbl.grid(
            row=7, column=2, sticky='snew')
        self.nohitscounterLbl = ttk.Label(
            self.actionFrm,
            textvariable=self.nohits)
        self.nohitscounterLbl.grid(
            row=7, column=3, sticky='snw')

        # action buttons
        self.processBtn = ttk.Button(
            self.actionFrm,
            text='process',
            command=self.process,
            cursor='hand2',
            width=12)
        self.processBtn.grid(
            row=9, column=1, sticky='nw')

        self.reportBtn = ttk.Button(
            self.actionFrm,
            text='report',
            command=self.report,
            cursor='hand2',
            width=12)
        self.reportBtn.grid(
            row=9, column=3, sticky='nw')

        # right panel
        # default logo & navigation buttons
        logo = tk.PhotoImage(file='./icons/upgrade.gif')
        self.logoDsp = ttk.Label(
            self, image=logo)
        # prevent image to be garbage collected
        self.logoDsp.image = logo
        self.logoDsp.grid(
            row=1, column=9, rowspan=2, columnspan=3, sticky='sew')

        self.helpBtn = ttk.Button(
            self,
            text='help',
            command=self.display_help,
            cursor='hand2',
            width=12)
        self.helpBtn.grid(
            row=5, column=8, columnspan=3, sticky='sew')

        self.closeBtn = ttk.Button(
            self,
            text='close',
            command=lambda: controller.show_frame('Main'),
            cursor='hand2',
            width=12)
        self.closeBtn.grid(
            row=6, column=8, columnspan=3, sticky='sew')

    def find_source(self):
        pass

    def find_out_directory(self):
        pass

    def process(self):
        pass

    def report(self):
        pass

    def display_help(self):
        pass

    def set_logo(self):
        # change logo
        if self.system.get() == 'NYPL':
            self.logoDsp.configure(image=self.nyplLogo)
            self.logoDsp.image = self.nyplLogo
        elif self.system.get() == 'BPL':
            self.logoDsp.configure(image=self.bplLogo)
            self.logoDsp.image = self.bplLogo

    def createToolTip(self, widget, text):
        toolTip = ToolTip(widget)

        def enter(event):
            toolTip.showtip(text)

        def leave(event):
            toolTip.hidetip()

        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)

    def system_observer(self, *args):
        # change logo
        self.set_logo()
        # show available api crendentials for system
        # pull available API from user_data
        user_data = shelve.open(USER_DATA)
        apis = user_data['WorldcatAPIs']
        user_data.close()

        if self.system.get() == 'NYPL':
            self.apiCbx['values'] = apis['NYPL'].keys()
        elif self.system.get() == 'BPL':
            self.apiCbx['values'] = apis['BPL'].keys()


    def observer(self, *args):
        if self.activeW.get() == 'UpgradeBibs':
            # load drop-down choics
            self.systemCbx['values'] = ('BPL', 'NYPL')
            self.libraryCbx['values'] = ('branches', 'research')
            self.actionCbx['values'] = ('upgrade', 'catalog')
            self.encode_levelCbx['values'] = (
                '# - Full level',
                '1 - Full level, mat. not examined',
                '2 - Less-than-full level',
                '3 - Abbreviated level',
                '4 - Core level',
                '5 - Partial level',
                '7 - Minimal level',
                '8 - Prepublication level'
            )

            self.encode_level.set('')
            self.rec_typeCbx['values'] = (
                'a - Language material',
                'c - Notated music',
                'd - Manus. notated music',
                'e - Cartographic material',
                'f - Manus. cartographic mat.',
                'g - Projected medium',
                'i - Nonmusical sound rec.',
                'j - Musical sound recording',
                'k - 2D nonprojectable graphic',
                'm - Computer file',
                'o - Kit',
                'p - Mixed materials',
                'r - 3D artifact',
                't - Manus. lang. material',
            )
            self.cat_rulesCbx['values'] = ('any', 'RDA-only')
            self.cat_rules.set('any')
            self.cat_sourceCbx['values'] = ('any', 'DLC')
            self.cat_source.set('any')
