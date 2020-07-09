# general tools to read, parse, and write MARC files

from pymarc import MARCReader, JSONReader, MARCWriter, Field
from pymarc.exceptions import RecordLengthInvalid, RecordDirectoryInvalid
from datetime import datetime


from errors import OverloadError
from parsers import parse_isbn, parse_issn, parse_upc, parse_sierra_id
from sierra_dicts import NBIB_DEFAULT_LOCATIONS, NYPL_BRANCHES


def read_marc21(file):
    reader = MARCReader(open(file, "r"), to_unicode=True, hide_utf8_warnings=True)
    return reader


def write_marc21(outfile, bib):
    try:
        writer = MARCWriter(open(outfile, "a"))
        writer.write(bib)
    except WindowsError:
        raise WindowsError
    finally:
        writer.close()


def read_marc_in_json(data):
    reader = JSONReader(data)
    return reader


def create_field(tag, indicators=[" ", " "], subfields=["a"]):
    return Field(tag=tag, indicators=indicators, subfields=subfields)


def create_target_id_field(system, bNumber):
    if len(bNumber) != 8:
        raise ValueError(
            "incorrect Sierra bib number encountered " "while creating target id field"
        )
    bNumber = ".b{}a".format(bNumber)
    system = system.lower()
    if system == "bpl":
        return Field(tag="907", indicators=[" ", " "], subfields=["a", bNumber])
    if system == "nypl":
        return Field(tag="945", indicators=[" ", " "], subfields=["a", bNumber])


def check_sierra_id_presence(system, bib):
    found = False
    if system == "nypl":
        if "945" in bib:
            found = True
    elif system == "bpl":
        if "907" in bib:
            found = True
    return found


def sierra_command_tag(bib):
    found = False
    try:
        if "949" in bib:
            for field in bib.get_fields("949"):
                if (
                    field.indicators == [" ", " "]
                    and "a" in field
                    and field["a"][0] == "*"
                ):
                    found = True
                    break
    except IndexError:
        raise IndexError("Encountered IndexError in vendor 949$a")
    return found


def set_nypl_sierra_bib_default_location(library, bib):
    """
    adds a 949 MARC tag command for setting bibliographic location
    args:
        bib: pymarc.record.Record
    returns:
        bib: pymarc.record.Record, with added command "bn=" to
            the "949  $a" field, the field is created if missing
    """

    # determine correct location code
    if library == "branches":
        defloc = NBIB_DEFAULT_LOCATIONS["branches"]
    elif library == "research":
        defloc = NBIB_DEFAULT_LOCATIONS["research"]
    else:
        raise OverloadError("Invalid library argument passed: {}".format(library))

    # determine if 949 already preset
    if sierra_command_tag(bib):
        for field in bib.get_fields("949"):
            if field.indicators == [" ", " "]:
                command = field["a"].strip()
                if "bn=" in command:
                    # skip, already present
                    break
                else:
                    if command[-1] == ";":
                        new_command = "{}{}".format(field["a"], "bn={};".format(defloc))
                    else:
                        new_command = "{}{}".format(
                            field["a"], ";bn={};".format(defloc)
                        )
                    field["a"] = new_command
                    break

    else:
        # command tag not preset add
        bib.add_field(
            Field(
                tag="949",
                indicators=[" ", " "],
                subfields=["a", "*bn={};".format(defloc)],
            )
        )
    return bib


def create_field_from_template(template):
    if template["ind1"] is None:
        ind1 = " "
    else:
        ind1 = template["ind1"]
    if template["ind2"] is None:
        ind2 = " "
    else:
        ind2 = template["ind2"]
    subfields = []
    [subfields.extend([k, v]) for k, v in template["subfields"].items()]
    field = Field(tag=template["tag"], indicators=[ind1, ind2], subfields=subfields)
    return field


def create_initials_field(system, library, value):
    """
    creates intitials marc field
    args:
        system: str, NYPL or BPL
        library: str, branches or research
        value: str, value to be entered in subfield $a
    returns:
        field: pymarc Field object
    """

    if system == "NYPL":
        tag = "901"
        if library == "research":
            subfields = ["a", value, "b", "CATRL"]
        else:
            subfields = ["a", value, "b", "CATBL"]
    elif system == "BPL":
        tag = "947"
        subfields = ["a", value]

    return Field(tag=tag, indicators=[" ", " "], subfields=subfields)


def create_controlfield(tag, data):
    return Field(tag=tag, data=data)


def count_bibs(file):
    reader = read_marc21(file)
    bib_count = 0
    try:
        for bib in reader:
            bib_count += 1
        return bib_count
    except RecordLengthInvalid:
        raise OverloadError(
            "Attempted to process non-MARC file,\n"
            "or invalid MARC file: {}".format(file)
        )
    except UnicodeDecodeError:
        raise OverloadError(
            "Character encoding error in file:\n{}\n"
            "Please convert character encoding to UTF-8\n"
            "using MARCEdit program.".format(file)
        )
    except RecordDirectoryInvalid:
        raise OverloadError(
            "Encountered malformed MARC record directory\n"
            'in file "{}".\nUse MARCEdit to identify '
            "incorrect record.".format(file)
        )


def db_template_to_960(template, vendor_960):
    """"passed attr must be an instance of NYPLOrderTemplate"""

    # order fixed fields mapping
    try:
        vsub = vendor_960.subfields
        # subfields present on the vendor record
        ven_subs = set([vsub[x] for x in range(0, len(vsub), 2)])

    except AttributeError:
        vsub = []
        ven_subs = set()

    # list of relevalnt to PVR subfields of 960
    pvr_subs = set(["a", "b", "c", "d", "e", "f", "g", "h", "i", "m", "v", "w", "x"])

    # find extra subfields to be carried over to the new field
    nsub = []
    diff_subs = ven_subs - pvr_subs
    for s in diff_subs:
        nsub.extend([vsub[vsub.index(s)], vsub[vsub.index(s) + 1]])

    # create list of subfield codes without subfield data as index
    vinx = [vsub[x] if x % 2 == 0 else None for x in range(0, len(vsub))]

    # use template values if provided else use original if exists
    try:
        if template.acqType:
            nsub.extend(["a", template.acqType])
        else:
            nsub.extend(["a", vsub[vinx.index("a") + 1]])
    except ValueError:
        pass

    try:
        if template.claim:
            nsub.extend(["b", template.claim])
        else:
            nsub.extend(["b", vsub[vinx.index("b") + 1]])
    except ValueError:
        pass

    try:
        if template.code1:
            nsub.extend(["c", template.code1])
        else:
            nsub.extend(["c", vsub[vinx.index("c") + 1]])
    except ValueError:
        pass

    try:
        if template.code2:
            nsub.extend(["d", template.code2])
        else:
            nsub.extend(["d", vsub[vinx.index("d") + 1]])
    except ValueError:
        pass

    try:
        if template.code3:
            nsub.extend(["e", template.code3])
        else:
            nsub.extend(["e", vsub[vinx.index("e") + 1]])
    except ValueError:
        pass

    try:
        if template.code4:
            nsub.extend(["f", template.code4])
        else:
            nsub.extend(["f", vsub[vinx.index("f") + 1]])
    except ValueError:
        pass

    try:
        if template.form:
            nsub.extend(["g", template.form])
        else:
            nsub.extend(["g", vsub[vinx.index("g") + 1]])
    except ValueError:
        pass

    try:
        if template.orderNote:
            nsub.extend(["h", template.orderNote])
        else:
            nsub.extend(["h", vsub[vinx.index("h") + 1]])
    except ValueError:
        pass

    try:
        if template.orderType:
            nsub.extend(["i", template.orderType])
        else:
            nsub.extend(["i", vsub[vinx.index("i") + 1]])
    except ValueError:
        pass

    try:
        if template.status:
            nsub.extend(["m", template.status])
        else:
            nsub.extend(["m", vsub[vinx.index("m") + 1]])
    except ValueError:
        pass

    try:
        if template.vendor:
            nsub.extend(["v", template.vendor])
        else:
            nsub.extend(["v", vsub[vinx.index("v") + 1]])
    except ValueError:
        pass

    try:
        if template.lang:
            nsub.extend(["w", template.lang])
        else:
            nsub.extend(["w", vsub[vinx.index("w") + 1]])
    except ValueError:
        pass

    try:
        if template.country:
            nsub.extend(["x", template.country])
        else:
            nsub.extend(["x", vsub[vinx.index("x") + 1]])
    except ValueError:
        pass

    if nsub == []:
        field = None
    else:
        field = Field(tag="960", indicators=[" ", " "], subfields=nsub)

    return field


def db_template_to_961(template, vendor_961):
    """combines vendor and template 961 field data in
    a new 961 field
    attrs:
        template (template datastore record),
        vendor_961 (vendor 961 field in form of pymarc object)
    returns:
        None (no data coded in the 961)
        field (pymarc Field object)"""

    # order variable fields
    try:
        vsub = vendor_961.subfields
        # subfields present on the vendor record
        ven_subs = set([vsub[x] for x in range(0, len(vsub), 2)])
    except AttributeError:
        vsub = []
        ven_subs = set()

    # list of relevalnt to PVR subfields of 960
    pvr_subs = set(["a", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m"])

    # find extra subfield to be carried over to the new field
    nsub = []
    diff_subs = ven_subs - pvr_subs

    for s in diff_subs:
        nsub.extend([vsub[vsub.index(s)], vsub[vsub.index(s) + 1]])

    # create list of subfield codes without subfield data as index
    vinx = [vsub[x] if x % 2 == 0 else None for x in range(0, len(vsub))]

    # apply from template if provided, else keep the vendor data
    try:
        if template.identity:
            nsub.extend(["a", template.identity])
        else:
            nsub.extend(["a", vsub[vinx.index("a") + 1]])
    except ValueError:
        pass

    try:
        if template.generalNote:
            nsub.extend(["c", template.generalNote])
        else:
            nsub.extend(["c", vsub[vinx.index("c") + 1]])
    except ValueError:
        pass

    try:
        if template.internalNote:
            nsub.extend(["d", template.internalNote])
        else:
            nsub.extend(["d", vsub[vinx.index("d") + 1]])
    except ValueError:
        pass

    try:
        if template.oldOrdNo:
            nsub.extend(["e", template.oldOrdNo])
        else:
            nsub.extend(["e", vsub[vinx.index("e") + 1]])
    except ValueError:
        pass

    try:
        if template.selector:
            nsub.extend(["f", template.selector])
        else:
            nsub.extend(["f", vsub[vinx.index("f") + 1]])
    except ValueError:
        pass

    try:
        if template.venAddr:
            nsub.extend(["g", template.venAddr])
        else:
            nsub.extend(["g", vsub[vinx.index("g") + 1]])
    except ValueError:
        pass

    try:
        if template.venNote:
            nsub.extend(["h", template.venNote])
        else:
            nsub.extend(["h", vsub[vinx.index("h") + 1]])
    except ValueError:
        pass

    try:
        if template.blanketPO:
            nsub.extend(["m", template.blanketPO])
        else:
            nsub.extend(["m", vsub[vinx.index("m") + 1]])
    except ValueError:
        pass

    try:
        if template.venTitleNo:
            nsub.extend(["i", template.venTitleNo])
        else:
            nsub.extend(["i", vsub[vinx.index("i") + 1]])
    except ValueError:
        pass

    try:
        if template.paidNote:
            nsub.extend(["j", template.paidNote])
        else:
            nsub.extend(["j", vsub[vinx.index("j") + 1]])
    except ValueError:
        pass

    try:
        if template.shipTo:
            nsub.extend(["k", template.shipTo])
        else:
            nsub.extend(["k", vsub[vinx.index("k") + 1]])
    except ValueError:
        pass

    try:
        if template.requestor:
            nsub.extend(["l", template.requestor])
        else:
            nsub.extend(["l", vsub[vinx.index("l") + 1]])
    except ValueError:
        pass

    if nsub == []:
        field = None
    else:
        field = Field(tag="961", indicators=[" ", " "], subfields=nsub)

    return field


def db_template_to_949(mat_format):
    field = Field(
        tag="949", indicators=[" ", " "], subfields=["a", "*b2={};".format(mat_format)]
    )
    return field


def create_command_line_field(command):
    field = Field(tag="949", indicators=[" ", " "], subfields=["a", command])
    return field


class BibMeta:
    """
    creates a general record meta object
    args:
        bib obj (pymarc)
        sierraId str
    """

    def __init__(self, bib, sierraId=None):
        self.t001 = None
        self.t003 = None
        self.t005 = None
        self.t020 = []
        self.t022 = []
        self.t024 = []
        self.t028 = []
        self.t336 = []
        self.t901 = []
        self.t947 = []
        self.sierraId = sierraId
        self.title = None
        self.bCallNumber = None
        self.rCallNumber = []

        # parse 001 field (control field)
        if "001" in bib:
            self.t001 = bib["001"].data

        # parse 003 field (control number identifier)
        if "003" in bib:
            self.t003 = bib["003"].data

        # parse 005 field (version date)
        if "005" in bib:
            try:
                self.t005 = datetime.strptime(bib["005"].data, "%Y%m%d%H%M%S.%f")
            except ValueError:
                pass

        for field in bib.get_fields("020"):
            for subfield in field.get_subfields("a"):
                isbn = parse_isbn(subfield)
                if isbn is not None:
                    self.t020.append(isbn)

        for field in bib.get_fields("022"):
            for subfield in field.get_subfields("a"):
                issn = parse_issn(subfield)
                if issn is not None:
                    self.t022.append(issn)

        for field in bib.get_fields("024"):
            for subfield in field.get_subfields("a"):
                upc = parse_upc(subfield)
                if upc is not None:
                    self.t024.append(upc)

        for field in bib.get_fields("028"):
            for subfield in field.get_subfields("a"):
                upc = parse_upc(subfield)
                if upc is not None:
                    self.t028.append(upc)

        for field in bib.get_fields("336"):
            for subfield in field.get_subfields("a"):
                self.t336.append(subfield)

        for field in bib.get_fields("901"):
            self.t901.append(field.value())

        for field in bib.get_fields("947"):
            self.t947.append(field.value())

        # parse Sierra number
        if self.sierraId is None:
            if "907" in bib:
                self.sierraId = parse_sierra_id(bib.get_fields("907")[0].value())
            elif "945" in bib:
                self.sierraId = parse_sierra_id(bib.get_fields("945")[0].value())

        # parse branches call number
        if "099" in bib:
            self.bCallNumber = bib.get_fields("099")[0].value()
        elif "091" in bib:
            self.bCallNumber = bib.get_fields("091")[0].value()

        # parese research call numbers
        if "852" in bib:
            for field in bib.get_fields("852"):
                if field.indicators[0] == "8":
                    self.rCallNumber.append(field.value())

        self.title = bib.title()

    def __repr__(self):
        return (
            "<BibMeta(001:{}, 003:{}, 005:{}, 020:{}, 022:{}, 024:{}, "
            "028:{}, 336: {}, 901:{}, 947:{}, sierraId:{}, "
            "bCallNumber:{}, rCallNumber:{})>".format(
                self.t001,
                self.t003,
                self.t005,
                self.t020,
                self.t022,
                self.t024,
                self.t028,
                self.t336,
                self.t901,
                self.t947,
                self.sierraId,
                self.bCallNumber,
                self.rCallNumber,
            )
        )


class VendorBibMeta(BibMeta):
    """
    Implements vendor specific bib metatada
    args:
        bib (pymarc obj)
        vendor str
        dstLibrary str ('research' or 'branches')
    """

    def __init__(self, bib, vendor=None, dstLibrary=None):
        BibMeta.__init__(self, bib)
        self.vendor = vendor
        self.dstLibrary = dstLibrary
        self.barcodes = []

        # NYPL item records
        for tag in bib.get_fields("949"):
            if tag.indicators == [" ", "1"]:
                for barcode in tag.get_subfields("i"):
                    self.barcodes.append(str(barcode))

        # BPL item records
        for tag in bib.get_fields("960"):
            if tag.indicators == [" ", " "]:
                for barcode in tag.get_subfields("i"):
                    self.barcodes.append(str(barcode))

    def __repr__(self):
        return (
            "<VendorBibMeta(001:{}, 003:{}, 005:{}, 020:{}, 022:{}, "
            "024:{}, 028:{}, 336:{}, 901:{}, 947:{}, "
            "sierraId:{}, bCallNumber:{}, rCallNumber:{}, "
            "vendor:{}, dstLibrary:{}, barcodes:{})>".format(
                self.t001,
                self.t003,
                self.t005,
                self.t020,
                self.t022,
                self.t024,
                self.t028,
                self.t336,
                self.t901,
                self.t947,
                self.sierraId,
                self.bCallNumber,
                self.rCallNumber,
                self.vendor,
                self.dstLibrary,
                self.barcodes,
            )
        )


class InhouseBibMeta(BibMeta):
    """
    Implements inhouse specific bib metadata
    args:
        bib obj (pymarc)
        sierraId str
        location list
    """

    def __init__(self, bib, sierraId=None, locations=[]):
        BibMeta.__init__(self, bib)
        if sierraId is not None:
            self.sierraId = sierraId
        self.catSource = "vendor"
        self.ownLibrary = self._determine_ownLibrary(bib, locations)

        # source of cataloging
        # check 049 code to determine library
        if "049" in bib:
            field = bib.get_fields("049")[0]["a"]
            if "BKLA" in field:  # BPL
                if self.t001 is not None:
                    if self.t001[0] == "o" and self.t003 == "OCoLC":
                        self.catSource = "inhouse"
            elif "NYPP" in field:  # NYPL
                if "901" in bib:
                    fields = bib.get_fields("901")
                    for field in fields:
                        if "b" in field:
                            subfield = field["b"][0]
                            if "CAT" in subfield:
                                self.catSource = "inhouse"
                                break

    def _determine_ownLibrary(self, bib, locations):
        # owning library
        # for nypl check also locations

        bl = False
        rl = False

        # brief order record scenario
        if "zzzzz" in locations:
            bl = True
        if "xxx" in locations:
            rl = True

        # full bib scenario
        if "091" in bib or "099" in bib:
            bl = True
        if "852" in bib:
            for field in bib.get_fields("852"):
                if field.indicators[0] == "8":
                    rl = True
                    break

        # explicit NYPL locations
        rl_my_locs = ["myd", "myh", "mym", "myt"]
        for l in locations:
            try:
                if l[:2] == "my":
                    if l in rl_my_locs:
                        rl = True
                    else:
                        bl = True
                elif l[:2] == "sc":
                    rl = True
                elif l[:2] == "ma":
                    rl = True
                elif l[:2] in NYPL_BRANCHES.keys():
                    bl = True
            except IndexError:
                pass
            except TypeError:
                pass

        if bl and not rl:
            return "branches"
        elif bl and rl:
            return "mixed"
        elif not bl and rl:
            return "research"

    def __repr__(self):
        return (
            "<InhouseBibMeta(001:{}, 003:{}, 005:{}, 020:{}, 022:{}, "
            "024:{}, 028:{}, 336:{}, 901:{}, 947:{}, "
            "sierraId:{}, bCallNumber:{}, rCallNumber:{}, "
            "catSource:{}, ownLibrary:{})>".format(
                self.t001,
                self.t003,
                self.t005,
                self.t020,
                self.t022,
                self.t024,
                self.t028,
                self.t336,
                self.t901,
                self.t947,
                self.sierraId,
                self.bCallNumber,
                self.rCallNumber,
                self.catSource,
                self.ownLibrary,
            )
        )


class BibOrderMeta:
    """
    Bib with corresponding order metadata
    """

    def __init__(
        self,
        system=None,
        dstLibrary=None,
        sierraId=None,
        oid=None,
        t010=None,
        t001=None,
        t005=None,
        t020=[],
        t024=[],
        title=None,
        locs=None,
        venNote=None,
        note=None,
        intNote=None,
        code2=None,
        code4=None,
        oFormat=None,
        vendor=None,
    ):

        self.system = system
        self.dstLibrary = dstLibrary
        self.sierraId = sierraId
        self.oid = oid
        self.t001 = t001
        self.t005 = t005
        self.t010 = t010
        self.t020 = t020
        self.t024 = t024
        self.title = title
        self.venNote = venNote
        self.note = note
        self.intNote = intNote
        self.code2 = code2
        self.code4 = code4
        self.locs = locs
        self.oFormat = oFormat
        self.vendor = vendor
        self.ord_conflicts = False
        self.callType = None
        self.callLabel = None
        self.wlPrefix = self._has_world_language_prefix()
        self.audnType = None
        self.bCallNumber = None
        self.rCallNumber = []

        self._normalize_data()
        self._determine_audience()
        self._determine_callLabel()
        self._determine_callNumber_type()
        self._determine_ord_conflicts()

    def _normalize_data(self):
        try:
            self.venNote = self.venNote.lower()
        except AttributeError:
            pass

        try:
            self.code2 = self.code2.lower()
        except AttributeError:
            pass

        try:
            self.code4 = self.code4.lower()
        except AttributeError:
            pass

        try:
            self.locs = self.locs.lower()
        except AttributeError:
            pass

        try:
            self.oFormat = self.oFormat.lower()
        except AttributeError:
            pass

        try:
            self.vendor = self.vendor.lower()

        except AttributeError:
            pass

        self.t020 = [parse_isbn(x) for x in self.t020]

    def _has_world_language_prefix(self):
        if self.system == "NYPL":
            try:
                if self.locs[4] == "l":
                    return True
                else:
                    return False
            except IndexError:
                return False
            except TypeError:
                return False
        elif self.system == "BPL":
            try:
                if self.locs[4] == "l":
                    return True
                else:
                    return False
            except IndexError:
                return False
            except TypeError:
                return False
        else:
            raise ValueError

    def _determine_audience(self):
        # default audn is adult/young adult
        self.audnType = "a"

        # use first location code only
        try:
            loc_audn = self.locs[2]
        except IndexError:
            loc_audn = None
        except TypeError:
            loc_audn = None

        if loc_audn not in ("a", "j", "y"):
            loc_audn = None

        if self.system == "NYPL":
            if self.code4 in ("n", "-", None):
                c4_audn = None
            else:
                c4_audn = self.code4

            if loc_audn and c4_audn is None:
                self.audnType = loc_audn
            elif c4_audn and loc_audn is None:
                self.audnType = c4_audn
            elif loc_audn == c4_audn:
                self.audnType = c4_audn
            else:
                self.audnType = None

        elif self.system == "BPL":
            # no need for special rules for BPL
            self.audnType = loc_audn
        else:
            raise ValueError

    def _determine_callNumber_type(self):
        """
        NYPL callTypes
            - pic
            - eas
            - fic
            - neu
            - mys
            - rom
            - sfn
            - wes
            - urb
            - gfc
            - bio
            - dew
        BPL callTypes:
            - pic
            - fic
            - bio
            - dew
            - neu
        """
        try:
            if self.system == "NYPL":
                if self.locs[4] == "i":
                    self.callType = "pic"
                elif self.locs[4] == "a":
                    self.callType = "eas"
                elif self.locs[4] in ("f", "y"):
                    self.callType = "fic"

                    # specific genres
                    if self.venNote is not None:
                        if "m" in self.venNote:
                            self.callType = "mys"  # MYSTERY
                        elif (
                            "r" in self.venNote
                            and "ref" not in self.venNote
                            and "yr" not in self.venNote
                        ):
                            self.callType = "rom"  # ROMANCE

                        elif "s" in self.venNote and "easy" not in self.venNote:
                            self.callType = "sfn"  # SCI-FI
                        elif "w" in self.venNote:
                            self.callType = "wes"  # WESTERN
                        elif "u" in self.venNote:
                            self.callType = "urb"  # URBAN
                        elif "g" in self.venNote:
                            self.callType = "gfi"  # Graphic fiction

                elif self.locs[4] in ("n", "1"):
                    # non-fiction
                    if "bio" in self.venNote:
                        self.callType = "bio"
                    else:
                        self.callType = "dew"
                else:
                    # including world languages
                    self.callType = "neu"

            if self.system == "BPL":

                if self.locs[3:5] in ("nb", "lp", "rf", "wl", "as", "  "):
                    self.callType = "neu"  # neutral, use other elements to determine

                if self.locs[3:5] in ("je", "er"):
                    self.callType = "pic"
                elif self.locs[3:5] in ("fc", "my", "sf", "sh"):
                    self.callType = "fic"
                elif self.locs[3:5] == "bi":
                    self.callType = "bio"
                elif self.locs[3:5] in ("nf", "ej"):
                    self.callType = "dew"
                else:
                    pass

                # if neutral callType pick venNote & callLabel
                if self.callType == "neu":
                    if self.callLabel == "lfc":
                        self.callType = "fic"

        except TypeError:
            pass

    def _determine_ord_conflicts(self):
        if self.system == "BPL":
            if self.callType == "pic":
                if self.callLabel not in (None, "pic", "boa", "con", "eas", "bpi"):
                    self.ord_conflicts = True
            elif self.callType == "fic":
                if self.callLabel not in (
                    None,
                    "fic",
                    "mys",
                    "sfn",
                    "sho",
                    "lfc",
                    "gra",
                    "rom",
                    "afc",
                    "bri",
                    "ser",
                    "lgp",
                ):
                    self.ord_conflicts = True
            elif self.callType == "bio":
                if self.callLabel not in (
                    None,
                    "bio",
                    "abi",
                    "lpg",
                    "lnf",
                    "soa",
                    "anf",
                ):
                    self.ord_conflicts = True
            elif self.callType == "dew":
                if self.callLabel not in (
                    None,
                    "lgp",
                    "lnf",
                    "ref",
                    "edu",
                    "soa",
                    "anf",
                    "fol",
                ):
                    self.ord_conflicts = True

        elif self.system == "NYPL":
            # develop later after consulting with Ching-Yen & Kenichi
            pass

    def _determine_callLabel(self):
        if self.venNote is None:
            pass
        elif self.system == "BPL":

            if self.venNote == "l":
                self.callLabel = "lgp"  # large print

            elif "b" in self.venNote:
                self.callLabel = "boa"  # board book

            elif self.venNote == "c":
                self.callLabel = "con"  # concept book

            elif "easy" in self.venNote:
                self.callLabel = "eas"  # early reader

            elif self.venNote == "k":
                self.callLabel = "bri"  # bridge

            elif "soa" in self.venNote:
                self.callLabel = "soa"  # SOA

            elif "bio" in self.venNote:
                self.callLabel = "bio"  # biography

            elif "m" in self.venNote:
                self.callLabel = "mys"  # mystery

            elif "s" in self.venNote:
                # after "soa"
                self.callLabel = "sfn"  # science fiction

            elif "y" in self.venNote:
                self.callLabel = "sho"  # short stories

            elif "lit;fic" in self.venNote:
                self.callLabel = "lfc"  # literacy fiction

            elif "lit;non" in self.venNote:
                self.callLabel = "lnf"  # literacy non-fic

            elif "ref" in self.venNote:
                self.callLabel = "ref"  # reference

            elif "r" in self.venNote:
                self.callLabel = "rom"  # romance

            elif "v" in self.venNote:
                self.callLabel = "edu"  # edu/career

            elif "g" in self.venNote:
                self.callLabel = "gra"  # graphic novel

            elif self.venNote == "a":
                self.callLabel = "asn"  # assigment

            # elif self.venNote == "a":
            #     self.callLabel = "afc"  # assignent fic

            elif "anon" in self.venNote:
                self.callLabel = "anf"  # assignment non-fic

            elif "auto" in self.venNote:
                self.callLabel = "abi"  # autobiography

            elif "q" in self.venNote:
                self.callLabel = "ser"  # series

            elif "pic" in self.venNote:
                self.callLabel = "pic"  # picture book
                if "bil" in self.venNote:
                    self.callLabel = "bpi"  # bilingual picture book
                elif "f" in self.venNote:
                    self.callLabel = "fol"  # folk/fairy tale

            elif "bil" in self.venNote:
                # bilingual books other than pic books
                self.callLabel = "bil"  # bilingual

        elif self.system == "NYPL":

            if "t" in self.venNote:
                self.callLabel = "lgp"  # large print

            elif "hol" in self.venNote:
                # note HOLIDAY label takes precedence over YR when applied
                # together; must go first
                self.callLabel = "hol"  # holiday

            elif "yr" in self.venNote:
                self.callLabel = "yrd"  # young reader

            elif self.venNote.lower() == "l":
                self.callLabel = "cla"  # classics

            elif "g" in self.venNote:
                self.callLabel = "gra"  # graphic novel

            elif "bil" in self.venNote:
                self.callLabel = "bil"  # bilingual

            elif "job" in self.venNote:
                self.callLabel = "job"

            elif "REF" in self.venNote:
                self.callLabel = "ref"

            elif "bbk" in self.venNote:
                self.callLabel = "boa"

            elif "FT" in self.venNote:
                self.callLabel = "fol"

    def __repr__(self):
        return (
            "<BibOrderMeta(system='%s', dstLibrary='%s', sierraId='%s', "
            " oid='%s', t001='%s', t005='%s', t010='%s', t020='%s', "
            "t024='%s', title='%s', locs='%s', venNote='%s', note='%s', "
            "intNote='%s', code2='%s', code4='%s', oFormat='%s', "
            "vendor='%s', callLabel='%s', callType='%s', audnType='%s', "
            "wlPrefix='%s')>"
            % (
                self.system,
                self.dstLibrary,
                self.sierraId,
                self.oid,
                self.t001,
                self.t005,
                self.t010,
                self.t020,
                self.t024,
                self.title,
                self.locs,
                self.venNote,
                self.note,
                self.intNote,
                self.code2,
                self.code4,
                self.oFormat,
                self.vendor,
                self.callLabel,
                self.callType,
                self.audnType,
                self.wlPrefix,
            )
        )
