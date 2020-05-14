import requests
import json


from __version__ import __version__, __title__
from accesstoken import WorldcatAccessToken
from bibs.crosswalks import string2xml
from bibs.xml_bibs import ONS


class WorldcatSession(requests.Session):
    """Inherits all requests.Session methods"""

    def __init__(self, credentials=None):
        requests.Session.__init__(self)

        if credentials is None:
            raise TypeError(
                "WorldcatSession credential argument requires ' \
                'WorldcatAccessToken instance or WSkey."
            )

        self.timeout = (10, 10)
        self.headers.update({"User-Agent": "{}/{}".format(__title__, __version__)})


def construct_sru_query(keyword, keyword_type=None, mat_type=None, cat_source=None):
    """
    Creates readable SRU/CQL query, does not encode white spaces or parenthesis - 
    this is handled by the session obj.
    """
    query_elems = []
    if keyword is None:
        raise TypeError("query argument cannot be None.")

    if keyword_type is None:
        # take as straight sru query and pass to sru_query method
        query_elems.append(keyword.strip())
    elif keyword_type == "ISBN":
        query_elems.append('srw.bn = "{}"'.format(keyword))
    elif keyword_type == "UPC":
        query_elems.append('srw.sn = "{}"'.format(keyword))
    elif keyword_type == "ISSN":
        query_elems.append('srw.in = "{}"'.format(keyword))
    elif keyword_type == "OCLC #":
        query_elems.append('srw.no = "{}"'.format(keyword))
    elif keyword_type == "LCCN":
        query_elems.append('srw.dn = "{}"'.format(keyword))

    if mat_type is None or mat_type == "any":
        pass
    elif mat_type == "print":
        query_elems.append('srw.mt = "bks"')
    elif mat_type == "large print":
        query_elems.append('srw.mt = "lpt"')
    elif mat_type == "dvd":
        query_elems.append('srw.mt = "dvv"')
    elif mat_type == "bluray":
        query_elems.append('srw.mt = "bta"')

    if cat_source is None or cat_source == "any":
        pass
    elif cat_source == "DLC":
        query_elems.append('srw.pc = "dlc"')

    return " AND ".join(query_elems)


def is_positive_response(response):
    if response.status_code == requests.codes.ok:
        # code 200
        return True
    else:
        # log the error code & message
        print(response.content)  # temp
        return False


def has_records(response):
    response_body = string2xml(response.content)

    numberOfRecords = response_body.find("response:numberOfRecords", ONS).text

    if numberOfRecords == "0":
        return False
    else:
        return True


def holdings_responses(response):
    holdings = dict()
    if response and response.status_code == 207:
        jres = response.json()
        for entry in jres["entries"]:
            oclcNo = entry["content"]["requestedOclcNumber"]
            res = entry["content"]
            status_msg = entry["content"]["status"]
            if status_msg == "HTTP 200 OK":
                status = "set"
            elif status_msg == "HTTP 409 Conflict":
                status = "exists"
            else:
                status = "unknown"
            holdings[oclcNo] = (status, res)

        return holdings
    else:
        # errors
        return


def extract_record_from_response(response):
    response_body = string2xml(response.content)
    record = response_body.find(".//atom:content/rb:response/marc:record", ONS)
    return record
