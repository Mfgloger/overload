import Tkinter as tk
import ttk
import tkMessageBox
import tkFileDialog
import shelve
import base64
import datetime
import os
import os.path
import shutil
import pandas as pd
from utils import md5
import logging


import bibs
from gui_utils import ToolTip, BusyManager
from validators import MARCEdit
import overload_help
import processes as proc
from connectors.sierra_api import SierraSession
from connectors.errors import APISettingsError, APICriticalError, \
    ExceededLimitsError, APITimeoutError, UnhandledException, APITokenError
from setup_dirs import MY_DOCS, USER_DATA, BATCH_STATS, CVAL_REP, \
    USER_STATS


overload_logger = logging.getLogger('main')


class ProcessVendorFiles(tk.Frame):
    """
    GUI to processing vendor files being imported into Sierra
    """

    def __init__(self, parent, controller, **app_data):
        self.parent = parent
        tk.Frame.__init__(self, parent, background='white')
        self.controller = controller
        self.activeW = app_data['activeW']
        self.activeW.trace('w', self.observer)

        self.cur_manager = BusyManager(self)

        # widget variables
        self.database = tk.StringVar()
        self.target_name = tk.StringVar()
        self.target = None
        self.file_count = tk.StringVar()
        self.marcVal = tk.IntVar()
        self.locVal = tk.IntVar()
        self.processed = tk.StringVar()
        self.archived = tk.StringVar()
        self.validated = tk.StringVar()
        self.statDetails = tk.StringVar()
        self.last_directory_check = tk.IntVar()
        self.last_directory = None
        self.files = None
        self.df = None

        # layout

        self.rowconfigure(0, minsize=25)
        self.rowconfigure(2, minsize=10)
        self.rowconfigure(20, minsize=25)
        self.columnconfigure(0, minsize=25)
        self.columnconfigure(2, minsize=20)
        self.columnconfigure(4, minsize=20)
        self.columnconfigure(10, minsize=50)

        self.baseFrm = ttk.LabelFrame(
            self,
            text='process vendor file')
        self.baseFrm.grid(
            row=1, column=1, rowspan=6, sticky='snew')
        self.baseFrm.rowconfigure(0, minsize=10)
        self.baseFrm.rowconfigure(2, minsize=20)
        self.baseFrm.rowconfigure(4, minsize=5)
        self.baseFrm.rowconfigure(6, minsize=5)
        self.baseFrm.rowconfigure(8, minsize=5)
        self.baseFrm.rowconfigure(10, minsize=5)
        self.baseFrm.rowconfigure(12, minsize=5)
        self.baseFrm.rowconfigure(14, minsize=5)
        self.baseFrm.rowconfigure(16, minsize=5)
        self.baseFrm.rowconfigure(18, minsize=5)
        self.baseFrm.rowconfigure(20, minsize=5)
        self.baseFrm.rowconfigure(22, minsize=5)
        self.baseFrm.rowconfigure(24, minsize=20)
        self.baseFrm.columnconfigure(0, minsize=10)
        self.baseFrm.columnconfigure(2, minsize=10)
        self.baseFrm.columnconfigure(3, minsize=200)
        self.baseFrm.columnconfigure(6, minsize=20)

        # widgets
        self.targetFrm = ttk.Frame(
            self.baseFrm)
        self.targetFrm.grid(
            row=1, column=1, columnspan=6, sticky='snew')
        self.targetLbl = ttk.Label(
            self.targetFrm,
            text='target:')
        self.targetLbl.grid(
            row=0, column=0, sticky='snw', padx=5)

        self.targetLbl = ttk.Label(
            self.targetFrm,
            style='Bold.TLabel',
            textvariable=self.target_name)
        self.targetLbl.grid(
            row=0, column=1, columnspan=3, sticky='snew')
        self.createToolTip(
            self.targetLbl,
            'target database and query method')

        self.changeBtn = ttk.Button(
            self.baseFrm,
            text='change',
            command=self.changeTarget,
            cursor='hand2',
            width=12)
        self.changeBtn.grid(
            row=1, column=5, sticky='new')

        self.selectBtn = ttk.Button(
            self.baseFrm,
            text='select files',
            command=self.select,
            cursor='hand2',
            width=12)
        self.selectBtn.grid(
            row=3, column=1, sticky='nw')

        self.selectedLbl = ttk.Label(
            self.baseFrm,
            textvariable=self.file_count)
        self.selectedLbl.grid(
            row=3, column=3, columnspan=3, sticky='nw')

        self.selected_filesEnt = ttk.Entry(
            self.baseFrm,
            style='Flat.TEntry',
            state='readonly')
        self.selected_filesEnt.grid(
            row=5, column=1, columnspan=5, sticky='nwe')

        self.default_directoryCbtn = ttk.Checkbutton(
            self.baseFrm,
            cursor='hand2',
            text='previous output directory',
            variable=self.last_directory_check)
        self.default_directoryCbtn.grid(
            row=7, column=1, columnspan=2, sticky='snew')

        self.marcEditValCbtn = ttk.Checkbutton(
            self.baseFrm,
            cursor='hand2',
            text='MARCEdit validation',
            variable=self.marcVal).grid(
            row=9, column=1, columnspan=2, sticky='snew')
        self.localValCbtn = ttk.Checkbutton(
            self.baseFrm,
            cursor='hand2',
            text='local specs validation',
            variable=self.locVal).grid(
            row=9, column=3, columnspan=2, sticky='snew', padx=15)

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
            orient=tk.HORIZONTAL)
        self.progbar.grid(
            row=15, column=1, sticky='snew')

        self.errorsBtn = ttk.Button(
            self.baseFrm,
            text='error report',
            command=self.errors,
            cursor='hand2',
            width=12)
        self.errorsBtn.grid(
            row=17, column=1, sticky='nw')
        self.createToolTip(
            self.errorsBtn,
            'display validation reports')

        self.archiveBtn = ttk.Button(
            self.baseFrm,
            text='archive',
            command=self.archive,
            cursor='hand2',
            width=12)
        self.archiveBtn.grid(
            row=21, column=1, sticky='nw')
        self.createToolTip(
            self.archiveBtn,
            'save statistics and archive output MARC files')

        self.statsBtn = ttk.Button(
            self.baseFrm,
            text='stats',
            command=self.details,
            cursor='hand2',
            width=12)
        self.statsBtn.grid(
            row=19, column=1, sticky='nw')
        self.createToolTip(
            self.statsBtn,
            'display statistics of your last processing')

        self.processedLbl = ttk.Label(
            self.baseFrm,
            textvariable=self.processed)
        self.processedLbl.grid(
            row=13, column=3, columnspan=3, sticky='nw')

        self.progbarLbl = ttk.Label(
            self.baseFrm,
            text='catalog query progress')
        self.progbarLbl.grid(
            row=15, column=3, columnspan=3, sticky='nw')

        self.validatedLbl = ttk.Label(
            self.baseFrm,
            textvariable=self.validated)
        self.validatedLbl.grid(
            row=17, column=3, columnspan=3, sticky='nw')

        self.archivedLbl = ttk.Label(
            self.baseFrm,
            textvariable=self.archived)
        self.archivedLbl.grid(
            row=21, column=3, columnspan=3, sticky='nw')

        # navigation buttons

        logo = tk.PhotoImage(file='./icons/ProcessVendorFilesLarge.gif')
        self.logoDsp = ttk.Label(
            self, image=logo)
        # prevent image to be garbage collected by Python
        self.logoDsp.image = logo
        self.logoDsp.grid(
            row=1, column=3, sticky='nw')

        self.helpBtn = ttk.Button(
            self,
            text='help',
            command=self.help,
            cursor='hand2',
            width=15)
        self.helpBtn.grid(
            row=5, column=3, sticky='sw')

        self.closeBtn = ttk.Button(
            self,
            text='close',
            command=lambda: controller.show_frame('Main'),
            cursor='hand2',
            width=15)
        self.closeBtn.grid(
            row=6, column=3, sticky='sw')

    def createToolTip(self, widget, text):
        toolTip = ToolTip(widget)

        def enter(event):
            toolTip.showtip(text)

        def leave(event):
            toolTip.hidetip()

        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)

    def select(self):
        # reset processed label
        self.reset()

        # determine last used directory
        user_data = shelve.open(USER_DATA)
        paths = user_data['paths']
        if 'ProcessVendorFiles_last_open_dir' in paths:
            last_open_dir = paths['ProcessVendorFiles_last_open_dir']
        else:
            last_open_dir = MY_DOCS

        # select files for processing
        self.files = tkFileDialog.askopenfilenames(
            parent=self,
            title='Select files',
            initialdir=last_open_dir)

        if len(self.files) > 0:
            # update selected qty
            self.file_count.set('{} file(s) selected'.format(len(self.files)))
            names = []
            for file in self.files:
                name = file.split('/')[-1]
                names.append(name)
            self.selected_filesEnt['state'] = '!readonly'
            self.selected_filesEnt.delete(0, tk.END)
            self.selected_filesEnt.insert(0, ','.join(names))
            self.selected_filesEnt['state'] = 'readonly'

            # save accessed directory for the future
            last_open_dir = '/'.join(self.files[-1].split('/')[:-1])
            paths = user_data['paths']
            paths['ProcessVendorFiles_last_open_dir'] = last_open_dir
            user_data['paths'] = paths
            user_data.close()

    def reset(self):
        self.processed.set('')
        self.processedLbl.update()
        self.validated.set('')
        self.validatedLbl.update()
        self.archived.set('')
        self.archivedLbl.update()
        self.progbar['value'] = 0

    def process(self):

        self.reset()

        # ask for folder for output marc files
        dir_opt = {}
        dir_opt['mustexist'] = False
        dir_opt['parent'] = self
        dir_opt['title'] = 'Please select directory for output files'

        user_data = shelve.open(USER_DATA)
        if self.last_directory_check.get() == 0:
            dir_opt['initialdir'] = MY_DOCS
            d = tkFileDialog.askdirectory(**dir_opt)
            if d != '':
                self.last_directory = d
                paths = user_data['paths']
                paths['ProcessVendorFiles_default_save_directory'] = d
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
            if 'ProcessVendorFiles_default_save_directory' in user_data[
                    'paths']:
                self.last_directory = user_data[
                    'paths']['ProcessVendorFiles_default_save_directory']
            else:
                dir_opt['initialdir'] = MY_DOCS
                d = tkFileDialog.askdirectory(**dir_opt)
                if d != '':
                    self.last_directory = d
                    paths = user_data['paths']
                    paths['ProcessVendorFiles_default_save_directory'] = d
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

        if self.target is None:
            m = 'Please select query target'
            tkMessageBox.showwarning('Query target', m)

        elif self.files is None:
            m = 'Please select files for processing.'
            tkMessageBox.showwarning('Select Files', m)

        else:
            self.cur_manager.busy()
            s = datetime.datetime.now()
            self.df = None
            user_data = shelve.open(USER_DATA)

            # set validation choices as default
            user_data['ProcessVendorFiles_marcVal'] = self.marcVal.get()
            user_data['ProcessVendorFiles_locVal'] = self.locVal.get()

            # calculate time needed to process
            valid_files = True
            total_bib_count = 0
            for file in self.files:
                bib_count = bibs.count_bibs(file)
                if bib_count is None:
                    # file is not a MARC file
                    valid_files = False
                else:
                    total_bib_count += bib_count

            self.progbar['maximum'] = total_bib_count

            # run validation if requested
            validation_report = {}

            if self.marcVal.get() == 1:
                # make sure MARCEdit is installed on the machine
                val_engine = MARCEdit.get_engine()
                if val_engine is None:
                    # display error message
                    m = 'Could not locate cmarcedit.exe and/or \n' \
                        'marcrules.txt files to complete validation.\n' \
                        'Please uncheck MARCEdit validation or \n' \
                        'point to a folders contaning these files in Settings'
                    tkMessageBox.showerror('Validation Error', m)
                else:
                    cme = val_engine[0]
                    rules = val_engine[1]
                    report_q = MVAL_REP
                    overwrite = True
                    # print cme, rules, report_q
                    for file in self.files:
                        file_q = file
                        success_process = MARCEdit.validate(
                            cme, file_q, report_q, rules, overwrite)
                        overwrite = False
                        if success_process:
                            result = MARCEdit.validation_check(MVAL_REP)
                            if not result[0]:
                                valid_files = False
                            validation_report[file] = result[1]
                        else:
                            valid_files = False
                            validation_report[file] = \
                                'Problem with the file \n. ' \
                                'Not able to validate in MARCEdit'

            if not valid_files:
                self.validated.set('!validation errors found!')
                self.processed.set('processing not completed')
                m = 'Some of the records in selected file(s) \n' \
                    'do not validate in MARCEdit.\n' \
                    'Please see error report for details.'
                tkMessageBox.showerror('MARCEdit validation', m)

            # remove after completing local validation routine
            if self.locVal.get() == 1:
                m = 'Local Specs Validation is still being developed.\n' \
                    'Uncheck the box to not display this warning'
                tkMessageBox.showwarning('Under construction', m)

            if valid_files:
                if self.marcVal.get() == 1:
                    self.validated.set('records are A-OK!')
                    self.validatedLbl.update()
                else:
                    self.validated.set('skipped...')
                    self.validatedLbl.update()

                new_report = True
                bib_counter = 0

                if self.target['method'] == 'Z3950':
                    for fh in self.files:
                        vbibs = bibs.read_from_marc_file(fh)
                        for vbib in vbibs:
                            proc.pvf_z3950_flow(
                                new_report,
                                fh,
                                vbib,
                                self.target,
                                self.last_directory)
                            new_report = False
                            bib_counter += 1
                            self.progbar['value'] = bib_counter
                            self.progbar.update()

                elif self.target['method'] == 'API':
                    # optain and decode stored client id and client secret
                    client_id = base64.b64decode(self.target['client_id'])
                    client_secret = base64.b64decode(
                        self.target['client_secret'])

                    # initiate Sierra API connection
                    try:
                        conn = SierraSession(
                            client_id, client_secret, self.target['host'])
                    except APISettingsError as e:
                        tkMessageBox.showerror('API error', e)
                    except APITimeoutError as e:
                        tkMessageBox.showerror('API error', e)
                    except APITokenError as e:
                        tkMessageBox.showerror(
                            'API error', e)
                    except UnhandledException as e:
                        tkMessageBox.showerror('Unexpected error', e)
                    else:
                            # loop over files and bibs and request data
                            try:
                                for fh in self.files:
                                    vbibs = bibs.read_from_marc_file(fh)
                                    for vbib in vbibs:

                                        proc.pvf_api_flow(
                                            conn,
                                            new_report,
                                            fh,
                                            vbib,
                                            self.target['library'],
                                            self.last_directory)
                                        new_report = False
                                        bib_counter += 1
                                        self.progbar['value'] = bib_counter
                                        self.progbar.update()
                            except APICriticalError as e:
                                tkMessageBox.showerror('API error', e)
                            except ExceededLimitsError as e:
                                tkMessageBox.showerror('API error', e)
                            except APITimeoutError as e:
                                tkMessageBox.showerror('API error', e)
                            except UnhandledException as e:
                                tkMessageBox.showerror('API error', e)

                else:
                    overload_logger.error(
                        'Query target error: '
                        'name=%s, method=%s, host=%s' % (
                            self.target['name'],
                            self.target['method'],
                            self.target['host']))
                    m = 'Encountered unexpected query target error'
                    tk.MessageBox.showerror('Target error', m)

                e = datetime.datetime.now()
                processing_time = e - s
                report = shelve.open(BATCH_STATS)
                report['processing_time'] = processing_time
                report.close()

                # confirm files have been processed
                self.processed.set(
                    '{} file(s) processed'.format(len(self.files)))

            user_data.close()
            self.cur_manager.notbusy()

    def archive(self):
        overload_logger.debug('PVF-Archive: Initiate process...')
        if self.df is None:
            overload_logger.debug(
                "PVF-Archive: self.df doesn't existis, compiling dataframe...")
            s = shelve.open(BATCH_STATS)
            data = dict(s)
            s.close()
            frames = []
            for file, bibs_meta in data['files'].iteritems():
                frames.append(pd.DataFrame.from_dict(bibs_meta))
            self.df = pd.concat(frames, ignore_index=True)

        checksum = md5(self.df.to_string(header=False))
        overload_logger.debug(
            "PVF-Archive: calculated checksum for data being added: {}".format(
                checksum))
        if os.path.isfile(USER_STATS):
            overload_logger.debug(
                'PVF-Archive: begin adding new data to existing user '
                'stats...')
            archive_df = pd.read_csv(
                USER_STATS,
                index_col=0)

            if checksum in archive_df['checksum'].unique():
                # batch work already saved
                overload_logger.debug(
                    'PVF-Archive: checksum found in existing user stats '
                    '(data already beging added), new data not added')
                m = 'Batch has already been saved and archived'
                tkMessageBox.showwarning('Info', m)
            else:
                overload_logger.debug(
                    'PVF-Archive: checksum not present in existing '
                    'user stats - adding new data...')
                self.df['checksum'] = checksum
                self.df['report date'] = datetime.date.today()
                try:
                    with open(USER_STATS, 'a') as f:
                        self.df.to_csv(f, header=False, encoding='utf-8')
                except:
                    overload_logger.error(
                        'PVF-Archive: NOT ABLE to add data to USER STATS')
                try:
                    with open(VENDOR_STATS, 'a') as f:
                        self.df.to_csv(f, header=False, encoding='utf-8')
                    self.archived.set('stats saved')
                    overload_logger.debug(
                        "PVF-Archive: Data added succesfully...")
                except:
                    overload_logger.error(
                        'PVF-Archive: NOT ABLE to add data to VENDOR STATS')
        else:
            overload_logger.debug(
                "PVF-Archive: USER_STATS does not exisist, "
                "creating new file...")
            self.df['checksum'] = checksum
            self.df['report date'] = datetime.date.today()
            try:
                overload_logger.debug(
                    "PVF-Archive: Writing data to new USER_STATS file...")
                self.df.to_csv(USER_STATS, encoding='utf-8')
            except:
                overload_logger.error(
                    "PVF-Archive: NOT ABLE create USER_STATS")
            try:
                self.df.to_csv(VENDOR_STATS, encoding='utf-8')
                self.archived.set('stats saved')
                overload_logger.debug(
                    "PVF-Archive: Writing completed...")
            except:
                overload_logger.error(
                    'PVF-Archive: NOT ABLE to create VENDOR STATS')

        # move created files to the archive
        archive_files = []
        for file in os.listdir(self.last_directory):
            if file.endswith('.mrc') and (
                    '_DUP-' in file or '_NEW-' in file):
                archive_files.append(file)
        if len(archive_files) > 0:
            self.topA = tk.Toplevel(self, background='white')
            # self.topD.minsize(width=800, height=500)
            self.topA.iconbitmap('./icons/archive.ico')
            self.topA.title('Select files to be archived')

            self.topA.columnconfigure(0, minsize=10)
            self.topA.columnconfigure(4, minsize=10)
            self.topA.rowconfigure(0, minsize=10)

            n = 1
            self.check_id = dict()
            for file in archive_files:
                self.check_id[file] = tk.IntVar()
                check = ttk.Checkbutton(
                    self.topA,
                    cursor='hand2',
                    text=file,
                    variable=self.check_id[file])
                check.grid(
                    row=n, column=1)
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
        user_data = shelve.open(USER_DATA)
        paths = user_data['paths']
        if self.target['library'] == 'BPL' and \
                'bpl_archive_dir' in paths:
            archive_dir = paths['bpl_archive_dir']
        elif self.target['library'] == 'NYPL' and \
                'nyp_archive_dir' in paths:
            archive_dir = paths['nyp_archive_dir']
        else:
            m = 'Please select archive directory in Settings'
            tkMessageBox.showerror('Error', m)
        user_data.close()

        if archive_dir is not None:
            all_archived = True
            for file, value in self.check_id.iteritems():
                if value.get() == 1:
                    # check if file exists
                    src = '{}/{}'.format(self.last_directory, file)
                    dst = '{}/{}'.format(archive_dir, file)
                    if os.path.exists(dst):
                        renaming = True
                        n = 1
                        while renaming:
                            file = '{}{}{}'.format(file[:-5], n, file[-4:])
                            dst = '{}/{}'.format(archive_dir, file)
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
                        overload_logger.error(
                            'Archiving error: not able to move '
                            'file: {} to: {}'.format(
                                src, dst))
                        m = 'Encounted error while ' \
                            'archiving file:\n{}'.format(src)
                        tkMessageBox.showerror('Archiving error', m)
                        self.topA.destroy()
            if all_archived:
                m = 'Your MARC files have been added to the archive'
                tkMessageBox.showinfo('Archiving message', m)
                self.topA.destroy()

    def errors(self):
        # local specs validation will be saved in a different file
        # and displayed in a cumulative report

        if os.path.isfile(CVAL_REP):
            self.topV = tk.Toplevel(self, background='white')
            self.topV.minsize(width=800, height=500)
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

            tk.Button(
                self.topV,
                text='close',
                width=12,
                cursor='hand2',
                command=self.topV.destroy).grid(
                row=12, column=6, sticky='nw', padx=5)

            # generate report
            self.create_validation_report()
        else:
            m = 'Validation report not available'
            tkMessageBox.showwarning('validation report', m)

    def details(self):

        # create report
        s = shelve.open(BATCH_STATS)
        data = dict(s)
        s.close()

        if 'processing_time' in data:

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
                text='close',
                width=12,
                cursor='hand2',
                command=self.topD.destroy).grid(
                row=12, column=6, sticky='nw', padx=5)

            # generate report
            self.create_processing_report(data)

        else:
            m = 'Stats report not available'
            tkMessageBox.showinfo('Stats Report', m)

    def create_validation_report(self):
        # reset report
        self.reportVTxt.delete(1.0, tk.END)

        # create new MARCEdit validation report
        self.reportVTxt.insert(tk.END, 'MARCEdit validation report(s):\n\n', 'red')
        mReport = open(CVAL_REP, 'r')
        for line in mReport:
            self.reportVTxt.insert(tk.END, line)
        mReport.close()
        self.reportVTxt['state'] = tk.DISABLED

    def create_processing_report(self, data):
        # reset report
        self.reportDTxt.delete(1.0, tk.END)

        # determine if any files have been processed
        # summary
        files = []
        bib_count = 0
        if 'files' in data:
            for key, value in data['files'].iteritems():
                files.append(key.split('/')[-1])
                bib_count += len(value)

            self.reportDTxt.insert(
                tk.END, 'total processed files: {}\n'.format(
                    len(files)), 'red')
            self.reportDTxt.insert(
                tk.END, 'file names: {}\n'.format(','.join(files)))
            self.reportDTxt.insert(
                tk.END, 'total process records: {}\n'.format(bib_count), 'red')
            self.reportDTxt.insert(
                tk.END, 'processing time: {}\n'.format(
                    data['processing_time']))
            self.reportDTxt.insert(
                tk.END, '\n')

            # create pandas dataframes to analyze
            if self.df is None:
                frames = []
                for file, bibs_meta in data['files'].iteritems():
                    frames.append(pd.DataFrame.from_dict(bibs_meta))
                self.df = pd.concat(frames, ignore_index=True)

            # tabulate by vendor & load type
            self.reportDTxt.insert(tk.END, 'Vendor breakdown:\n', 'blue')
            self.reportDTxt.insert(tk.END, 'vendor\t\t\tnew\tdup\ttotal\n')
            # print df.head()
            for vendor, data in self.df.groupby('vendor'):
                new = data[
                    data['overlay'] == True]['overlay'].count()
                # new = new['overlay'].count()
                dup = data[data['overlay'] == False]['overlay'].count()
                self.reportDTxt.insert(
                    tk.END, '{}\t\t\t{}\t{}\t{}\n'.format(
                        vendor, new, dup, new + dup))

            # identify new bibs without call number
            # ncself.df = self.df[self.df['vCallNumber'].isnull()]
            # no_vcall_df = ncdf[ncdf['overlay'] == True].sort_values('vendor')
            no_vcall_df = self.df[(self.df['overlay'] == True) & (
                self.df['vCallNumber'].isnull())].sort_values('vendor')
            self.reportDTxt.insert(tk.END, '\n')
            self.reportDTxt.insert(
                tk.END, 'Missing  call number on vendor record:\n', 'blue')
            if no_vcall_df.empty:
                self.reportDTxt.insert(tk.END, 'ALL CLEAR\n')
            else:
                self.reportDTxt.insert(
                    tk.END,
                    'bNumber\t   vendor\t\tvendor call#\t\tinhouse call#\t\tISBN\n')
                for index, row in no_vcall_df.iterrows():
                    self.reportDTxt.insert(
                        tk.END, 'b{}a\t|{}\t\t|{}\t\t|{}\t\t|{}\n'.format(
                            row['target_id'],
                            row['vendor'],
                            row['vCallNumber'],
                            row['bCallNumber'],
                            ','.join(row['vISBN'])))

            # report incoming call numbers that don't match
            # does not display brief records being overlayed with full one
            no_call_match_df = self.df[
                (self.df['callNumber_match'] == False) & (
                    self.df['bCallNumber'].notnull()) & (
                    self.df['vCallNumber'].notnull())].sort_values('vendor')
            # print no_call_match_df.head()
            self.reportDTxt.insert(tk.END, '\n')
            self.reportDTxt.insert(
                tk.END, 'Different call number on vendor record:\n', 'blue')
            if no_call_match_df.empty:
                self.reportDTxt.insert(tk.END, 'ALL CLEAR\n')
            else:
                self.reportDTxt.insert(
                    tk.END,
                    'bNumber\t   vendor\t\tvendor call#\t\t\tinhouse call#\t\tISBN\n')
                for index, row in no_call_match_df.iterrows():
                    self.reportDTxt.insert(
                        tk.END, 'b{}a\t|{}\t\t|{}\t\t\t|{}\t\t|{}\n'.format(
                            row['target_id'],
                            row['vendor'],
                            row['vCallNumber'],
                            row['bCallNumber'],
                            ','.join(row['vISBN'])))

            # report duplicates found
            dups_df = self.df[self.df['dups'] == True].sort_values('vendor')
            self.reportDTxt.insert(tk.END, '\n')
            self.reportDTxt.insert(
                tk.END,
                'Duplicate records found in catalog:\n', 'blue')
            if dups_df.empty:
                self.reportDTxt.insert(tk.END, 'ALL CLEAR\n')
            else:
                self.reportDTxt.insert(
                    tk.END,
                    'vendor\t\t|vendor ISBN  \t\t\t\t|vendor call#\t\t'
                    '|inhouse call#\t\t\t|bNumber\t\t'
                    '|bib numbers of dups\n')
                self.reportDTxt.insert(
                    tk.END,
                    '      \t\t             \t          \t\t        matched to\t\t\t  matched to\t\n')
                for index, row in dups_df.iterrows():
                    self.reportDTxt.insert(
                        tk.END, '{}\t\t|{}\t      |{}\t\t|{}       \t\t\t|{} \t\t\t\t|{}\n'.format(
                            row['vendor'],
                            ','.join(row['vISBN']),
                            row['vCallNumber'],
                            row['bCallNumber'],
                            'b' + row['target_id'] + 'a',
                            ','.join(['b{}a'.format(x) for x in row['dups_id']])))

            # report protected bibs
            self.reportDTxt.insert(tk.END, '\n')
            protected_df = self.df[
                ((self.df['overlay'] == False) &
                    (self.df['fullBib'] == True)) |
                ((self.df['overlay'] == True) &
                    (self.df['rCallNumber'] == True))]
            # exclude CLS & MidWest? ask
            self.reportDTxt.insert(tk.END, '\n')
            self.reportDTxt.insert(
                tk.END,
                'Protected inhouse records:\n', 'blue')

            # determine library & show protected records
            if protected_df.empty:
                self.reportDTxt.insert(tk.END, 'total: ')
                self.reportDTxt.insert(tk.END, '0\n\n', 'red')
            else:
                library = protected_df['library'].iloc[0]
                if library == 'NYPL':
                    self.reportDTxt.insert(
                        tk.END,
                        'total\tRL bibs only\n')
                    total_bibs = protected_df.shape[0]
                    rl_bibs = protected_df[
                        protected_df[
                            'rCallNumber'] == True].shape[0]
                    self.reportDTxt.insert(
                        tk.END,
                        '{}\t{}\n\n'.format(
                            total_bibs,
                            rl_bibs))

                else:  # BPL
                    self.reportDTxt.insert(
                        tk.END,
                        'total:  ')
                    total_bibs = protected_df['target_id'].shape[0]
                    self.reportDTxt.insert(
                        tk.END,
                        '{}\n\n'.format(
                            total_bibs), 'red')

            # updated by vendor and overlayed?
            updated_count = self.df[(self.df['bCallNumber'].notnull()) &
                (self.df['fullBib'] == False) & (
                    self.df['overlay'] == True)].shape[0]
            self.reportDTxt.insert(
                tk.END,
                'Records updated by vendor:\n', 'blue')
            self.reportDTxt.insert(
                tk.END,
                'total: {}\n\n'.format(updated_count))

            self.reportDTxt['state'] = tk.DISABLED

        else:
            self.reportDTxt.insert(tk.END, 'NOTHING TO REPORT :/')
        self.reportDTxt['state'] = tk.DISABLED

    def changeTarget(self):
        user_data = shelve.open(USER_DATA)
        conns = dict()

        if 'Z3950s' in user_data:
            conns.update(user_data['Z3950s'])
        if 'APIs' in user_data:
            conns.update(user_data['APIs'])

        user_data.close()

        if len(conns.keys()) > 0:
            self.targetSelectFrm = tk.Toplevel(background='white')
            self.targetSelectFrm.iconbitmap('./icons/ProcessVendorFiles.ico')
            n = 0
            for conn, params in sorted(conns.iteritems()):
                n += 1
                method = ' (' + params['method'] + ')'
                ttk.Radiobutton(
                    self.targetSelectFrm,
                    cursor='hand2',
                    text=conn + method,
                    value=conn + method,
                    variable=self.target_name).grid(
                    row=n, column=0, columnspan=4,
                    sticky='snew', padx=10, pady=5)

            self.targetSelectBtn = ttk.Button(
                self.targetSelectFrm,
                text='select',
                cursor='hand2',
                command=self.selectTarget,
                width=12)
            self.targetSelectBtn.grid(
                row=n + 1, column=1, sticky='sw', padx=10, pady=10)

            self.targetSelectCloseBtn = ttk.Button(
                self.targetSelectFrm,
                text='close',
                cursor='hand2',
                command=self.targetSelectFrm.destroy,
                width=12)
            self.targetSelectCloseBtn.grid(
                row=n + 1, column=2, sticky='ew', padx=10, pady=10)
        else:
            m = 'Query targets were not found.\n' \
                'Please set up Z3950 or Sierra API targets in Settings.'
            tkMessageBox.showwarning('Query targets', m)

    def selectTarget(self):
        self.target_name.set(self.target_name.get())
        user_data = shelve.open(USER_DATA)
        if 'Z3950' in self.target_name.get():
            method = 'Z3950'
        elif 'API' in self.target_name.get():
            method = 'API'
        target = self.target_name.get()[:self.target_name.get().index(' (')]
        user_data['ProcessVendorFiles_default_target'] = {
            'target': target,
            'method': method}
        if method == 'Z3950':
            self.target = user_data['Z3950s'][target]
        elif method == 'API':
            self.target = user_data['APIs'][target]
        user_data.close()
        self.targetSelectFrm.destroy()

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
            yscrollcommand=yscrollbar.set)
        helpTxt.grid(
            row=0, column=0, sticky='snew', padx=10, pady=10)
        yscrollbar.config(command=helpTxt.yview)
        for line in help:
            helpTxt.insert(tk.END, line)
        helpTxt['state'] = tk.DISABLED

    def observer(self, *args):
        if self.activeW.get() == 'ProcessVendorFiles':
            # reset values
            self.file_count.set('')
            self.processed.set('')
            self.validated.set('')
            self.archived.set('')
            self.selected_filesEnt['state'] = '!readonly'
            self.selected_filesEnt.delete(0, tk.END)
            self.selected_filesEnt['state'] = 'readonly'

            user_data = shelve.open(USER_DATA)
            if 'ProcessVendorFiles_default_target' in user_data:
                if user_data[
                        'ProcessVendorFiles_default_target'][
                        'method'] == 'Z3950':
                    self.target = user_data[
                        'Z3950s'][user_data[
                            'ProcessVendorFiles_default_target']['target']]
                    self.target_name.set(user_data[
                        'ProcessVendorFiles_default_target']['target'] + ' (' +
                        user_data[
                        'ProcessVendorFiles_default_target']['method'] + ')')
                elif user_data[
                        'ProcessVendorFiles_default_target'][
                        'method'] == 'API':
                    self.target = user_data[
                        'APIs'][user_data[
                            'ProcessVendorFiles_default_target']['target']]
                    self.target_name.set(user_data[
                        'ProcessVendorFiles_default_target']['target'] + ' (' +
                        user_data[
                        'ProcessVendorFiles_default_target']['method'] + ')')
            else:
                self.target_name.set('NONE')

            # set default validation
            if 'ProcessVendorFiles_marcVal' in user_data:
                self.marcVal.set(user_data['ProcessVendorFiles_marcVal'])
            if 'ProcessVendorFiles_locVal' in user_data:
                self.locVal.set(user_data['ProcessVendorFiles_locVal'])
            if 'ProcessVendorFiles_default_save_directory' in user_data[
                    'paths']:
                self.last_directory = user_data[
                    'paths']['ProcessVendorFiles_default_save_directory']
                self.createToolTip(
                    self.default_directoryCbtn,
                    self.last_directory)
                self.last_directory_check.set(1)
            user_data.close()
