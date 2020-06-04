from cs_context import (
    ONS,
    session_scope,
    WCHit,
    retrieve_record,
    xml2string,
    string2xml,
    results2record_list,
    meets_upgrade_criteria,
    meets_catalog_criteria,
    meets_user_criteria,
    has_records,
    create_rec_lvl_range,
    meets_rec_lvl,
    is_english_cataloging,
    get_cat_lang,
    get_datafield_040,
    meets_mat_type,
    get_record_leader,
    get_cuttering_fields,
    get_subject_fields,
)


def check_criteria_output(ids, lvl):
    with session_scope() as session:
        lvl_range = create_rec_lvl_range(lvl)

        for n in ids:
            rec = retrieve_record(session, WCHit, wchid=n)
            res = results2record_list(rec.query_results)
            # print(xml2string(res))
            c = 0
            for r in res:
                print("wchid: {}, rec: {}".format(n, c))
                print("\tis_english_cataloging: {}".format(is_english_cataloging(r)))
                print(
                    "\tmeets_rec_lvl: {}, \t\tlvl range: {}".format(
                        meets_rec_lvl(r, lvl_range), lvl_range
                    )
                )
                print("\tmeets_mat_type: {}".format(meets_mat_type(r)))
                print("\tmeets_user_criteria: {}".format(meets_user_criteria(r, lvl)))
                print(
                    "\tmeets_catalog_criteria: {}".format(
                        meets_catalog_criteria(r, "branches")
                    )
                )
                c += 1


def check_cutter_subject_options(ids):
    with session_scope() as session:
        for n in ids:
            rec = retrieve_record(session, WCHit, wchid=n)
            res = results2record_list(rec.query_results)
            # print(xml2string(res))
            c = 0
            for r in res:
                print("wchid: {}, rec: {}".format(n, c))
                print("cuttering opts: {}".format(get_cuttering_fields(r)))
                print("subject opts: {}".format(get_subject_fields(r)))
                c += 1


if __name__ == "__main__":

    # check_criteria_output([1, 5, 7, 11, 12], "level 3")
    check_cutter_subject_options([2])
