from bibs import BibMeta


class VendorBibMeta(BibMeta):
    """
    Implements vendor specific bib metatada
    """
    def __init__(self, bib, dstLibrary=None):
        BibMeta.__init__(self, bib)
        self.vendor = None
        self.dstLibrary = dstLibrary
        self.action = 'attach'


    def __repr__(self):
        return "<VendorBibMeta(001:{}, 005:{}, 020:{}, 022:{}, " \
            "024:{}, 028:{}, " \
            "sierraID:{}, bCallNumber:{}, rCallNumber:{}, " \
            "dstLibrary:{}, action:{})>".format(
                self.t001, self.t005,
                self.t020,
                self.t022,
                self.t024,
                self.t028,
                self.sierraID,
                self.bCallNumber,
                self.rCallNumber,
                self.dstLibrary,
                self.action)


class InhouseBibMeta(BibMeta):
    """
    Implements inhouse specific bib metadata
    """

    def __init__(self, bib, sierraID=None, locations=[]):
        BibMeta.__init__(self, bib)
        self.sierraID = sierraID
        self.catSource = None
        self.ownLibrary = None

        # source of cataloging

        # owning library
        # for nypl check also locations
        bl = False
        rl = False
        if 'zzzzz' in locations:
            bl = True
        if 'xxx' in locations:
            rl = True
        if self.ownLibrary is None:
            if '091' in bib or '099' in bib:
                bl = True
            if '852' in bib:
                for field in bib.get_fields('852'):
                    if field.indicators[0] == '8':
                        rl = True
                        break

        if bl and not rl:
            self.ownLibrary = 'branches'
        elif bl and rl:
            self.ownLibrary = 'mixed'
        elif not bl and rl:
            self.ownLibrary = 'research'

    def __repr__(self):
        return "<VendorBibMeta(001:{}, 005:{}, 020:{}, 022:{}, " \
            "024:{}, 028:{}, " \
            "sierraID:{}, bCallNumber:{}, rCallNumber:{}, " \
            "catSource:{}, ownLibrary:{})>".format(
                self.t001, self.t005,
                self.t020,
                self.t022,
                self.t024,
                self.t028,
                self.sierraID,
                self.bCallNumber,
                self.rCallNumber,
                self.catSource,
                self.ownLibrary)
