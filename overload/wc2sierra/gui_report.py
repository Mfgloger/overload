import logging
import shelve
import Tkinter as tk
import ttk
import tkFileDialog
import tkMessageBox


# from errors import OverloadError
from gui_utils import BusyManager
from logging_setup import format_traceback, LogglyAdapter
from manager import (
    get_bib,
    count_total,
    persist_choice,
    create_marc_file,
    set_oclc_holdings,
    get_batch_criteria_record,
)
from setup_dirs import USER_DATA, MY_DOCS


mlogger = LogglyAdapter(logging.getLogger("overload"), None)


class W2SReport(tk.Frame):
    """
    GUI for verification and selection of records retrieved
    using Worldcat2Sierra module
    """

    def __init__(self, parent):
        self.parent = parent
        tk.Frame.__init__(self, self.parent, background="white")
        self.top = tk.Toplevel(self, background="white")
        self.cur_manager = BusyManager(self)
        self.top.iconbitmap("./icons/report.ico")
        self.top.title("W2S Report & Selection")

        # variables
        self.system = None
        self.library = None
        self.sel_lbl = tk.StringVar()
        self.sel_lbl.set("select all")
        self.sel_var = tk.IntVar()
        self.sel_var.trace("w", self.selection_observer)
        self.hold_var = tk.IntVar()
        self.hold_msg = tk.IntVar()
        self.dst_fh = tk.StringVar()

        self.disp_record = tk.StringVar()
        self.disp_record_no = 0
        self.jump_record = tk.StringVar()
        self.total_count = 0
        self.selected_count = 0

        # register barcode validation
        self.vb = (self.register(self.onValidateBarcode), "%d", "%i", "%P")
        self.vj = (self.register(self.onValidateJump), "%d", "%i", "%P")

        # heading frame
        self.headFrm = ttk.Frame(self.top)
        self.headFrm.grid(row=0, column=0, sticky="snew", padx=20, pady=10)

        # options frame
        self.optFrm = ttk.Frame(self.headFrm)
        self.optFrm.grid(row=0, column=0, rowspan=3, columnspan=3, sticky="snew")

        self.selCbn = ttk.Checkbutton(
            self.optFrm, textvariable=self.sel_lbl, variable=self.sel_var
        )
        self.selCbn.grid(row=0, column=0, columnspan=3, sticky="snew", padx=10)

        self.holdCbn = ttk.Checkbutton(
            self.optFrm, text="set holdings", variable=self.hold_var
        )
        self.holdCbn.grid(row=1, column=0, columnspan=3, sticky="snw", padx=10)

        self.holdmsgCbn = ttk.Checkbutton(
            self.optFrm, text="add no holdings note", variable=self.hold_msg
        )
        self.holdmsgCbn.grid(row=2, column=0, columnspan=3, sticky="snw", padx=10)
        ttk.Separator(self.optFrm, orient=tk.HORIZONTAL).grid(
            row=3, column=0, columnspan=3, sticky="new", padx=10
        )

        # info box
        self.settingsTxt = tk.Text(
            self.headFrm, height=2, width=100, wrap="word", borderwidth=0,
        )
        self.settingsTxt.grid(row=0, column=3, rowspan=3, sticky="snew", padx=10)

        # navigation frame
        self.navFrm = ttk.Frame(self.top)
        self.navFrm.grid(row=1, column=0, sticky="snew", padx=20)

        self.position_dispLbl = ttk.Label(self.navFrm, textvariable=self.disp_record)
        self.position_dispLbl.grid(
            row=0, column=0, columnspan=2, sticky="snew", padx=10
        )
        self.leftBtn = ttk.Button(
            self.navFrm, text="<<", width=3, command=self.previous_record
        )
        self.leftBtn.grid(row=1, column=0, columnspan=2, sticky="nsw", padx=10, pady=5)

        self.rightBtn = ttk.Button(
            self.navFrm, text=">>", width=3, command=self.next_record
        )
        self.rightBtn.grid(row=1, column=0, columnspan=2, sticky="nse", padx=10, pady=5)

        ttk.Label(self.navFrm, text="jump to:").grid(
            row=1, column=2, sticky="snw", padx=10, pady=5
        )
        self.jumpEnt = ttk.Entry(
            self.navFrm, textvariable=self.jump_record, width=5, validatecommand=self.vj
        )
        self.jumpEnt.grid(row=1, column=3, sticky="snw", padx=10, pady=5)

        self.jumpBtn = ttk.Button(
            self.navFrm, text="go", width=3, command=self.jump_to_record
        )
        self.jumpBtn.grid(row=1, column=4, sticky="snw", padx=10, pady=5)

        # output
        searchICO = tk.PhotoImage(file="./icons/search.gif")
        self.dstLbl = ttk.Label(self.navFrm, text="output:")
        self.dstLbl.grid(row=0, column=5, sticky="sne", padx=10, pady=5)
        self.dstEnt = ttk.Entry(self.navFrm, width=60, textvariable=self.dst_fh)
        self.dstEnt.grid(row=0, column=6, sticky="snew", padx=10, pady=5)
        self.dstEnt["state"] = "readonly"
        self.dstBtn = ttk.Button(
            self.navFrm, image=searchICO, cursor="hand2", command=self.find_destination
        )
        self.dstBtn.image = searchICO
        self.dstBtn.grid(row=0, column=7, sticky="ne", padx=10, pady=5)

        self.confirmBtn = ttk.Button(
            self.navFrm, text="confirm", width=8, command=self.confirm
        )
        self.confirmBtn.grid(row=0, column=8, sticky="nsw", padx=10, pady=5)

        self.cancelBtn = ttk.Button(
            self.navFrm, text="cancel", width=8, command=self.top.destroy
        )
        self.cancelBtn.grid(row=0, column=9, sticky="nse", padx=10, pady=5)

        # worlcat records display frame
        self.dispFrm = ttk.LabelFrame(self.top, text="Sierra & Worldcat records")
        self.dispFrm.grid(row=2, column=0, sticky="snew", padx=20, pady=5)

        self.xscrollbar = ttk.Scrollbar(self.dispFrm, orient=tk.HORIZONTAL)
        self.xscrollbar.grid(row=0, column=1, columnspan=10, sticky="nwe")
        self.yscrollbar = ttk.Scrollbar(self.dispFrm, orient=tk.VERTICAL)
        self.yscrollbar.grid(row=1, column=0, rowspan=20, sticky="nse")
        self.preview_base = tk.Canvas(
            self.dispFrm,
            bg="gray",
            height="18c",
            width="27c",
            xscrollcommand=self.xscrollbar.set,
            yscrollcommand=self.yscrollbar.set,
        )
        self.preview_base.grid(row=1, column=1, rowspan=20, columnspan=10)
        self.preview_base.bind_all("<MouseWheel>", self.on_mousewheel)
        self.preview()

        # populate preview_frame with Sierra & Worldcat data
        self.display_criteria()
        self.display_totals()
        self.populate_preview(self.meta_ids[self.disp_record_no])
        # update count display
        self.disp_record.set(
            "record {} / {}".format(self.disp_record_no + 1, self.count_total)
        )

    def verify_barcodes(self):
        valid = True
        if self.system == "NYPL" and self.library == "research":
            for v in self.tracker.values():
                if len(v["barcode"].get()) not in (0, 14):
                    valid = False
        return valid

    def save_choices(self):
        self.cur_manager.busy()
        valid_barcodes = self.verify_barcodes()
        if valid_barcodes:
            for k, v in self.tracker.items():
                if v["check"].get():
                    persist_choice([v["wcsmid"]], True, barcode_var=v["barcode"])
                else:
                    persist_choice([v["wcsmid"]], False, barcode_var=v["barcode"])
            self.cur_manager.notbusy()
        else:
            self.cur_manager.notbusy()
            msg = "Invalid barcodes have been found.\n" "Unable to save data."
            tkMessageBox.showwarning("Barcode warning", msg, parent=self.top)

    def previous_record(self):
        self.save_choices()
        if self.disp_record_no > 0:
            self.disp_record_no -= 1
            self.preview_frame.destroy()
            self.preview()
            mlogger.debug("Displaying record: {}".format(self.disp_record_no))
            self.populate_preview(self.meta_ids[self.disp_record_no])
            self.disp_record.set(
                "record {} / {}".format(self.disp_record_no + 1, self.count_total)
            )

    def next_record(self):
        self.save_choices()
        if self.disp_record_no < self.count_total - 1:
            self.disp_record_no += 1
            self.preview_frame.destroy()
            self.preview()
            mlogger.debug("Displaying record: {}".format(self.disp_record_no))
            self.populate_preview(self.meta_ids[self.disp_record_no])
            self.disp_record.set(
                "record {} / {}".format(self.disp_record_no + 1, self.count_total)
            )

    def jump_to_record(self):
        self.save_choices()
        rec_no = int(self.jump_record.get().strip()) - 1
        if rec_no >= 0 and rec_no <= self.count_total:
            self.disp_record_no = rec_no
            self.preview_frame.destroy()
            self.preview()
            mlogger.debug("Displaying record: {}".format(self.disp_record_no))
            self.populate_preview(self.meta_ids[self.disp_record_no])
            self.disp_record.set(
                "record {} / {}".format(self.disp_record_no + 1, self.count_total)
            )

    def find_destination(self):
        # ask destination file
        user_data = shelve.open(USER_DATA)
        paths = user_data["paths"]
        if "pvr_last_open_dir" in paths:
            last_open_dir = paths["pvr_last_open_dir"]
        else:
            last_open_dir = MY_DOCS
        user_data.close()

        dst_fh = tkFileDialog.asksaveasfilename(
            parent=self.top,
            title="Save as",
            # filetypes=(('marc file', '*.mrc')),
            initialfile="worldcat_bibs.mrc",
            initialdir=last_open_dir,
        )
        if dst_fh:
            self.dst_fh.set(dst_fh)

    def output_data(self):
        self.cur_manager.busy()
        # write pymarc obj to a MARC file and create
        # csv file

        create_marc_file(self.dst_fh.get(), self.hold_msg.get())

        if self.hold_var.get():
            msg = "Records have been saved to a file.\n"

            holdings = set_oclc_holdings(self.dst_fh.get())
            if holdings:
                msg += "OCLC holdings have been set."
            else:
                msg += (
                    "Unable to set holding for all records.\n"
                    'See "holdings-issues.cvs" for a list of\n'
                    "OCLC numbers for which holdings were not set."
                )
        else:
            msg = (
                "Records have been saved to a file.\n" "No OCLC holdings have been set."
            )

        self.cur_manager.notbusy()

        tkMessageBox.showinfo("Info", msg, parent=self.top)

    def confirm(self):
        self.save_choices()
        if self.dst_fh.get():
            self.output_data()
        else:
            self.find_destination()
            if self.dst_fh.get():
                self.output_data()

    def display_criteria(self):
        rec = get_batch_criteria_record()
        self.system = rec.system
        self.library = rec.library
        line2 = (
            "system: {}, library: {}, action: {}, API: {}, "
            "data source: {}".format(
                rec.system, rec.library, rec.action, rec.api, rec.data_source
            )
        )
        line3 = (
            "encode lvl: {}, mat type: {}, cat rules: {}, "
            "cat source: {}, id type: {}".format(
                rec.encode_level,
                rec.mat_type,
                rec.cat_rules,
                rec.cat_source,
                rec.id_type,
            )
        )
        self.settingsTxt.insert(1.0, rec.file + "\n")
        self.settingsTxt.insert(2.0, line2 + "\n")
        self.settingsTxt.insert(3.0, line3)
        self.settingsTxt["state"] = "disable"

    def display_totals(self):
        self.count_total, self.meta_ids = count_total()

    def populate_preview(self, meta_ids):
        self.cur_manager.busy()
        data = get_bib(meta_ids)
        row = 0
        self.tracker = {}
        for d in data:
            wid, wdict = self.create_resource(d, row)
            self.tracker[wid] = wdict
            row += 1
        self.cur_manager.notbusy()

    def create_resource(self, data, row):
        unitFrm = tk.Frame(self.preview_frame)
        unitFrm.grid(row=row, column=0, columnspan=10, sticky="snew")
        unitFrm.configure(background="white")
        # unitFrm.columnconfigure(0, minsize=40)

        var = tk.IntVar()
        var.set(data[1]["choice"])
        barcode = tk.StringVar()
        if data[1]["barcode"] is not None:
            barcode.set(data[1]["barcode"])

        selCbn = ttk.Checkbutton(unitFrm, var=var)
        selCbn.grid(row=0, column=0, sticky="snew", padx=5)

        sierraTxt = tk.Text(unitFrm, height=5, width=123, wrap="word", borderwidth=0)
        sierraTxt.grid(row=0, column=1, sticky="snew", pady=5)

        inputFrm = ttk.Frame(unitFrm)
        inputFrm.grid(row=1, column=1, sticky="snw", padx=5, pady=5)
        ttk.Label(inputFrm, text="barcode:").grid(row=0, column=0, sticky="snw", pady=5)
        barcodeEnt = ttk.Entry(
            inputFrm, textvariable=barcode, validate="key", validatecommand=self.vb
        )
        barcodeEnt.grid(row=0, column=1, sticky="sne", padx=5, pady=5)

        self.populate_sierra_data(sierraTxt, data[1])

        worldcatTxt = tk.Text(
            unitFrm, wrap="word", height=100, width=114, borderwidth=0
        )
        worldcatTxt.grid(row=2, column=1, sticky="snew", padx=2, pady=5)

        self.populate_worldcat_data(worldcatTxt, data[2])

        return (selCbn.winfo_name(), dict(check=var, wcsmid=data[0], barcode=barcode))

    def populate_sierra_data(self, widget, data):
        l1 = "  {}\n".format(data["title"])
        l2 = "  bib #: {}, ord #: {}  notes: {} | {} | {}\n".format(
            data["sierraId"],
            data["oid"],
            data["venNote"],
            data["note"],
            data["intNote"],
        )
        l3 = "  location: {}\n".format(data["locs"])

        widget.insert(1.0, l1)
        widget.insert(2.0, l2)
        widget.insert(3.0, l3)

        widget.tag_add("header", "1.0", "1.end")
        widget.tag_config("header", font=("tahoma", "11", "bold"))
        widget.tag_add("location", "3.11", "3.end")
        widget.tag_config(
            "location", font=("tahoma", "11", "bold"), foreground="tomato2"
        )
        widget["state"] = "disable"

    def populate_worldcat_data(self, widget, data):
        if data:
            # highlight important data
            c = 0
            for tag in data:
                c += 1
                pos = float("{}.0".format(c))
                widget.insert(pos, "{}\n".format(tag))
                if "=008" in tag:
                    widget.tag_add("audn", "{}.28".format(c))
                    widget.tag_add("litform", "{}.39".format(c))
                    widget.tag_add("bio", "{}.40".format(c))
                    widget.tag_add("lang", "{}.41".format(c), "{}.44".format(c))

                elif tag[1:4] in ("082", "100", "110", "111", "130", "245"):
                    widget.tag_add("highlight", str(pos), "{}.{}".format(c, len(tag)))
                elif "=091" in tag:
                    widget.tag_add("call", str(pos), "{}.{}".format(c, len(tag)))
                elif "=600" in tag:
                    if tag[7] == "0":
                        widget.tag_add(
                            "highlight", str(pos), "{}.{}".format(c, len(tag))
                        )

            # widget.insert(1.0, data)
            widget.tag_add("lvl", "1.23")

            widget.tag_config(
                "audn", font=("tahoma", "10", "bold"), foreground="chocolate2"
            )
            widget.tag_config(
                "litform", font=("tahoma", "10", "bold"), foreground="blue2"
            )
            widget.tag_config(
                "bio", font=("tahoma", "10", "bold"), foreground="firebrick"
            )
            widget.tag_config(
                "lang", font=("tahoma", "10", "bold"), foreground="darkgreen"
            )
            widget.tag_config(
                "lvl", font=("tahoma", "13", "bold"), foreground="tomato2"
            )
            widget.tag_config(
                "highlight", font=("tahoma", "10", "bold"), foreground="purple3"
            )
            widget.tag_config(
                "call", font=("tahoma", "10", "bold"), foreground="tomato2"
            )
        else:
            l1 = "NO GOOD MATCHES FOUND IN WORLDCAT"
            widget.insert(1.0, l1)
            widget.configure(height=2)

        widget["state"] = "disable"

    def selection_observer(self, *args):
        if self.sel_var.get() == 1:
            self.sel_lbl.set("unselect all")
            for key, value in self.tracker.items():
                value["check"].set(1)
            persist_choice(self.meta_ids, True)
        elif self.sel_var.get() == 0:
            self.sel_lbl.set("select all")
            for key, value in self.tracker.items():
                value["check"].set(0)
            persist_choice(self.meta_ids, False)

    def preview(self):
        self.preview_frame = tk.Frame(self.preview_base)
        self.xscrollbar.config(command=self.preview_base.xview)
        self.yscrollbar.config(command=self.preview_base.yview)
        self.preview_base.create_window(
            (0, 0), window=self.preview_frame, anchor="nw", tags="self.preview_frame"
        )
        self.preview_frame.bind("<Configure>", self.onFrameConfigure)

    def onFrameConfigure(self, event):
        self.preview_base.config(scrollregion=self.preview_base.bbox("all"))

    def on_mousewheel(self, event):
        try:
            self.preview_base.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except tk.TclError:
            pass

    def onValidateBarcode(self, d, i, P):
        valid = True
        if self.system == "NYPL":
            if self.library == "research":
                if d == "1":
                    if int(i) in (0, 1, 3, 4):
                        if P[int(i)] != "3":
                            valid = False
                    if int(i) == 2:
                        if P[2] != "4":
                            valid = False
                    if int(i) > 4:
                        if not P.isdigit():
                            valid = False
                    if int(i) > 13:
                        valid = False
        return valid

    def onValidateJump(self, d, i, P):
        valid = True
        return valid
