# creates pvr statistical reports

from datetime import date
import logging
import os
import pandas as pd
import shelve
from sqlalchemy import func


from datastore import PVR_Batch, PVR_File, Vendor, session_scope
from logging_setup import LogglyAdapter


module_logger = LogglyAdapter(logging.getLogger('overload'), None)


def generate_processing_summary(batch_meta):
    """
    creates a summary for processed batch
    args:
        system (nypl or bpl)
        library (branches or research)
        agent (cat, sel, acq)
    return:
        list of summary lines
    """
    meta = shelve.open(batch_meta)
    summary = []
    system = meta['system'].upper()
    library = meta['library']
    agent = meta['agent']
    summary.append(
        'system: {}, library: {}, user: {}\n'.format(
            system,
            library,
            meta['agent'].upper()))
    summary.append(
        'total processed files: {}  '.format(
            meta['processed_files']))
    summary.append(
        'total process records: {}\n'.format(
            meta['processed_bibs']))
    summary.append(
        'file names: {}\n'.format(
            ','.join(
                os.path.basename(name) for name in meta['file_names'])))
    summary.append(
        'processing time: {}\n'.format(
            meta['processing_time']))
    if agent == 'cat':
        try:
            summary.append(
                'integrity of processed files: {}\n'.format(
                    meta['processed_integrity']))
            summary.append(
                'missing barcodes in processed files: {}\n'.format(
                    meta['missing_barcodes']))
        except KeyError:
            pass
        try:
            summary.append(
                'duplicates: {}\n'.format(meta['duplicate_bibs']))
        except KeyError:
            pass

    meta.close()
    module_logger.debug('Processing summary: {}'.format(
        summary))

    return system, library, agent, summary


def shelf2dataframe(batch_stats, system):
    stats = shelve.open(batch_stats)
    frames = []
    list2str = ['inhouse_dups', 'mixed', 'other']
    for key, value in stats.iteritems():
        if value['target_sierraId'] is not None:
            if len(value['target_sierraId']) == 8:
                value['target_sierraId'] = 'b{}a'.format(
                    value['target_sierraId'])
            elif len(value['target_sierraId']) == 7:
                value['target_sierraId'] = 'o{}a'.format(
                    value['target_sierraId'])
            else:
                value['target_sierraId'] = None
        for cat in list2str:
            if cat in value:
                if value[cat] == []:
                    value[cat] = None
                else:
                    value[cat] = ','.join(
                        ['b{}a'.format(bid) for bid in value[cat]])
        frames.append(pd.DataFrame(value, index=[int(key)]))
    df = pd.concat(frames)
    stats.close()
    return df


def create_stats(system, df):
    frames = []
    n = 0
    for vendor, data in df.groupby('vendor'):
        n += 1
        attach = data[
            data['action'] == 'attach']['action'].count()
        insert = data[
            data['action'] == 'insert']['action'].count()
        update = data[
            data['action'] == 'overlay']['action'].count()
        if system == 'nypl':
            mixed = data[
                data['mixed'].notnull()]['mixed'].count()
            other = data[
                data['other'].notnull()]['other'].count()
            frames.append(pd.DataFrame(
                data={
                    'vendor': vendor,
                    'attach': attach,
                    'insert': insert,
                    'update': update,
                    'total': attach + insert + update,
                    'mixed': mixed,
                    'other': other},
                columns=[
                    'vendor', 'attach', 'insert', 'update',
                    'total', 'mixed', 'other'],
                index=[n]))
        else:
            # bpl stats
            frames.append(pd.DataFrame(
                data={
                    'vendor': vendor,
                    'attach': attach,
                    'insert': insert,
                    'update': update,
                    'total': attach + insert + update},
                columns=['vendor', 'attach', 'insert', 'update', 'total'],
                index=[n]))
    df_rep = pd.concat(frames)
    return df_rep


def report_dups(system, library, df):
    if system == 'NYPL':
        if library == 'branches':
            other = 'research'
        else:
            other = 'branches'
        dups = '{} dups'.format(library)

        if library == 'research':
            # research reports are simpler since
            # PVR always inserts bibs
            df_rep = df[[
                'vendor', 'vendor_id', 'target_sierraId',
                'inhouse_dups', 'mixed', 'other']]
            df_rep = df_rep[
                df_rep['inhouse_dups'].notnull()|df_rep['mixed'].notnull()|df_rep['other'].notnull()].sort_index()
            df_rep.columns = [
                'vendor', 'vendor_id', 'target_id',
                dups, 'mixed', other]
        else:
            df_rep = df[[
                'vendor', 'vendor_id', 'target_sierraId',
                'inhouse_dups', 'mixed', 'other']]

            df_rep = df_rep[
                df_rep['inhouse_dups'].notnull()|df_rep['mixed'].notnull()|df_rep['other'].notnull()].sort_index()
            df_rep.columns = [
                'vendor', 'vendor_id', 'target_id',
                dups, 'mixed', other]
    else:
        # bpl stats
        df_rep = df[[
            'vendor', 'vendor_id', 'target_sierraId',
            'inhouse_dups']]

        df_rep = df_rep[
            df_rep['inhouse_dups'].notnull()].sort_index()
        df_rep.columns = ['vendor', 'vendor_id', 'target_id', 'duplicate bibs']
    return df_rep


def dups_report_for_sheet(system, library, agency, df):
    """
    generates list of rows with data that can be appended to
    a spreadesheet
    args:
        system: string, 'NYPL' or 'BPL'
        library: string, 'branches' or 'research'
        df: class, pandas.core.frame.DataFrame

    returns:
        data: list of lists (rows for spreadsheet)
    """
    if system == 'NYPL':
        if library == 'branches':
            dups = 'branches dups'
            other = 'research'
        elif library == 'research':
            dups = 'research dups'
            other = 'branches'
        columns = [
            'date', 'agency', 'vendor', 'vendor_id',
            'target_id', dups, 'mixed', other, 'corrected']
    else:
        # BPL
        columns = [
            'date', 'agency', 'vendor', 'vendor_id',
            'target_id', 'duplicate bibs', 'corrected']

    # append date to data
    gdf = df.copy()
    date_today = date.today().strftime('%y-%m-%d')
    gdf = gdf.assign(date=date_today, corrected='no', agency=agency)

    # rearrange columns and their values
    gdf = gdf[columns]

    if system == 'NYPL':
        mask = ((gdf.iloc[:, 5].isnull()&gdf.iloc[:, 6].isnull())&~(gdf.iloc[:, 7].notnull()&gdf.iloc[:, 7].str.contains(',')))
        gdf.loc[mask, 'corrected'] = 'no action'
    elif system == 'BPL':
        mask = gdf.iloc[:, 5].isnull()
        gdf.loc[mask, 'corrected'] = 'no action'

    return gdf.values.tolist()


def report_callNo_issues(df, agent):
    df_call = df[~df['callNo_match']].sort_index()
    if agent == 'cat':
        df_supp = df[
            df['vendor_callNo'].isnull() & df['target_callNo'].isnull()]
        df_call = pd.concat([df_call, df_supp])
    df_call = df_call[
        ['vendor', 'vendor_id', 'target_sierraId',
         'vendor_callNo', 'target_callNo', 'inhouse_dups']]
    df_call.columns = [
        'vendor', 'vendor_id', 'target_id', 'vendor_callNo',
        'target_callNo', 'duplicate bibs']
    return df_call


def callNos_report_for_sheet(df):
    """
    generates list of rows from erorrs dataframe that can
    be appended to Google Sheet
    args:
        system: string, 'NYPL' or 'BPL'
        df: class, pandas.core.frame.DataFrame
    returns:
        data: list of row values (list of lists)
    """

    cdf = df.copy()
    date_today = date.today().strftime('%y-%m-%d')
    cdf = cdf.assign(date=date_today, corrected='no')
    columns = [
        'date', 'vendor', 'vendor_id', 'target_id',
        'vendor_callNo', 'target_callNo',
        'duplicate bibs', 'corrected']
    cdf = cdf[columns]

    return cdf.values.tolist()


def report_details(system, library, df):
    df = df.sort_index()
    if system == 'NYPL':
        dups = '{} dups'.format(library)
        if library == 'branches':
            other = 'research bibs'
            df = df[[
                'vendor', 'vendor_id', 'action', 'target_sierraId',
                'updated_by_vendor',
                'callNo_match', 'vendor_callNo', 'target_callNo',
                'inhouse_dups', 'mixed', 'other']]
            df.columns = [
                'vendor', 'vendor_id', 'action', 'target_id',
                'updated',
                'callNo_match', 'vendor_callNo', 'target_callNo',
                dups, 'mixed bibs', other]
        else:
            other = 'branches bibs'
            df = df[[
                'vendor', 'vendor_id', 'action', 'target_sierraId',
                'updated_by_vendor', 'callNo_match', 'vendor_callNo',
                'target_callNo', 'inhouse_dups', 'mixed', 'other']]
            df.columns = [
                'vendor', 'vendor_id', 'action', 'target_sierraId',
                'updated', 'callNo_match', 'vendor_callNo',
                'target_callNo', dups, 'mixed bibs', other]
    else:
        # bpl stats
        df = df[[
            'vendor', 'vendor_id', 'action', 'target_sierraId',
            'updated_by_vendor',
            'callNo_match', 'vendor_callNo', 'target_callNo',
            'inhouse_dups']]
        df.columns = [
            'vendor', 'vendor_id', 'action', 'target_id',
            'updated',
            'callNo_match', 'vendor_callNo', 'target_callNo',
            'duplicate bibs']
    return df


def cumulative_nypl_stats(start_date, end_date):
    with session_scope() as session:
        query = session.query(
            PVR_Batch.system,
            PVR_Batch.library,
            func.sum(PVR_File.new),
            func.sum(PVR_File.dups),
            func.sum(PVR_File.updated),
            func.sum(PVR_File.mixed),
            func.sum(PVR_File.other),
            Vendor.name)
        query = query.join(PVR_File).join(Vendor)
        nypl_results = query.filter(
            PVR_Batch.timestamp >= start_date,
            PVR_Batch.timestamp < end_date,
            PVR_Batch.system == 'nypl').group_by(Vendor.name).all()

    nypl_labels = [
        'system', 'library', 'insert',
        'attach', 'overlay', 'mixed',
        'other', 'vendor']
    df = pd.DataFrame.from_records(nypl_results, columns=nypl_labels)
    bdf = df[df['library'] == 'branches']
    bdf = bdf[['vendor', 'insert', 'attach', 'overlay', 'mixed', 'other']]
    bdf['total loaded'] = bdf['insert'] + bdf['attach'] + bdf['overlay']
    bdf.columns = [
        'vendor', 'insert', 'attach',
        'overlay', 'mixed dups', 'research dups', 'total loaded']
    rdf = df[df['library'] == 'research']
    rdf = rdf[['vendor', 'insert', 'attach', 'overlay', 'mixed', 'other']]
    rdf['total loaded'] = rdf['insert'] + rdf['attach'] + rdf['overlay']
    rdf.columns = [
        'vendor', 'insert', 'attach',
        'overlay', 'mixed dups', 'branches dups', 'total loaded']
    return (bdf, rdf)


def cumulative_bpl_stats(start_date, end_date):
    """
    Produces dataframe with cumulative statistics of
    processed BPL records
    """

    with session_scope() as session:
        query = session.query(
            PVR_Batch.system,
            func.sum(PVR_File.new),
            func.sum(PVR_File.dups),
            func.sum(PVR_File.updated),
            Vendor.name)
        query = query.join(PVR_File).join(Vendor)
        results = query.filter(
            PVR_Batch.timestamp >= start_date,
            PVR_Batch.timestamp < end_date,
            PVR_Batch.system == 'bpl').group_by(Vendor.name).all()
    labels = [
        'system', 'insert', 'attach', 'overlay', 'vendor']
    df = pd.DataFrame.from_records(results, columns=labels)
    df['total loaded'] = df['insert'] + df['attach'] + df['overlay']
    df = df[['vendor', 'insert', 'attach', 'overlay', 'total loaded']]
    return df


def cumulative_vendor_stats(start_date, end_date):
    """
    Produces dataframe of vendor statistics during span of time
    """

    with session_scope() as session:
        query = session.query(
            PVR_Batch.system,
            PVR_Batch.library,
            func.sum(PVR_File.new),
            func.sum(PVR_File.dups),
            func.sum(PVR_File.updated),
            func.sum(PVR_File.mixed),
            func.sum(PVR_File.other),
            Vendor.name)
        query = query.join(PVR_File).join(Vendor)

        nypl_br_results = query.filter(
            PVR_Batch.timestamp >= start_date,
            PVR_Batch.timestamp < end_date,
            PVR_Batch.system == 'nypl',
            PVR_Batch.library == 'branches').group_by(Vendor.name).all()
        nypl_rl_results = query.filter(
            PVR_Batch.timestamp >= start_date,
            PVR_Batch.timestamp < end_date,
            PVR_Batch.system == 'nypl',
            PVR_Batch.library == 'research').group_by(Vendor.name).all()
        bpl_results = query.filter(
            PVR_Batch.timestamp >= start_date,
            PVR_Batch.timestamp < end_date,
            PVR_Batch.system == 'bpl').group_by(Vendor.name).all()
    labels = [
        'system', 'library', 'insert',
        'attach', 'overlay', 'mixed',
        'other', 'vendor']
    nbdf = pd.DataFrame.from_records(nypl_br_results, columns=labels)
    nrdf = pd.DataFrame.from_records(nypl_rl_results, columns=labels)
    bdf = pd.DataFrame.from_records(bpl_results, columns=labels)
    nbdf['total loaded'] = nbdf['insert'] + nbdf['attach'] + nbdf['overlay']
    nbdf = nbdf[[
        'vendor', 'insert', 'attach', 'overlay',
        'total loaded', 'mixed', 'other']]
    nrdf['total loaded'] = nrdf['insert'] + nrdf['attach'] + nrdf['overlay']
    nrdf = nrdf[[
        'vendor', 'insert', 'attach', 'overlay',
        'total loaded', 'mixed', 'other']]
    bdf['total loaded'] = bdf['insert'] + bdf['attach'] + bdf['overlay']
    bdf = bdf[['vendor', 'insert', 'attach', 'overlay', 'total loaded']]

    return nbdf, nrdf, bdf
