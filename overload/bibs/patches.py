# custom bib behavior

from pymarc import Field


def remove_oclc_prefix(controlNo):
    changed = False
    try:
        if controlNo[:3] == "ocm" or controlNo[:3] == "ocn":
            changed = True
            controlNo = controlNo[3:]
        elif controlNo[:2] == "on":
            changed = True
            controlNo = controlNo[2:]
    except TypeError:
        pass
    finally:
        return changed, controlNo


def bib_patches(system, library, agent, vendor, bib):
    """
    Treatment of specific records; special cases
    """

    # nypl remove OCLC prefix
    if system == "nypl":
        if "001" in bib:
            controlNo = bib.get_fields("001")[0].data
            changed, controlNo = remove_oclc_prefix(controlNo)
            if changed:
                bib.remove_fields("001")
                field = Field(tag="001", data=controlNo)
                bib.add_ordered_field(field)

    # nypl branches cat patch for BT Series
    if (
        system == "nypl"
        and library == "branches"
        and agent == "cat"
        and vendor == "BT SERIES"
    ):
        # parse the call number
        new_callno = []
        pos = 0
        if "091" in bib:
            callno = bib.get_fields("091")[0].value()

            # langugage and audience prefix
            if callno[:6] == "J SPA ":
                new_callno.extend(["p", "J SPA"])
            elif callno[:2] == "J ":
                new_callno.extend(["p", "J"])

            # format prefix
            if "GRAPHIC " in callno:
                new_callno.extend(["f", "GRAPHIC"])
            elif "HOLIDAY " in callno:
                new_callno.extend(["f", "HOLIDAY"])
            elif "YR " in callno:
                new_callno.extend(["f", "YR"])

            # main subfield
            if "GN FIC " in callno:
                pos = callno.index("GN FIC ") + 7
                new_callno.extend(["a", "GN FIC"])
            elif "FIC " in callno:
                pos = callno.index("FIC ") + 4
                new_callno.extend(["a", "FIC"])
            elif "PIC " in callno:
                pos = callno.index("PIC ") + 4
                new_callno.extend(["a", "PIC"])
            elif callno[:4] == "J E ":
                pos = callno.index("J E ") + 4
                new_callno.extend(["a", "E"])
            elif callno[:8] == "J SPA E ":
                pos = callno.index("J SPA E ") + 8
                new_callno.extend(["a", "E"])

            # cutter subfield
            new_callno.extend(["c", callno[pos:]])
            field = Field(tag="091", indicators=[" ", " "], subfields=new_callno)

            # verify nothing has been lost
            if callno != field.value():
                raise AssertionError(
                    "Constructed call # does not match original."
                    "New={}, original={}".format(callno, field.value())
                )
            else:
                # if correct remove the original and replace with new
                bib.remove_fields("091")
                bib.add_ordered_field(field)

    return bib


def remove_unsupported_subject_headings(system, marc):
    if marc is not None:
        # remove local marc tags
        marc.remove_fields("653", "654", "690", "691", "696", "697", "698", "699")

        # fine comb remaining subject tags
        subjects = marc.subjects()
        for field in subjects:
            if field.indicators[1] == "0":
                continue
            elif field.indicators[1] == "1":
                # LC subject headings for children's literature
                if system == "NYPL":
                    continue
                elif system == "BPL":
                    marc.remove_field(field)
            elif field.indicators[1] == "7":
                try:
                    if field["2"] in ("fast", "gsafd", "lcgft", "gmgpc"):
                        continue
                    else:
                        marc.remove_field(field)
                except IndexError:
                    marc.remove_field(field)
            else:
                marc.remove_field(field)


def remove_unwanted_tags(marc):
    if marc is not None:
        marc.remove_fields("263", "242")


def remove_ebook_isbns(marc):
    if marc is not None:
        for field in marc.get_fields("020"):
            for term in [
                "ebk",
                "ebook",
                "e-book",
                "electronic",
                "e-isbn",
                "e-mhid",
                "pdf",
                "epub",
                "e-mobi",
                "html",
                "mobil",
                "el.",
            ]:
                if term in field.value().lower():
                    marc.remove_field(field)
                    break
