import logging
import shelve
import Tkinter as tk
import ttk
import tkFileDialog
import tkMessageBox

from gui_utils import ToolTip, BusyManager
from logging_setup import format_traceback, LogglyAdapter
from setup_dirs import USER_DATA, MY_DOCS
from manager import launch_process


module_logger = LogglyAdapter(logging.getLogger('overload'), None)


class GetBibs(tk.Frame):
    """
    GUI for module retrieving records or bib numbers from Sierra
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
        self.target = None
        self.dst_fh = tk.StringVar()
        self.id_type = tk.StringVar()
        self.hit_counter = tk.IntVar()
        self.nohit_counter = tk.IntVar()
        self.source_fh = tk.StringVar()
        self.dst_fh = tk.StringVar()

        # logos
        self.nyplLogo = tk.PhotoImage(file='./icons/nyplLogo.gif')
        self.bplLogo = tk.PhotoImage(file='./icons/bplLogo.gif')

        # layout of the main frame
        self.rowconfigure(0, minsize=10)
        self.rowconfigure(2, minsize=10)
        self.columnconfigure(0, minsize=5)
        self.columnconfigure(2, minsize=15)

        # layout of the base frame
        self.baseFrm = ttk.LabelFrame(
            self,
            text='Get Bib')
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
        self.paramsFrm.rowconfigure(6, minsize=10)
        self.paramsFrm.columnconfigure(0, minsize=10)
        self.paramsFrm.columnconfigure(2, minsize=150)
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
            text='database/method')
        self.apiLbl.grid(
            row=4, column=1, sticky='snew')
        self.apiCbx = ttk.Combobox(
            self.paramsFrm,
            textvariable=self.api,
            width=25)
        self.apiCbx.grid(
            row=4, column=2, sticky='nsw', padx=5, pady=5)

        self.idTypeLbl = ttk.Label(
            self.paramsFrm,
            text='ID type')
        self.idTypeLbl.grid(
            row=5, column=1, sticky='snew')
        self.idTypeCbx = ttk.Combobox(
            self.paramsFrm,
            textvariable=self.id_type,
            width=25)
        self.idTypeCbx.grid(
            row=5, column=2, sticky='nsw', padx=5, pady=5)

        self.actionFrm = ttk.Frame(
            self.baseFrm,
            borderwidth=2,
            relief='ridge')
        self.actionFrm.grid(
            row=3, column=1, columnspan=6, sticky='snew')
        self.actionFrm.rowconfigure(0, minsize=10)
        self.actionFrm.rowconfigure(3, minsize=20)
        self.actionFrm.rowconfigure(5, minsize=5)
        self.actionFrm.rowconfigure(7, minsize=10)
        self.actionFrm.rowconfigure(10, minsize=20)
        self.actionFrm.rowconfigure(12, minsize=10)
        self.actionFrm.columnconfigure(0, minsize=10)
        self.actionFrm.columnconfigure(2, minsize=5)
        self.actionFrm.columnconfigure(4, minsize=50)
        self.actionFrm.columnconfigure(6, minsize=5)
        self.actionFrm.columnconfigure(7, minsize=170)
        self.actionFrm.columnconfigure(8, minsize=5)

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
            row=1, column=3, columnspan=8, sticky='snew', pady=5)
        searchICO = tk.PhotoImage(file='./icons/search.gif')
        self.sourceBtn = ttk.Button(
            self.actionFrm, image=searchICO,
            cursor='hand2',
            command=self.find_source)
        self.sourceBtn.image = searchICO
        self.sourceBtn.grid(
            row=1, column=11, sticky='ne', padx=5, pady=5)

        # destination row
        self.dstLbl = ttk.Label(
            self.actionFrm,
            text='destination')
        self.dstLbl.grid(
            row=2, column=1, sticky='snew')
        self.dstEnt = ttk.Entry(
            self.actionFrm,
            textvariable=self.dst_fh)
        self.dstEnt.grid(
            row=2, column=3, columnspan=8, sticky='snew', pady=5)
        self.dstBtn = ttk.Button(
            self.actionFrm, image=searchICO,
            cursor='hand2',
            command=self.find_destination)
        self.dstBtn.image = searchICO
        self.dstBtn.grid(
            row=2, column=11, sticky='ne', padx=5, pady=5)

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
            row=4, column=3, columnspan=8, sticky='snew')

        self.tallyLbl = ttk.Label(
            self.actionFrm,
            text='status')
        self.tallyLbl.grid(
            row=6, column=3, sticky='snew')

        self.foundLbl = ttk.Label(
            self.actionFrm,
            text='found:')
        self.foundLbl.grid(
            row=7, column=3, sticky='snew')

        self.foundcounterLbl = ttk.Label(
            self.actionFrm,
            textvariable=self.hit_counter)
        self.foundcounterLbl.grid(
            row=7, column=4, sticky='snw')

        self.nohitsLbl = ttk.Label(
            self.actionFrm,
            text='no bib found:')
        self.nohitsLbl.grid(
            row=8, column=3, sticky='snew')

        self.nohitscounterLbl = ttk.Label(
            self.actionFrm,
            textvariable=self.nohit_counter)
        self.nohitscounterLbl.grid(
            row=8, column=4, sticky='snw')

        # action buttons
        self.processBtn = ttk.Button(
            self.actionFrm,
            text='process',
            command=self.process,
            cursor='hand2',
            width=12)
        self.processBtn.grid(
            row=11, column=3, sticky='nw')

        self.reportBtn = ttk.Button(
            self.actionFrm,
            text='report',
            command=self.report,
            cursor='hand2',
            width=12)
        self.reportBtn.grid(
            row=11, column=5, sticky='nw')

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
        # determine last used directory
        user_data = shelve.open(USER_DATA)
        paths = user_data['paths']
        if 'pvr_last_open_dir' in paths:
            last_open_dir = paths['pvr_last_open_dir']
        else:
            last_open_dir = MY_DOCS

        # select files for processing
        file = tkFileDialog.askopenfilename(
            parent=self,
            title='Select file',
            filetypes=(('text files', '*.txt'),
                       ('csv files', '*.csv'),
                       ('tab files', '*.tsv')),
            initialdir=last_open_dir)

        if file:
            self.source_fh.set(file)

        user_data.close()

    def find_destination(self):
        # ask destination file
        dst_fh = tkFileDialog.asksaveasfilename(
            parent=self,
            title='Save as',
            initialfile='bibNos.txt',
            initialdir=MY_DOCS)
        if dst_fh:
            self.dst_fh.set(dst_fh)

    def process(self):
        self.reset()

        # validate all required elements are provided
        if not self.source_fh.get():
            self.find_source()

        if not self.dst_fh.get():
            self.find_destination()

        issues = []

        if not self.system.get():
            issues.append('- system not selected')
        if self.system.get() == 'NYPL' and not self.library.get():
            issues.append('- library parameter is required')
        if not self.action.get():
            issues.append('- action parameter is required')
        if not self.api.get():
            issues.append('- API not selected')

        # temp issues
        if self.library.get() == 'research':
            issues.append('- Research functionality not developed')
        if self.action.get() == 'update':
            issues.append('- updating functionality not developed')
        if self.id_type.get() != 'ISBN':
            issues.append('- only ISBN id is permitted at the moment')

        if issues:
            issues.insert(0, 'Parameters error(s):\n')
            tkMessageBox.showerror('Error', '\n'.join(issues))
        else:
            if self.source_fh.get() and self.dst_fh.get():
                # both paths provided
                # wrap later in an exception catching & displaying
                        # record used connection target
                if 'Z3950' in self.api.get():
                    name = self.api.get().split(' (')[0]
                    method = 'Z3950'
                elif 'Sierra API' in self.api.get():
                    name = self.api.get().split(' (')[0]
                    method = 'Sierra API'
                elif 'Platform API' in self.api.get():
                    name = self.api.get().split(' (')[0]
                    method = 'Platform API'
                else:
                    name = None
                    method = None
                self.target = {'name': name, 'method': method}

                launch_process(
                    self.system.get(), self.library.get(), self.target,
                    self.id_type.get(), self.action.get(),
                    self.source_fh.get(), self.dst_fh.get(), self.progbar,
                    self.hit_counter, self.nohit_counter)
                tkMessageBox.showinfo('Processing', 'Processing complete.')

    def report(self):
        tkMessageBox.showinfo(
            'Report',
            'Detailed report here, that includes all retrieved and\n'
            'processed records, option to make final selection and\n'
            'mark bibs to update holdings')

    def display_help(self):
        tkMessageBox.showinfo(
            'Help', 'Help info displayed here.')

    def reset(self):
        self.progbar['value'] = 0
        self.hit_counter.set(0)
        self.nohit_counter.set(0)
        self.update()

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
        self.api.set('')
        # show available api crendentials for system
        # pull available API from user_data
        user_data = shelve.open(USER_DATA)
        apis = []
        try:
            if self.system.get() == 'NYPL':
                if 'PlatformAPIs' in user_data:
                    for conn, params in user_data['PlatformAPIs'].iteritems():
                        apis.append(
                            conn + ' (' + params['method'] + ')')
            elif self.system.get() == 'BPL':
                if 'Z3950s' in user_data:
                    for conn, params in user_data['Z3950s'].iteritems():
                        if params['library'] == 'BPL':
                            apis.append(
                                conn + ' (' + params['method'] + ')')

        except KeyError:
            m = 'Please complete Platform and Z3950 APIs setup first\n' \
                'by going to Settings>Platform APIs and \n' \
                'Settings>Z3950.'
            tkMessageBox.showerror('Setup Error', m)
        finally:
            self.apiCbx['values'] = apis
            self.apiCbx['state'] = 'readonly'
            user_data.close()

    def observer(self, *args):
        if self.activeW.get() == 'GetBibs':
            # load drop-down choics
            self.systemCbx['values'] = ('BPL', 'NYPL')
            self.system.set('NYPL')
            self.systemCbx['state'] = 'readonly'
            self.libraryCbx['values'] = ('branches', 'research')
            self.library.set('branches')
            self.libraryCbx['state'] = 'readonly'
            self.actionCbx['values'] = ('get bib #', 'get marc record')
            self.action.set('get bib #')
            self.actionCbx['state'] = 'readonly'
            self.idTypeCbx['values'] = (
                'ISBN', 'ISSN', 'UPC', 'LCCN', 'OCLC #')
            self.id_type.set('ISBN')
            self.idTypeCbx['state'] = 'readonly'
