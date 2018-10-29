# GUI for OpsUtils

import base64
import calendar
import datetime
import json
import keyring
from keyring.backends.Windows import WinVaultKeyring
import logging
import logging.config
import loggly.handlers
import os
import os.path
import re
import shelve
import subprocess
import Tkinter as tk
import ttk
import tkMessageBox
import tkFileDialog


from datastore import session_scope, PVR_Batch
from db_worker import retrieve_values
from connectors import goo
from connectors.goo_settings.scopes import SHEET_SCOPE, FDRIVE_SCOPE
from connectors.goo_settings.access_names import GAPP, GUSER
import credentials
from errors import OverloadError
from gui_utils import BusyManager, ToolTip
from logging_setup import LOGGING, DEV_LOGGING, LogglyAdapter
import overload_help
from pvf.pvf_gui import ProcessVendorFiles
from pvf.reports import cumulative_nypl_stats, cumulative_bpl_stats, \
    cumulative_vendor_stats
from setup_dirs import *


def updates(manual=True):
    with open('version.txt', 'r') as app_fh:
        app_version = app_fh.readline()[9:].strip()
        overload_logger.debug(
            'Checking for Overload updates. Current version: {}'.format(
                app_version))

    user_data = shelve.open(USER_DATA)
    if 'update_dir' in user_data['paths']:
        update_dir = user_data['paths']['update_dir']
        overload_logger.debug(
            'Using update directory from user_data: {}'.format(
                update_dir))
        if os.path.isfile(update_dir + r'\version.txt'):
            overload_logger.debug(
                'Found version.txt in update directory')
            up_fh = update_dir + r'\version.txt'
            with open(up_fh, 'r') as up_f:
                update_version = up_f.readline()[9:].strip()
                overload_logger.debug(
                    'Version available for pull: {}'.format(
                        update_version))
                if app_version != update_version:
                    overload_logger.debug(
                        'Local version different than in update directory')
                    m = 'A new version ({}) of Overload has been ' \
                        'found.\nWould you like to run the ' \
                        'update?'.format(update_version)
                    if tkMessageBox.askyesno('Update Info', m):
                        overload_logger.info(
                            '{} user is upgrading to overload version {}'.format(
                                USER_NAME, update_version))
                        # launch updater & quit main app
                        user_data.close()
                        args = '{} "{}"'.format(
                            'updater.exe', update_dir)
                        CREATE_NO_WINDOW = 0x08000000
                        subprocess.call(
                            args, creationflags=CREATE_NO_WINDOW)
                else:
                    if manual:
                        overload_logger.debug(
                            'Local and update directory versions are '
                            'the same')
                        m = 'Babel is up-to-date'
                        tkMessageBox.showinfo('Info', m)
        else:
            overload_logger.error(
                'Missing files. Failed to find version.txt in ({})'.format(
                    update_dir))
            m = '"version.txt" file in update folder not found.\n' \
                'Please provide update directory to correct folder\n' \
                'Go to:\n' \
                'settings>default directories>update folder'
            tkMessageBox.showwarning('Missing Files', m)
    else:
        overload_logger.warning(
            'Update directory not setup in Settings: user={}'.format(
                USER_NAME))
        m = 'please provide update directory\n' \
            'Go to:\n' \
            'settings>default directories>update folder'
        tkMessageBox.showwarning('Missing Directory', m)
    user_data.close()


class MainApplication(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        # container where frames are stacked
        container = ttk.Frame(self)
        container.grid()

        # bind shared data between windows
        self.activeW = tk.StringVar()
        self.app_data = {'activeW': self.activeW}

        # spawn Overload frames
        self.frames = {}
        for F in (
                Main, ProcessVendorFiles, UpgradeBib, Reports,
                Settings, DefaultDirs, SierraAPIs, PlatformAPIs,
                Z3950s, GooAPI, About):
            page_name = F.__name__
            frame = F(parent=container, controller=self,
                      **self.app_data)
            self.frames[page_name] = frame

            # put all windows in the same location
            frame.grid(row=0, column=0, sticky='snew', padx=10, pady=10)

        # set up menu bar
        menubar = tk.Menu(self)
        navig_menu = tk.Menu(menubar, tearoff=0)
        navig_menu.add_command(label='home',
                               command=lambda: self.show_frame('Main'))
        navig_menu.add_command(label='process vendor files',
                               command=lambda: self.show_frame(
                                   'ProcessVendorFiles'))
        navig_menu.add_command(label='upgrade bibs',
                               command=lambda: self.show_frame(
                                   'UpgradeBib'))
        navig_menu.add_command(label='settings',
                               command=lambda: self.show_frame('Settings'))
        navig_menu.add_separator()
        navig_menu.add_command(label='exit', command=self.quit)
        menubar.add_cascade(label='Menu', menu=navig_menu)
        report_menu = tk.Menu(menubar, tearoff=0)
        report_menu.add_command(
            label='reports', command=lambda: self.show_frame('Reports'))
        menubar.add_cascade(label='Reports', menu=report_menu)
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label='help index', command=None)
        help_menu.add_command(label='updates', command=updates)
        help_menu.add_command(label='about...',
                              command=lambda: self.show_frame('About'))
        menubar.add_cascade(label='Help', menu=help_menu)
        self.config(menu=menubar)

        # lift to the top main window
        self.show_frame('Main')

    def show_frame(self, page_name):
        """show frame for the given page name"""
        frame = self.frames[page_name]
        # set tier for behavioral control
        self.activeW.set(page_name)
        frame.tkraise()


class Main(tk.Frame):

    def __init__(self, parent, controller, **app_data):
        self.parent = parent
        tk.Frame.__init__(self, parent, background='white')
        self.controller = controller

        self.rowconfigure(0, minsize=25)
        self.rowconfigure(2, minsize=10)
        self.rowconfigure(10, minsize=25)
        self.columnconfigure(0, minsize=30)
        self.columnconfigure(2, minsize=20)
        self.columnconfigure(4, minsize=20)
        self.columnconfigure(6, minsize=20)
        self.columnconfigure(8, minsize=30)

        getRecNoICO = tk.PhotoImage(file='./icons/ProcessVendorFiles.gif')
        self.getRecNoBtn = ttk.Button(
            self, image=getRecNoICO,
            text='process vendor file',
            compound=tk.TOP,
            cursor='hand2',
            width=15,
            command=lambda: controller.show_frame('ProcessVendorFiles'))

        # prevent image to be garbage collected by Python
        self.getRecNoBtn.image = getRecNoICO
        self.getRecNoBtn.grid(
            row=1, column=1, sticky='snew')

        upgradeICO = tk.PhotoImage(file='./icons/upgrade.gif')
        self.upgradeBtn = ttk.Button(
            self, image=upgradeICO,
            text='upgrade bib',
            compound=tk.TOP,
            cursor='hand2',
            width=15,
            command=None)
        self.upgradeBtn.image = upgradeICO
        self.upgradeBtn.grid(
            row=1, column=3, sticky='snew')
        self.createToolTip(self.upgradeBtn, 'coming soon ...')

        jsonQueryICO = tk.PhotoImage(file='./icons/json_query_icon.gif')
        self.jsonQueryBtn = ttk.Button(
            self, image=jsonQueryICO,
            text='JSON query',
            compound=tk.TOP,
            cursor='hand2',
            width=15,
            command=None)
        self.jsonQueryBtn.image = jsonQueryICO
        self.jsonQueryBtn.grid(
            row=1, column=5, sticky='snew')
        self.createToolTip(
            self.jsonQueryBtn,
            'creates Sierra List\n'
            'query in JSON format\n'
            '(coming soon...)')

        nextICO = tk.PhotoImage(file='./icons/killer_tool.gif')
        self.nextToolBtn = ttk.Button(
            self, image=nextICO,
            text='(TBA)',
            compound=tk.TOP,
            cursor='hand2',
            width=15,
            command=None)
        self.nextToolBtn.image = nextICO
        self.nextToolBtn.grid(
            row=1, column=7, sticky='snew')
        self.createToolTip(
            self.nextToolBtn,
            'Do you have an idea for a tool that\n'
            'could improve your work?\n'
            'Let us know and we may build it!')

        reportsICO = tk.PhotoImage(file='./icons/report.gif')
        self.reportsBtn = ttk.Button(
            self, image=reportsICO,
            text='reports',
            compound=tk.TOP,
            cursor='hand2',
            width=15,
            command=lambda: controller.show_frame('Reports'))
        self.reportsBtn.image = reportsICO
        self.reportsBtn.grid(
            row=3, column=1, sticky='snew')
        self.createToolTip(
            self.reportsBtn,
            'user monthly reports')

        settingsICO = tk.PhotoImage(file='./icons/settings.gif')
        self.settingsBtn = ttk.Button(
            self, image=settingsICO,
            text='settings',
            compound=tk.TOP,
            cursor='hand2',
            width=15,
            command=lambda: controller.show_frame('Settings'))
        self.settingsBtn.image = settingsICO
        self.settingsBtn.grid(
            row=3, column=3, sticky='snew')

    def createToolTip(self, widget, text):
        toolTip = ToolTip(widget)

        def enter(event):
            toolTip.showtip(text)

        def leave(event):
            toolTip.hidetip()

        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)


class UpgradeBib(tk.Frame):
    """Upgrades bibs in a file by quering and finding fuller records in
       WorldCat"""

    def __init__(self, parent, controller, **app_data):
        self.parent = parent
        tk.Frame.__init__(self, parent)
        self.controller = controller


class Reports(tk.Frame):
    """
    Displays user and combined statistics for all clients
    """

    def __init__(self, parent, controller, **app_data):
        self.parent = parent
        tk.Frame.__init__(self, parent, background='white')
        self.controller = controller
        self.activeW = app_data['activeW']
        self.activeW.trace('w', self.observer)

        # variables
        self.pvf_user_months = tk.StringVar()
        self.pvf_ven_dateA = tk.StringVar()
        self.pvf_ven_dateB = tk.StringVar()
        self.pvf_err_dateA = tk.StringVar()
        self.pvf_err_dateB = tk.StringVar()

        # configure layout
        self.rowconfigure(0, minsize=10)
        self.rowconfigure(6, minsize=10)
        self.rowconfigure(8, minsize=10)
        self.columnconfigure(0, minsize=10)
        self.columnconfigure(6, minsize=10)

        self.helpBtn = ttk.Button(
            self,
            text='help',
            command=self.help,
            cursor='hand2',
            width=15)
        self.helpBtn.grid(
            row=7, column=2, sticky='sw')

        self.closeBtn = ttk.Button(
            self,
            text='close',
            command=lambda: controller.show_frame('Main'),
            cursor='hand2',
            width=15)
        self.closeBtn.grid(
            row=7, column=4, sticky='sw')

        self.mainFrm = ttk.LabelFrame(
            self,
            text='reports')
        self.mainFrm.grid(
            row=1, column=1, rowspan=5, columnspan=5, sticky='snew')

        self.yscrollbar = tk.Scrollbar(self.mainFrm, orient=tk.VERTICAL)
        self.yscrollbar.grid(
            row=0, column=10, rowspan=10, sticky='nse', padx=2)
        self.base = tk.Canvas(
            self.mainFrm, bg='white',
            width=720,
            height=400,
            yscrollcommand=self.yscrollbar.set)
        self.base.grid(
            row=0, column=0, columnspan=10, rowspan=10)

        self.baseFrm = tk.Frame(
            self.base)
        self.yscrollbar.config(command=self.base.yview)
        self.base.create_window(
            (0, 0), window=self.baseFrm, anchor="nw",
            tags="self.baseFrm")
        self.baseFrm.bind("<Configure>", self.onFrameConfigure)

        self.pvfFrm = ttk.LabelFrame(
            self.baseFrm,
            text='processing vendor files user stats')
        self.pvfFrm.grid(
            row=0, column=0, columnspan=10, sticky='snew', padx=10, pady=10)
        self.pvfFrm.rowconfigure(0, minsize=10)
        self.pvfFrm.columnconfigure(4, minsize=200)
        self.pvfFrm.rowconfigure(4, minsize=10)

        # user monthly usage stats
        ttk.Label(self.pvfFrm, text='user stats: ').grid(
            row=1, column=0, sticky='nsw', padx=5, pady=5)

        self.userReportCbx = ttk.Combobox(
            self.pvfFrm,
            textvariable=self.pvf_user_months,
            width=20)
        self.userReportCbx.grid(
            row=1, column=1, sticky='nsw', padx=5, pady=10)

        self.pvf_openUserRepBtn = ttk.Button(
            self.pvfFrm,
            text='open',
            command=self.pvf_user_report,
            cursor='hand2',
            width=10)
        self.pvf_openUserRepBtn.grid(
            row=1, column=2, sticky='sw', padx=5, pady=5)

        ttk.Label(self.pvfFrm, text='vendor stats: ').grid(
            row=2, column=0, sticky='nsw', padx=5, pady=5)

        # vendor combined reports
        self.ven_dateAReportCbx = ttk.Combobox(
            self.pvfFrm,
            textvariable=self.pvf_ven_dateA,
            width=20)
        self.ven_dateAReportCbx.grid(
            row=2, column=1, sticky='nsw', padx=5, pady=10)
        self.ven_dateBReportCbx = ttk.Combobox(
            self.pvfFrm,
            textvariable=self.pvf_ven_dateB,
            width=20)
        self.ven_dateBReportCbx.grid(
            row=2, column=2, sticky='nsw', padx=5, pady=10)
        self.pvf_openVenRepBtn = ttk.Button(
            self.pvfFrm,
            text='open',
            command=self.pvf_vendor_report,
            cursor='hand2',
            width=10)
        self.pvf_openVenRepBtn.grid(
            row=2, column=3, sticky='sw', padx=5, pady=5)

        # error combined reports
        ttk.Label(self.pvfFrm, text='error stats: ').grid(
            row=3, column=0, sticky='nsw', padx=5, pady=5)
        self.err_dateAReportCbx = ttk.Combobox(
            self.pvfFrm,
            textvariable=self.pvf_err_dateA,
            width=20)
        self.err_dateAReportCbx.grid(
            row=3, column=1, sticky='nsw', padx=5, pady=10)
        self.err_dateBReportCbx = ttk.Combobox(
            self.pvfFrm,
            textvariable=self.pvf_err_dateB,
            width=20)
        self.err_dateBReportCbx.grid(
            row=3, column=2, sticky='nsw', padx=5, pady=10)
        self.pvf_openErrRepBtn = ttk.Button(
            self.pvfFrm,
            text='open',
            command=self.pvf_error_report,
            cursor='hand2',
            width=10)
        self.pvf_openErrRepBtn.grid(
            row=3, column=3, sticky='sw', padx=5, pady=5)

    def onFrameConfigure(self, event):
        self.base.config(scrollregion=self.base.bbox('all'))

    def report_display(self):
        self.repTop = tk.Toplevel(self, background='white')
        self.repTop.iconbitmap('./icons/report.ico')
        self.repTop.title('Vendor files report')

        self.repTop.columnconfigure(0, minsize=10)
        self.repTop.columnconfigure(1, minsize=750)
        self.repTop.columnconfigure(11, minsize=10)
        self.repTop.rowconfigure(0, minsize=10)
        self.repTop.rowconfigure(1, minsize=450)
        self.repTop.rowconfigure(11, minsize=10)
        self.repTop.rowconfigure(13, minsize=10)

        self.yscrollbarD = tk.Scrollbar(self.repTop, orient=tk.VERTICAL)
        self.yscrollbarD.grid(
            row=1, column=10, rowspan=9, sticky='nse', padx=2)
        self.xscrollbarD = tk.Scrollbar(self.repTop, orient=tk.HORIZONTAL)
        self.xscrollbarD.grid(
            row=10, column=1, columnspan=9, sticky='swe')

        self.reportTxt = tk.Text(
            self.repTop,
            borderwidth=0,
            wrap=tk.NONE,
            yscrollcommand=self.yscrollbarD.set,
            xscrollcommand=self.xscrollbarD.set)
        self.reportTxt.grid(
            row=1, column=1, rowspan=9, columnspan=9, sticky='snew')
        self.reportTxt.tag_config('blue', foreground='blue', underline=1)
        self.reportTxt.tag_config('red', foreground='red')

        self.yscrollbarD.config(command=self.reportTxt.yview)
        self.xscrollbarD.config(command=self.reportTxt.xview)

        ttk.Button(
            self.repTop,
            text='close',
            width=12,
            cursor='hand2',
            command=self.repTop.destroy).grid(
            row=12, column=6, sticky='nw', padx=5)

    def pvf_user_report(self):
        overload_logger.debug(
            'Displaying user reports')
        month = self.pvf_user_months.get()
        if month == '':
            m = 'plase select month to display user stats'
            tkMessageBox.showwarning('Input Error', m)
        else:
            self.report_display()
            start_date = datetime.datetime.strptime(month, "%Y-%m").date()
            days_in_month = calendar.monthrange(
                start_date.year, start_date.month)[1]
            end_date = start_date + datetime.timedelta(days=days_in_month)
            nypl_stats = cumulative_nypl_stats(start_date, end_date)
            nypl_branch_stats = nypl_stats[0]
            nypl_research_stats = nypl_stats[1]
            self.reportTxt.insert(
                tk.END, 'Report for period from {} to {}\n'.format(
                    start_date, end_date))
            self.reportTxt.insert(
                tk.END, 'NYPL\n', 'red')
            self.reportTxt.insert(
                tk.END, 'Branches vendor breakdown:\n', 'blue')
            self.reportTxt.insert(
                tk.END, nypl_branch_stats.to_string(index=False) + '\n')
            self.reportTxt.insert(
                tk.END, 'Research vendor breakdown:\n', 'blue')
            self.reportTxt.insert(
                tk.END, nypl_research_stats.to_string(index=False) + '\n')
            self.reportTxt.insert(tk.END, '\n' + ('-' * 60) + '\n')
            self.reportTxt.insert(
                tk.END, 'BPL\n', 'red')
            self.reportTxt.insert(tk.END, 'Vendor breakdown:\n', 'blue')
            bpl_stats = cumulative_bpl_stats(start_date, end_date)
            self.reportTxt.insert(
                tk.END, bpl_stats.to_string(index=False) + '\n')

    def pvf_vendor_report(self):
        overload_logger.debug(
            'Displaying vendor reports')
        start_month = self.pvf_ven_dateA.get()
        end_month = self.pvf_ven_dateB.get()
        if start_month == '' or end_month == '':
            m = 'Please select start and end month\nto display vendor stats.'
            tkMessageBox.showwarning('Input Error', m)
        else:
            # summon the widget
            self.report_display()

            # parse start and end dates
            start_date = datetime.datetime.strptime(
                start_month, "%Y-%m").date()
            end_date = datetime.datetime.strptime(
                end_month, "%Y-%m").date()
            days_in_month = calendar.monthrange(
                end_date.year, end_date.month)[1]
            end_date = end_date + datetime.timedelta(days=days_in_month)

            # get dataframes for specified time period
            nbdf, nrdf, bdf = cumulative_vendor_stats(start_date, end_date)

            # enter stats into widget
            self.reportTxt.insert(
                tk.END, 'Report for period from {} to {}\n'.format(
                    start_date, end_date))
            self.reportTxt.insert(
                tk.END, 'NYPL\n', 'red')
            self.reportTxt.insert(
                tk.END, 'Branches vendor breakdown:\n', 'blue')
            self.reportTxt.insert(
                tk.END, nbdf.to_string(index=False) + '\n')
            self.reportTxt.insert(
                tk.END, 'Research vendor breakdown:\n', 'blue')
            self.reportTxt.insert(
                tk.END, nrdf.to_string(index=False) + '\n')
            self.reportTxt.insert(tk.END, '\n' + ('-' * 60) + '\n')
            self.reportTxt.insert(
                tk.END, 'BPL\n', 'red')
            self.reportTxt.insert(tk.END, 'Vendor breakdown:\n', 'blue')
            self.reportTxt.insert(
                tk.END, bdf.to_string(index=False) + '\n')

    def pvf_error_report(self):
        m = 'Functionality not ready yet. Error reports are being developed'
        tkMessageBox.showinfo('Under construction...', m)

    def help(self):
        m = 'help not available yet...'
        tkMessageBox.showinfo('Under construction...', m)

    def reset(self):
        self.pvf_user_months.set('')
        self.pvf_ven_dateA.set('')
        self.pvf_ven_dateB.set('')
        self.pvf_err_dateA.set('')
        self.pvf_err_dateB.set('')

    def observer(self, *args):
        if self.activeW.get() == 'Reports':
            # reset variables
            self.reset()

            # find out date values for PFV report
            with session_scope() as session:
                records = retrieve_values(session, PVR_Batch, 'timestamp')
                values = list(
                    set([record.timestamp[:7] for record in records]))
            self.userReportCbx['values'] = values
            self.userReportCbx['state'] = 'readonly'
            self.ven_dateAReportCbx['values'] = values
            self.ven_dateAReportCbx['state'] = 'readonly'
            self.ven_dateBReportCbx['values'] = values
            self.ven_dateBReportCbx['state'] = 'readonly'


class Settings(tk.Frame):
    """sets default folders, Z3950 settings, and OCLC API credentials"""

    def __init__(self, parent, controller, **app_data):
        self.parent = parent
        tk.Frame.__init__(self, parent, background='white')
        self.controller = controller

        self.rowconfigure(0, minsize=25)
        self.rowconfigure(2, minsize=10)
        self.rowconfigure(4, minsize=200)
        self.rowconfigure(10, minsize=25)
        self.columnconfigure(0, minsize=30)
        self.columnconfigure(2, minsize=20)
        self.columnconfigure(4, minsize=20)
        self.columnconfigure(8, minsize=50)
        self.columnconfigure(10, minsize=30)

        foldersICO = tk.PhotoImage(file='./icons/folders.gif')
        self.defaultDirBtn = ttk.Button(
            self, image=foldersICO,
            text='default directories',
            compound=tk.TOP,
            cursor='hand2',
            width=15,
            command=lambda: controller.show_frame('DefaultDirs'))
        # prevent image to be garbage collected by Python
        self.defaultDirBtn.image = foldersICO
        self.defaultDirBtn.grid(
            row=1, column=1, sticky='snew')

        apiICO = tk.PhotoImage(file='./icons/remoteDB.gif')

        self.platform_apiBtn = ttk.Button(
            self, image=apiICO,
            text='Platform APIs',
            compound=tk.TOP,
            cursor='hand2',
            width=15,
            command=lambda: controller.show_frame('PlatformAPIs'))

        self.platform_apiBtn.image = apiICO
        self.platform_apiBtn.grid(
            row=1, column=3, sticky='snew')

        gooICO = tk.PhotoImage(file='./icons/key-lock.gif')

        self.goo_apiBtn = ttk.Button(
            self, image=gooICO,
            text='Google APIs',
            compound=tk.TOP,
            cursor='hand2',
            width=15,
            command=lambda: controller.show_frame('GooAPI'))

        self.goo_apiBtn.image = gooICO
        self.goo_apiBtn.grid(
            row=1, column=5, sticky='snew')

        self.sierra_apiBtn = ttk.Button(
            self, image=apiICO,
            text='Z950s',
            compound=tk.TOP,
            cursor='hand2',
            width=15,
            command=lambda: controller.show_frame('Z3950s'))
        self.sierra_apiBtn.image = apiICO
        self.sierra_apiBtn.grid(
            row=3, column=1, sticky='snew')

        self.sierra_apiBtn = ttk.Button(
            self, image=apiICO,
            text='Sierra APIs',
            compound=tk.TOP,
            cursor='hand2',
            width=15,
            command=lambda: controller.show_frame('SierraAPIs'))

        self.sierra_apiBtn.image = apiICO
        self.sierra_apiBtn.grid(
            row=3, column=3, sticky='snew')

        self.closeBtn = ttk.Button(
            self, text='close',
            cursor='hand2',
            width=15,
            command=lambda: controller.show_frame('Main'))
        self.closeBtn.grid(
            row=5, column=1, sticky='sew')


class SierraAPIs(tk.Frame):

    """records Sierra API settings for both libraries"""

    def __init__(self, parent, controller, **app_data):
        self.parent = parent
        tk.Frame.__init__(self, parent, background='white')
        self.controller = controller
        self.activeW = app_data['activeW']
        self.activeW.trace('w', self.observer)

        # widget variables
        self.conn_name = tk.StringVar()
        self.conn_name.trace('w', self.populate_form)
        self.host = tk.StringVar()
        self.client_id = tk.StringVar()
        self.client_secret = tk.StringVar()
        self.library = tk.StringVar()

        # configure layout
        self.rowconfigure(0, minsize=25)
        self.rowconfigure(2, minsize=10)
        self.rowconfigure(10, minsize=25)
        self.columnconfigure(0, minsize=20)
        self.columnconfigure(2, minsize=20)
        self.columnconfigure(4, minsize=20)

        # settings frame
        self.baseFrm = ttk.LabelFrame(self, text='API settings')
        self.baseFrm.grid(
            row=1, column=1, rowspan=6, sticky='snew')
        self.baseFrm.rowconfigure(0, minsize=2)
        self.baseFrm.rowconfigure(2, minsize=2)
        self.baseFrm.rowconfigure(4, minsize=2)
        self.baseFrm.rowconfigure(6, minsize=2)
        self.baseFrm.rowconfigure(8, minsize=2)
        self.baseFrm.rowconfigure(10, minsize=2)

        # entry widgets
        self.conn_nameCbx = ttk.Combobox(
            self.baseFrm,
            textvariable=self.conn_name,
            width=50)
        self.conn_nameCbx.grid(
            row=1, column=0, sticky='new')

        self.libraryCbx = ttk.Combobox(
            self.baseFrm,
            textvariable=self.library,
            value=['BPL', 'NYPL'],
            width=50)
        self.libraryCbx.grid(
            row=3, column=0, sticky='new')

        self.hostEnt = ttk.Entry(
            self.baseFrm,
            textvariable=self.host,
            width=50)
        self.hostEnt.grid(
            row=7, column=0, sticky='new')

        self.client_idEnt = ttk.Entry(
            self.baseFrm,
            textvariable=self.client_id,
            show='*',
            width=50)
        self.client_idEnt.grid(
            row=9, column=0, sticky='new')

        self.client_secretEnt = ttk.Entry(
            self.baseFrm,
            textvariable=self.client_secret,
            show='*',
            width=50)
        self.client_secretEnt.grid(
            row=11, column=0, sticky='new')

        # label widgets

        self.conn_nameLbl = ttk.Label(
            self.baseFrm,
            text='connection name',
            width=20)
        self.conn_nameLbl.grid(
            row=1, column=2, sticky='new')

        self.libraryLbl = ttk.Label(
            self.baseFrm,
            text='library',
            width=20)
        self.libraryLbl.grid(
            row=3, column=2, sticky='new')

        self.hostLbl = ttk.Label(
            self.baseFrm,
            text='API base URL',
            width=20)
        self.hostLbl.grid(
            row=7, column=2, sticky='new')

        self.databaseLbl = ttk.Label(
            self.baseFrm,
            text='client id',
            width=20)
        self.databaseLbl.grid(
            row=9, column=2, sticky='new')

        self.portLbl = ttk.Label(
            self.baseFrm,
            text='client secret',
            width=20)
        self.portLbl.grid(
            row=11, column=2, sticky='new')

        # right menu buttons

        self.saveBtn = ttk.Button(
            self, text='save',
            width=15,
            command=self.save)
        self.saveBtn.grid(
            row=3, column=3, sticky='new')

        self.helpBtn = ttk.Button(
            self, text='help',
            width=15,
            command=self.help)
        self.helpBtn.grid(
            row=4, column=3, sticky='new')

        self.deleteBtn = ttk.Button(
            self, text='delete',
            width=15,
            command=self.delete)
        self.deleteBtn.grid(
            row=5, column=3, sticky='new')

        self.closeBtn = ttk.Button(
            self, text='close',
            width=15,
            command=lambda: controller.show_frame('Settings'))
        self.closeBtn.grid(
            row=6, column=3, sticky='new')

    def save(self):
        # validate data
        self.stop_tracer = True
        valid_results = self.validate()
        correct = valid_results[0]
        new_conn_name = self.conn_name.get()

        if correct:
            if self.client_id.get() == '' or \
                    self.client_id.get() == 'None':
                client_id = None
            else:
                client_id = self.client_id.get()
            encoded_client_id = base64.b64encode(client_id)
            if self.client_secret.get() == '' or \
                    self.client_secret.get() == 'None':
                client_secret = None
            else:
                client_secret = self.client_secret.get()

            new_conn = dict(
                host=self.host.get(),
                client_id=encoded_client_id,
                library=self.library.get(),
                method='SierraAPI')

            user_data = shelve.open(USER_DATA, writeback=True)
            if 'SierraAPIs' in user_data:
                APIs = user_data['SierraAPIs']
            else:
                user_data['SierraAPIs'] = {}
                APIs = user_data['SierraAPIs']
            APIs[new_conn_name] = new_conn
            user_data.close()

            # store critical data in Windows Vault
            credentials.standard_to_vault(
                self.host.get(), client_id, client_secret)

            tkMessageBox.showinfo('Input', 'Settings have been saved')
            self.observer()

        else:
            m = valid_results[1]
            tkMessageBox.showerror('Input error', m)

    def help(self):
        info = 'Please contact your ILS administrator for the\n' \
               'details of API settings.\n' \
               'Please note,\n' \
               'you will need Sierra API authorization, that \n' \
               'includes client id and client secret to use this\n' \
               'feature.'
        tkMessageBox.showinfo('help', info)

    def validate(self):
        m = ''
        correct = True

        conn_name = self.conn_name.get()
        self.conn_name.set(conn_name.strip())

        if conn_name == '':
            m += 'connection name field cannot be empty\n'
            correct = False
        if len(conn_name) > 50:
            m += 'connection name cannot be longer than 50 characters\n'
            correct = False

        host = self.host.get().strip()
        p = re.compile(
            r'https://[a-z].*\.[com|org]/iii/sierra-api/v\d|', re.IGNORECASE)

        if not p.match(host):
            m += 'API URL appears to be invalid\n'
            correct = False

        client_id = self.client_id.get().strip()
        if client_id == '':
            m += 'cliend id field cannot be empty\n'
            correct = False

        client_secret = self.client_secret.get().strip()
        if client_secret == '':
            m += 'client secret field cannot be empty\n'
            correct = False

        if self.library.get() == '':
            m += 'missing library field\n'
            correct = False

        self.host.set(host)
        self.client_id.set(client_id)
        self.client_secret.set(client_secret)

        return (correct, m)

    def delete(self):
        if self.conn_name.get() == '':
            m = 'please select connection for deletion'
            tkMessageBox.showerror('Input error', m)
        else:
            if tkMessageBox.askokcancel('Deletion', 'delete connection?'):
                user_data = shelve.open(USER_DATA, writeback=True)
                conn = user_data['SierraAPIs'][self.conn_name.get()]

                # delete from Windows Vault
                keyring.delete_password(
                    conn['host'],
                    base64.b64decode(conn['client_id']))

                # delete from user_data
                user_data['SierraAPIs'].pop(self.conn_name.get(), None)
                user_data.close()
                # update indexes & reset to blank form
                self.observer()

    def reset_form(self):
        self.conn_name.set('')
        self.library.set('')
        self.host.set('')
        self.client_id.set('')
        self.client_secret.set('')
        self.stop_tracer = False

    def populate_form(self, *args):
        if self.conn_name.get() != '' and \
                self.stop_tracer is False:
            user_data = shelve.open(USER_DATA)
            try:
                conn = user_data['SierraAPIs'][self.conn_name.get()]
                self.library.set(conn['library'])
                self.host.set(conn['host'])
                self.client_id.set(base64.b64decode(conn['client_id']))
                self.client_secret.set(
                    credentials.get_from_vault(
                        conn['host'],
                        base64.b64decode(conn['client_id'])))
            except KeyError:
                pass
            finally:
                user_data.close()

    def observer(self, *args):
        if self.activeW.get() == 'SierraAPIs':
            self.stop_tracer = False
            self.reset_form()
            user_data = shelve.open(USER_DATA)
            if 'SierraAPIs' in user_data:
                if len(user_data['SierraAPIs']) > 0:
                    APIs = user_data['SierraAPIs']
                    conn_names = []
                    for name in APIs.iterkeys():
                        conn_names.append(name)
                    self.conn_nameCbx['value'] = sorted(conn_names)
            user_data.close()


class PlatformAPIs(tk.Frame):

    """records NYPL PLatform API settings"""

    def __init__(self, parent, controller, **app_data):
        self.parent = parent
        tk.Frame.__init__(self, parent, background='white')
        self.controller = controller
        self.activeW = app_data['activeW']
        self.activeW.trace('w', self.observer)

        # widget variables
        self.conn_name = tk.StringVar()
        self.conn_name.trace('w', self.populate_form)
        self.oauth_server = tk.StringVar()
        self.host = tk.StringVar()
        self.client_id = tk.StringVar()
        self.client_secret = tk.StringVar()

        # configure layout
        self.rowconfigure(0, minsize=25)
        self.rowconfigure(2, minsize=10)
        self.rowconfigure(10, minsize=25)
        self.columnconfigure(0, minsize=20)
        self.columnconfigure(2, minsize=20)
        self.columnconfigure(4, minsize=20)

        # settings frame
        self.baseFrm = ttk.LabelFrame(self, text='Platform API settings')
        self.baseFrm.grid(
            row=1, column=1, rowspan=6, sticky='snew')
        self.baseFrm.rowconfigure(0, minsize=2)
        self.baseFrm.rowconfigure(2, minsize=2)
        self.baseFrm.rowconfigure(4, minsize=2)
        self.baseFrm.rowconfigure(6, minsize=2)
        self.baseFrm.rowconfigure(8, minsize=2)
        self.baseFrm.rowconfigure(10, minsize=2)

        # entry widgets
        self.conn_nameCbx = ttk.Combobox(
            self.baseFrm,
            textvariable=self.conn_name,
            width=50)
        self.conn_nameCbx.grid(
            row=1, column=0, sticky='new')

        self.oauth_serverEnt = ttk.Entry(
            self.baseFrm,
            textvariable=self.oauth_server,
            width=50)
        self.oauth_serverEnt.grid(
            row=3, column=0, sticky='new')

        self.hostEnt = ttk.Entry(
            self.baseFrm,
            textvariable=self.host,
            width=50)
        self.hostEnt.grid(
            row=7, column=0, sticky='new')

        self.client_idEnt = ttk.Entry(
            self.baseFrm,
            textvariable=self.client_id,
            show='*',
            width=50)
        self.client_idEnt.grid(
            row=9, column=0, sticky='new')

        self.client_secretEnt = ttk.Entry(
            self.baseFrm,
            textvariable=self.client_secret,
            show='*',
            width=50)
        self.client_secretEnt.grid(
            row=11, column=0, sticky='new')

        # label widgets

        self.conn_nameLbl = ttk.Label(
            self.baseFrm,
            text='connection name',
            width=20)
        self.conn_nameLbl.grid(
            row=1, column=2, sticky='new')

        self.oauth_serverLbl = ttk.Label(
            self.baseFrm,
            text='authorization server',
            width=20)
        self.oauth_serverLbl.grid(
            row=3, column=2, sticky='new')

        self.hostLbl = ttk.Label(
            self.baseFrm,
            text='API base URL',
            width=20)
        self.hostLbl.grid(
            row=7, column=2, sticky='new')

        self.databaseLbl = ttk.Label(
            self.baseFrm,
            text='client id',
            width=20)
        self.databaseLbl.grid(
            row=9, column=2, sticky='new')

        self.portLbl = ttk.Label(
            self.baseFrm,
            text='client secret',
            width=20)
        self.portLbl.grid(
            row=11, column=2, sticky='new')

        # right menu buttons

        self.saveBtn = ttk.Button(
            self, text='save',
            width=15,
            command=self.save)
        self.saveBtn.grid(
            row=3, column=3, sticky='new')

        self.helpBtn = ttk.Button(
            self, text='help',
            width=15,
            command=self.help)
        self.helpBtn.grid(
            row=4, column=3, sticky='new')

        self.deleteBtn = ttk.Button(
            self, text='delete',
            width=15,
            command=self.delete)
        self.deleteBtn.grid(
            row=5, column=3, sticky='new')

        self.closeBtn = ttk.Button(
            self, text='close',
            width=15,
            command=lambda: controller.show_frame('Settings'))
        self.closeBtn.grid(
            row=6, column=3, sticky='new')

    def save(self):
        # validate data
        self.stop_tracer = True
        valid_results = self.validate()
        correct = valid_results[0]
        new_conn_name = self.conn_name.get()
        overload_logger.debug(
            'Saving new Platform API settings under name {}'.format(
                new_conn_name))

        if correct:
            if self.oauth_server.get() == '' or \
                    self.oauth_server.get() == 'None':
                oauth_server = None
            else:
                oauth_server = self.oauth_server.get().strip()
            if self.client_id.get() == '' or \
                    self.client_id.get() == 'None':
                client_id = None
            else:
                client_id = self.client_id.get()
            encoded_client_id = base64.b64encode(client_id)
            if self.client_secret.get() == '' or \
                    self.client_secret.get() == 'None':
                client_secret = None
            else:
                client_secret = self.client_secret.get()

            # save info in shelf
            new_conn = dict(
                oauth_server=oauth_server,
                host=self.host.get(),
                client_id=encoded_client_id,
                last_token=None,
                method='Platform API',
                library='NYPL')

            user_data = shelve.open(USER_DATA, writeback=True)
            if 'PlatformAPIs' in user_data:
                APIs = user_data['PlatformAPIs']
            else:
                user_data['PlatformAPIs'] = {}
                APIs = user_data['PlatformAPIs']
            APIs[new_conn_name] = new_conn
            user_data.close()

            # store critical data in Windows Vault
            credentials.standard_to_vault(
                oauth_server, client_id, client_secret)

            tkMessageBox.showinfo('Input', 'Settings have been saved')
            self.observer()

        else:
            m = valid_results[1]
            tkMessageBox.showerror('Input error', m)

    def help(self):
        info = 'Please contact your ILS administrator for the\n' \
               'details of API settings.\n' \
               'Please note,\n' \
               'you will need Platform API authorization, that \n' \
               'includes client id and client secret to use this\n' \
               'feature.'
        tkMessageBox.showinfo('help', info)

    def validate(self):
        m = ''
        correct = True

        conn_name = self.conn_name.get()
        self.conn_name.set(conn_name.strip())

        if conn_name == '':
            m += 'connection name field cannot be empty\n'
            correct = False
        if len(conn_name) > 50:
            m += 'connection name cannot be longer than 50 characters\n'
            correct = False

        self.oauth_server.set(self.oauth_server.get().strip())
        if self.oauth_server.get() == '':
            m += 'authorization server info is required\n'
            correct = False

        self.host.set(self.host.get().strip())
        host = self.host.get().strip()
        p = re.compile(
            r'https://[a-z].*\.org/api/v\d\.\d', re.IGNORECASE)

        if not p.match(host):
            m += 'API URL appears to be invalid\n'
            correct = False

        self.client_id.set(self.client_id.get().strip())
        client_id = self.client_id.get().strip()
        if client_id == '':
            m += 'cliend id field is required\n'
            correct = False

        self.client_secret.set(self.client_secret.get().strip())
        client_secret = self.client_secret.get().strip()
        if client_secret == '':
            m += 'client secret field is required\n'
            correct = False

        overload_logger.debug(
            'Validation of entered Platform API settings. '
            'Correct: {}, errors: {}'.format(
                correct, m))
        return (correct, m)

    def delete(self):
        if self.conn_name.get() == '':
            m = 'please select connection for deletion'
            tkMessageBox.showerror('Input error', m)
        else:
            if tkMessageBox.askokcancel('Deletion', 'delete connection?'):
                user_data = shelve.open(USER_DATA, writeback=True)

                # delete creds from Windows Vault
                conn = user_data['PlatformAPIs'][self.conn_name.get()]
                keyring.delete_password(
                    conn['oauth_server'],
                    base64.b64decode(conn['client_id']))

                # delete from user_data
                user_data['PlatformAPIs'].pop(self.conn_name.get(), None)
                user_data.close()
                # update indexes & reset to blank form
                self.observer()

    def reset_form(self):
        self.conn_name.set('')
        self.oauth_server.set('')
        self.host.set('')
        self.client_id.set('')
        self.client_secret.set('')
        self.stop_tracer = False

    def populate_form(self, *args):
        if self.conn_name.get() != '' and \
                self.stop_tracer is False:
            user_data = shelve.open(USER_DATA)
            try:
                conn = user_data['PlatformAPIs'][self.conn_name.get()]
                self.oauth_server.set(conn['oauth_server'])
                self.host.set(conn['host'])
                self.client_id.set(base64.b64decode(conn['client_id']))
                # retrieve secret from Windows Vault
                secret = credentials.get_from_vault(
                    self.oauth_server.get(),
                    self.client_id.get())
                self.client_secret.set(secret)
            except KeyError:
                pass
            finally:
                user_data.close()

    def observer(self, *args):
        if self.activeW.get() == 'PlatformAPIs':
            self.stop_tracer = False
            self.reset_form()
            user_data = shelve.open(USER_DATA)
            if 'PlatformAPIs' in user_data:
                if len(user_data['PlatformAPIs']) > 0:
                    APIs = user_data['PlatformAPIs']
                    conn_names = []
                    for name in APIs.iterkeys():
                        conn_names.append(name)
                    self.conn_nameCbx['value'] = sorted(conn_names)
            user_data.close()


class Z3950s(tk.Frame):
    """records Sierra Z3950 settings for both libraries"""

    def __init__(self, parent, controller, **app_data):
        self.parent = parent
        tk.Frame.__init__(self, parent, background='white')
        self.controller = controller
        self.activeW = app_data['activeW']
        self.activeW.trace('w', self.observer)

        # widget variables
        self.conn_name = tk.StringVar()
        self.conn_name.trace('w', self.populate_form)
        self.host = tk.StringVar()
        self.database = tk.StringVar()
        self.port = tk.StringVar()
        self.username = tk.StringVar()
        self.password = tk.StringVar()
        self.syntax = tk.StringVar()
        self.library = tk.StringVar()

        self.rowconfigure(0, minsize=25)
        self.rowconfigure(2, minsize=10)
        self.rowconfigure(10, minsize=25)
        self.columnconfigure(0, minsize=20)
        self.columnconfigure(2, minsize=20)
        self.columnconfigure(4, minsize=20)

        # settings frame
        self.baseFrm = ttk.LabelFrame(self, text='Z3950 settings')
        self.baseFrm.grid(
            row=1, column=1, rowspan=6, sticky='snew')
        self.baseFrm.columnconfigure(1, minsize=5)

        # entry widgets

        self.conn_nameCbx = ttk.Combobox(
            self.baseFrm,
            textvariable=self.conn_name,
            width=35)
        self.conn_nameCbx.grid(
            row=0, column=0, sticky='new')

        self.libraryCbx = ttk.Combobox(
            self.baseFrm,
            textvariable=self.library,
            value=['BPL', 'NYPL'],
            width=35)
        self.libraryCbx.grid(
            row=1, column=0, sticky='new')

        self.hostEnt = ttk.Entry(
            self.baseFrm,
            textvariable=self.host,
            width=35)
        self.hostEnt.grid(
            row=2, column=0, sticky='new')

        self.databaseEnt = ttk.Entry(
            self.baseFrm,
            textvariable=self.database,
            width=35)
        self.databaseEnt.grid(
            row=3, column=0, sticky='new')

        self.portEnt = ttk.Entry(
            self.baseFrm,
            textvariable=self.port,
            width=35)
        self.portEnt.grid(
            row=4, column=0, sticky='new')

        self.usernameEnt = ttk.Entry(
            self.baseFrm,
            textvariable=self.username,
            width=35)
        self.usernameEnt.grid(
            row=5, column=0, sticky='new')

        self.passwordEnt = ttk.Entry(
            self.baseFrm,
            textvariable=self.password,
            show='*',
            width=35)
        self.passwordEnt.grid(
            row=6, column=0, sticky='new')

        self.syntaxCbx = ttk.Combobox(
            self.baseFrm,
            values=('USMARC', 'MARC21', 'XML'),
            textvariable=self.syntax,
            width=35)
        self.syntaxCbx.grid(
            row=7, column=0, sticky='new')
        self.syntax.set('MARC21')

        # entry widgets' labels

        self.conn_nameLbl = ttk.Label(
            self.baseFrm,
            text='connection name',
            width=20)
        self.conn_nameLbl.grid(
            row=0, column=2, sticky='new')

        self.libraryLbl = ttk.Label(
            self.baseFrm,
            text='library',
            width=20)
        self.libraryLbl.grid(
            row=1, column=2, sticky='new')

        self.hostLbl = ttk.Label(
            self.baseFrm,
            text='host or IP address',
            width=20)
        self.hostLbl.grid(
            row=2, column=2, sticky='new')

        self.databaseLbl = ttk.Label(
            self.baseFrm,
            text='database',
            width=20)
        self.databaseLbl.grid(
            row=3, column=2, sticky='new')

        self.portLbl = ttk.Label(
            self.baseFrm,
            text='port',
            width=20)
        self.portLbl.grid(
            row=4, column=2, sticky='new')

        self.usernameLbl = ttk.Label(
            self.baseFrm,
            text='username',
            width=20)
        self.usernameLbl.grid(
            row=5, column=2, sticky='new')

        self.passwordLbl = ttk.Label(
            self.baseFrm,
            text='password',
            width=20)
        self.passwordLbl.grid(
            row=6, column=2, sticky='new')

        self.syntaxLbl = ttk.Label(
            self.baseFrm,
            text='synax',
            width=20)
        self.syntaxLbl.grid(
            row=7, column=2, sticky='new')

        # right menu buttons
        self.saveBtn = ttk.Button(
            self, text='save',
            width=15,
            command=self.save)
        self.saveBtn.grid(
            row=3, column=3, sticky='new')

        self.helpBtn = ttk.Button(
            self, text='help',
            width=15,
            command=self.help)
        self.helpBtn.grid(
            row=4, column=3, sticky='new')

        self.deleteBtn = ttk.Button(
            self, text='delete',
            width=15,
            command=self.delete)
        self.deleteBtn.grid(
            row=5, column=3, sticky='new')

        self.closeBtn = ttk.Button(
            self, text='close',
            width=15,
            command=lambda: controller.show_frame('Settings'))
        self.closeBtn.grid(
            row=6, column=3, sticky='new')

    def save(self):
        # validate data
        self.stop_tracer = True
        valid_results = self.validate()
        correct = valid_results[0]
        new_conn_name = self.conn_name.get()

        if correct:
            if self.username.get() == '' or \
                    self.username.get() == 'None':
                user = None
            else:
                user = self.username.get()
            if self.password.get() == '' or \
                    self.password.get() == 'None':
                password = None
            else:
                password = self.password.get()

            new_conn = dict(
                host=self.host.get(),
                database=self.database.get(),
                port=int(self.port.get()),
                user=user,
                password=password,
                syntax=self.syntax.get(),
                library=self.library.get(),
                method='Z3950')

            user_data = shelve.open(USER_DATA, writeback=True)
            if 'Z3950s' in user_data:
                Z3950s = user_data['Z3950s']
            else:
                user_data['Z3950s'] = {}
                Z3950s = user_data['Z3950s']
            Z3950s[new_conn_name] = new_conn
            user_data.close()
            tkMessageBox.showinfo('Input', 'Settings have been saved')
            self.observer()

        else:
            m = valid_results[1]
            tkMessageBox.showerror('Input error', m)

    def help(self):
        info = 'Please contact your ILS administrator for the\n' \
               'details of Z3950 settings.\n' \
               'Please note,\n' \
               'OpsUtils tools use USMARC syntax by default.'
        tkMessageBox.showinfo('help', info)

    def delete(self):
        if self.conn_name.get() == '':
            m = 'please select connection for deletion'
            tkMessageBox.showerror('Input error', m)
        else:
            if tkMessageBox.askokcancel('Deletion', 'delete connection?'):
                user_data = shelve.open(USER_DATA, writeback=True)
                user_data['Z3950s'].pop(self.conn_name.get(), None)
                user_data.close()
                # update indexes & reset to blank form
                self.observer()
                self.reset_form()

    def validate(self):
        m = ''
        correct = True

        conn_name = self.conn_name.get()
        self.conn_name.set(conn_name.strip())
        if conn_name == '':
            m += 'connection name field cannot be empty\n'
            correct = False
        if len(conn_name) > 50:
            m += 'connection name cannot be longer than 50 characters\n'
            correct = False

        host = self.host.get()
        self.host.set(host.strip())
        if '.' not in host:
            m += 'host name appears to be incorrect\n'
            correct = False

        database = self.database.get()
        self.database.set(database.strip())
        if database == '':
            m += 'database field cannot be empty\n'
            correct = False

        port = self.port.get()
        self.port.set(port.strip())
        if port == '':
            m += 'port field cannot be empty\n'
            correct = False
        try:
            port = int(port)
        except:
            m += 'port field must consist of integers'
            correct = False

        self.username.set(self.username.get().strip())
        self.password.set(self.password.get().strip())

        syntax = self.syntax.get()
        self.syntax.set(syntax.strip())
        if syntax == '':
            m += 'syntax field cannot be empty\n'
            correct = False

        return (correct, m)

    def reset_form(self):
        self.conn_name.set('')
        self.host.set('')
        self.database.set('')
        self.port.set('')
        self.username.set(None)
        self.password.set(None)
        self.syntax.set('USMARC')
        self.library.set('')

    def populate_form(self, *args):
        if self.conn_name.get() != '' and \
                self.stop_tracer is False:
            user_data = shelve.open(USER_DATA)
            try:
                conn = user_data['Z3950s'][self.conn_name.get()]
                self.library.set(conn['library'])
                self.host.set(conn['host'])
                self.database.set(conn['database'])
                self.port.set(conn['port'])
                self.username.set(conn['user'])
                self.password.set(conn['password'])
                self.syntax.set(conn['syntax'])
            except KeyError:
                pass
            finally:
                user_data.close()

    def observer(self, *args):
        if self.activeW.get() == 'Z3950s':
            self.stop_tracer = False
            self.reset_form()
            user_data = shelve.open(USER_DATA)
            if 'Z3950s' in user_data:
                if len(user_data['Z3950s']) > 0:
                    Z3950s = user_data['Z3950s']
                    conn_names = []
                    for name in Z3950s.iterkeys():
                        conn_names.append(name)
                    self.conn_nameCbx['value'] = sorted(conn_names)
            user_data.close()


class DefaultDirs(tk.Frame):
    """
    Widget where user sets default directories
    """

    def __init__(self, parent, controller, **app_data):
        self.parent = parent
        tk.Frame.__init__(self, parent, background='white')
        self.controller = controller
        self.activeW = app_data['activeW']
        self.activeW.trace('w', self.observer)

        # widget variables
        self.update_dir = tk.StringVar()
        self.nyp_archive_dir = tk.StringVar()
        self.bpl_archive_dir = tk.StringVar()
        self.option = tk.IntVar()

        # configure layout
        self.rowconfigure(0, minsize=25)
        self.rowconfigure(2, minsize=10)
        self.rowconfigure(8, minsize=25)
        self.columnconfigure(0, minsize=20)
        self.columnconfigure(4, minsize=10)

        # settings frame
        self.baseFrm = ttk.LabelFrame(self, text='default directories')
        self.baseFrm.grid(
            row=1, column=1, rowspan=6, sticky='snew')
        self.baseFrm.columnconfigure(2, minsize=380)
        self.baseFrm.rowconfigure(6, minsize=10)
        self.baseFrm.rowconfigure(8, minsize=10)

        ttk.Radiobutton(
            self.baseFrm,
            cursor='hand2',
            text='upgrade folder',
            value=0,
            variable=self.option).grid(
            row=0, column=0, columnspan=2,
            sticky='snew', padx=10, pady=5)
        update_dirLbl = ttk.Label(
            self.baseFrm,
            style='Small.TLabel',
            textvariable=self.update_dir)
        update_dirLbl.grid(
            row=1, column=0, columnspan=10, sticky='nw', padx=26)

        ttk.Radiobutton(
            self.baseFrm,
            cursor='hand2',
            text='NYPL archive folder',
            value=1,
            variable=self.option).grid(
            row=2, column=0, columnspan=2,
            sticky='snew', padx=10, pady=5)
        nyp_archive_dirLbl = ttk.Label(
            self.baseFrm,
            style='Small.TLabel',
            textvariable=self.nyp_archive_dir)
        nyp_archive_dirLbl.grid(
            row=3, column=0, columnspan=10, sticky='nw', padx=26)

        ttk.Radiobutton(
            self.baseFrm,
            cursor='hand2',
            text='BPL archive folder',
            value=2,
            variable=self.option).grid(
            row=4, column=0, columnspan=2,
            sticky='snew', padx=10, pady=5)
        nyp_archive_dirLbl = ttk.Label(
            self.baseFrm,
            style='Small.TLabel',
            textvariable=self.bpl_archive_dir)
        nyp_archive_dirLbl.grid(
            row=5, column=0, columnspan=10, sticky='nw', padx=26)

        ttk.Button(
            self.baseFrm,
            text='set',
            width=15,
            cursor='hand2',
            command=self.set_dir).grid(
            row=7, column=0, sticky='sw', padx=5)

        ttk.Button(
            self.baseFrm,
            text='cancel',
            width=15,
            cursor='hand2',
            command=lambda: self.controller.show_frame('Settings')).grid(
            row=7, column=1, sticky='sw', padx=5)

    def set_dir(self):
        dir_opt = {}
        dir_opt['mustexist'] = False
        dir_opt['parent'] = self
        dir_opt['title'] = 'Please select directory'
        dir_opt['initialdir'] = MY_DOCS
        d = tkFileDialog.askdirectory(**dir_opt)
        if d != '':
            user_data = shelve.open(USER_DATA, writeback=True)
            paths = user_data['paths']
            if self.option.get() == 0:
                paths['update_dir'] = d
                self.update_dir.set('current: {}'.format(d))
            elif self.option.get() == 1:
                paths['nyp_archive_dir'] = d
                self.nyp_archive_dir.set('current: {}'.format(d))
            elif self.option.get() == 2:
                paths['bpl_archive_dir'] = d
                self.bpl_archive_dir.set('current: {}'.format(d))
            user_data['paths'] = paths
            user_data.close()

    def observer(self, *args):
        if self.activeW.get() == 'DefaultDirs':
            user_data = shelve.open(USER_DATA)
            paths = user_data['paths']
            if 'update_dir' in paths:
                self.update_dir.set('current: {}'.format(paths['update_dir']))
            else:
                self.update_dir.set('current: NONE')
            if 'nyp_archive_dir' in paths:
                self.nyp_archive_dir.set('current: {}'.format(
                    paths['nyp_archive_dir']))
            else:
                self.nyp_archive_dir.set('current: NONE')
            if 'bpl_archive_dir' in paths:
                self.bpl_archive_dir.set('current: {}'.format(
                    paths['bpl_archive_dir']))
            else:
                self.bpl_archive_dir.set('current: NONE')
            user_data.close()


class GooAPI(tk.Frame):
    """
    widget for ingesting Google API credentials
    """

    def __init__(self, parent, controller, **app_data):
        self.parent = parent
        tk.Frame.__init__(self, parent, background='white')
        self.controller = controller
        self.activeW = app_data['activeW']
        self.activeW.trace('w', self.observer)

        self.creds = None
        self.folder_ids = {}
        self.key = tk.StringVar()
        self.status = ''

        # settings frame
        self.baseFrm = ttk.LabelFrame(self, text='Google API settings')
        self.baseFrm.grid(
            row=1, column=1, rowspan=6, sticky='snew')
        self.baseFrm.rowconfigure(0, minsize=20)
        self.baseFrm.rowconfigure(2, minsize=5)
        self.baseFrm.rowconfigure(4, minsize=5)
        self.baseFrm.rowconfigure(6, minsize=5)
        self.baseFrm.rowconfigure(8, minsize=250)
        self.baseFrm.rowconfigure(10, minsize=20)
        self.baseFrm.columnconfigure(0, minsize=10)
        self.baseFrm.columnconfigure(4, minsize=10)

        self.linkBtn = ttk.Button(
            self.baseFrm, text='link G-Drive',
            cursor='hand2',
            width=15,
            command=self.link_GSuite)
        self.linkBtn.grid(
            row=1, column=1, sticky='sew')

        self.testBtn = ttk.Button(
            self.baseFrm, text='test',
            cursor='hand2',
            width=15,
            command=self.test_link_to_GSuite)
        self.testBtn.grid(
            row=3, column=1, sticky='sew')

        self.unlinkBtn = ttk.Button(
            self.baseFrm, text='unlink G-Drive',
            cursor='hand2',
            width=15,
            command=self.unlink_GSuite)
        self.unlinkBtn.grid(
            row=5, column=1, sticky='sew')

        self.helpBtn = ttk.Button(
            self.baseFrm, text='help',
            cursor='hand2',
            width=15,
            command=self.help)
        self.helpBtn.grid(
            row=7, column=1, sticky='sew')

        self.closeBtn = ttk.Button(
            self.baseFrm, text='close',
            cursor='hand2',
            width=15,
            command=lambda: controller.show_frame('Main'))
        self.closeBtn.grid(
            row=9, column=1, sticky='sew')

        self.linkDetailsTxt = tk.Text(
            self.baseFrm,
            wrap=tk.WORD,
            width=72,
            state=tk.DISABLED,
            borderwidth=0)
        self.linkDetailsTxt.grid(
            row=1, column=3, rowspan=8, sticky='ne', padx=10, pady=5)

    def link_GSuite(self):
        # look up update folder and determine path to
        # credential file
        self.creds = credentials.locate_goo_credentials(USER_DATA, GOO_CREDS)
        if self.creds:
            if not os.path.isfile(self.creds):
                overload_logger.error(
                    'goo_credentials.bin not found at {}'.format(
                        os.path.split(self.creds)[0]))
                m = 'Google credentials at {}\n' \
                    'appear to be missing. Please report the problem.'.format(
                        os.path.split(self.creds)[0])
                tkMessageBox.showerror('Settings Error', m)
            else:
                # ask for decryption key, decrypt creds and
                # store in Windows vault
                self.ask_decryption_key()
                self.wait_window(self.top)
        else:
            overload_logger.error(
                'User settings error. Missing "Overload Creds" directory')
            m = 'Unable to locate "Overload Creds" folder with ' \
                '"goo_credentials.bin" file on the shared drive. \n' \
                'Specify correct upgrade folder at  \n'\
                'Settings>Default Directories>Upgrade Folder and try again.'
            tkMessageBox.showerror('Settings Error', m)

        # verify and store in user_data g-drive folder ids
        if not credentials.store_goo_folder_ids(USER_DATA, GOO_FOLDERS):
            overload_logger.error(
                'User settings error. '
                'Unable to located goo_folders.json file.')
            m = 'Unable to locate "goo_folder.json" file on the shared ' \
                'drive.\nSpecify correct upgrade folder at \n' \
                'Settings>Default Directories>Upgrade Folder and try again.'
            tkMessageBox.showerror('Settings Error', m)

        self.test_link_to_GSuite()

    def ask_decryption_key(self):
        self.top = tk.Toplevel(self, background='white')
        self.top.iconbitmap('./icons/key.ico')
        self.top.title('Decryption Key')

        # reset key
        self.key.set('')

        # layout
        self.top.columnconfigure(0, minsize=10)
        self.top.columnconfigure(2, minsize=5)
        self.top.columnconfigure(4, minsize=10)
        self.top.rowconfigure(0, minsize=10)
        self.top.rowconfigure(2, minsize=5)
        self.top.rowconfigure(4, minsize=5)
        self.top.rowconfigure(6, minsize=10)

        ttk.Label(
            self.top,
            text='please provide decryption key:').grid(
                row=1, column=1, columnspan=3, sticky='nw', padx=10)

        self.keyEnt = tk.Entry(
            self.top, textvariable=self.key, show='*')
        self.keyEnt.grid(
            row=3, column=1, columnspan=3, sticky='snew', padx=10)

        self.decryptBtn = ttk.Button(
            self.top,
            text='decrypt',
            command=self.decrypt_creds)
        self.decryptBtn.grid(
            row=5, column=1, sticky='sew', padx=10, pady=10)

        self.closeBtn = ttk.Button(
            self.top,
            text='close',
            command=self.top.destroy)
        self.closeBtn.grid(
            row=5, column=3, sticky='sew', padx=10, pady=10)

    def decrypt_creds(self):
        key = self.key.get().strip()
        try:
            decrypted_creds = credentials.decrypt_file_data(key, self.creds)
        except OverloadError as e:
            overload_logger.error('Decryption error: {}'.format(e))
            m = 'Decryption error: {}'.format(e)
            tkMessageBox.showerror('Decryption error', m, parent=self.top)
        else:
            # store temp json file
            cred_fh = os.path.join(TEMP_DIR, 'credentials.json')
            with open(cred_fh, 'w') as file:
                json.dump(json.loads(decrypted_creds), file)

            # insert credentials into Windows Vault
            if goo.store_access_token(
                    GAPP, GUSER,
                    cred_fh,
                    [SHEET_SCOPE, FDRIVE_SCOPE]):

                # browser will open to complete the authorization
                # close the widget
                self.top.destroy()
            else:
                self.top.destroy()
                tkMessageBox.showerror(
                    'Google Drive', 'Unable to link Google Drive.')

            # clean-up
            # delete decoded creds file
            try:
                os.remove(cred_fh)
            except WindowsError as e:
                overload_logger.error(
                    'Unable to delete temp creds from {}. Error: {}'.format(
                        TEMP_DIR, e))

    def unlink_GSuite(self):
        # remove credentials from credentials manager
        credentials.delete_from_vault(GAPP, GUSER)

        # remove folder ids from user_data
        try:
            user_data = shelve.open(USER_DATA, writeback=True)
            user_data.pop('gdrive', None)
        except KeyError:
            pass
        finally:
            user_data.close()

        # verify
        self.test_link_to_GSuite()

    def test_link_to_GSuite(self):
        self.status = ''
        if not credentials.get_from_vault(GAPP, GUSER):
            self.status = '\tMissing Google API credentials. ' \
                'Unable to connect to the Google Drive\n'
        else:
            self.status = '\tGoogle API credentials stored in ' \
                'Windows Credential Manager.\n'

        user_data = shelve.open(USER_DATA)
        try:
            self.status = self.status + \
                '\tNYPL Google Drive folder id: {}\n'.format(
                    user_data['gdrive']['nypl_folder_id'])
        except KeyError:
            self.status = self.status + \
                '\tNYPL Google Drive folder id: missing\n'
        try:
            self.status = self.status + \
                '\tBPL Google Drive folder id: {}\n'.format(
                    user_data['gdrive']['bpl_folder_id'])
        except KeyError:
            self.status = self.status + \
                '\tBPL Google Drive folder id: missing\n'
        user_data.close()

        self.update_status()

    def update_status(self):
        self.status = 'Status:\n' + self.status
        self.linkDetailsTxt['state'] = tk.NORMAL
        self.linkDetailsTxt.delete(1.0, tk.END)
        self.linkDetailsTxt.insert(tk.END, self.status)
        self.linkDetailsTxt['state'] = tk.DISABLED

    def help(self):
        text = overload_help.open_help(
            'goo_help.txt')
        help_popup = tk.Toplevel(background='white')
        help_popup.iconbitmap('./icons/help.ico')
        yscrollbar = tk.Scrollbar(help_popup, orient=tk.VERTICAL)
        yscrollbar.grid(
            row=0, column=1, rowspan=10, sticky='nsw', padx=2)
        helpTxt = tk.Text(
            help_popup,
            wrap=tk.WORD,
            background='white',
            relief=tk.FLAT,
            yscrollcommand=yscrollbar.set)
        helpTxt.grid(
            row=0, column=0, sticky='snew', padx=10, pady=10)
        yscrollbar.config(command=helpTxt.yview)
        for line in text:
            helpTxt.insert(tk.END, line)
        helpTxt['state'] = tk.DISABLED

    def observer(self, *args):
        if self.activeW.get() == 'GooAPI':
            self.test_link_to_GSuite()


class About(tk.Frame):
    """info about OpsUtils"""

    def __init__(self, parent, controller, **user_data):
        self.parent = parent
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.activeW = user_data['activeW']
        self.activeW.trace('w', self.observer)

        self.rowconfigure(0, minsize=20)
        self.rowconfigure(3, minsize=20)
        self.rowconfigure(10, minsize=20)
        self.columnconfigure(0, minsize=20)
        self.columnconfigure(10, minsize=20)

        self.closeBtn = ttk.Button(
            self, text='close',
            width=15,
            cursor='hand2',
            command=lambda: controller.show_frame('Main'))
        self.closeBtn.grid(
            row=4, column=0, sticky='sw')

    def display_info(self, info, credits):
        # app info

        self.utilsFrm = ttk.LabelFrame(self, text='about app:')
        self.utilsFrm.grid(
            row=1, column=0, sticky='snew')
        ttk.Label(self.utilsFrm, text=info).grid(
            row=0, column=0, sticky='snew')

        self.aboutFrm = ttk.LabelFrame(self, text='credits:')
        self.aboutFrm.grid(
            row=2, column=0, sticky='snew')
        ttk.Label(self.aboutFrm, text=credits).grid(
            row=0, column=0, sticky='snew')

    def observer(self, *args):
        if self.activeW.get() == 'About':
            info = ''
            with open('version.txt') as fh:
                for line in fh:
                    info += line
            if os.path.isfile(PATCHING_RECORD):
                with open(PATCHING_RECORD, 'r') as fh:
                    info += '\ninstalled patches:\n'
                    for line in fh:
                        info += '  {}'.format(line)
            credits = ''
            with open('./help/icon_credits.txt') as fh:
                for line in fh:
                    credits += line
            self.display_info(info, credits)


if __name__ == "__main__":

    # check if required folders & files exist
    if not os.path.isdir(APP_DIR):
        os.mkdir(APP_DIR)
    if not os.path.isdir(TEMP_DIR):
        os.mkdir(TEMP_DIR)

    # configure local settings
    user_data = shelve.open(USER_DATA)
    if 'paths' not in user_data:
        user_data['paths'] = {}
    user_data.close()

    about = {}
    with open('__version__.py') as f:
        exec(f.read(), about)
    version = about['__version__']

    # set up app logger
    logging.config.dictConfig(DEV_LOGGING)
    logger = logging.getLogger('overload')
    overload_logger = LogglyAdapter(logger, None)

    # set the backend for credentials
    keyring.set_keyring(WinVaultKeyring())

    # launch application
    app = MainApplication()
    cur_manager = BusyManager(app)
    app.iconbitmap('./icons/SledgeHammer.ico')
    app.title('Overload version {}'.format(version))
    s = ttk.Style()
    s.theme_use('clam')
    s.configure('.', font=('Helvetica', 12),
                background='white')
    s.configure('TFrame', background='white')
    s.map('TButton', background=[('active', 'white')])
    s.configure('Flat.TEntry', borderwidth=0)
    s.configure('Bold.TLabel', font=('Helvetica', 12, 'bold'))
    s.configure('Small.TLabel', font=('Helvetica', 8))
    s.configure('Medium.Treeview', font=('Helvetica', 9))

    updates(manual=False)

    app.mainloop()
