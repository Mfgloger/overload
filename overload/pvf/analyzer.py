# compares vendor bib meta and inhouse bib meta and returns analysis object


class PVRReport:
    """
    A general analysis report class.
    Use analysis classes specific to each system.
    """
    def __init__(self, meta_vendor, meta_inhouse):
        self._meta_vendor = meta_vendor
        self._meta_inhouse = meta_inhouse
        self.vendor_id = None
        self.vendor = meta_vendor.vendor
        self.updated_by_vendor = False
        self.callNo_match = False
        self.vendor_callNo = meta_vendor.bCallNumber
        self.target_sierraId = None
        self.target_callNo = None
        self.inhouse_dups = []
        self.action = 'insert'

        self._determine_resource_id()
        self._determine_vendor_callNo()
        self._order_inhouse_meta()

    def _determine_resource_id(self):
        if self._meta_vendor.t001 is not None:
            self.vendor_id = self._meta_vendor.t001
        elif self._meta_vendor.t020 != []:
            self.vendor_id = self._meta_vendor.t020[0]
        elif self._meta_vendor.t024 != []:
            self.vendor_id = self._meta_vendor.t024[0]

    def _determine_vendor_callNo(self):
        if self._meta_vendor.dstLibrary == 'branches':
            self.vendor_callNo = self._meta_vendor.bCallNumber
        elif self._meta_vendor.dstLibrary == 'research':
            try:
                self.vendor_callNo = self._meta_vendor.rCallNumber[0]
            except IndexError:
                self.vendor_callNo = None

    def _order_inhouse_meta(self):
        # will remove any duplicates from the Sierra results
        # order from the newest bib to the oldest
        descending_order = []
        bib_order = dict()
        n = -1
        for meta in self._meta_inhouse:
            n += 1
            bib_order[meta.sierraId] = n

        for key, value in sorted(bib_order.iteritems()):
            descending_order.append(self._meta_inhouse[value])
        self._meta_inhouse = descending_order

    def _compare_update_timestamp(self, meta_inhouse):
        updated = False
        if self._meta_vendor.t005 is None:
            pass
        elif meta_inhouse.t005 is None:
            updated = True
        elif self._meta_vendor.t005 > meta_inhouse.t005:
            updated = True
        return updated

    def _determine_callNo_match(self, meta_inhouse):
        match = False
        if self._meta_vendor.dstLibrary == 'branches':
            if meta_inhouse.bCallNumber is None:
                match = True
            elif self._meta_vendor.bCallNumber == \
                    meta_inhouse.bCallNumber:
                match = True
        return match


class PVR_NYPLReport(PVRReport):
    """
    Creates a NYPL analysis report of a vendor record in relation
    to retrieved from the catalog existing matching bibs
    """
    def __init__(self, agent, meta_vendor, meta_inhouse):
        PVRReport.__init__(self, meta_vendor, meta_inhouse)
        self._matched = []
        self.mixed = []
        self.other = []

        self._group_by_library()

        if agent == 'cat':
            self._cataloging_workflow()
        elif agent == 'sel':
            self._selection_workflow()
        elif agent == 'acq':
            self._acquisition_workflow()

    def _group_by_library(self):

        for meta in self._meta_inhouse:
            # print self._meta_vendor.dstLibrary, print self.li
            if self._meta_vendor.dstLibrary == meta.ownLibrary:
                # correct library
                self._matched.append(meta)
            elif meta.ownLibrary == 'mixed':
                self.mixed.append(meta.sierraId)
            else:
                self.other.append(meta.sierraId)

    def _cataloging_workflow(self):
        # default action = 'insert'
        n = len(self._matched)
        if n == 0:
            # no matches found
            self.callNo_match = True
        elif n > 0:
            c = 0
            for meta in self._matched:
                c += 1
                if meta.bCallNumber is not None or \
                        len(meta.rCallNumber) > 0:
                    # full record
                    if self._meta_vendor.dstLibrary == 'branches':
                        # check if call number matches
                        call_match = self._determine_callNo_match(meta)
                        if call_match:
                            self.callNo_match = True
                            self.target_sierraId = meta.sierraId
                            self.target_callNo = meta.bCallNumber
                            if meta.catSource == 'inhouse':
                                self.action = 'attach'
                            else:
                                updated = self._compare_update_timestamp(meta)
                                if updated:
                                    self.updated_by_vendor = True
                                    self.action = 'overlay'
                                else:
                                    self.action = 'attach'
                            # do not check any further
                            break
                        else:
                            if c == n:
                                self.target_sierraId = meta.sierraId
                                self.target_callNo = meta.bCallNumber
                                if meta.catSource == 'inhouse':
                                    self.action = 'attach'
                                else:
                                    updated = self._compare_update_timestamp(
                                        meta)
                                    if updated:
                                        self.updated_by_vendor = True
                                        self.action = 'overlay'
                                    else:
                                        self.action = 'attach'
                    else:
                        # research path, no callNo match checking
                        self.callNo_match = True
                        self.target_sierraId = meta.sierraId
                        self.target_callNo = ','.join(meta.rCallNumber)
                        if meta.catSource == 'inhouse':
                            self.action = 'attach'
                        else:
                            updated = self._compare_update_timestamp(meta)
                            if updated:
                                self.updated_by_vendor = True
                                self.action = 'overlay'
                            else:
                                self.action = 'attach'
                        break
                else:
                    # brief record matching dstLibrary
                    # overlay the earliest record
                    if c == n:
                        # no other bibs to consider
                        self.callNo_match = True
                        self.target_sierraId = meta.sierraId
                        self.action = 'overlay'
        if n > 1:
            self.inhouse_dups = [meta.sierraId for meta in self._matched]

    def _selection_workflow(self):
        # default action = 'insert'
        self.callNo_match = True
        n = len(self._matched)
        if n > 0:
            c = 0
            for meta in self._matched:
                c += 1
                if meta.bCallNumber is not None or \
                        len(meta.rCallNumber) > 0:
                    # full bib situation
                    self.action = 'attach'
                    self.target_sierraId = meta.sierraId

                    # determine Sierra target call number
                    if self._meta_vendor.dstLibrary == 'branches':
                        self.target_callNo = meta.bCallNumber
                        break
                    elif self._meta_vendor.dstLibrary == 'research':
                        self.target_callNo = ','.join(meta.rCallNumber)
                        break
                else:
                    # brief record situation
                    if c == n:
                        # no other bibs to consider
                        self.action = 'attach'
                        self.target_sierraId = meta.sierraId
        if n > 1:
            self.inhouse_dups = [meta.sierraId for meta in self._matched]

    def _acquisition_workflow(self):
        pass

    def to_dict(self):
        return {
            'vendor_id': self.vendor_id,
            'vendor': self.vendor,
            'updated_by_vendor': self.updated_by_vendor,
            'callNo_match': self.callNo_match,
            'target_callNo': self.target_callNo,
            'vendor_callNo': self.vendor_callNo,
            'inhouse_dups': self.inhouse_dups,
            'target_sierraId': self.target_sierraId,
            'mixed': self.mixed,
            'other': self.other,
            'action': self.action}

    def __repr__(self):
        return "<PVF Report(vendor_id={}, vendor={}, " \
            "callNo_match={}, target_callNo={}, vendor_callNo={}, " \
            "updated_by_vendor={}, " \
            "inhouse_dups={}, target_sierraId={}, mixed={}, "\
            "other={}, action={})>".format(
                self.vendor_id,
                self.vendor,
                self.callNo_match,
                self.target_callNo,
                self.vendor_callNo,
                self.updated_by_vendor,
                ','.join(self.inhouse_dups),
                self.target_sierraId,
                ','.join(self.mixed),
                ','.join(self.other),
                self.action)
