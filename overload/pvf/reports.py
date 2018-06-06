# creates pvr statistical reports

import pandas as pd
import shelve
from sqlalchemy import func


from datastore import PVR_Batch, PVR_File, Vendor, session_scope


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
    summary.append(
        'system: {}, library: {}, user: {}\n'.format(
            meta['system'].upper(),
            meta['library'],
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
                name.split('/')[-1] for name in meta['file_names'])))
    summary.append(
        'processing time: {}\n'.format(
            meta['processing_time']))
    meta.close()
    return summary


def shelf2dataframe(batch_stats):
    stats = shelve.open(batch_stats)
    frames = []
    list2str = ['inhouse_dups', 'mixed', 'other']
    for key, value in stats.iteritems():
        if value['target_sierraId'] is not None:
            value['target_sierraId'] = 'b{}a'.format(
                value['target_sierraId'])

        for cat in list2str:
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
                'vendor', 'vendor_id',
                'inhouse_dups', 'mixed', 'other']]
            df_rep = df_rep[
                df_rep['inhouse_dups'].notnull()|df_rep['mixed'].notnull()|df_rep['other'].notnull()].sort_index()
            df_rep.columns = [
                'vendor', 'vendor_id',
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


def report_callNo_issues(df):
    df_call = df[~df['callNo_match']].sort_index()
    df_call = df_call[
        ['vendor', 'vendor_id', 'target_sierraId',
         'vendor_callNo', 'target_callNo', 'inhouse_dups']]
    df_call.columns = [
        'vendor', 'vendor_id', 'target_id', 'vendor_callNo',
        'target_callNo', 'duplicate bibs']
    return df_call


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
                'vendor', 'vendor_id', 'action',
                'vendor_callNo', 'inhouse_dups', 'mixed', 'other']]
            df.columns = [
                'vendor', 'vendor_id', 'action',
                'vendor_callNo', dups, 'mixed bibs', other]
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
