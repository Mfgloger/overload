import shelve

import pandas as pd


from setup_dirs import USER_DATA, GETBIB_REP
from utils import csv2df


def compile_batch_info():
    """
    Compiles for display to user data on the last batch processed
    by GetBib
    """

    try:
        user_data = shelve.open(USER_DATA)
        data = user_data['getbib_batch']
        disp_info = 'Summary:\ntimestamp: {}\t|\tprocessing time: {}\n' \
            'target: {}\ntotal queries: {}\nhits: {}\tmisses: {}\t' \
            'dups: {}\nduplicate IDs:\n\t{}'.format(
                data['timestamp'],
                data['time_elapsed'],
                '-'.join(data['target'].values()),
                data['total_queries'],
                data['hits'],
                data['misses'],
                data['dup_count'],
                ','.join(list(data['dups'])))
    except KeyError:
        disp_info = 'Summary:\nNo data.'
    finally:
        user_data.close()

    return disp_info


def prep_results_data():
    """
    Compiles three dataframes for
    """

    df = csv2df(GETBIB_REP)
    df = df[[
        'pos', 'vendor_id', 'target_sierraId',
        'target_title', 'target_callNo',
        'inhouse_dups', 'mixed', 'other'
    ]]
    fdf = df[df['target_callNo'].notnull()]
    mdf = df[df['mixed'].notnull()]
    ddf = df[df['inhouse_dups'].notnull()]
    ndf = df[df['target_sierraId'].isnull()]
    cdf = df[
        (df['target_callNo'].isnull()) & (
            df['mixed'].isnull()) & (
            df['inhouse_dups'].isnull()) & (
            df['target_sierraId'].notnull())]

    return (cdf, fdf, mdf, ddf, ndf)
