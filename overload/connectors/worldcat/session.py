import requests


from __version__ import __version__, __title__
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


def extract_record_from_response(response):
    response_body = string2xml(response.content)
    record = response_body.find(".//atom:content/rb:response/marc:record", ONS)
    return record
