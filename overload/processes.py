import os
import shelve
import datetime
import logging
from pymarc import Record

from connectors.sierra_z3950 import Z3950_QUALIFIERS, z3950_query
import bibs
from setup_dirs import BATCH_STATS


class VendorBibAnalysis:

    """
    compares vendor data to retrieved from Sierra info and
    returns a metadata dictionary of the analysis
    """

    def __init__(self, vfile, library, query_data, retrieved_data):

        self.module_logger = logging.getLogger('main.analysis')

        self.module_logger.debug('Begin bib analysis')
        self.module_logger.debug(
            'analized data: query data={}; retrieved data={}'.format(
                query_data, retrieved_data))
        self.vfile = vfile
        self.library = library
        self.query_data = query_data
        self.retrieved_data = retrieved_data

        self.analysis = {
            'vendor': None,
            'library': self.library,
            'exists': False,
            'fullBib': False,
            'format': 'a',
            'dups': False,
            'dups_id': [],
            'overlay': False,
            'target_id': None,
            'vCallNumber': self.query_data['bCallNumber'],
            'bCallNumber': None,
            'rCallNumber': False,
            'callNumber_match': False,
            'vTitle': self.query_data['title'],
            'vISBN': self.query_data['isbns'],
        }

        if self.library == 'BPL':
            self.apply_bpl_rules()
        elif self.library == 'NYPL':
            self.apply_nyp_rules()

        self.module_logger.debug('Record: {}'.format(
            self.analysis))

    def apply_bpl_rules(self):

        """
        applies BPL rules to retrieved results
        """

        self.module_logger.debug('applying  BPL rules')
        # use print ('a') as a default format
        if self.query_data['itemForm'] == 'd':
            self.analysis['format'] = 'l'
        else:
            self.analysis['format'] = 'a'

        # determine vendor
        self.analysis['format'] = 'a'
        for value in self.query_data['acqSource']:
            if 'URBAN' in value.upper():
                self.analysis['vendor'] = 'URBAN'
            elif 'SERIES' in value.upper():
                self.analysis['vendor'] = 'SERIES'
            elif 'ROMANCE' in value.upper():
                self.analysis['vendor'] = 'ROMANCE'
            elif 'PBP' in value.upper():
                self.analysis['vendor'] = 'PBP'
            elif 'LEASE' in value.upper():
                if self.query_data['litForm'] in '1,f,j':
                    self.analysis['vendor'] = 'LEASE FIC'
                else:
                    self.analysis['vendor'] = 'LEASE NON-FIC'

        if self.analysis['vendor'] is None:
            if self.query_data['bibType'] == 'a':
                self.analysis['vendor'] = 'CLS'
            elif self.query_data['bibType'] == 'g':
                self.analysis['vendor'] = 'MIDWEST DVD'
                # change Sierra format from default 'a'
                self.analysis['format'] = 'h'
            elif self.query_data['bibType'] == 'i':
                self.analysis['vendor'] = 'MIDWEST AUDIO'
                self.analysis['format'] = 'i'
            elif self.query_data['bibType'] == 'j':
                self.analysis['vendor'] = 'MIDWEST CD'
                self.analysis['format'] = 'j'
            else:
                self.analysis['vendor'] = 'UNKNOWN'

        if self.query_data['bNumber'] is not None and \
                len(self.query_data['bNumber']) == 7:
            # vendor provided oNumber as target for overlaying (MidWest);
            # treat as duplicate; not possible to search with Z3950;
            # will come as empty results
            # fix if searched via Sierra API
            self.analysis['callNumber_match'] = True  # unknown really
        elif len(self.retrieved_data) == 0:
            # no matching bibs retrieved from catalog
            self.analysis['overlay'] = True
            self.analysis['callNumber_match'] = True
        else:
            self.analysis['exists'] = True

            # consider only unique hits
            unique = set()
            hits = []
            for hit in self.retrieved_data:
                if hit['bNumber'] not in unique:
                    unique.add(hit['bNumber'])
                    hits.append(hit)

            # multiple hits, match to the best one        
            if len(hits) > 1:
                # multiple hits mean duplicates in the catalog
                # find the best one to
                # overlay or attach items, record bNumbers of duplicates
                self.analysis['dups'] = True
                dups = {}
                dups_id = []
                matched = False
                for hit in hits:
                    dups[hit['bNumber']] = hit
                    dups_id.append(hit['bNumber'])
                self.analysis['dups_id'] = dups_id

                for id, hit in sorted(dups.iteritems()):  # sort from oldest to the newest bib
                    if hit['fullBib'] and \
                            hit[
                            'bCallNumber'] == self.query_data['bCallNumber']:
                        hits = [hit, ]
                        matched = True
                        break
                if not matched:
                    for id, hit in sorted(dups.iteritems()):
                        if hit['bCallNumber'] == self.query_data['bCallNumber'] \
                                and hit['bCallNumber'] is not None:
                            hits = [hit, ]
                            break

                if not matched:
                    for id, hit in sorted(dups.iteritems()):
                        hits = [hit, ]
                        break

            hit = hits[0]

            # indicate Sierra bNumber to overlay or attach items
            self.analysis['target_id'] = hit['bNumber']
            self.analysis['bCallNumber'] = hit['bCallNumber']

            if hit['bCallNumber'] is None:
                # brief order record scenario
                self.analysis['overlay'] = True
                if self.query_data['bCallNumber'] is None:
                    if self.analysis['vendor'] == 'LEASE NON-FIC':
                        # to allow non-fic call number override situation
                        self.analysis['callNumber_match'] = True

            else:
                # full bib found in catalog
                # determine if call numbers on vendor bib and
                # retrieved bib match
                if hit['bCallNumber'] == self.query_data['bCallNumber']:
                    self.analysis['callNumber_match'] = True
                if not hit['fullBib']:
                    if hit['lastUpdate'] is None:
                        self.analysis['overlay'] = True
                    elif self.query_data['lastUpdate'] is not None and (
                        self.query_data[
                            'lastUpdate'] > hit['lastUpdate']):
                        self.analysis['overlay'] = True
                else:
                    self.analysis['fullBib'] = True

    def apply_nyp_rules(self):

        """
        applies NYP rules to retrieved results
        """
        self.module_logger.debug('applying NYPL rules')
        # determine incoming vendor record characteristics
        if self.query_data['itemForm'] == 'd':
            self.analysis['format'] = 'l'
        else:
            self.analysis['format'] = 'a'

        # print material
        if self.query_data['bibType'] == 'a':
            for value in self.query_data['catSource']:
                if 'BTURBN' in value.upper():
                    self.analysis['vendor'] = 'URBAN'
                elif 'SERIES' in value.upper():
                    self.analysis['vendor'] = 'SERIES'
                elif 'BTROMAN' in value.upper():
                    self.analysis['vendor'] = 'ROMANCE'
                elif 'PARADE' in value.upper():
                    self.analysis['vendor'] = 'PARADE'
                elif 'LEASE' in value.upper():
                    if self.query_data['litForm'] in '1,f,j':
                        self.analysis['vendor'] = 'LEASE FIC'
                    else:
                        self.analysis['vendor'] = 'LEASE NON-FIC'
                elif 'BTODC' in value.upper():
                    self.analysis['vendor'] = 'BTODC'
                else:
                    self.analysis['vendor'] = 'UNKOWN'

        elif self.query_data['bibType'] == 'g':
            self.analysis['vendor'] = 'MIDWEST DVD'
            # does not distiguish between DVD & Blue-ray
            # but in most cases (vendor provides 949 with format)
            # this will not be an issue
            self.analysis['format'] = 'v'
        elif self.query_data['bibType'] == 'i':
            self.analysis['vendor'] = 'MIDWEST AUDIO'
            self.analysis['format'] = 'u'
        elif self.query_data['bibType'] == 'j':
            self.analysis['vendor'] = 'MIDWEST CD'
            self.analysis['format'] = 'y'
        else:
            self.analysis['vendor'] = 'UNKOWN'

        # consider only unique hits
        unique = set()
        hits = []
        for hit in self.retrieved_data:
            if hit['bNumber'] not in unique:
                unique.add(hit['bNumber'])
                hits.append(hit)

        # determine if any query results have been returned
        if len(hits) == 0:
            # no matching bibs retrieved from catalog
            self.analysis['overlay'] = True
            self.analysis['callNumber_match'] = True

        else:
            # query returned hits
            self.analysis['exists'] = True

            if len(hits) > 1:
                # multiple hits mean duplicates in the catalog
                # find the best one to
                # overlay or attach items, record bNumbers of duplicates
                self.analysis['dups'] = True
                dups = {}
                dups_id = []
                matched = False
                for hit in hits:
                    dups[hit['bNumber']] = hit
                    dups_id.append(hit['bNumber'])
                self.analysis['dups_id'] = dups_id

                # sort from oldest to the newest bib
                for id, hit in sorted(dups.iteritems()):
                    if hit['fullBib'] and \
                            hit[
                            'bCallNumber'] == self.query_data['bCallNumber']:
                        hits = [hit, ]
                        matched = True
                        break
                if not matched:
                    for id, hit in sorted(dups.iteritems()):
                        if hit['bCallNumber'] == self.query_data[
                                'bCallNumber'] \
                                and hit['bCallNumber'] is not None:
                            hits = [hit, ]
                            break

                if not matched:
                    for id, hit in sorted(dups.iteritems()):
                        hits = [hit, ]
                        break

            # compare to single hit
            hit = hits[0]

            # indicate Sierra bNumber to overlay or attach items
            self.analysis['target_id'] = hit['bNumber']
            self.analysis['bCallNumber'] = hit['bCallNumber']
            self.analysis['rCallNumber'] = hit['rCallNumber']

            # determine if call number match
            if self.analysis['bCallNumber'] == self.analysis[
                    'vCallNumber']:
                self.analysis['callNumber_match'] = True

            # determine if overlay needed
            if hit['bCallNumber'] is None and not \
                    hit['rCallNumber']:
                # brief order record scenario
                self.analysis['overlay'] = True

            elif hit['rCallNumber']:
                # research bib present
                if self.query_data['bCallNumber'] is not None:
                    if hit['bCallNumber'] is None:
                        # need to add branch call number to record
                        # in catalog
                        # mark for re-query:
                        # rCallNumber and overlay are True
                        self.analysis['overlay'] = True

            elif not hit['rCallNumber']:
                # circ library record only
                if hit['fullBib']:
                    self.analysis['fullBib'] = True
                    # allow updating Midwest records since they
                    # are condidered fullBib
                    if 'MIDWEST' in self.analysis['vendor']:
                        if hit['lastUpdate'] is None:
                            self.analysis['overlay'] = True
                        elif self.query_data[
                                'lastUpdate'] is not None and (
                                self.query_data[
                                'lastUpdate'] > hit['lastUpdate']):
                            self.analysis['overlay'] = True
                else:
                    # only a vendor record in catalog
                    if hit['lastUpdate'] is None:
                        self.analysis['overlay'] = True
                    elif self.query_data[
                            'lastUpdate'] is not None and (
                            self.query_data[
                            'lastUpdate'] > hit['lastUpdate']):
                        self.analysis['overlay'] = True

    def data(self):
        return self.analysis

    def save(self, new_report):

        """
        stores analysis for report in a temp file
        """
        self.module_logger.debug('Save: initiate saving')
        session_report = BATCH_STATS

        if new_report:
            self.module_logger.debug('Save: as new report')
            # delete session temp file
            try:
                os.remove(session_report)
                self.module_logger.debug(
                    'Save: old report deleted successfuly')
            except WindowsError:
                self.module_logger.error(
                    'Save: NOT ABLE to delete old report ({})'.format(
                        session_report))

        # save analysis
        report = shelve.open(session_report, writeback=True)
        self.module_logger.debug('Save: report shelve opended...')

        if 'files' not in report:
            report['files'] = dict()

        if str(self.vfile) in report['files']:
            self.module_logger.debug(
                'Save: adding bib analysis to existing meta'
                'for file: {}'.format(str(self.vfile)))
            bibs = report['files'][str(self.vfile)]
            bibs.append(self.analysis)
            report['files'][str(self.vfile)] = bibs
        else:
            self.module_logger.debug(
                'Save: new file ({}) bib analysis'.format(
                    str(self.vfile)))
            bibs = []
            bibs.append(self.analysis)
            report['files'][str(self.vfile)] = bibs

        report.close()
        self.module_logger.debug('Save: report shelve closed.')

    def __repr__(self):
        return "file='%s'; library='%s'; vendor='%s'; exists='%s';" \
               "fullBib='%s'" \
               "format='%s'; dups='%s';dups_id='%s'; overlay='%s';" \
               "target_id='%s'; vCallNumber='%s';" \
               "bCallNumber='%s'; rCallNumber='%s'; callNum_match='%s';" \
               "vTitle='%s'; vISBN='%s'" % (
                   self.vfile,
                   self.library,
                   self.analysis['vendor'],
                   self.analysis['exists'],
                   self.analysis['fullBib'],
                   self.analysis['format'],
                   self.analysis['dups'],
                   ','.join(self.analysis['dups_id']),
                   self.analysis['overlay'],
                   self.analysis['target_id'],
                   self.analysis['vCallNumber'],
                   self.analysis['bCallNumber'],
                   self.analysis['rCallNumber'],
                   self.analysis['callNumber_match'],
                   self.analysis['vTitle'],
                   ','.join(self.analysis['vISBN']))


def pvf_api_flow(conn, new_report, fh, bib, library, save_directory):

    module_logger = logging.getLogger('main.processing_api_flow')

    # parse significant data from bibs including elements
    # that can be used for Sierra API queries 
    query_data = bibs.meta_from_marc(bib)

    # query order id
    if query_data['bNumber'] is not None and \
            len(query_data['bNumber']) == 7:
        # seems only using bib JSON query will get bib number
        # based on order nubmer; very slow process 12 sec per bib:()
        results = conn.get_bib_by_order_id(query_data['bNumber'])
        retrieved_data = bibs.api_results_parser(results)
    # query bib id
    elif query_data['bNumber'] is not None and \
            len(query_data['bNumber']) == 8:
        results = conn.get_bib_by_id(query_data['bNumber'])
        retrieved_data = bibs.api_results_parser(results)
    elif len(query_data['isbns']) > 0:
        results = conn.get_bib_by_isbn(query_data['isbns'][0])
        retrieved_data = bibs.api_results_parser(results)
    else:
        # alternative query method needed
        retrieved_data = []
        module_logger.warning('%s', {
            'msg': 'missing good data for query',
            'library': library,
            'query_meta': query_data})

    pvf_analysis(
        conn, new_report, fh, library,
        bib, query_data, retrieved_data, save_directory)


def pvf_z3950_flow(new_report, fh, bib, target, save_directory):

    module_logger = logging.getLogger('main.processing_z3950_flow')

    query_data = bibs.meta_from_marc(bib)

    if query_data['bNumber'] is not None and \
            len(query_data['bNumber']) == 7 and \
            target['library'] == 'BPL':
        # BPL MidWest scenario (overlay on oNumber) - not possible
        # to query via Z3950
        # treat as duplicates that will only attach itmes
        module_logger.debug(
            'skipping query - no vialable endpoints to query .o number'.format(
                query_data))
        retrieved_data = []

    elif query_data['bNumber'] is not None and \
            len(query_data['bNumber']) == 8:
        # CLS scenario
        # result should be always one bib
        if target['method'] == 'Z3950':

            qualifier = Z3950_QUALIFIERS['bib number']
            results = z3950_query(
                target, query_data['bNumber'], qualifier)

            if results[0]:
                # query succesfull
                retrieved_data = []
                for item in results[1]:
                    record = Record(data=item.data)
                    retrieved_data.append(bibs.meta_from_marc(record))
            else:
                # query failed
                retrieved_data = []

    elif len(query_data['isbns']) > 0:
        # result can have more than one bib
        qualifier = Z3950_QUALIFIERS['isbn']
        for isbn in query_data['isbns']:
            results = z3950_query(target, isbn, qualifier)
            if results[0]:
                # query successful
                retrieved_data = []
                for item in results[1]:
                    record = Record(data=item.data)
                    retrieved_data.append(bibs.meta_from_marc(record))
            else:
                # query failed
                retrieved_data = []
    else:
        # code here alternative query methods
        module_logger.warning(
            'not able to find best query method for: {}'.format(
                query_data))
        retrieved_data = []
    pvf_analysis(
        None,
        new_report, fh, target['library'],
        bib, query_data, retrieved_data, save_directory)


def pvf_analysis(
        conn,
        new_report, fh, library, bib, query_data,
        retrieved_data, save_directory):

    module_logger = logging.getLogger('main.processing_analysis')

    # analize and save report
    analysis = VendorBibAnalysis(
        fh, library, query_data, retrieved_data)
    # print analysis
    analysis.save(new_report)
    new_report = False

    # interpret analysis and save bibs to files
    if library == 'BPL':
        date_today = datetime.date.today().strftime('%m%d%y')
    else:
        date_today = datetime.date.today().strftime('%y%m%d')
    fh_dup = save_directory + '/{}_DUP-{}.mrc'.format(
        date_today, 0)
    fh_new = save_directory + '/{}_NEW-{}.mrc'.format(
        date_today, 0)
    a = analysis.data()

    # re-query if NYPL research bib needs branch call number
    if library == 'NYPL' and a['rCallNumber'] is True and \
            a['bCallNumber'] is None and a['overlay'] is True:
        module_logger.info(
            'protecting NYPL RL bib: %s', a['target_id'])
        response = conn.get_marc(a['target_id'])
        if response is not None:
            reader = bibs.read_from_json(response)
            # there should be only one hit, maybe replace looping with
            # first element or something else
            # to be able to recreate order of MARC tags a new
            # record must be created and populated with tags in the
            # correct order ; results from API do not have particular order
            for res_bib in reader:
                res_bib.add_ordered_field(query_data['marc_bCallNumber'])
                res_bib.remove_fields('901', '908', '946', '981')
                for item in query_data['item_data']:
                    res_bib.add_field(item)
                bib = res_bib
                module_logger.debug('Special case: new bib: {}'.format(
                    bibs.meta_from_marc(bib)))

    bib.leader = bib.leader[0:9] + 'a' + bib.leader[10:]
    if a['overlay']:
        if a['exists']:
            # matching record found in the catalog;
            # add target id to incoming bib and treat as new
            # (only order record preset or bib updated by vendor)

            if library == 'BPL' and '907' not in bib:
                bib.add_field(
                    bibs.create_target_id_field(
                        library,
                        a['target_id']))
            if library == 'NYPL' and '945' not in bib:
                bib.add_field(
                    bibs.create_target_id_field(
                        library,
                        a['target_id']))

        # add Sierra format code if not present
        needed = True
        if '949' in bib:
            for field in bib.get_fields('949'):
                if field.indicators == [' ', ' ']:
                    needed = False
        if needed:
            bib.add_field(
                bibs.create_sierra_format_field(a['format']))
  
        # write record in the new bibs file
        module_logger.debug('Writing bib to NEW file')
        bibs.write_bib(fh_new, bib)
    else:
        # only protected records found in catalog
        # add bib target id to attach items
        # save in dups file
        if (library == 'BPL' and '907' not in bib) or \
                (library == 'NYPL' and '945' not in bib):
            bib.add_field(
                bibs.create_target_id_field(
                    library,
                    a['target_id']))
        module_logger.debug('Writing bib to DUP file')
        bibs.write_bib(fh_dup, bib)
