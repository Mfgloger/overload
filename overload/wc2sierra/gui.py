import logging
import shelve
import Tkinter as tk
import ttk
import tkFileDialog
import tkMessageBox
import sys


from errors import OverloadError
from gui_utils import ToolTip, BusyManager
from logging_setup import format_traceback, LogglyAdapter
from setup_dirs import USER_DATA, MY_DOCS
from manager import launch_process
from gui_report import W2SReport


module_logger = LogglyAdapter(logging.getLogger("overload"), None)


class Worldcat2Sierra(tk.Frame):
    """
    GUI for module upgrading records from Worldcat
    """

    def __init__(self, parent, controller, **app_data):
        self.parent = parent
        tk.Frame.__init__(self, parent, background="white")
        self.controller = controller
        self.activeW = app_data["activeW"]
        self.activeW.trace("w", self.observer)

        self.cur_manager = BusyManager(self)

        # variables
        self.system = tk.StringVar()
        self.system.trace("w", self.system_observer)
        self.library = tk.StringVar()
        self.action = tk.StringVar()
        self.api = tk.StringVar()
        self.encode_level = tk.StringVar()
        self.mat_type = tk.StringVar()
        self.cat_rules = tk.StringVar()
        self.cat_source = tk.StringVar()
        self.source_fh = tk.StringVar()
        self.data_source = tk.StringVar()
        self.data_source.trace("w", self.data_source_observer)
        self.id_type = tk.StringVar()
        self.proc_label = tk.StringVar()
        self.nohits = tk.IntVar()
        self.found = tk.IntVar()
        self.skipped = tk.IntVar()
        self.meet_crit_counter = tk.IntVar()
        self.fail_user_crit_counter = tk.IntVar()
        self.fail_glob_crit_counter = tk.IntVar()
        self.recap_start = tk.StringVar()
        self.recap_end = tk.StringVar()
        self.recap_range = None

        # logos
        self.nyplLogo = tk.PhotoImage(file="./icons/nyplLogo.gif")
        self.bplLogo = tk.PhotoImage(file="./icons/bplLogo.gif")

        # layout of the main frame
        self.rowconfigure(0, minsize=10)
        self.rowconfigure(2, minsize=10)
        self.columnconfigure(0, minsize=5)
        self.columnconfigure(2, minsize=5)

        # layout of the base frame
        self.baseFrm = ttk.LabelFrame(self, text="Worldcat2Sierra")
        self.baseFrm.grid(row=1, column=1, rowspan=6, sticky="snew")
        self.baseFrm.rowconfigure(0, minsize=10)
        self.baseFrm.rowconfigure(18, minsize=10)
        self.baseFrm.columnconfigure(0, minsize=10)
        self.baseFrm.columnconfigure(7, minsize=10)

        # layout of parameters
        self.paramsFrm = ttk.Frame(self.baseFrm, borderwidth=2, relief="ridge")
        self.paramsFrm.grid(row=1, column=1, columnspan=6, sticky="snew")
        self.paramsFrm.rowconfigure(0, minsize=10)
        self.paramsFrm.rowconfigure(6, minsize=10)
        self.paramsFrm.columnconfigure(0, minsize=10)
        self.paramsFrm.columnconfigure(3, minsize=20)
        self.paramsFrm.columnconfigure(6, minsize=10)

        # params drop down menu
        self.systemLbl = ttk.Label(self.paramsFrm, text="system:")
        self.systemLbl.grid(row=1, column=1, sticky="snew")
        self.systemCbx = ttk.Combobox(
            self.paramsFrm, textvariable=self.system, width=25
        )
        self.systemCbx.grid(row=1, column=2, sticky="nsw", padx=5, pady=5)

        self.libraryLbl = ttk.Label(self.paramsFrm, text="library:")
        self.libraryLbl.grid(row=2, column=1, sticky="snew")
        self.libraryCbx = ttk.Combobox(
            self.paramsFrm, textvariable=self.library, width=25
        )
        self.libraryCbx.grid(row=2, column=2, sticky="nsw", padx=5, pady=5)

        self.actionLbl = ttk.Label(self.paramsFrm, text="action:")
        self.actionLbl.grid(row=3, column=1, sticky="snew")
        self.actionCbx = ttk.Combobox(
            self.paramsFrm, textvariable=self.action, width=25
        )
        self.actionCbx.grid(row=3, column=2, sticky="nsw", padx=5, pady=5)

        self.apiLbl = ttk.Label(self.paramsFrm, text="worlcat credentials:")
        self.apiLbl.grid(row=4, column=1, sticky="snew")
        self.apiCbx = ttk.Combobox(self.paramsFrm, textvariable=self.api, width=25)
        self.apiCbx.grid(row=4, column=2, sticky="nsw", padx=5, pady=5)

        self.dataSrcLbl = ttk.Label(self.paramsFrm, text="data source")
        self.dataSrcLbl.grid(row=5, column=1, sticky="snew")
        self.dataSrcCbx = ttk.Combobox(
            self.paramsFrm, textvariable=self.data_source, width=25
        )
        self.dataSrcCbx.grid(row=5, column=2, sticky="nsw", padx=5, pady=5)

        self.encode_levelLbl = ttk.Label(self.paramsFrm, text="record level:")
        self.encode_levelLbl.grid(row=1, column=3, sticky="snew")
        self.encode_levelCbx = ttk.Combobox(
            self.paramsFrm, textvariable=self.encode_level, width=25
        )
        self.encode_levelCbx.grid(row=1, column=4, sticky="nsw", padx=5, pady=5)

        self.mat_typeLbl = ttk.Label(self.paramsFrm, text="record type:")
        self.mat_typeLbl.grid(row=2, column=3, sticky="snew")
        self.mat_typeCbx = ttk.Combobox(
            self.paramsFrm, textvariable=self.mat_type, width=25
        )
        self.mat_typeCbx.grid(row=2, column=4, sticky="nsw", padx=5, pady=5)

        self.cat_rulesLbl = ttk.Label(self.paramsFrm, text="cataloging rules:")
        self.cat_rulesLbl.grid(row=3, column=3, sticky="snew")
        self.cat_rulesCbx = ttk.Combobox(
            self.paramsFrm, textvariable=self.cat_rules, width=25
        )
        self.cat_rulesCbx.grid(row=3, column=4, sticky="nsw", padx=5, pady=5)

        self.cat_sourceLbl = ttk.Label(self.paramsFrm, text="cat source:")
        self.cat_sourceLbl.grid(row=4, column=3, sticky="snew")
        self.cat_sourceCbx = ttk.Combobox(
            self.paramsFrm, textvariable=self.cat_source, width=25
        )
        self.cat_sourceCbx.grid(row=4, column=4, sticky="nsw", padx=5, pady=5)

        self.idTypeLbl = ttk.Label(self.paramsFrm, text="ID type")
        self.idTypeLbl.grid(row=5, column=3, sticky="snew")
        self.idTypeCbx = ttk.Combobox(
            self.paramsFrm, textvariable=self.id_type, width=25
        )
        self.idTypeCbx.grid(row=5, column=4, sticky="nsw", padx=5, pady=5)

        self.actionFrm = ttk.Frame(self.baseFrm, borderwidth=2, relief="ridge")
        self.actionFrm.grid(row=3, column=1, columnspan=6, sticky="snew")
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
        self.actionFrm.columnconfigure(7, minsize=100)
        self.actionFrm.columnconfigure(8, minsize=5)

        # source row
        self.sourceLbl = ttk.Label(self.actionFrm, text="source file")
        self.sourceLbl.grid(row=1, column=1, sticky="snew")
        self.sourceEnt = ttk.Entry(self.actionFrm, textvariable=self.source_fh)
        self.sourceEnt.grid(row=1, column=3, columnspan=8, sticky="snew", pady=5)
        self.sourceEnt["state"] = "readonly"
        searchICO = tk.PhotoImage(file="./icons/search.gif")
        self.sourceBtn = ttk.Button(
            self.actionFrm, image=searchICO, cursor="hand2", command=self.find_source
        )
        self.sourceBtn.image = searchICO
        self.sourceBtn.grid(row=1, column=11, sticky="ne", padx=5, pady=5)

        # progess area
        self.prog1Lbl = ttk.Label(self.actionFrm, text="progress")
        self.prog1Lbl.grid(row=4, column=1, sticky="snew")
        self.progbar1 = ttk.Progressbar(
            self.actionFrm, mode="determinate", orient=tk.HORIZONTAL,
        )
        self.progbar1.grid(row=4, column=3, columnspan=2, sticky="snew")
        self.prog2Lbl = ttk.Label(self.actionFrm, textvariable=self.proc_label)
        self.prog2Lbl.grid(row=4, column=5, sticky="sne", padx=10)
        self.progbar2 = ttk.Progressbar(
            self.actionFrm, mode="determinate", orient=tk.HORIZONTAL,
        )
        self.progbar2.grid(row=4, column=6, columnspan=2, sticky="snew")

        self.tallyLbl = ttk.Label(self.actionFrm, text="status")
        self.tallyLbl.grid(row=6, column=3, sticky="snew")

        self.foundLbl = ttk.Label(self.actionFrm, text="OCLC match:")
        self.foundLbl.grid(row=7, column=3, sticky="snew")

        self.foundcounterLbl = ttk.Label(self.actionFrm, textvariable=self.found)
        self.foundcounterLbl.grid(row=7, column=4, sticky="snw")

        self.nohitsLbl = ttk.Label(self.actionFrm, text="match not found:")
        self.nohitsLbl.grid(row=8, column=3, sticky="snew")

        self.nohitscounterLbl = ttk.Label(self.actionFrm, textvariable=self.nohits)
        self.nohitscounterLbl.grid(row=8, column=4, sticky="snw")

        self.skippedLbl = ttk.Label(self.actionFrm, text="skipped:")
        self.skippedLbl.grid(row=9, column=3, sticky="snew")

        self.skippedcounterLbl = ttk.Label(self.actionFrm, textvariable=self.skipped)
        self.skippedcounterLbl.grid(row=9, column=4, sticky="snew")

        self.meetCritLbl = ttk.Label(self.actionFrm, text="meets criteria:")
        self.meetCritLbl.grid(row=7, column=5, sticky="snew")

        self.meetCritCounterLbl = ttk.Label(
            self.actionFrm, textvariable=self.meet_crit_counter
        )
        self.meetCritCounterLbl.grid(row=7, column=6, columnspan=2, sticky="snw")

        self.userCritFailLbl = ttk.Label(self.actionFrm, text="failed user criteria:")
        self.userCritFailLbl.grid(row=8, column=5, sticky="snew")

        self.userCritFailCounterLbl = ttk.Label(
            self.actionFrm, textvariable=self.fail_user_crit_counter
        )
        self.userCritFailCounterLbl.grid(row=8, column=6, columnspan=2, sticky="snw")

        self.globCritFailLbl = ttk.Label(self.actionFrm, text="failed global criteria:")
        self.globCritFailLbl.grid(row=9, column=5, sticky="snew")

        self.globCritFailCounterLbl = ttk.Label(
            self.actionFrm, textvariable=self.fail_glob_crit_counter
        )
        self.globCritFailCounterLbl.grid(row=9, column=6, columnspan=2, sticky="snw")

        # action buttons
        self.processBtn = ttk.Button(
            self.actionFrm,
            text="process",
            command=self.process,
            cursor="hand2",
            width=12,
        )
        self.processBtn.grid(row=11, column=3, sticky="nw")

        self.reportBtn = ttk.Button(
            self.actionFrm, text="report", command=self.report, cursor="hand2", width=12
        )
        self.reportBtn.grid(row=11, column=5, sticky="nw")

        # right panel
        # default logo & navigation buttons
        logo = tk.PhotoImage(file="./icons/upgrade.gif")
        self.logoDsp = ttk.Label(self, image=logo)
        # prevent image to be garbage collected
        self.logoDsp.image = logo
        self.logoDsp.grid(row=1, column=9, rowspan=2, columnspan=3, sticky="sew")

        self.helpBtn = ttk.Button(
            self, text="help", command=self.display_help, cursor="hand2", width=12
        )
        self.helpBtn.grid(row=5, column=8, columnspan=3, sticky="sew")

        self.closeBtn = ttk.Button(
            self,
            text="close",
            command=lambda: controller.show_frame("Main"),
            cursor="hand2",
            width=12,
        )
        self.closeBtn.grid(row=6, column=8, columnspan=3, sticky="sew")

    def find_source(self):
        # determine last used directory
        user_data = shelve.open(USER_DATA)
        paths = user_data["paths"]
        if "pvr_last_open_dir" in paths:
            last_open_dir = paths["pvr_last_open_dir"]
        else:
            last_open_dir = MY_DOCS

        # select files for processing
        file = tkFileDialog.askopenfilename(
            parent=self,
            title="Select file",
            filetypes=(
                ("text files", "*.txt"),
                ("csv files", "*.csv"),
                ("tab files", "*.tsv"),
            ),
            initialdir=last_open_dir,
        )

        if file:
            self.source_fh.set(file)

        user_data.close()

    def process(self):
        self.reset()

        # validate all required elements are provided
        if not self.source_fh.get():
            self.find_source()

        issues = []

        if not self.system.get():
            issues.append("- system not selected")
        if self.system.get() == "NYPL" and not self.library.get():
            issues.append("- library parameter is required")
        if not self.action.get():
            issues.append("- action parameter is required")
        if not self.api.get():
            issues.append("- API not selected")
        if not self.encode_level.get():
            issues.append("- encoding level not selected")

        # temp issues
        # if self.action.get() == 'update':
        #     issues.append('- updating functionality not developed')
        if self.cat_rules.get() != "any":
            issues.append("- cat rules functionality not developed")
        if self.cat_source.get() != "any":
            issues.append("- cat source functionality not developed")
        if self.data_source.get() == "IDs list" and self.id_type.get() not in (
            "ISBN",
            "OCLC #",
        ):
            issues.append("- only ISBN & OCLC # id is permitted at the moment")

        if issues:
            issues.insert(0, "Parameters error(s):\n")
            tkMessageBox.showerror("Error", "\n".join(issues))
        else:
            if self.source_fh.get():
                # both paths provided
                # wrap later in an exception catching & displaying

                if (
                    self.system.get() == "NYPL"
                    and self.library.get() == "research"
                    and self.action.get() == "catalog"
                ):
                    # ask for ReCap call number range
                    self.recap_range_widget()
                    if self.recap_range:
                        self.launch_processing()
                else:
                    self.launch_processing()

    def launch_processing(self):
        self.progbar1["value"] = 0
        self.progbar2["value"] = 0
        try:
            launch_process(
                self.source_fh.get(),
                self.data_source.get(),
                self.system.get(),
                self.library.get(),
                self.progbar1,
                self.progbar2,
                self.proc_label,
                self.found,
                self.nohits,
                self.skipped,
                self.meet_crit_counter,
                self.fail_user_crit_counter,
                self.fail_glob_crit_counter,
                self.action.get(),
                self.encode_level.get(),
                self.mat_type.get(),
                self.cat_rules.get(),
                self.cat_source.get(),
                self.recap_range,
                id_type=self.id_type.get(),
                api=self.api.get(),
            )

            # display report
            self.report()

        except OverloadError as e:
            tkMessageBox.showerror("Error", e)

        except Exception as exc:
            # unhandled exception
            _, _, exc_traceback = sys.exc_info()
            tb = format_traceback(exc, exc_traceback)
            module_logger.error("Unhandled error on W2S process. {}".format(tb))
            tkMessageBox.showerror("Error", exc)

    def recap_range_widget(self):
        recap_start = tk.StringVar()
        recap_end = tk.StringVar()
        self.topRecap = tk.Toplevel(self, background="white")
        self.topRecap.iconbitmap("./icons/archive.ico")
        self.topRecap.title("ReCAP Call numbers")
        ttk.Label(
            self.topRecap, text="Please provide range of available ReCAP call numbers."
        ).grid(row=0, column=0, columnspan=5, sticky="snew", padx=20, pady=20)
        ttk.Label(self.topRecap, text="start:").grid(
            row=1, column=1, sticky="sne", padx=20, pady=2
        )
        ttk.Entry(self.topRecap, textvariable=recap_start).grid(
            row=1, column=2, sticky="snew", pady=2
        )
        ttk.Label(self.topRecap, text="end:").grid(
            row=2, column=1, sticky="sne", padx=20, pady=2
        )
        ttk.Entry(self.topRecap, textvariable=recap_end).grid(
            row=2, column=2, sticky="snew", pady=2
        )

        okBtn = ttk.Button(
            self.topRecap,
            text="OK",
            width=10,
            command=lambda: self.add_recap_range(recap_start.get(), recap_end.get()),
        )
        okBtn.grid(row=3, column=0, columnspan=2, sticky="snw", padx=30, pady=20)

        cancelBtn = ttk.Button(
            self.topRecap, text="cancel", width=10, command=self.topRecap.destroy
        )
        cancelBtn.grid(row=3, column=2, columnspan=2, sticky="sne", padx=30, pady=20)

        self.topRecap.wait_window()

    def add_recap_range(self, recap_start, recap_end):
        try:
            start = int(recap_start.strip())
            end = int(recap_end.strip())
            self.recap_range = (start, end)
            module_logger.debug("ReCap range entered: {}".format(self.recap_range))
            self.topRecap.destroy()
        except ValueError:
            tkMessageBox.showerror("Input error", "Only digits are permitted")

    def report(self):
        W2SReport(self)

    def display_help(self):
        tkMessageBox.showinfo("Help", "Help info displayed here.")

    def reset(self):
        self.progbar1["value"] = 0
        self.progbar2["value"] = 0
        self.found.set(0)
        self.nohits.set(0)
        self.meet_crit_counter.set(0)
        self.fail_user_crit_counter.set(0)
        self.fail_glob_crit_counter.set(0)
        self.recap_range = None

    def set_logo(self):
        # change logo
        if self.system.get() == "NYPL":
            self.logoDsp.configure(image=self.nyplLogo)
            self.logoDsp.image = self.nyplLogo
        elif self.system.get() == "BPL":
            self.logoDsp.configure(image=self.bplLogo)
            self.logoDsp.image = self.bplLogo

    def createToolTip(self, widget, text):
        toolTip = ToolTip(widget)

        def enter(event):
            toolTip.showtip(text)

        def leave(event):
            toolTip.hidetip()

        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)

    def system_observer(self, *args):
        # change logo
        self.set_logo()
        # show available api crendentials for system
        # pull available API from user_data
        user_data = shelve.open(USER_DATA)
        try:
            apis = user_data["WorldcatAPIs"]
            user_data.close()

            if self.system.get() == "NYPL":
                self.api.set("")
                self.apiCbx["values"] = apis["NYPL"].keys()
                self.libraryCbx["state"] = "readonly"
            elif self.system.get() == "BPL":
                self.api.set("")
                self.apiCbx["values"] = apis["BPL"].keys()
                self.libraryCbx.set("branches")
                self.libraryCbx["state"] = "disabled"
            self.apiCbx["state"] = "readonly"
        except KeyError:
            m = (
                "Please complete Worldcat APIs setup first\n"
                "by going to Settings>Worldcat APIs and \n"
                'launching "auto credentials".'
            )
            tkMessageBox.showerror("Setup Error", m)

    def data_source_observer(self, *args):
        if self.data_source.get() == "IDs list":
            self.idTypeCbx["state"] = "!disabled"
            self.id_type.set("ISBN")
        else:
            self.id_type.set("")
            self.idTypeCbx["state"] = "disabled"

    def observer(self, *args):
        if self.activeW.get() == "Worldcat2Sierra":
            # load drop-down choics
            self.systemCbx["values"] = ("BPL", "NYPL")
            self.systemCbx["state"] = "readonly"
            self.libraryCbx["values"] = ("branches", "research")
            self.libraryCbx["state"] = "readonly"
            self.actionCbx["values"] = ("upgrade", "catalog")
            self.actionCbx["state"] = "readonly"
            self.encode_levelCbx["values"] = (
                "Level 1 - blank, I, 4 ",
                "Level 2 & up - M, K, 7, 1, 2",
                "Level 3 & up - 3, 8",
            )
            self.encode_levelCbx["state"] = "readonly"
            self.encode_level.set("")
            self.mat_typeCbx["values"] = (
                "any",
                "print",
                "large print",
                "dvd",
                "bluray",
            )
            self.mat_typeCbx["state"] = "readonly"
            self.cat_rulesCbx["values"] = ("any", "RDA-only")
            self.cat_rules.set("any")
            self.cat_rulesCbx["state"] = "readonly"
            self.mat_type.set("any")
            self.mat_typeCbx["state"] = "readonly"
            self.cat_sourceCbx["values"] = ("any", "DLC")
            self.cat_source.set("any")
            self.dataSrcCbx["values"] = ("Sierra export", "IDs list")
            self.dataSrcCbx["state"] = "readonly"
            self.data_source.set("IDs list")
            self.idTypeCbx["values"] = ("ISBN", "ISSN", "UPC", "LCCN", "OCLC #")
            self.idTypeCbx["state"] = "readonly"
