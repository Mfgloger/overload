from datetime import date
from ftplib import error_perm
import logging
import os
import os.path
import shelve
import shutil
import sys
import time
import Tkinter as tk
import ttk
import tkFileDialog
import tkMessageBox


from bibs import bibs
import bibs.sierra_dicts as sd
from datastore import NYPLOrderTemplate, session_scope
from db_worker import retrieve_record
import connectors.goo as goo
from connectors.goo_settings.access_names import GAPP, GUSER
from errors import OverloadError
from ftp_manager import store_connection, delete_connection, \
    get_ftp_connections, get_connection_details, connect2ftp, \
    disconnect_ftp, read_ftp_content, move2ftp, move2local
from gui_utils import ToolTip, BusyManager
from logging_setup import format_traceback, LogglyAdapter
from manager import run_processing, save_stats, save_template, \
    update_template, delete_template, get_template_names
import overload_help
from pvf import goo_comms
import reports
from setup_dirs import MY_DOCS, USER_DATA, CVAL_REP, \
    LSPEC_REP, DVAL_REP, BATCH_META, BATCH_STATS
from utils import convert_file_size
from validation import validate_files
from validators.marcedit import delete_validation_report


module_logger = LogglyAdapter(logging.getLogger('overload'), None)


class TransferFiles(tk.Frame):
    """GUI for connecting to vendor's FTPs"""

    def __init__(self, parent, system):
        self.parent = parent
        self.system = system
        tk.Frame.__init__(self, self.parent, background='white')
        self.top = tk.Toplevel(self, background='white')
        self.cur_manager = BusyManager(self)
        self.top.iconbitmap('./icons/ftp.ico')
        self.top.title('Transfer files')
        self.top.protocol("WM_DELETE_WINDOW", self._delete_window)

        # variable
        self.ftp = None
        self.name = tk.StringVar()
        self.name.trace('w', self.set_host_details)
        self.host = None
        self.user = None
        self.password = None
        self.files = None
        self.rename_option = tk.IntVar()
        self.new_fh = None
        self.transfer_type = tk.StringVar()
        self.local_directory = None
        self.local_directoryDsp = tk.StringVar()
        self.ftp_directory = None
        self.ftp_directoryDsp = tk.StringVar()
        self.ftp_directoryDsp.set('remote: not connected')

        # icons
        self.file_ico = tk.PhotoImage(file='./icons/file.gif')
        self.dir_ico = tk.PhotoImage(file='./icons/dir.gif')
        self.back_ico = tk.PhotoImage(file='./icons/back.gif')

        # layout
        self.top.columnconfigure(0, minsize=5)
        self.top.columnconfigure(1, minsize=30)
        # self.top.columnconfigure(7, minsize=40)
        self.top.columnconfigure(12, minsize=5)
        self.top.rowconfigure(0, minsize=5)
        # self.top.rowconfigure(2, minsize=15)
        self.top.rowconfigure(27, minsize=5)
        self.top.rowconfigure(30, minsize=5)

        # widgets
        ttk.Label(self.top, text='host:').grid(
            row=1, column=1, sticky='ne', padx=10, pady=10)
        self.nameCbx = ttk.Combobox(
            self.top, textvariable=self.name,
            postcommand=self.get_available_connections)
        self.nameCbx.grid(
            row=1, column=2, columnspan=3, sticky='snew', pady=10)
        self.nameCbx['state'] = 'readonly'

        self.connBtn = ttk.Button(
            self.top,
            text='connect',
            command=self.connect)
        self.connBtn.grid(
            row=1, column=5, sticky='nw', padx=10, pady=5)

        self.disconnBtn = ttk.Button(
            self.top,
            text='disconnect',
            command=self.disconnect)
        self.disconnBtn.grid(
            row=1, column=7, sticky='nw', padx=10, pady=5)

        self.newBtn = ttk.Button(
            self.top,
            text='new',
            command=self.new_connection)
        self.newBtn.grid(
            row=1, column=8, sticky='new', padx=10, pady=5)

        self.deleteBtn = ttk.Button(
            self.top,
            text='delete',
            command=self.delete)
        self.deleteBtn.grid(
            row=1, column=9, sticky='new', padx=10, pady=5)

        self.leftBtn = ttk.Button(
            self.top,
            text='<=',
            width=2,
            command=self.move_left)
        self.leftBtn.grid(
            row=13, column=6, sticky='nw', pady=5)
        self.createToolTip(
            self.leftBtn,
            'download to your computer')
        self.rightBtn = ttk.Button(
            self.top,
            text='=>',
            width=2,
            command=self.move_right)
        self.rightBtn.grid(
            row=14, column=6, sticky='nw', pady=5)
        self.createToolTip(
            self.rightBtn,
            'upload to remote server')

        self.locLbl = ttk.Label(
            self.top,
            style='Small.TLabel',
            textvariable=self.local_directoryDsp)
        self.locLbl.grid(
            row=2, column=1, columnspan=5, sticky='sw', padx=10)

        columns = ('name', 'size', 'date')

        # local frame
        self.locFrm = ttk.Frame(
            self.top)
        self.locFrm.grid(
            row=3, column=1, rowspan=20, columnspan=5, sticky='snew', padx=10)

        self.locTrv = ttk.Treeview(
            self.locFrm,
            columns=columns,
            displaycolumns='#all',
            # show='headings',
            selectmode='browse',
            style='Medium.Treeview')

        self.locTrv.bind('<Double-Button-1>', self.change_loc_directory)

        # sorting columns functionality
        for col in columns:
            self.locTrv.heading(
                col,
                text=col,
                command=lambda _col=col: self.treeview_sort_column(
                    self.locTrv, _col, False))

        self.locTrv.column('#0', width=36)
        self.locTrv.column('name', width=250)
        self.locTrv.column('size', width=60)
        self.locTrv.column('date', width=110)
        self.locTrv.tag_configure('d', image=self.dir_ico)
        self.locTrv.tag_configure('f', image=self.file_ico)
        self.locTrv.tag_configure('o', image=self.back_ico)

        self.locTrv.grid(
            row=0, column=0, columnspan=5, sticky='snew')

        # local frame scrollbar
        locSB = ttk.Scrollbar(
            self.locFrm, orient="vertical", command=self.locTrv.yview)
        locSB.grid(row=0, rowspan=20, column=5, sticky='ns')
        self.locTrv.configure(yscrollcommand=locSB.set)

        self.remLbl = ttk.Label(
            self.top,
            style='Small.TLabel',
            textvariable=self.ftp_directoryDsp)
        self.remLbl.grid(
            row=2, column=7, columnspan=5, sticky='sw', padx=10)

        # remote frame
        self.remFrm = ttk.Frame(
            self.top)
        self.remFrm.grid(
            row=3, column=7, rowspan=20, columnspan=5, sticky='snew', padx=10)

        self.remTrv = ttk.Treeview(
            self.remFrm,
            columns=('name', 'size', 'date'),
            displaycolumns=('name', 'size', 'date'),
            selectmode='browse',
            style='Medium.Treeview')

        self.remTrv.bind('<Double-Button-1>', self.change_rem_directory)

        # sorting columns functionality
        for col in columns:
            self.remTrv.heading(
                col,
                text=col,
                command=lambda _col=col: self.treeview_sort_column(
                    self.remTrv, _col, False))

        self.remTrv.column('#0', width=36)
        self.remTrv.column('name', width=250)
        self.remTrv.column('size', width=60)
        self.remTrv.column('date', width=110)
        self.remTrv.tag_configure('d', image=self.dir_ico)
        self.remTrv.tag_configure('f', image=self.file_ico)
        self.remTrv.tag_configure('o', image=self.back_ico)
        self.remTrv.grid(
            row=0, column=0, columnspan=6, sticky='snew')

        # remote frame scrollbar
        remSB = ttk.Scrollbar(
            self.remFrm, orient="vertical", command=self.remTrv.yview)
        remSB.grid(row=0, rowspan=20, column=6, sticky='ns')
        self.remTrv.configure(yscrollcommand=remSB.set)

        ttk.Label(self.top, text='transfer type').grid(
            row=24, column=1, sticky='sw', padx=10, pady=10)
        self.transferCbx = ttk.Combobox(
            self.top,
            width=6,
            textvariable=self.transfer_type)
        self.transferCbx.grid(
            row=24, column=2, sticky='sw', padx=10, pady=10)
        self.transferCbx['values'] = ['binary', 'ASCII']
        self.transferCbx['state'] = 'readonly'
        self.transfer_type.set('binary')

        self.renameCtn = ttk.Checkbutton(
            self.top,
            cursor='hand2',
            text='rename files upon transfer',
            variable=self.rename_option)
        self.renameCtn.grid(
            row=24, column=3, columnspan=3, sticky='sew', padx=10, pady=10)

        self.helpBtn = ttk.Button(
            self.top,
            text='help',
            command=self.help)
        self.helpBtn.grid(
            row=25, column=8, sticky='sew', padx=10, pady=10)

        self.closeBtn = ttk.Button(
            self.top,
            text='close',
            command=self._delete_window)
        self.closeBtn.grid(
            row=25, column=9, sticky='sew', padx=10, pady=10)

        # use last used settings
        self.retrieve_last_local_directory()
        self.populate_local_panel()

    def get_available_connections(self):
        conns = get_ftp_connections(self.system)
        self.nameCbx['values'] = conns
        self.nameCbx['state'] = 'readonly'

    def connect(self):
        if self.ftp:
            pass
        elif self.name.get() != '':
            try:
                self.cur_manager.busy()
                self.ftp = connect2ftp(
                    self.host, self.user, self.password)
                if self.ftp_directory:
                    self.ftp.cwd(self.ftp_directory)
                    self.ftp_directoryDsp.set(
                        'remote: {}'.format(
                            self.shorten_directory(self.ftp_directory)))
                else:
                    self.ftp_directory = self.ftp.pwd()
                    self.ftp_directoryDsp.set(
                        'remote: {}'.format(
                            self.shorten_directory(self.ftp_directory)))
                self.populate_remote_panel()
            except OverloadError as e:
                tkMessageBox.showerror(
                    'FTP Error', e, parent=self.top)
            finally:
                self.cur_manager.notbusy()
        else:
            tkMessageBox.showerror(
                'FTP', 'Please select host to connect to',
                parent=self.top)

    def disconnect(self):
        if self.ftp:
            disconnect_ftp(self.ftp)
            self.ftp = None
        self.remTrv.delete(*self.remTrv.get_children())
        self.ftp_directoryDsp.set('remote: not connected')

    def new_connection(self):
        self.conn_top = tk.Toplevel(self, background='white')
        self.conn_top.iconbitmap('./icons/settings.ico')
        self.conn_top.title('FTP setup')
        self.new_name = tk.StringVar()
        self.new_host = tk.StringVar()
        self.new_user = tk.StringVar()
        self.new_password = tk.StringVar()
        self.new_folder = tk.StringVar()

        self.conn_top.columnconfigure(0, minsize=5)
        self.conn_top.columnconfigure(4, minsize=10)
        self.conn_top.rowconfigure(0, minsize=5)
        self.conn_top.rowconfigure(4, minsize=5)

        ttk.Label(self.conn_top, text='name').grid(
            row=1, column=1, sticky='nw', padx=10, pady=10)
        nameEnt = ttk.Entry(
            self.conn_top, textvariable=self.new_name)
        nameEnt.grid(
            row=1, column=2, sticky='ne', pady=10)

        ttk.Label(self.conn_top, text='host').grid(
            row=2, column=1, sticky='nw', padx=10, pady=10)
        hostEnt = ttk.Entry(
            self.conn_top, textvariable=self.new_host)
        hostEnt.grid(
            row=2, column=2, sticky='ne', pady=10)

        ttk.Label(self.conn_top, text='folder').grid(
            row=3, column=1, sticky='nw', padx=10, pady=10)
        folderEnt = ttk.Entry(
            self.conn_top, textvariable=self.new_folder)
        folderEnt.grid(
            row=3, column=2, sticky='ne', pady=10)

        ttk.Label(self.conn_top, text='user').grid(
            row=4, column=1, sticky='nw', padx=10, pady=10)
        userEnt = ttk.Entry(
            self.conn_top, textvariable=self.new_user)
        userEnt.grid(
            row=4, column=2, sticky='snew', pady=10)

        ttk.Label(self.conn_top, text='password').grid(
            row=5, column=1, sticky='nw', padx=10, pady=10)
        passEnt = ttk.Entry(
            self.conn_top, textvariable=self.new_password, show='*')
        passEnt.grid(
            row=5, column=2, sticky='snew', pady=10)

        saveBtn = ttk.Button(
            self.conn_top, text='save',
            command=self.save)
        saveBtn.grid(
            row=6, column=1, columnspan=2, sticky='snew', padx=50, pady=10)

    def save(self):
        try:
            store_connection(
                self.new_name.get().strip(),
                self.new_host.get().strip(),
                self.new_folder.get().strip(),
                self.new_user.get().strip(),
                self.new_password.get().strip(),
                self.system)
            tkMessageBox.showinfo(
                'Datastore', 'Connection details saved.',
                parent=self.conn_top)
            self.conn_top.destroy()
        except OverloadError as e:
            tkMessageBox.showerror('FTP', e, parent=self.conn_top)

    def delete(self):
        proceed = tkMessageBox.askokcancel(
            'FTP details', 'Delete {} FTP details?'.format(
                self.name.get()))
        self.reset()
        if proceed:
            try:
                delete_connection(self.name.get(), self.system)
                self.name.set('')
            except OverloadError as e:
                tkMessageBox.showerror(
                    'Datastore', e,
                    parent=self.top)

    def save_new_fh(self, from_location):
        if from_location == 'local':
            self.new_fh = self.rem_fh.get()
        elif from_location == 'remote':
            self.new_fh = self.loc_fh.get()
        self.new_fh = self.new_fh.strip()
        if self.new_fh == '':
            tkMessageBox.showwarning(
                'Renaming File',
                'New file name cannot be empty',
                parent=self.rename_top)
        else:
            self.rename_top.destroy()

    def rename_file(self, fh, from_location):
        self.rename_top = tk.Toplevel(self, background='white')
        self.rename_top.iconbitmap('./icons/pen.ico')
        self.rename_top.title('Renaming File')
        self.loc_fh = tk.StringVar()
        self.loc_fh.set(fh)
        self.rem_fh = tk.StringVar()
        self.rem_fh.set(fh)

        self.rename_top.columnconfigure(0, minsize=5)
        self.rename_top.columnconfigure(1, minsize=200)
        self.rename_top.columnconfigure(2, minsize=15)
        self.rename_top.columnconfigure(3, minsize=200)
        self.rename_top.columnconfigure(4, minsize=10)

        self.rename_top.rowconfigure(0, minsize=5)
        self.rename_top.rowconfigure(4, minsize=5)

        ttk.Label(
            self.rename_top, text='local name:',
            style='Small.TLabel').grid(
            row=1, column=1, sticky='sw')
        ttk.Label(
            self.rename_top, text='remote name:',
            style='Small.TLabel').grid(
            row=1, column=3, sticky='sw')

        loc_fhEnt = ttk.Entry(
            self.rename_top,
            textvariable=self.loc_fh)
        loc_fhEnt.grid(
            row=2, column=1, sticky='snew', pady=5)
        rem_fhEnt = ttk.Entry(
            self.rename_top,
            textvariable=self.rem_fh)
        rem_fhEnt.grid(
            row=2, column=3, sticky='snew', pady=5)

        saveBtn = ttk.Button(
            self.rename_top,
            text='OK',
            command=lambda:self.save_new_fh(from_location))
        saveBtn.grid(
            row=3, column=1, sticky='snew', padx=50, pady=10)
        cancelBtn = ttk.Button(
            self.rename_top,
            text='cancel',
            command=self.rename_top.destroy)
        cancelBtn.grid(
            row=3, column=3, sticky='snew', padx=50, pady=10)

        if from_location == 'local':
            loc_fhEnt['state'] = 'readonly'
        elif from_location == 'remote':
            rem_fhEnt['state'] = 'readonly'

        self.rename_top.wait_window()

    def move_left(self):
        if self.ftp:
            curItem = self.remTrv.focus()
            # allow download of files only
            if self.remTrv.item(curItem)['tags'][0] == 'f':
                # find file handle
                remote_fh = self.remTrv.item(curItem)['values'][0]
                module_logger.debug(
                    'Selected file: {}'.format(remote_fh))

                if self.rename_option.get() == 1:
                    module_logger.debug('Renaming transfer file.')
                    self.rename_file(remote_fh, 'remote')
                    local_fh = self.new_fh
                    module_logger.debug(
                        'Transfer file renamed to: {}'.format(local_fh))
                else:
                    local_fh = remote_fh

                # local path to file
                lfh = os.path.join(self.local_directory, local_fh)
                module_logger.debug(
                    'Desination path: {}'.format(lfh))

                self.cur_manager.busy()
                try:
                    move2local(
                        self.host, self.ftp, remote_fh, lfh,
                        self.transfer_type.get())
                    transfered = True
                except OverloadError as e:
                    tkMessageBox.showerror(
                        'Transfer Error', e, parent=self.top)
                    transfered = False
                finally:
                    self.cur_manager.notbusy()
                if transfered:
                    self.populate_local_panel()

    def move_right(self):
        if self.ftp:
            curItem = self.locTrv.focus()
            # allow upload of files only
            if self.locTrv.item(curItem)['tags'][0] == 'f':
                # file handle
                fh = self.locTrv.item(curItem)['values'][0]
                module_logger.debug('Selected file: {}'.format(
                    fh))
                # local path to file
                lfh = os.path.join(
                    self.local_directory,
                    self.locTrv.item(curItem)['values'][0])
                module_logger.debug('Selected file path: {}'.format(
                    lfh))

                # file handle on the remote
                if self.rename_option.get() == 1:
                    module_logger.debug('Renaming transfer file.')
                    self.rename_file(fh, 'local')
                    fh = self.new_fh
                    module_logger.debug(
                        'Transfer file renamed to: {}'.format(fh))

                self.cur_manager.busy()
                try:
                    move2ftp(
                        self.host, self.ftp, lfh, fh,
                        self.transfer_type.get())
                    transfered = True
                except OverloadError as e:
                    tkMessageBox.showerror(
                        'Transfer Error', e, parent=self.top)
                    transfered = False
                finally:
                    self.cur_manager.notbusy()
                if transfered:
                    self.populate_remote_panel()

    def help():
        text = overload_help.open_help(
            'pvr_ftp_help.txt')
        help_popup = tk.Toplevel(background='white')
        help_popup.iconbitmap('./icons/help.ico')
        yscrollbar = tk.Scrollbar(help_popup, orient=tk.VERTICAL)
        yscrollbar.grid(
            row=0, column=1, rowspan=10, sticky='nsw', padx=2)
        helpTxt = tk.Text(
            help_popup,
            background='white',
            relief=tk.FLAT,
            yscrollcommand=yscrollbar.set)
        helpTxt.grid(
            row=0, column=0, sticky='snew', padx=10, pady=10)
        yscrollbar.config(command=helpTxt.yview)
        for line in text:
            helpTxt.insert(tk.END, line)
        helpTxt['state'] = tk.DISABLED

    def set_host_details(self, *args):
        self.disconnect()
        if self.name.get() != '':
            self.host, self.user, self.password, \
                self.ftp_directory = get_connection_details(
                    self.name.get(), self.system)

    def _delete_window(self):
        try:
            self.disconnect()
            self.store_last_local_directory()
            self.top.destroy()
        except:
            pass

    def shorten_directory(self, directory):
        n = len(directory)
        dlist = directory.split('/')
        while len('/'.join(dlist)) > 70:
            dlist = dlist[1:]
        if n > len('/'.join(dlist)):
            return '../{}'.format('/'.join(dlist))
        else:
            return '/'.join(dlist)

    def treeview_sort_column(self, tv, col, reverse):
        tree_list = [(tv.set(k, col), k) for k in tv.get_children('')]
        tree_list.sort(reverse=reverse)

        # rearrange items in sorted positions
        for index, (val, k) in enumerate(tree_list):
            tv.move(k, '', index)

        # reverse sort next time
        tv.heading(
            col,
            command=lambda: self.treeview_sort_column(tv, col, not reverse))

    def retrieve_last_local_directory(self):
        user_data = shelve.open(USER_DATA)
        if 'pvr_last_open_dir' in user_data['paths']:
            self.local_directory = user_data['paths']['pvr_last_open_dir']
            disp_dir = self.shorten_directory(self.local_directory)
        else:
            self.local_directory = MY_DOCS
        self.local_directoryDsp.set('local: {}'.format(
            disp_dir))
        user_data.close()

    def store_last_local_directory(self):
        if self.local_directory:
            user_data = shelve.open(USER_DATA)
            user_data['paths']['pvr_last_open_dir'] = self.local_directory
            user_data.close()

    def change_loc_directory(self, *args):
        curItem = self.locTrv.focus()
        try:
            # up the current directory
            if self.locTrv.item(curItem)['tags'][0] == 'o':
                self.local_directory = os.path.split(
                    self.local_directory)[0]
            # down the directory
            elif self.locTrv.item(curItem)['tags'][0] == 'd':
                self.local_directory = os.path.join(
                    self.local_directory,
                    self.locTrv.item(curItem)['values'][0])
            # set path
            self.local_directoryDsp.set('local: {}'.format(
                self.shorten_directory(self.local_directory)))
            # populate the panel
            self.populate_local_panel()
        except IndexError:
            pass

    def change_rem_directory(self, *args):
        curItem = self.remTrv.focus()
        try:
            if self.remTrv.item(curItem)['tags'][0] == 'o':
                self.ftp_directory = os.path.split(self.ftp.pwd())[0]
                self.ftp.cwd(self.ftp_directory)
            elif self.remTrv.item(curItem)['tags'][0] == 'd':
                self.ftp_directory = os.path.join(
                    self.ftp.pwd(),
                    self.remTrv.item(curItem)['values'][0])
                self.ftp.cwd(self.ftp_directory)

            # set path
            self.ftp_directoryDsp.set('remote: {}'.format(
                self.shorten_directory(self.ftp_directory)))
            # # populate the panel
            self.populate_remote_panel()
        except error_perm as e:
            module_logger.error(
                'Unable to access FTP directory: {}, {}. Error: {}'.format(
                    self.host, self.ftp_directory, e))
            tkMessageBox.showerror(
                'FTP Error', 'Unable to change the FTP directory',
                parent=self.top)
        except IndexError:
            # incorrect item double-clicked
            pass

    def populate_local_panel(self):
        # empty current list
        self.locTrv.delete(*self.locTrv.get_children())

        # build lists of available files and directories
        files = []
        dirs = []
        try:
            for i in os.listdir(self.local_directory):
                if os.path.isfile(os.path.join(self.local_directory, i)):
                    files.append(i)
                elif os.path.isdir(os.path.join(self.local_directory, i)):
                    dirs.append(i)

            # populate the panel
            self.locTrv.insert(
                '', tk.END, values=('...', '', ''),
                tags='o', open=False)
            for d in sorted(dirs):
                self.locTrv.insert(
                    '', tk.END, values=(d, '', ''), tags='d', open=False)
            for f in sorted(files):
                # get size
                try:
                    size_bytes = os.path.getsize('{}/{}'.format(
                        self.local_directory, f))
                    size = convert_file_size(size_bytes)
                except OSError:
                    size = '?'

                # get last modification date
                try:
                    mtime = os.path.getmtime('{}/{}'.format(
                        self.local_directory, f))
                    mtime = time.strftime(
                        '%Y-%m-%d %H:%M',
                        time.localtime(mtime))
                except OSError:
                    mtime = '?'

                # add new row
                self.locTrv.insert(
                    '', tk.END, values=(f, size, mtime),
                    tags='f', open=False)

        except WindowsError as e:
            module_logger.error(
                'WindowsError when populating FTP local panel.'
                'Error: {}'.format(e))
            self.locTrv.insert(
                '', tk.END, values=('...', '', ''),
                tags='o', open=False)

    def populate_remote_panel(self):
        self.remTrv.delete(*self.remTrv.get_children())

        show = True
        try:
            dirs, files = read_ftp_content(self.ftp, self.host)
        except OverloadError as e:
            tkMessageBox.showerror(
                'FTP Error', e, parent=self.top)
            show = False

        if show:
            self.remTrv.insert(
                '', tk.END, values=('...', '', ''), tags='o', open=False)

            for d in sorted(dirs):
                self.remTrv.insert(
                    '', tk.END, values=(d, '', ''), tags='d', open=False)

            # temp solution sorting by date
            file_dict = dict()
            for f in files:
                file_dict[f[0]] = (f[1], f[2])
            files = []
            for k, v in sorted(file_dict.iteritems()):
                files.append((k, v[0], v[1]))

            for f in files:
                try:
                    size = convert_file_size(int(f[1]))
                except ValueError:
                    self.remTrv.insert(
                        '', tk.END, values=(f, '', ''),
                        tags='d', open=False)

                mtime = f[2]

                self.remTrv.insert(
                    '', tk.END,
                    values=(f[0], size, f[2]),
                    tags='f', open=False)

    def reset(self):
        self.host = None
        self.user = None
        self.password = None
        self.ftp_directory = None

    def createToolTip(self, widget, text):
        toolTip = ToolTip(widget)

        def enter(event):
            toolTip.showtip(text)

        def leave(event):
            toolTip.hidetip()

        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)


class OrderTemplate(tk.Frame):
    """GUI for selection order templates"""

    def __init__(self, parent, **kwargs):
        self.parent = parent
        self.agent = kwargs['agent']
        tk.Frame.__init__(self, self.parent, background='white')
        self.top = tk.Toplevel(self, background='white')
        self.cur_manager = BusyManager(self)
        self.top.iconbitmap('./icons/templates.ico')
        self.top.title('Record Templates')

        # variables
        self.otid = tk.IntVar()
        self.template_name = tk.StringVar()
        self.acqType = tk.StringVar()
        self.claim = tk.StringVar()
        self.oCode1 = tk.StringVar()
        self.oCode2 = tk.StringVar()
        self.oCode3 = tk.StringVar()
        self.oCode4 = tk.StringVar()
        self.oForm = tk.StringVar()
        self.oNote = tk.StringVar()
        self.oType = tk.StringVar()
        self.vendor = tk.StringVar()
        self.lang = tk.StringVar()
        self.country = tk.StringVar()
        self.raction = tk.StringVar()
        self.identity = tk.StringVar()
        self.genNote = tk.StringVar()
        self.intNote = tk.StringVar()
        self.oldOrdNo = tk.StringVar()
        self.selector = tk.StringVar()
        self.venAddr = tk.StringVar()
        self.venNote = tk.StringVar()
        self.venTitleNo = tk.StringVar()
        self.blanketPO = tk.StringVar()
        self.shipTo = tk.StringVar()
        self.requestor = tk.StringVar()
        self.paidNote = tk.StringVar()
        self.bibMatForm = tk.StringVar()
        self.primary_match = tk.StringVar()
        self.secondary_match = tk.StringVar()
        self.tertiary_match = tk.StringVar()

        # layout of the main frame
        self.top.columnconfigure(0, minsize=5)
        self.top.columnconfigure(1, minsize=250)
        self.top.columnconfigure(9, minsize=5)
        self.top.columnconfigure(16, minsize=5)
        self.top.rowconfigure(21, minsize=5)
        self.top.rowconfigure(23, minsize=10)

        # templates list
        ttk.Label(self.top, text='{} templates:'.format(self.agent)).grid(
            row=0, column=1, sticky='sw', pady=10)
        scrollbar = ttk.Scrollbar(self.top, orient=tk.VERTICAL)
        scrollbar.grid(
            row=1, column=2, sticky='nsw', rowspan=20, padx=2, pady=10)
        self.templateLst = tk.Listbox(
            self.top,
            selectmode=tk.SINGLE,
            yscrollcommand=scrollbar.set)
        self.templateLst.bind('<<ListboxSelect>>', self.show_details)
        self.templateLst.grid(
            row=1, column=1, sticky='snew', rowspan=20, pady=10)
        scrollbar['command'] = self.templateLst.yview

        # template name
        ttk.Label(self.top, text='name:').grid(
            row=0, column=4, sticky='sw', padx=5, pady=10)
        self.templateEnt = ttk.Entry(
            self.top, textvariable=self.template_name)
        self.templateEnt.grid(
            row=0, column=5, columnspan=8, sticky='sew', pady=10)

        # fixed fields frame
        self.fixedFrm = ttk.LabelFrame(
            self.top,
            text='order fixed fields')
        self.fixedFrm.grid(
            row=1, rowspan=12, column=4, columnspan=5,
            sticky='snew', padx=5, pady=5)
        self.fixedFrm.columnconfigure(0, minsize=5)
        self.fixedFrm.columnconfigure(3, minsize=25)
        self.fixedFrm.rowconfigure(14, minsize=5)

        # fixed fields widgets
        ttk.Label(self.fixedFrm, text='ACQ Type', style='Small.TLabel').grid(
            row=0, column=1, columnspan=2, sticky='sw')
        self.acqTypeCbx = ttk.Combobox(
            self.fixedFrm, textvariable=self.acqType)
        self.acqTypeCbx.grid(
            row=1, column=1, columnspan=2, sticky='sew')

        ttk.Label(self.fixedFrm, text='Claim', style='Small.TLabel').grid(
            row=2, column=1, columnspan=2, sticky='sw')
        self.claimCbx = ttk.Combobox(
            self.fixedFrm, textvariable=self.claim)
        self.claimCbx.grid(
            row=3, column=1, columnspan=2, sticky='sew')

        ttk.Label(
            self.fixedFrm, text='OrderCode 1',
            style='Small.TLabel').grid(
            row=4, column=1, sticky='sw')
        self.oCode1Cbx = ttk.Combobox(
            self.fixedFrm, textvariable=self.oCode1)
        self.oCode1Cbx.grid(
            row=5, column=1, columnspan=2, sticky='sew')

        ttk.Label(
            self.fixedFrm, text='OrderCode 2',
            style='Small.TLabel').grid(
            row=6, column=1, columnspan=2, sticky='sw')
        self.oCode2Cbx = ttk.Combobox(
            self.fixedFrm, textvariable=self.oCode2)
        self.oCode2Cbx.grid(
            row=7, column=1, columnspan=2, sticky='sew')

        ttk.Label(
            self.fixedFrm, text='OrderCode 3',
            style='Small.TLabel').grid(
            row=8, column=1, columnspan=2, sticky='sw')
        self.oCode3Cbx = ttk.Combobox(
            self.fixedFrm, textvariable=self.oCode3)
        self.oCode3Cbx.grid(
            row=9, column=1, columnspan=2, sticky='sew')

        ttk.Label(
            self.fixedFrm, text='OrderCode 4',
            style='Small.TLabel').grid(
            row=10, column=1, columnspan=2, sticky='sw')
        self.oCode4Cbx = ttk.Combobox(
            self.fixedFrm, textvariable=self.oCode4)
        self.oCode4Cbx.grid(
            row=11, column=1, columnspan=2, sticky='sew')

        ttk.Label(
            self.fixedFrm, text='Recv Action',
            style='Small.TLabel').grid(
            row=12, column=1, columnspan=2, sticky='sw')
        self.ractionCbx = ttk.Combobox(
            self.fixedFrm, textvariable=self.raction)
        self.ractionCbx.grid(
            row=13, column=1, columnspan=2, sticky='sew')

        ttk.Label(
            self.fixedFrm, text='Form',
            style='Small.TLabel').grid(
            row=0, column=4, columnspan=2, sticky='sw')
        self.oFormCbx = ttk.Combobox(
            self.fixedFrm, textvariable=self.oForm)
        self.oFormCbx.grid(
            row=1, column=4, columnspan=2, sticky='sew')

        ttk.Label(
            self.fixedFrm, text='Order Note',
            style='Small.TLabel').grid(
            row=2, column=4, columnspan=2, sticky='sw')
        self.oNoteCbx = ttk.Combobox(
            self.fixedFrm, textvariable=self.oNote)
        self.oNoteCbx.grid(
            row=3, column=4, columnspan=2, sticky='sew')

        ttk.Label(
            self.fixedFrm, text='Order Type',
            style='Small.TLabel').grid(
            row=4, column=4, columnspan=2, sticky='sw')
        self.oTypeCbx = ttk.Combobox(
            self.fixedFrm, textvariable=self.oType)
        self.oTypeCbx.grid(
            row=5, column=4, columnspan=2, sticky='sew')

        ttk.Label(
            self.fixedFrm, text='Vendor',
            style='Small.TLabel').grid(
            row=6, column=4, columnspan=2, sticky='sw')
        self.vendorEnt = ttk.Entry(
            self.fixedFrm, textvariable=self.vendor)
        self.vendorEnt.grid(
            row=7, column=4, columnspan=2, sticky='sew')

        ttk.Label(
            self.fixedFrm, text='Language',
            style='Small.TLabel').grid(
            row=8, column=4, columnspan=2, sticky='sw')
        self.langCbx = ttk.Combobox(
            self.fixedFrm, textvariable=self.lang)
        self.langCbx.grid(
            row=9, column=4, columnspan=2, sticky='sew')

        ttk.Label(
            self.fixedFrm, text='Country',
            style='Small.TLabel').grid(
            row=10, column=4, columnspan=2, sticky='sw')
        self.countryCbx = ttk.Combobox(
            self.fixedFrm, textvariable=self.country)
        self.countryCbx.grid(
            row=11, column=4, columnspan=2, sticky='sew')

        # variable fields frame
        self.varFrm = ttk.LabelFrame(
            self.top,
            text='order variable fields')
        self.varFrm.grid(
            row=1, rowspan=12, column=10, columnspan=5,
            sticky='snew', padx=5, pady=5)
        self.varFrm.columnconfigure(0, minsize=5)
        self.varFrm.columnconfigure(3, minsize=25)
        self.varFrm.rowconfigure(14, minsize=5)

        # variable field widgets
        ttk.Label(self.varFrm, text='Identity', style='Small.TLabel').grid(
            row=0, column=1, columnspan=2, sticky='sw')
        self.identityEnt = ttk.Entry(
            self.varFrm, textvariable=self.identity)
        self.identityEnt.grid(
            row=1, column=1, columnspan=2, sticky='sew')

        ttk.Label(
            self.varFrm, text='General Note',
            style='Small.TLabel').grid(
            row=2, column=1, columnspan=2, sticky='sw')
        self.genNoteEnt = ttk.Entry(
            self.varFrm, textvariable=self.genNote)
        self.genNoteEnt.grid(
            row=3, column=1, columnspan=2, sticky='sew')

        ttk.Label(
            self.varFrm, text='Internal Note',
            style='Small.TLabel').grid(
            row=4, column=1, columnspan=2, sticky='sw')
        self.intNoteEnt = ttk.Entry(
            self.varFrm, textvariable=self.intNote)
        self.intNoteEnt.grid(
            row=5, column=1, columnspan=2, sticky='sew')

        ttk.Label(
            self.varFrm, text='Old Order No.',
            style='Small.TLabel').grid(
            row=6, column=1, columnspan=2, sticky='sw')
        self.oldOrdNoEnt = ttk.Entry(
            self.varFrm, textvariable=self.oldOrdNo)
        self.oldOrdNoEnt.grid(
            row=7, column=1, columnspan=2, sticky='sew')

        ttk.Label(
            self.varFrm, text='Selector',
            style='Small.TLabel').grid(
            row=8, column=1, columnspan=2, sticky='sw')
        self.selectorEnt = ttk.Entry(
            self.varFrm, textvariable=self.selector)
        self.selectorEnt.grid(
            row=9, column=1, columnspan=2, sticky='sew')

        ttk.Label(
            self.varFrm, text='Vendor Addr',
            style='Small.TLabel').grid(
            row=10, column=1, columnspan=2, sticky='sw')
        self.venAddrEnt = ttk.Entry(
            self.varFrm, textvariable=self.venAddr)
        self.venAddrEnt.grid(
            row=11, column=1, columnspan=2, sticky='sew')

        ttk.Label(
            self.varFrm, text='Vendor Note',
            style='Small.TLabel').grid(
            row=0, column=4, columnspan=2, sticky='sw')
        self.venNoteEnt = ttk.Entry(
            self.varFrm, textvariable=self.venNote)
        self.venNoteEnt.grid(
            row=1, column=4, columnspan=2, sticky='sew')

        ttk.Label(
            self.varFrm, text='Vendor Title No.',
            style='Small.TLabel').grid(
            row=2, column=4, columnspan=2, sticky='sw')
        self.venTitleNoEnt = ttk.Entry(
            self.varFrm, textvariable=self.venTitleNo)
        self.venTitleNoEnt.grid(
            row=3, column=4, columnspan=2, sticky='sew')

        ttk.Label(
            self.varFrm, text='Blanket PO',
            style='Small.TLabel').grid(
            row=4, column=4, columnspan=2, sticky='sw')
        self.blanketPOEnt = ttk.Entry(
            self.varFrm, textvariable=self.blanketPO)
        self.blanketPOEnt.grid(
            row=5, column=4, columnspan=2, sticky='sew')

        ttk.Label(
            self.varFrm, text='Ship To', style='Small.TLabel').grid(
            row=6, column=4, columnspan=2, sticky='sw')
        self.shipToEnt = ttk.Entry(
            self.varFrm, textvariable=self.shipTo)
        self.shipToEnt.grid(
            row=7, column=4, columnspan=2, sticky='sew')

        ttk.Label(
            self.varFrm, text='Requestor', style='Small.TLabel').grid(
            row=8, column=4, columnspan=2, sticky='sw')
        self.requestorEnt = ttk.Entry(
            self.varFrm, textvariable=self.requestor)
        self.requestorEnt.grid(
            row=9, column=4, columnspan=2, sticky='sew')

        ttk.Label(
            self.varFrm, text='Paid Note', style='Small.TLabel').grid(
            row=10, column=4, columnspan=2, sticky='sw')
        self.paidNoteEnt = ttk.Entry(
            self.varFrm, textvariable=self.paidNote)
        self.paidNoteEnt.grid(
            row=11, column=4, columnspan=2, sticky='sew')

        # sierra bibliographic format frame
        self.bibFrm = ttk.LabelFrame(
            self.top, text='sierra bib format')
        self.bibFrm.grid(
            row=20, column=4, sticky='snew', padx=5, pady=10)
        self.bibFrm.columnconfigure(0, minsize=5)
        self.bibFrm.columnconfigure(3, minsize=5)
        self.bibFrm.rowconfigure(2, minsize=5)

        ttk.Label(
            self.bibFrm, text='Material Form',
            style='Small.TLabel').grid(
            row=0, column=1, columnspan=2, sticky='sw')
        self.bibMatFormCbx = ttk.Combobox(
            self.bibFrm, textvariable=self.bibMatForm)
        self.bibMatFormCbx.grid(
            row=1, column=1, sticky='sew')

        # matchpoints frame
        self.matchFrm = ttk.LabelFrame(
            self.top, text='sierra matchpoints')
        self.matchFrm.grid(
            row=20, column=6, columnspan=9, sticky='snew', padx=5, pady=10)

        ttk.Label(
            self.matchFrm, text='primary',
            style='Small.TLabel').grid(
            row=0, column=0, sticky='sw', padx=10)
        self.primaryCbx = ttk.Combobox(
            self.matchFrm, postcommand=self.list_available_matches,
            textvariable=self.primary_match)
        self.primaryCbx.grid(
            row=1, column=0, sticky='sew', padx=10)
        self.primaryCbx['state'] = 'readonly'

        ttk.Label(
            self.matchFrm, text='seconary',
            style='Small.TLabel').grid(
            row=0, column=2, sticky='sw', padx=10)
        self.secondaryCbx = ttk.Combobox(
            self.matchFrm, postcommand=self.list_available_matches,
            textvariable=self.secondary_match)
        self.secondaryCbx.grid(
            row=1, column=2, sticky='sew', padx=10)
        self.secondaryCbx['state'] = 'readonly'

        ttk.Label(
            self.matchFrm, text='tertiary',
            style='Small.TLabel').grid(
            row=0, column=4, sticky='sw', padx=10)
        self.tertiaryCbx = ttk.Combobox(
            self.matchFrm, postcommand=self.list_available_matches,
            textvariable=self.tertiary_match)
        self.tertiaryCbx.grid(
            row=1, column=4, sticky='sew', padx=10)
        self.tertiaryCbx['state'] = 'readonly'

        # bottom buttons
        self.newBtn = ttk.Button(
            self.top,
            text='new',
            command=self.reset)
        self.newBtn.grid(
            row=22, column=1, columnspan=3, sticky='swe', padx=70, pady=5)

        self.saveBtn = ttk.Button(
            self.top,
            text='save',
            # width=8,
            command=self.save_template)
        self.saveBtn.grid(
            row=22, column=4, sticky='nwe', padx=25, pady=5)

        self.deleteBtn = ttk.Button(
            self.top,
            text='delete',
            # width=8,
            command=self.delete_template)
        self.deleteBtn.grid(
            row=22, column=6, sticky='nwe', padx=10, pady=5)

        self.helpBtn = ttk.Button(
            self.top,
            text='help',
            # width=8,
            command=self.help)
        self.helpBtn.grid(
            row=22, column=10, sticky='nwe', padx=10, pady=5)

        self.closeBtn = ttk.Button(
            self.top,
            text='close',
            # width=8,
            command=self.top.destroy)
        self.closeBtn.grid(
            row=22, column=13, sticky='nwe', padx=10, pady=5)

        self.update_template_lst()
        self.populate_cbxs()

    def show_details(self, *args):
        self.reset()
        name = self.templateLst.get(self.templateLst.curselection())

        with session_scope() as session:
            t = retrieve_record(
                session, NYPLOrderTemplate, tName=name, agent=self.agent[:3])
            self.template_name.set(t.tName)
            self.otid.set(t.otid)

            if t.acqType is not None:
                self.acqType.set(
                    '{} ({})'.format(t.acqType, sd.NACQ_TYPE[t.acqType]))
            if t.claim is not None:
                self.claim.set(
                    '{} ({})'.format(t.claim, sd.NCLAIM[t.claim]))
            if t.code1 is not None:
                self.oCode1.set(
                    '{} ({})'.format(t.code1, sd.NORDER_CODE1[t.code1]))
            if t.code2 is not None:
                self.oCode2.set(
                    '{} ({})'.format(t.code2, sd.NORDER_CODE2[t.code2]))
            if t.code3 is not None:
                self.oCode3.set(
                    '{} ({})'.format(t.code3, sd.NORDER_CODE3[t.code3]))
            if t.code4 is not None:
                self.oCode4.set(
                    '{} ({})'.format(t.code4, sd.NORDER_CODE4[t.code4]))
            if t.form is not None:
                self.oForm.set(
                    '{} ({})'.format(t.form, sd.N_OFORM[t.form]))
            if t.orderType is not None:
                self.oType.set(
                    '{} ({})'.format(t.orderType, sd.NORDER_TYPE[t.orderType]))
            if t.orderNote is not None:
                self.oNote.set(
                    '{} ({})'.format(t.orderNote, sd.NORDER_NOTE[t.orderNote]))
            if t.lang is not None:
                self.lang.set(
                    '{} ({})'.format(t.lang, sd.LANG[t.lang]))
            if t.country is not None:
                self.country.set(
                    '{} ({})'.format(t.country, sd.COUNTRIES[t.country]))

            if t.vendor is not None:
                self.vendor.set(t.vendor)
            if t.identity is not None:
                self.identity.set(t.identity)
            if t.generalNote is not None:
                self.genNote.set(t.generalNote)
            if t.internalNote is not None:
                self.intNote.set(t.internalNote)
            if t.oldOrdNo is not None:
                self.oldOrdNo.set(t.oldOrdNo)
            if t.selector is not None:
                self.selector.set(t.selector)
            if t.venAddr is not None:
                self.venAddr.set(t.venAddr)
            if t.venNote is not None:
                self.venNote.set(t.venNote)
            if t.blanketPO is not None:
                self.blanketPO.set(t.blanketPO)
            if t.venTitleNo is not None:
                self.venTitleNo.set(t.venTitleNo)
            if t.paidNote is not None:
                self.paidNote.set(t.paidNote)
            if t.shipTo is not None:
                self.shipTo.set(t.shipTo)
            if t.requestor is not None:
                self.requestor.set(t.requestor)
            if t.bibFormat is not None:
                self.bibMatForm.set(t.bibFormat)

            if t.match1st is not None:
                self.primary_match.set(t.match1st)
            if t.match2nd is not None:
                self.secondary_match.set(t.match2nd)
            if t.match3rd is not None:
                self.tertiary_match.set(t.match3rd)

    def save_template(self):
        record = dict()

        # comboboxes
        f = dict(
            tName=self.template_name.get().strip(),
            agent=self.agent[:3],
            acqType=self.acqType.get(),
            claim=self.claim.get(),
            code1=self.oCode1.get(),
            code2=self.oCode2.get(),
            code3=self.oCode3.get(),
            code4=self.oCode4.get(),
            raction=self.raction.get(),
            form=self.oForm.get(),
            orderNote=self.oNote.get(),
            orderType=self.oType.get(),
            lang=self.lang.get(),
            country=self.country.get(),
            bibFormat=self.bibMatForm.get(),
            match1st=self.primary_match.get(),
            match2nd=self.secondary_match.get(),
            match3rd=self.tertiary_match.get()
        )

        for key, value in f.iteritems():
            if value == '':
                value = None
            else:
                if key in ('match1st', 'match2nd', 'match3rd'):
                    if value == '':
                        value = None
                    record[key] = value
                elif key == 'country':
                    value = value.split(' (')[0]
                else:
                    value = value.split('(')[0].strip()
            record[key] = value

        # entry boxes
        v = dict(
            vendor=self.vendor.get().strip(),
            identity=self.identity.get().strip(),
            generalNote=self.genNote.get().strip(),
            internalNote=self.intNote.get().strip(),
            oldOrdNo=self.oldOrdNo.get().strip(),
            selector=self.selector.get().strip(),
            venAddr=self.venAddr.get().strip(),
            venNote=self.venNote.get().strip(),
            venTitleNo=self.venTitleNo.get().strip(),
            blanketPO=self.blanketPO.get().strip(),
            shipTo=self.shipTo.get().strip(),
            requestor=self.requestor.get().strip(),
            paidNote=self.paidNote.get().strip(),
        )

        for key, value in v.iteritems():
            if value == '':
                value = None
            record[key] = value

        # determine if new record or update
        if self.otid.get() != 0:
            # existing template
            proceed = tkMessageBox.askokcancel(
                'Templates',
                'Modify existing template?',
                parent=self.top)
            if proceed:
                # update
                try:
                    update_template(self.otid.get(), record)
                    tkMessageBox.showinfo(
                        'Info', 'Template successfully saved.',
                        parent=self.top)
                except OverloadError as e:
                    tkMessageBox.showerror(
                        'Data Error',
                        e,
                        parent=self.top)
        else:
            # new template
            try:
                save_template(record)
                tkMessageBox.showinfo(
                    'Info', 'Template successfully saved.',
                    parent=self.top)
                # reset the form
                self.reset()
            except OverloadError as e:
                tkMessageBox.showerror(
                    'Data error', e,
                    parent=self.top)

        # update template list
        self.update_template_lst()

    def delete_template(self):
        proceed = tkMessageBox.askyesno(
            'Template Deletion',
            'You are about to delete\n{}\nProceed?'.format(
                self.template_name.get()),
            parent=self.top)
        if proceed:
            delete_template(self.otid.get())
            self.reset()
            self.update_template_lst()

    def list_available_matches(self):
        available_matches = ['sierra_id', '001', '020', '024']
        if self.primary_match.get() in available_matches:
            available_matches.remove(self.primary_match.get())
        if self.secondary_match.get() in available_matches:
            available_matches.remove(self.secondary_match.get())
        if self.tertiary_match.get() in available_matches:
            available_matches.remove(self.tertiary_match.get())
        available_matches.append('')
        self.primaryCbx['values'] = available_matches
        self.secondaryCbx['values'] = available_matches
        self.tertiaryCbx['values'] = available_matches

    def help(self):
        text = overload_help.open_help(
            'pvr_templates_help.txt')
        help_popup = tk.Toplevel(background='white')
        help_popup.iconbitmap('./icons/help.ico')
        yscrollbar = tk.Scrollbar(help_popup, orient=tk.VERTICAL)
        yscrollbar.grid(
            row=0, column=1, rowspan=10, sticky='nsw', padx=2)
        helpTxt = tk.Text(
            help_popup,
            background='white',
            relief=tk.FLAT,
            yscrollcommand=yscrollbar.set)
        helpTxt.grid(
            row=0, column=0, sticky='snew', padx=10, pady=10)
        yscrollbar.config(command=helpTxt.yview)
        for line in text:
            helpTxt.insert(tk.END, line)
        helpTxt['state'] = tk.DISABLED

    def update_template_lst(self):
        self.templateLst.delete(0, tk.END)
        names = get_template_names(self.agent[:3])
        for name in sorted(names):
            self.templateLst.insert(tk.END, name)

    def populate_cbxs(self):
        # unblock comoboxes
        for child in self.fixedFrm.winfo_children():
            if child.winfo_class() == 'TCombobox':
                child['state'] = '!readonly'

        # populate with values
        self.acqTypeCbx['values'] = [
            '{} ({})'.format(x, y) for x, y in sorted(
                sd.NACQ_TYPE.iteritems())]
        self.acqTypeCbx['values'] = self.acqTypeCbx['values'] + ('', )
        self.claimCbx['values'] = [
            '{} ({})'.format(x, y) for x, y in sorted(
                sd.NCLAIM.iteritems())]
        self.claimCbx['values'] = self.claimCbx['values'] + ('', )
        self.oCode1Cbx['values'] = [
            '{} ({})'.format(x, y) for x, y in sorted(
                sd.NORDER_CODE1.iteritems())]
        self.oCode1Cbx['values'] = self.oCode1Cbx['values'] + ('', )
        self.oCode2Cbx['values'] = [
            '{} ({})'.format(x, y) for x, y in sorted(
                sd.NORDER_CODE2.iteritems())]
        self.oCode2Cbx['values'] = self.oCode2Cbx['values'] + ('', )
        self.oCode3Cbx['values'] = [
            '{} ({})'.format(x, y) for x, y in sorted(
                sd.NORDER_CODE3.iteritems())]
        self.oCode3Cbx['values'] = self.oCode3Cbx['values'] + ('', )
        self.oCode4Cbx['values'] = [
            '{} ({})'.format(x, y) for x, y in sorted(
                sd.NORDER_CODE4.iteritems())]
        self.oCode4Cbx['values'] = self.oCode4Cbx['values'] + ('', )
        self.ractionCbx['values'] = [
            '{} ({})'.format(x, y) for x, y in sorted(sd.NRACTION.iteritems())]
        self.ractionCbx['values'] = self.ractionCbx['values'] + ('', )
        self.oFormCbx['values'] = [
            '{} ({})'.format(x, y) for x, y in sorted(
                sd.N_OFORM.iteritems())]
        self.oFormCbx['values'] = self.oFormCbx['values'] + ('', )
        self.oTypeCbx['values'] = [
            '{} ({})'.format(x, y) for x, y in sorted(
                sd.NORDER_TYPE.iteritems())]
        self.oTypeCbx['values'] = self.oTypeCbx['values'] + ('', )
        self.oNoteCbx['values'] = [
            '{} ({})'.format(x, y) for x, y in sorted(
                sd.NORDER_NOTE.iteritems())]
        self.oNoteCbx['values'] = self.oNoteCbx['values'] + ('', )
        self.langCbx['values'] = [
            '{} ({})'.format(x, y) for x, y in sorted(
                sd.LANG.iteritems())]
        self.langCbx['values'] = self.langCbx['values'] + ('', )
        self.countryCbx['values'] = [
            '{} ({})'.format(x, y) for x, y in sorted(
                sd.COUNTRIES.iteritems())]
        self.countryCbx['values'] = self.countryCbx['values'] + ('', )

        # block comboboxes
        for child in self.fixedFrm.winfo_children():
            if child.winfo_class() == 'TCombobox':
                child['state'] = 'readonly'

        self.bibMatFormCbx['state'] = '!readonly'
        self.bibMatFormCbx['values'] = [
            '{} ({})'.format(x, y) for x, y in sorted(
                sd.N_MATFORM.iteritems())]
        self.bibMatFormCbx['values'] = self.bibMatFormCbx[
            'values'] + ('', )
        self.bibMatFormCbx['state'] = 'readonly'

    def reset(self):
        self.otid.set(0)
        self.template_name.set('')
        self.acqType.set('')
        self.claim.set('')
        self.oCode1.set('')
        self.oCode2.set('')
        self.oCode3.set('')
        self.oCode4.set('')
        self.raction.set('')
        self.oForm.set('')
        self.oNote.set('')
        self.oType.set('')
        self.vendor.set('')
        self.lang.set('')
        self.country.set('')
        self.identity.set('')
        self.genNote.set('')
        self.intNote.set('')
        self.oldOrdNo.set('')
        self.selector.set('')
        self.venAddr.set('')
        self.venNote.set('')
        self.venTitleNo.set('')
        self.blanketPO.set('')
        self.shipTo.set('')
        self.requestor.set('')
        self.paidNote.set('')
        self.bibMatForm.set('')
        self.primary_match.set('')
        self.secondary_match.set('')
        self.tertiary_match.set('')


class ProcessVendorFiles(tk.Frame):
    """
    GUI to processing vendor files module which preprocesses records
    for Sierra import
    """

    def __init__(self, parent, controller, **app_data):
        self.parent = parent
        tk.Frame.__init__(self, parent, background='white')
        self.controller = controller
        self.activeW = app_data['activeW']
        self.activeW.trace('w', self.observer)

        self.cur_manager = BusyManager(self)

        # widget variables
        self.target_name = tk.StringVar()
        self.target = None
        self.file_count = tk.StringVar()
        self.marcVal = tk.IntVar()
        self.locVal = tk.IntVar()
        self.processed = tk.StringVar()
        self.current_process = tk.StringVar()
        self.archived = tk.StringVar()
        self.validated = tk.StringVar()
        self.last_directory_check = tk.IntVar()
        self.last_directory = None
        self.files = None
        self.system = tk.StringVar()
        self.system.trace('w', self.system_observer)
        self.last_used_sys = None
        self.library = tk.StringVar()
        self.last_used_lib = None
        self.agent = tk.StringVar()
        self.agent.trace('w', self.agent_observer)
        self.last_used_agent = None
        self.template = tk.StringVar()

        # logos
        self.nyplLogo = tk.PhotoImage(file='./icons/nyplLogo.gif')
        self.bplLogo = tk.PhotoImage(file='./icons/bplLogo.gif')

        # layout of the main frame
        self.rowconfigure(0, minsize=5)
        self.rowconfigure(1, minsize=120)
        self.rowconfigure(15, minsize=10)
        self.columnconfigure(0, minsize=5)
        self.columnconfigure(2, minsize=10)
        self.columnconfigure(4, minsize=5)

        # layout of the base frame
        self.baseFrm = ttk.LabelFrame(
            self,
            text='Process Vendor File')
        self.baseFrm.grid(
            row=1, column=1, rowspan=6, sticky='snew')
        self.baseFrm.rowconfigure(0, minsize=10)
        self.baseFrm.rowconfigure(2, minsize=5)
        self.baseFrm.rowconfigure(4, minsize=5)
        self.baseFrm.rowconfigure(7, minsize=5)
        self.baseFrm.rowconfigure(9, minsize=5)
        self.baseFrm.rowconfigure(14, minsize=10)
        self.baseFrm.rowconfigure(18, minsize=10)
        self.baseFrm.columnconfigure(0, minsize=10)
        self.baseFrm.columnconfigure(7, minsize=10)

        # layout of target parameters
        self.targetFrm = ttk.Frame(
            self.baseFrm,
            borderwidth=2,
            relief='ridge')
        self.targetFrm.grid(
            row=1, column=1, columnspan=6, sticky='snew')

        # system drop down menu
        self.systemLbl = ttk.Label(
            self.targetFrm,
            text='system:')
        self.systemLbl.grid(
            row=0, column=0, sticky='snew')
        self.systemCbx = ttk.Combobox(
            self.targetFrm,
            textvariable=self.system,
            width=10)
        self.systemCbx.grid(
            row=0, column=1, sticky='nsw', padx=5, pady=10)

        # destination library drop down menu
        self.libraryLbl = ttk.Label(
            self.targetFrm,
            text='destination:')
        self.libraryLbl.grid(
            row=0, column=2, sticky='snew')
        self.libraryCbx = ttk.Combobox(
            self.targetFrm,
            textvariable=self.library,
            width=10)
        self.libraryCbx.grid(
            row=0, column=3, sticky='nsw', padx=5, pady=10)

        # department drop down menu
        self.agentLbl = ttk.Label(
            self.targetFrm,
            text='department:')
        self.agentLbl.grid(
            row=0, column=4, sticky='snew')
        self.agentCbx = ttk.Combobox(
            self.targetFrm,
            textvariable=self.agent)
        self.agentCbx.grid(
            row=0, column=5, columnspan=3, sticky='snew', padx=5, pady=10)

        # query method/database
        self.query_targetLbl = ttk.Label(
            self.targetFrm,
            text='query database/method:')
        self.query_targetLbl.grid(
            row=1, column=0, columnspan=2, sticky='snew')
        self.query_targetCbx = ttk.Combobox(
            self.targetFrm,
            textvariable=self.target_name)
        self.query_targetCbx.grid(
            row=1, column=2, columnspan=6, sticky='snew', padx=5, pady=10)

        # templates to be applied
        self.templateLbl = ttk.Label(
            self.targetFrm,
            text='apply template:')
        self.templateLbl.grid(
            row=2, column=0, columnspan=2, sticky='snew')
        self.templateCbx = ttk.Combobox(
            self.targetFrm,
            postcommand=self.list_templates,
            textvariable=self.template)
        self.templateCbx.grid(
            row=2, column=2, columnspan=5, sticky='sew', padx=5, pady=10)
        # edit template button
        edit = tk.PhotoImage(file='./icons/edit.gif')
        self.templateBtn = ttk.Button(
            self.targetFrm,
            image=edit,
            command=self.create_template)
        self.templateBtn.grid(
            row=2, column=7, sticky='ne', padx=5)
        self.templateBtn.image = edit

        # browse & ftp buttons
        self.selectBtn = ttk.Button(
            self.baseFrm,
            text='browse files',
            command=self.select,
            cursor='hand2',
            width=12)
        self.selectBtn.grid(
            row=3, column=1, sticky='nw', padx=5, pady=10)
        self.ftpBtn = ttk.Button(
            self.baseFrm,
            text='get via FTP',
            command=self.ftp,
            cursor='hand2',
            width=12)
        self.ftpBtn.grid(
            row=3, column=2, sticky='nw', padx=5, pady=10)

        # default output directory
        self.default_directoryCbtn = ttk.Checkbutton(
            self.baseFrm,
            cursor='hand2',
            text='previous output directory',
            variable=self.last_directory_check)
        self.default_directoryCbtn.grid(
            row=3, column=3, sticky='snew')

        # selected files
        self.selectedLbl = ttk.Label(
            self.baseFrm,
            textvariable=self.file_count)
        self.selectedLbl.grid(
            row=5, column=1, columnspan=2, sticky='nw')

        self.selected_filesEnt = ttk.Entry(
            self.baseFrm,
            style='Flat.TEntry',
            state='readonly')
        self.selected_filesEnt.grid(
            row=6, column=1, columnspan=6, sticky='nwe')

        # validation area
        self.validateLbl = ttk.Label(
            self.baseFrm,
            text='validation:')
        self.validateLbl.grid(
            row=8, column=1, sticky='nw')
        self.marcEditValCbtn = ttk.Checkbutton(
            self.baseFrm,
            cursor='hand2',
            text='MARCEdit validation',
            variable=self.marcVal).grid(
            row=8, column=2, sticky='snw')
        self.localValCbtn = ttk.Checkbutton(
            self.baseFrm,
            cursor='hand2',
            text='local specs validation',
            variable=self.locVal).grid(
            row=8, column=3, columnspan=2, sticky='snw', padx=15)

        self.processBtn = ttk.Button(
            self.baseFrm,
            text='process',
            command=self.process,
            cursor='hand2',
            width=12)
        self.processBtn.grid(
            row=13, column=1, sticky='nw')

        self.progbar = ttk.Progressbar(
            self.baseFrm,
            mode='determinate',
            orient=tk.HORIZONTAL,)
        self.progbar.grid(
            row=13, column=2, sticky='snew', pady=10)

        self.current_processLbl = ttk.Label(
            self.baseFrm,
            textvariable=self.current_process)
        self.current_processLbl.grid(
            row=13, column=3, columnspan=2, sticky='snw', padx=5, pady=10)

        # report layout
        self.reportFrm = ttk.Frame(
            self.baseFrm,
            borderwidth=2,
            relief='ridge')
        self.reportFrm.grid(
            row=15, column=1, rowspan=3, columnspan=6, sticky='snew')

        self.reportFrm.rowconfigure(0, minsize=5)
        self.reportFrm.rowconfigure(4, minsize=5)
        self.reportFrm.rowconfigure(7, minsize=5)
        self.reportFrm.columnconfigure(0, minsize=2)
        self.reportFrm.columnconfigure(2, minsize=50)
        self.reportFrm.columnconfigure(4, minsize=50)
        self.reportFrm.columnconfigure(6, minsize=50)
        self.reportFrm.columnconfigure(7, minsize=2)

        self.validatedLbl = ttk.Label(
            self.reportFrm,
            textvariable=self.validated)
        self.validatedLbl.grid(
            row=1, column=1, columnspan=6, sticky='nw')

        self.processedLbl = ttk.Label(
            self.reportFrm,
            textvariable=self.processed)
        self.processedLbl.grid(
            row=2, column=1, columnspan=6, sticky='nw')

        self.archivedLbl = ttk.Label(
            self.reportFrm,
            textvariable=self.archived)
        self.archivedLbl.grid(
            row=3, column=1, columnspan=6, sticky='nw')

        self.valid_reportBtn = ttk.Button(
            self.reportFrm,
            text='validation',
            command=self.errors,
            cursor='hand2',
            width=10)
        self.valid_reportBtn.grid(
            row=5, column=1, sticky='sw')
        self.createToolTip(
            self.valid_reportBtn,
            'display validation reports')

        self.statsBtn = ttk.Button(
            self.reportFrm,
            text='stats',
            command=self.batch_summary_window,
            cursor='hand2',
            width=10)
        self.statsBtn.grid(
            row=5, column=3, sticky='sw')
        self.createToolTip(
            self.statsBtn,
            'display statistics of your last processing')

        self.archiveBtn = ttk.Button(
            self.reportFrm,
            text='archive',
            command=self.archive,
            cursor='hand2',
            width=10)
        self.archiveBtn.grid(
            row=5, column=5, sticky='sw')
        self.createToolTip(
            self.archiveBtn,
            'save statistics and archive output MARC files')

        # default logo
        logo = tk.PhotoImage(file='./icons/PVRsmall.gif')
        self.logoDsp = ttk.Label(
            self, image=logo)
        # prevent image to be garbage collected by Python
        self.logoDsp.image = logo
        self.logoDsp.grid(
            row=1, column=8, columnspan=3, sticky='snew')

        # default activation labels
        self.libraryLbl = ttk.Label(
            self, textvariable=self.library,
            style='Bold.TLabel')
        self.libraryLbl.grid(
            row=2, column=9, sticky='new')

        self.agentLbl = ttk.Label(
            self, textvariable=self.agent,
            style='Bold.TLabel')
        self.agentLbl.grid(
            row=3, column=9, sticky='new')

        # navigation buttons
        self.helpBtn = ttk.Button(
            self,
            text='help',
            command=self.help,
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

    def createToolTip(self, widget, text):
        toolTip = ToolTip(widget)

        def enter(event):
            toolTip.showtip(text)

        def leave(event):
            toolTip.hidetip()

        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)

    def select(self):

        # determine last used directory
        user_data = shelve.open(USER_DATA)
        paths = user_data['paths']
        if 'pvr_last_open_dir' in paths:
            last_open_dir = paths['pvr_last_open_dir']
        else:
            last_open_dir = MY_DOCS

        # select files for processing
        files = tkFileDialog.askopenfilenames(
            parent=self,
            title='Select files',
            initialdir=last_open_dir)

        if len(files) > 0:
            self.files = files
            # update selected qty
            self.file_count.set('{} file(s) selected:'.format(len(self.files)))
            names = []
            for file in self.files:
                names.append(os.path.split(file)[1])
            self.selected_filesEnt['state'] = '!readonly'
            self.selected_filesEnt.delete(0, tk.END)
            self.selected_filesEnt.insert(0, ','.join(names))
            self.selected_filesEnt['state'] = 'readonly'

            # save accessed directory for the future
            last_open_dir = os.path.split(self.files[0])[0]
            paths = user_data['paths']
            paths['pvr_last_open_dir'] = last_open_dir
            user_data['paths'] = paths
            user_data.close()

            self.reset()

    def ftp(self):
        if self.system.get() == '':
            tkMessageBox.showwarning(
                'FTP', 'Please select system first')
        else:
            TransferFiles(self, self.system.get())

    def list_templates(self):
        names = get_template_names(self.agent.get()[:3])
        self.templateCbx['values'] = names
        self.templateCbx['state'] = 'readonly'

    def create_template(self):
        if self.agent.get() == 'cataloging' or \
                self.agent.get() == '':
            pass
        else:
            OrderTemplate(self, agent=self.agent.get())

    def process(self):
        self.reset()
        delete_validation_report()

        user_data = shelve.open(USER_DATA)

        # store parameters for the next time
        user_data['pvr_system'] = self.system.get()
        user_data['pvr_library'] = self.library.get()
        user_data['pvr_agent'] = self.agent.get()
        user_data['pvr_locval'] = self.locVal.get()
        user_data['pvr_marcval'] = self.marcVal.get()
        user_data['pvr_template'] = self.template.get()

        # record used connection target
        if 'Z3950' in self.target_name.get():
            name = self.target_name.get().split(' (')[0]
            method = 'Z3950'
        elif 'Sierra API' in self.target_name.get():
            name = self.target_name.get().split(' (')[0]
            method = 'Sierra API'
        elif 'Platform API' in self.target_name.get():
            name = self.target_name.get().split(' (')[0]
            method = 'Platform API'
        else:
            name = None
            method = None
        self.target = {'target': name, 'method': method}
        user_data['pvr_default_target'] = self.target

        # ask for folder for output marc files
        dir_opt = {}
        dir_opt['mustexist'] = False
        dir_opt['parent'] = self
        dir_opt['title'] = 'Please select directory for output files'

        if self.last_directory_check.get() == 0:
            dir_opt['initialdir'] = MY_DOCS
            d = tkFileDialog.askdirectory(**dir_opt)
            if d != '':
                self.last_directory = d
                paths = user_data['paths']
                paths['pvr_default_save_dir'] = d
                user_data['paths'] = paths
                # update tooltip displaying the folder
                self.createToolTip(
                    self.default_directoryCbtn,
                    self.last_directory)
            else:
                m = 'Please select a destination folder for ' \
                    'output MARC files to procceed.'
                tkMessageBox.showwarning('Missing Destination Folder', m)
        else:
            if 'pvr_default_save_dir' in user_data[
                    'paths']:
                self.last_directory = user_data[
                    'paths']['pvr_default_save_dir']
            else:
                dir_opt['initialdir'] = MY_DOCS
                d = tkFileDialog.askdirectory(**dir_opt)
                if d != '':
                    self.last_directory = d
                    paths = user_data['paths']
                    paths['pvr_default_save_dir'] = d
                    user_data['paths'] = paths
                    # update tooltip displaying the folder
                    self.createToolTip(
                        self.default_directoryCbtn,
                        self.last_directory)
                else:
                    m = 'Please select a destination folder for ' \
                        'output MARC files to procceed.'
                    tkMessageBox.showwarning('Missing Destination Folder', m)
        user_data.close()

        # verify all paramaters are present
        required_params = True
        missing_params = []
        if self.system.get() == '':
            required_params = False
            missing_params.append('Please select system')
        if self.system.get() == 'NYPL':
            if self.library.get() == '':
                required_params = False
                missing_params.append('Please select destination library')
            if self.agent.get() == '':
                required_params = False
                missing_params.append('Please select department')
        if self.target_name.get() == '':
            required_params = False
            missing_params.append('Please select query target')
        if self.files is None:
            required_params = False
            missing_params.append('Please select files for processing.')
        if self.last_directory is None:
            required_params = False
            missing_params.append(
                'Please select a directory to output processed files')

        if self.agent.get() in ('selection', 'acquisition') and \
                self.template.get() == '':
            required_params = False
            missing_params.append(
                'Selection and Acquisition users must specify the template')

        if not required_params:
            tkMessageBox.showwarning(
                'Missing parameters', '\n '.join(missing_params))
        else:
            # run process
            self.cur_manager.busy()

            # clear batch summary and stats from previous run
            batch = shelve.open(BATCH_META)
            batch.clear()
            batch.close()

            stats = shelve.open(BATCH_STATS)
            stats.clear()
            stats.close()

            # calculate maximum for progbar
            legal_files = True
            total_bib_count = 0
            for file in self.files:
                try:
                    bib_count = bibs.count_bibs(file)
                    total_bib_count += bib_count
                except OverloadError as e:
                    self.cur_manager.notbusy()
                    legal_files = False
                    tkMessageBox.showerror('Incorrect file', e)

            if legal_files:
                self.progbar['maximum'] = total_bib_count

            # run validation if requested
            if self.marcVal.get() == 1:
                marcval = True
            else:
                marcval = False
                self.validated.set('validation: MARC syntax check skipped')

            if self.locVal.get() == 1:
                locval = True
            else:
                msg = self.validated.get() + ', local specs check skipped'
                self.validated.set(msg)
                locval = False

            # run validation
            try:
                module_logger.debug('Validating files.')
                self.current_process.set('validating...')
                valid_files = validate_files(
                    self.system.get().lower(),
                    self.agent.get()[:3],
                    self.files, marcval, locval)

                if valid_files:
                    module_logger.info(
                        'Validating batch of records. '
                        'Active validators: marcval={}, locval={}. '
                        'Results: records are valid.'.format(
                            self.marcVal.get(), self.locVal.get()))
                    self.validated.set('validation: records are A-OK!')
                else:
                    module_logger.warning(
                        'Validating batch of records. '
                        'Active validators: marcVal={}, locVal={}. '
                        'Results: errors found.'.format(
                            self.marcVal.get(), self.locVal.get()))
                    self.current_process.set('')
                    self.cur_manager.notbusy()
                    self.validated.set('validation: ERRORS FOUND!')
                    m = 'Some of the records in selected file(s) \n' \
                        'are not valid.\n' \
                        'Please see error report for details.'
                    tkMessageBox.showerror('Validation', m)
            except OverloadError as e:
                self.current_process.set('')
                module_logger.error(
                    'Error while validating. Error: {}'.format(
                        e))
                valid_files = False
                self.cur_manager.notbusy()
                tkMessageBox.showerror('Validation', e)

            if legal_files and valid_files:
                if self.template.get() == '':
                    template = None
                else:
                    template = self.template.get()

                try:
                    run_processing(
                        self.files, self.system.get().lower(),
                        self.library.get(), self.agent.get()[:3],
                        self.target['method'], self.target['target'],
                        template,
                        self.last_directory,
                        self.progbar, self.current_process)

                    # confirm files have been processed
                    self.processed.set(
                        'processed: {} file(s) including {} record(s)'.format(
                            len(self.files), total_bib_count))

                    self.current_process.set('')

                    # launch processing report
                    self.batch_summary_window()

                except OverloadError as e:
                    self.current_process.set('interrupted...')
                    self.cur_manager.notbusy()
                    tkMessageBox.showerror(
                        'Processing Error', e)
                except Exception as exc:
                    self.current_process.set('interrupted...')
                    self.cur_manager.notbusy()
                    # log and display error
                    _, _, exc_traceback = sys.exc_info()
                    tb = format_traceback(exc, exc_traceback)
                    module_logger.error(
                        'Unhandled error: {}'.format(tb))
                    tkMessageBox.showerror(
                        'Processing Error', exc)
                finally:
                    self.cur_manager.notbusy()

    def archive(self):
        try:
            save_stats()
        except OverloadError as e:
            tkMessageBox.showerror('Stats error', e)

        # move created files to the archive
        archive_files = []
        for file in os.listdir(self.last_directory):
            if file.endswith('.mrc') and (
                    '.DUP-' in file or '.NEW-' in file or
                    '.PRC-' in file):
                archive_files.append(file)
        if len(archive_files) > 0:
            self.topA = tk.Toplevel(self, background='white')
            # self.topD.minsize(width=800, height=500)
            self.topA.iconbitmap('./icons/archive.ico')
            self.topA.title('Select files to be archived')

            self.topA.columnconfigure(0, minsize=10)
            self.topA.columnconfigure(4, minsize=10)
            self.topA.rowconfigure(0, minsize=10)

            ttk.Label(
                self.topA, text='Check files to be archived:').grid(
                row=1, column=1, columnspan=2, sticky='snw')

            n = 2
            self.check_id = dict()
            for file in archive_files:
                self.check_id[file] = tk.IntVar()
                check = ttk.Checkbutton(
                    self.topA,
                    cursor='hand2',
                    text=file,
                    variable=self.check_id[file])
                check.grid(
                    row=n, column=1, columnspan=3, sticky='nsw')
                n += 1
            self.topA.rowconfigure(n + 1, minsize=10)
            ttk.Button(
                self.topA,
                text='archive',
                width=12,
                cursor='hand2',
                command=self.move_files).grid(
                    row=n + 2, column=1, sticky='nw', padx=5)
            ttk.Button(
                self.topA,
                text='close',
                width=12,
                cursor='hand2',
                command=self.topA.destroy).grid(
                    row=n + 2, column=3, sticky='nw', padx=5)
            self.topA.rowconfigure(n + 3, minsize=10)

    def move_files(self):
        batch = shelve.open(BATCH_META)
        system = batch['system']
        batch.close()

        user_data = shelve.open(USER_DATA)
        paths = user_data['paths']
        if system == 'bpl' and \
                'bpl_archive_dir' in paths:
            archive_dir = paths['bpl_archive_dir']
        elif system == 'nypl' and \
                'nyp_archive_dir' in paths:
            archive_dir = paths['nyp_archive_dir']
        else:
            archive_dir = None
            m = 'Please select archive directory in Settings'
            tkMessageBox.showerror('Error', m)
        user_data.close()

        if archive_dir is not None:
            all_archived = True
            for file, value in self.check_id.iteritems():
                if value.get() == 1:
                    # check if file exists
                    src = os.path.join(self.last_directory, file)
                    dst = os.path.join(archive_dir, file)
                    if os.path.exists(dst):
                        renaming = True
                        n = 1
                        while renaming:
                            if '.DUP-' in file:
                                s = '.DUP-'
                            elif '.NEW-' in file:
                                s = '.NEW-'
                            elif '.PRC-' in file:
                                s = '.PRC-'
                            p = file.index(s)
                            file = '{}{}{}'.format(file[:p + 5], n, file[-4:])
                            dst = os.path.join(archive_dir, file)
                            if not os.path.exists(dst):
                                renaming = False
                            else:
                                n += 1

                    # archive selected
                    try:
                        shutil.copy2(src, dst)
                        os.remove(src)
                    except IOError:
                        all_archived = False
                        module_logger.error(
                            'Archiving error: not able to move '
                            'file: {} to: {}'.format(
                                src, dst))
                        m = 'Encounted error while ' \
                            'archiving file:\n{}'.format(src)
                        tkMessageBox.showerror('Archiving error', m)
                        self.topA.destroy()
            if all_archived:
                self.archived.set('archived: completed')
                m = 'Your MARC files have been added to the archive'
                tkMessageBox.showinfo('Archiving message', m)
                self.topA.destroy()

    def errors(self):
        # local specs validation will be saved in a different file
        # and displayed in a cumulative report

        if os.path.isfile(CVAL_REP) or os.path.isfile(LSPEC_REP) or \
                os.path.isfile(DVAL_REP):
            self.topV = tk.Toplevel(self, background='white')
            # self.topV.minsize(width=800, height=500)
            self.topV.iconbitmap('./icons/report.ico')
            self.topV.title('Vendor files validation report')

            self.topV.columnconfigure(0, minsize=10)
            self.topV.columnconfigure(1, minsize=750)
            self.topV.columnconfigure(11, minsize=10)
            self.topV.rowconfigure(0, minsize=10)
            self.topV.rowconfigure(1, minsize=450)
            self.topV.rowconfigure(11, minsize=10)
            self.topV.rowconfigure(13, minsize=10)

            self.yscrollbarV = tk.Scrollbar(self.topV, orient=tk.VERTICAL)
            self.yscrollbarV.grid(
                row=1, column=10, rowspan=10, sticky='nse', padx=2)
            self.xscrollbarV = tk.Scrollbar(self.topV, orient=tk.HORIZONTAL)
            self.xscrollbarV.grid(
                row=10, column=1, columnspan=9, sticky='new', padx=2)

            self.reportVTxt = tk.Text(
                self.topV,
                borderwidth=0,
                wrap=tk.NONE,
                xscrollcommand=self.xscrollbarV.set,
                yscrollcommand=self.yscrollbarV.set)
            self.reportVTxt.grid(
                row=1, column=1, rowspan=9, columnspan=9, sticky='snew')
            self.reportVTxt.tag_config('red', foreground='red', underline=1)

            self.yscrollbarV.config(command=self.reportVTxt.yview)
            self.xscrollbarV.config(command=self.reportVTxt.xview)

            ttk.Button(
                self.topV,
                text='close',
                width=12,
                cursor='hand2',
                command=self.topV.destroy).grid(
                row=12, column=6, sticky='ne', padx=5)

            ttk.Button(
                self.topV,
                text='download',
                width=12,
                cursor='hand2',
                command=self.download_validation).grid(
                row=12, column=5, sticky='nw', padx=5)

            # generate report
            self.create_validation_report()
        else:
            m = 'Validation report not available'
            tkMessageBox.showwarning('validation report', m)

    def batch_summary_window(self):

        self.topD = tk.Toplevel(self, background='white')
        # self.topD.minsize(width=800, height=500)
        self.topD.iconbitmap('./icons/report.ico')
        self.topD.title('Vendor files report')

        self.topD.columnconfigure(0, minsize=10)
        self.topD.columnconfigure(1, minsize=750)
        self.topD.columnconfigure(11, minsize=10)
        self.topD.rowconfigure(0, minsize=10)
        self.topD.rowconfigure(1, minsize=450)
        self.topD.rowconfigure(11, minsize=10)
        self.topD.rowconfigure(13, minsize=10)

        self.yscrollbarD = tk.Scrollbar(self.topD, orient=tk.VERTICAL)
        self.yscrollbarD.grid(
            row=1, column=10, rowspan=9, sticky='nse', padx=2)
        self.xscrollbarD = tk.Scrollbar(self.topD, orient=tk.HORIZONTAL)
        self.xscrollbarD.grid(
            row=10, column=1, columnspan=9, sticky='swe')

        self.reportDTxt = tk.Text(
            self.topD,
            borderwidth=0,
            wrap=tk.NONE,
            yscrollcommand=self.yscrollbarD.set,
            xscrollcommand=self.xscrollbarD.set)
        self.reportDTxt.grid(
            row=1, column=1, rowspan=9, columnspan=9, sticky='snew')
        self.reportDTxt.tag_config('blue', foreground='blue', underline=1)
        self.reportDTxt.tag_config('red', foreground='red')

        self.yscrollbarD.config(command=self.reportDTxt.yview)
        self.xscrollbarD.config(command=self.reportDTxt.xview)

        ttk.Button(
            self.topD,
            text='detailed view',
            width=12,
            cursor='hand2',
            command=self.detailed_view_window).grid(
            row=12, column=1, sticky='ne', padx=5)

        ttk.Button(
            self.topD,
            text='download',
            width=12,
            cursor='hand2',
            command=self.download_errors).grid(
            row=12, column=2, sticky='nw', padx=5)

        ttk.Button(
            self.topD,
            text='send',
            width=12,
            cursor='hand2',
            command=self.send_to_sheet).grid(
            row=12, column=3, sticky='nw', padx=5)

        ttk.Button(
            self.topD,
            text='close',
            width=12,
            cursor='hand2',
            command=self.topD.destroy).grid(
            row=12, column=6, sticky='nw', padx=5)

        # generate report
        self.create_processing_report()

    def detailed_view_window(self):

        self.topB = tk.Toplevel(self, background='white')
        # self.topD.minsize(width=800, height=500)
        self.topB.iconbitmap('./icons/report.ico')
        self.topB.title('Vendor files detailed view')

        self.topB.columnconfigure(0, minsize=10)
        self.topB.columnconfigure(1, minsize=750)
        self.topB.columnconfigure(11, minsize=10)
        self.topB.rowconfigure(0, minsize=10)
        self.topB.rowconfigure(1, minsize=450)
        self.topB.rowconfigure(11, minsize=10)
        self.topB.rowconfigure(13, minsize=10)

        self.yscrollbarB = tk.Scrollbar(self.topB, orient=tk.VERTICAL)
        self.yscrollbarB.grid(
            row=1, column=10, rowspan=9, sticky='nse', padx=2)
        self.xscrollbarB = tk.Scrollbar(self.topB, orient=tk.HORIZONTAL)
        self.xscrollbarB.grid(
            row=10, column=1, columnspan=9, sticky='swe')

        self.reportBTxt = tk.Text(
            self.topB,
            borderwidth=0,
            wrap=tk.NONE,
            yscrollcommand=self.yscrollbarB.set,
            xscrollcommand=self.xscrollbarB.set)
        self.reportBTxt.grid(
            row=1, column=1, rowspan=9, columnspan=9, sticky='snew')
        self.reportBTxt.tag_config('blue', foreground='blue', underline=1)
        self.reportBTxt.tag_config('red', foreground='red')

        self.yscrollbarB.config(command=self.reportBTxt.yview)
        self.xscrollbarB.config(command=self.reportBTxt.xview)

        ttk.Button(
            self.topB,
            text='download',
            width=12,
            cursor='hand2',
            command=self.download_details).grid(
            row=12, column=5, sticky='nw', padx=5)

        ttk.Button(
            self.topB,
            text='close',
            width=12,
            cursor='hand2',
            command=self.topB.destroy).grid(
            row=12, column=6, sticky='nw', padx=5)

        # generate report
        self.create_detailed_report()

    def create_validation_report(self):
        # reset report
        self.reportVTxt.delete(1.0, tk.END)

        # create new MARCEdit validation report
        try:
            with open(DVAL_REP, 'r') as dReport:
                self.reportVTxt.insert(
                    tk.END, 'Default validation report(s):\n', 'red')
                for line in dReport:
                    self.reportVTxt.insert(tk.END, line)
        except IOError:
            pass

        try:
            with open(CVAL_REP, 'r') as mReport:
                self.reportVTxt.insert(
                    tk.END, '\n\nMARCEdit validation report(s):\n\n', 'red')
                for line in mReport:
                    self.reportVTxt.insert(tk.END, line)
        except IOError:
            pass
        try:
            with open(LSPEC_REP, 'r') as lReport:
                self.reportVTxt.insert(
                    tk.END, '\n\nLocal specs validation report(s):\n\n', 'red')
                for line in lReport:
                    self.reportVTxt.insert(tk.END, line)

        except IOError:
            pass

        self.reportVTxt['state'] = tk.DISABLED

    def create_processing_report(self):
        # reset report
        self.reportDTxt.delete(1.0, tk.END)

        # generate summary
        try:
            self.last_used_sys, self.last_used_lib, \
                self.last_used_agent, summary = \
                reports.generate_processing_summary(
                    BATCH_META)
            for line in summary:
                self.reportDTxt.insert(tk.END, line)
        except KeyError:
            self.reportDTxt.insert(tk.END, 'SUMMARY PARSING ERROR\n')
        self.reportDTxt.insert(tk.END, ('-' * 60) + '\n')

        # create dataframe to be tabulated
        try:
            module_logger.debug(
                'Mapping BATCH_STATS to dataframe for general '
                'stats report for {}.'.format(self.last_used_sys))
            df = reports.shelf2dataframe(BATCH_STATS, self.last_used_sys)
        except KeyError as e:
            module_logger.error(
                'Unable to map BATCH_STATS to dataframe. '
                'Error: {}'.format(e))
            df = None
        except ValueError as e:
            module_logger.error(
                'Unable to map BATCH_STATS to dataframe.'
                'Error: {}'.format(e))
            df = None

        # generate vendor stats
        module_logger.debug(
            'Generating vendor breakdown section for '
            '{}.'.format(self.last_used_sys))
        self.reportDTxt.insert(tk.END, 'Vendor breakdown:\n', 'blue')
        if df is not None:
            if df.size > 0:
                stats = reports.create_stats(self.last_used_sys, df)
                self.reportDTxt.insert(tk.END, stats.to_string())
            elif df.size == 0:
                self.reportDTxt.insert(tk.END, 'Nothing to report.')
        else:
            self.reportDTxt.insert(tk.END, 'STATS PARSING ERROR\n')
        self.reportDTxt.insert(
            tk.END, '\n' + ('-' * 120) + '\n')

        # report duplicates
        module_logger.debug(
            'Generating duplicate reports section for {}-{}.'.format(
                self.last_used_sys, self.last_used_lib))
        self.reportDTxt.insert(tk.END, 'Duplicates report:\n', 'blue')
        if df is not None:
            self.dups = reports.report_dups(
                self.last_used_sys, self.last_used_lib, df)
            if self.dups.size == 0:
                self.reportDTxt.insert(tk.END, 'All clear\n')
            else:
                self.reportDTxt.insert(tk.END, self.dups.to_string() + '\n')
        else:
            self.dups = None
            self.reportDTxt.insert(
                tk.END, 'DUPLICATE REPORT PARSING ERROR\n')
        self.reportDTxt.insert(
            tk.END, '\n' + ('-' * 120) + '\n')

        # report callNo issues
        module_logger.debug(
            'Generating call number issues section.')
        if self.last_used_lib != 'research':
            self.reportDTxt.insert(tk.END, 'Call number issues:\n', 'blue')

            if df is not None:
                self.callNos = reports.report_callNo_issues(
                    df, self.last_used_agent)
                if self.callNos.size == 0:
                    self.reportDTxt.insert(tk.END, 'All clear\n')
                else:
                    if self.last_used_agent == 'cat':
                        self.reportDTxt.insert(
                            tk.END,
                            "Please note: in case of BT LEASED bibs without vendor "
                            "supplied call number (None in column 'vendor_callNo')\n"
                            "a cataloger must copy the call number from order's PO per line "
                            "to the bib MARC field '{}' and supply appropriate subfield "
                            "codes.\n\n".format(
                                '091' if self.last_used_sys == 'NYPL' else '099'))
                    self.reportDTxt.insert(
                        tk.END, self.callNos.to_string() + '\n')
            else:
                self.callNos = None
                self.reportDTxt.insert(
                    tk.END, 'CALL NUMBER CONFLICTS PARSING ERROR\n')
            self.reportDTxt.insert(
                tk.END, '\n' + ('-' * 120) + '\n')
        else:
            self.callNos = None

        # prevent edits
        self.reportDTxt['state'] = tk.DISABLED

    def create_detailed_report(self):
        # reset report
        self.reportBTxt.delete(1.0, tk.END)

        # create dataframe to be tabulated
        try:
            df = reports.shelf2dataframe(BATCH_STATS, self.last_used_sys)
        except KeyError as e:
            module_logger.error(
                'Unable to map BATCH_STATS to dataframe. '
                'Error: {}'.format(e))
            df = None
        except ValueError as e:
            module_logger.error(
                'Unable to map BATCH_STATS to dataframe.'
                'Error: {}'.format(e))
            df = None

        module_logger.debug(
            'Generating detailed report for {}-{}'.format(
                self.last_used_sys, self.last_used_lib))
        if df is not None:
            self.df_details = reports.report_details(
                self.last_used_sys, self.last_used_lib, df)
            self.reportBTxt.insert(tk.END, self.df_details.to_string())
        else:
            self.df_details = None
            self.reportBTxt.insert(tk.END, 'DETAILED REPORT PARSING ERROR')

        # prevent edits
        self.reportBTxt['state'] = tk.DISABLED

    def download_validation(self):
        date_today = date.today().strftime('%y%m%d')
        fh = '{}-{}-pvr-validation-{}.txt'.format(
            self.last_used_sys, self.last_used_lib, date_today)

        dir_opt = {}
        dir_opt['parent'] = self.topV
        dir_opt['title'] = 'Save As'
        dir_opt['initialdir'] = self.last_directory
        dir_opt['initialfile'] = fh

        fh = tkFileDialog.asksaveasfilename(**dir_opt)
        try:
            if fh != '':
                sep = '{}\n'.format('#' * 50)
                with open(fh, 'w') as report:
                    if os.path.isfile(DVAL_REP):
                        with open(DVAL_REP, 'r') as dReport:
                            report.write(sep)
                            report.write('Default validation:\n')
                            for line in dReport:
                                report.write(line)
                    if os.path.isfile(CVAL_REP):
                        with open(CVAL_REP, 'r') as mReport:
                            report.write('\n\n' + sep)
                            report.write('MARCEdit validation:\n')
                            for line in mReport:
                                report.write(line)
                    if os.path.isfile(LSPEC_REP):
                        with open(LSPEC_REP, 'r') as lReport:
                            report.write('\n\n' + sep)
                            report.write('Local specs validation:\n')
                            for line in lReport:
                                report.write(line)

                tkMessageBox.showinfo(
                    'Download', 'Report saved successfully.', parent=self.topV)

        except IOError as e:
            module_logger.error(
                'Unable to download validation report. Error: {}'.format(e))
            tkMessageBox.showerror(
                'Save Error',
                'Encountered error while saving the report. Aborting.',
                parent=self.topV)

    def download_errors(self):
        # suggested name
        date_today = date.today().strftime('%y%m%d')
        fh = '{}-{}-pvr-errors-{}.csv'.format(
            self.last_used_sys, self.last_used_lib, date_today)

        dir_opt = {}
        dir_opt['parent'] = self.topD
        dir_opt['title'] = 'Save As'
        dir_opt['initialdir'] = self.last_directory
        dir_opt['initialfile'] = fh

        fh = tkFileDialog.asksaveasfilename(**dir_opt)
        try:
            if fh != '':
                if self.dups is not None:
                    with open(fh, 'w') as file:
                        file.write('Duplicate Report:\n')
                    self.dups.to_csv(fh, index=False, mode='a')
                if self.callNos is not None:
                    with open(fh, 'a') as file:
                        file.write('\nCall Number Report:\n')
                    self.callNos.to_csv(fh, index=False, mode='a')
                tkMessageBox.showinfo(
                    'Download', 'Report saved successfully.', parent=self.topD)
        except IOError as e:
            module_logger.error(
                'Unable to download report. Error: {}'.format(e))
            tkMessageBox.showerror(
                'Save Error',
                'Encountered error while saving the report. Aborting.',
                parent=self.topD)

    def send_to_sheet(self):
        self.cur_manager.busy()
        final_msg = ''

        # identify correct google folder id
        user_data = shelve.open(USER_DATA)
        try:
            if self.last_used_sys == 'NYPL':
                parent_id = user_data['gdrive']['nypl_folder_id']
                tabs = ['branches', 'research']
                if self.last_used_lib == 'branches':
                    active_tab = 'branches'
                else:
                    active_tab = 'research'
            elif self.last_used_sys == 'BPL':
                parent_id = user_data['gdrive']['bpl_folder_id']
                tabs = ['duplicates']
                active_tab = 'duplicates'
        except KeyError:
            m = 'Google parent folder IDs cannot be retrieved.\n' \
                'Please check Settings>Google API and re-link if\n' \
                'needed.'
            tkMessageBox.showerror('Google API Error', m)
        finally:
            module_logger.debug(
                'Preping data for transfer to Google Sheet: '
                'system: {}, google parent_id: {}, '
                'active tab: {}'.format(
                    self.last_used_sys, parent_id, active_tab))
            user_data.close()
        try:
            if self.dups is not None and self.dups.size > 0:
                # prep data for report there
                data = reports.dups_report_for_sheet(
                    self.last_used_sys, self.last_used_lib,
                    self.last_used_agent, self.dups)

                # determine google sheet name
                sheet_name = goo_comms.name_pvf_sheet('dups')

                # determine if such sheet exists
                # get authorization
                goo_auth = goo.get_access_token(GAPP, GUSER)
                # get sheet id
                sheet_id = goo.get_latest_file_id_in_folder(
                    goo_auth, sheet_name, parent_id)

                # if doesn't exist create one
                if not sheet_id:
                    sheet_id = goo_comms.create_sheet_for_system(
                        self.last_used_sys, goo_auth, sheet_name,
                        tabs, parent_id)

                module_logger.debug(
                    'Appending data to sheet (id: {}).'.format(
                        sheet_id))
                results = goo.append2sheet(
                    goo_auth, sheet_id, active_tab, data)

                module_logger.debug(
                    'Google Sheet response: {}'.format(results))

                try:
                    if results['updates']['updatedRows'] == len(data):
                        final_msg += 'Dups: appended successfully {} row(s) ' \
                            'to sheet "{}".\n'.format(
                                results['updates']['updatedRows'],
                                sheet_name)
                    else:
                        final_msg += 'Dups: unable to save some data ' \
                            'to Google Sheet.\n' \
                            'Appended {} row(s) out of {} to ' \
                            'sheet "{}"\n'.format(
                                results['updates']['updatedRows'],
                                len(data),
                                sheet_name)
                except KeyError:
                    module_logger.error(
                        'Google API response malformed.')
                    m = 'Google API response error.'
                    tkMessageBox.showerror('Google Drive', m, parent=self.topD)
                except TypeError:
                    module_logger.error(
                        'Google API response type error.')
                    m = 'Google API response error.'
                    tkMessageBox.showerror('Google Drive', m, parent=self.topD)

            if self.callNos is not None and self.callNos.size > 0:
                data = reports.callNos_report_for_sheet(self.callNos)

                # determine google sheet name
                sheet_name = goo_comms.name_pvf_sheet('callnos')
                tabs = ['errors']

                # determine if such sheet exists
                # get authorization
                goo_auth = goo.get_access_token(GAPP, GUSER)
                # get sheet id
                sheet_id = goo.get_latest_file_id_in_folder(
                    goo_auth, sheet_name, parent_id)

                # if doesn't exist create one
                if not sheet_id:
                    sheet_id = goo_comms.create_sheet_for_system(
                        self.last_used_sys, goo_auth, sheet_name,
                        tabs, parent_id)

                module_logger.debug(
                    'Appending data to sheet (id: {}).'.format(
                        sheet_id))
                results = goo.append2sheet(
                    goo_auth, sheet_id, tabs[0], data)

                module_logger.debug(
                    'Google Sheet response: {}'.format(results))

                try:
                    if results['updates']['updatedRows'] == len(data):
                        final_msg += 'CallNo: Appended successfully {} ' \
                            'row(s) to sheet "{}".\n'.format(
                                results['updates']['updatedRows'],
                                sheet_name)
                    else:
                        final_msg += 'CallNo: unable to save some data ' \
                            'to Google Sheet.\n' \
                            'Appended {} row(s) out of {} to ' \
                            'sheet "{}"\n'.format(
                                results['updates']['updatedRows'],
                                len(data),
                                sheet_name)
                except KeyError:
                    module_logger.error(
                        'Google API response malformed.')
                    m = 'Google API response error.'
                    tkMessageBox.showerror('Google Drive', m, parent=self.topD)
                except TypeError:
                    module_logger.error(
                        'Google API response type error.')
                    m = 'Google API response error.'
                    tkMessageBox.showerror('Google Drive', m, parent=self.topD)

        except OverloadError as exc:
            module_logger.error('GDrive error: {}'.format(exc))
            tkMessageBox.showerror(
                'Google Drive', exc, parent=self.topD)
        except Exception as exc:
            # general exception to catch unhandled situations
            _, _, exc_traceback = sys.exc_info()
            tb = format_traceback(exc, exc_traceback)
            module_logger.error('Unhandled error: {}'.format(tb))
            tkMessageBox.showerror(
                'Google Drive',
                'Unexpected error occured.\nError: {}'.format(exc))
        finally:
            self.cur_manager.notbusy()
            if final_msg != '':
                tkMessageBox.showinfo(
                    'Google Drive', final_msg, parent=self.topD)

    def download_details(self):
        # suggested name
        date_today = date.today().strftime('%y%m%d')
        fh = '{}-{}-pvr-detailed-{}.csv'.format(
            self.last_used_sys, self.last_used_lib, date_today)

        dir_opt = {}
        dir_opt['parent'] = self.topB
        dir_opt['title'] = 'Save As'
        dir_opt['initialdir'] = self.last_directory
        dir_opt['initialfile'] = fh

        fh = tkFileDialog.asksaveasfilename(**dir_opt)
        try:
            if fh != '' and self.df_details is not None:
                with open(fh, 'w') as file:
                    self.df_details.to_csv(file, index=False, mode='a')
                tkMessageBox.showinfo(
                    'Download', 'Report saved successfully.', parent=self.topB)
        except IOError as e:
            module_logger.error(
                'Unable to download report. Error: {}'.format(e))
            tkMessageBox.showerror(
                'Save Error',
                'Encountered error while saving the report. Aborting.',
                parent=self.topB)

    def help(self):
        # add scrollbar
        help = overload_help.open_help('process_vendor_help.txt')
        help_popup = tk.Toplevel(background='white')
        help_popup.iconbitmap('./icons/help.ico')
        yscrollbar = tk.Scrollbar(help_popup, orient=tk.VERTICAL)
        yscrollbar.grid(
            row=0, column=1, rowspan=10, sticky='nsw', padx=2)
        helpTxt = tk.Text(
            help_popup,
            background='white',
            relief=tk.FLAT,
            wrap=tk.WORD,
            yscrollcommand=yscrollbar.set)
        helpTxt.grid(
            row=0, column=0, sticky='snew', padx=10, pady=10)
        yscrollbar.config(command=helpTxt.yview)
        for line in help:
            helpTxt.insert(tk.END, line)
        helpTxt['state'] = tk.DISABLED

    def reset(self):
        self.validated.set('validation:')
        self.processed.set('processed:')
        self.archived.set('archived:')
        self.current_process.set('')
        self.progbar['value'] = 0

    def set_logo(self):
        # change logo
        if self.system.get() == 'NYPL':
            self.logoDsp.configure(image=self.nyplLogo)
            self.logoDsp.image = self.nyplLogo
        elif self.system.get() == 'BPL':
            self.logoDsp.configure(image=self.bplLogo)
            self.logoDsp.image = self.bplLogo

    def system_observer(self, *args):
        user_data = shelve.open(USER_DATA)
        conns_display = []
        # self.target_name.set('')
        if self.system.get() == 'BPL':
            # display only relevant connections
            if 'Z3950s' in user_data:
                for conn, params in user_data['Z3950s'].iteritems():
                    if params['library'] == 'BPL':
                        conns_display.append(
                            conn + ' (' + params['method'] + ')')
            if 'SierraAPIs' in user_data:
                for conn, params in user_data['SierraAPIs'].iteritems():
                    if params['library'] == 'BPL':
                        conns_display.append(
                            conn + ' (' + params['method'] + ')')

            # disable unwanted widgets
            self.library.set('branches')
            self.libraryCbx['state'] = 'disabled'
            self.agent.set('cataloging')
            self.agentCbx['state'] = 'disabled'

        elif self.system.get() == 'NYPL':
            # display only relevant connections
            if 'Z3950s' in user_data:
                for conn, params in user_data['Z3950s'].iteritems():
                    if params['library'] == 'NYPL':
                        conns_display.append(
                            conn + ' (' + params['method'] + ')')
            if 'SierraAPIs' in user_data:
                for conn, params in user_data['SierraAPIs'].iteritems():
                    if params['library'] == 'NYPL':
                        conns_display.append(
                            conn + ' (' + params['method'] + ')')
            if 'PlatformAPIs' in user_data:
                for conn, params in user_data['PlatformAPIs'].iteritems():
                    conns_display.append(
                        conn + ' (' + params['method'] + ')')
            self.libraryCbx['state'] = '!disabled'
            self.libraryCbx['state'] = 'readonly'
            self.agentCbx['state'] = '!disabled'
            self.agentCbx['state'] = 'readonly'

        # change log
        self.set_logo()

        # empty comobox selected target name if not on the list for the
        # system
        if self.target_name.get() not in conns_display:
            self.target_name.set('')
        # set list for drop down values
        self.query_targetCbx['values'] = conns_display
        self.query_targetCbx['state'] = 'readonly'
        user_data.close()

    def agent_observer(self, *args):
        if self.agent.get() == 'cataloging':
            self.template.set('')
            # self.templateCbx.set('')
            self.templateCbx['state'] = 'disabled'
        else:
            self.template.set('')
            self.templateCbx['state'] = '!disabled'
            self.templateCbx['state'] = 'readonly'

    def observer(self, *args):
        if self.activeW.get() == 'ProcessVendorFiles':
            # reset values
            self.file_count.set('0 files(s) selected:')
            self.validated.set('validation:')
            self.processed.set('processed:')
            self.archived.set('archived:')
            self.selected_filesEnt['state'] = '!readonly'
            self.selected_filesEnt.delete(0, tk.END)
            self.selected_filesEnt['state'] = 'readonly'
            self.systemCbx['values'] = ['BPL', 'NYPL']
            self.systemCbx['state'] = 'readonly'
            self.libraryCbx['values'] = ['branches', 'research']
            self.libraryCbx['state'] = 'readonly'
            self.agentCbx['values'] = [
                'cataloging', 'selection', 'acquisition']
            self.agentCbx['state'] = 'readonly'

            # default database target
            user_data = shelve.open(USER_DATA)

            if 'pvr_default_target' in user_data:
                self.target_name.set(
                    '{} ({})'.format(
                        user_data['pvr_default_target']['target'],
                        user_data['pvr_default_target']['method']))
                self.target = user_data['pvr_default_target']

            # set default validation
            if 'pvr_marcval' in user_data:
                self.marcVal.set(user_data['pvr_marcval'])
            if 'pvr_locval' in user_data:
                self.locVal.set(user_data['pvr_locval'])
            if 'pvr_default_save_dir' in user_data[
                    'paths']:
                self.last_directory = user_data[
                    'paths']['pvr_default_save_dir']
                self.createToolTip(
                    self.default_directoryCbtn,
                    self.last_directory)
                self.last_directory_check.set(1)

            if 'pvr_system' in user_data:
                self.system.set(user_data['pvr_system'])
            if 'pvr_library' in user_data:
                self.library.set(user_data['pvr_library'])
            if 'pvr_agent' in user_data:
                self.agent.set(user_data['pvr_agent'])
            if 'pvr_template' in user_data:
                self.template.set(user_data['pvr_template'])

            user_data.close()

            # last used
            try:
                meta = shelve.open(BATCH_META)
                self.last_used_sys = meta['system']
                self.last_used_lib = meta['library']
                self.last_used_agent = meta['agent']
                meta.close()
            except KeyError:
                pass
