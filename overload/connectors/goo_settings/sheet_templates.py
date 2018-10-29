# Google Sheets templates encoded in request body


def nypl_pvf_dup_report_template(tab_id):
    """
    args:
        tab_id: string, id of Google Sheet tab
    returns:
        body: dictionary, encodes in requests body properties of the tab
    """

    return {
        "requests": [
            {
                "repeatCell": {
                    "range": {
                        "sheetId": tab_id,
                        "startRowIndex": 0,
                        "endRowIndex": 1
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": {
                                "red": 0.64313725,
                                "green": 0.76078431,
                                "blue": 0.95686275
                            },
                            "horizontalAlignment": "CENTER",
                            "textFormat": {
                                "fontSize": 10,
                                "bold": True
                            }
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
                }
            },
            {
                'updateSheetProperties': {
                    'properties': {
                        'sheetId': tab_id,
                        'gridProperties': {
                            'frozenRowCount': 1
                        },
                    },
                    'fields': 'gridProperties.frozenRowCount'
                },
            },
            {
                "addConditionalFormatRule": {
                    "rule": {
                        "ranges": [
                            {
                                "sheetId": tab_id,
                                "startRowIndex": 1,
                                "startColumnIndex": 8,
                                "endColumnIndex": 9
                            }
                        ],
                        "booleanRule": {
                            "condition": {
                                "type": "TEXT_EQ",
                                "values": [
                                    {
                                        "userEnteredValue": "yes"
                                    }
                                ]
                            },
                            "format": {
                                'backgroundColor':
                                    {
                                        'red': 0.7176471,
                                        'green': 0.88235295,
                                        'blue': 0.8039216,
                                    }
                            }
                        }
                    },
                    "index": 0
                }
            },
            {
                "addConditionalFormatRule": {
                    "rule": {
                        "ranges": [
                            {
                                "sheetId": tab_id,
                                "startRowIndex": 1,
                                "startColumnIndex": 8,
                                "endColumnIndex": 9
                            }
                        ],
                        "booleanRule": {
                            "condition": {
                                "type": "TEXT_EQ",
                                "values": [
                                    {
                                        "userEnteredValue": "no"
                                    }
                                ]
                            },
                            "format": {
                                'backgroundColor':
                                    {
                                        'red': 0.95686275,
                                        'green': 0.78039217,
                                        'blue': 0.7647059,
                                    }
                            }
                        }
                    },
                    "index": 1
                }
            },
            {
                "setDataValidation": {
                    "range": {
                        "sheetId": tab_id,
                        "startRowIndex": 1,
                        "startColumnIndex": 8,
                        "endColumnIndex": 9,
                    },
                    "rule": {
                        "condition": {
                            "type": 'ONE_OF_LIST',
                            "values": [
                                {
                                    "userEnteredValue": 'yes'
                                },
                                {
                                    "userEnteredValue": 'no'
                                },
                                {
                                    "userEnteredValue": 'no action'
                                },
                            ]
                        },
                        "inputMessage": 'only yes,no,no action permitted',
                        "strict": False,
                        "showCustomUi": True
                    }
                }
            },
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": tab_id,
                        "dimension": "COLUMNS",
                        "startIndex": 0,
                        "endIndex": 1
                    },
                    "properties": {
                        "pixelSize": 75
                    },
                    "fields": "pixelSize"
                }
            },
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": tab_id,
                        "dimension": "COLUMNS",
                        "startIndex": 1,
                        "endIndex": 2
                    },
                    "properties": {
                        "pixelSize": 53
                    },
                    "fields": "pixelSize"
                }
            },
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": tab_id,
                        "dimension": "COLUMNS",
                        "startIndex": 2,
                        "endIndex": 3
                    },
                    "properties": {
                        "pixelSize": 100
                    },
                    "fields": "pixelSize"
                }
            },
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": tab_id,
                        "dimension": "COLUMNS",
                        "startIndex": 3,
                        "endIndex": 4
                    },
                    "properties": {
                        "pixelSize": 90
                    },
                    "fields": "pixelSize"
                }
            },
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": tab_id,
                        "dimension": "COLUMNS",
                        "startIndex": 4,
                        "endIndex": 5
                    },
                    "properties": {
                        "pixelSize": 82
                    },
                    "fields": "pixelSize"
                }
            },
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": tab_id,
                        "dimension": "COLUMNS",
                        "startIndex": 5,
                        "endIndex": 6
                    },
                    "properties": {
                        "pixelSize": 250
                    },
                    "fields": "pixelSize"
                }
            },
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": tab_id,
                        "dimension": "COLUMNS",
                        "startIndex": 6,
                        "endIndex": 7
                    },
                    "properties": {
                        "pixelSize": 100
                    },
                    "fields": "pixelSize"
                }
            },
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": tab_id,
                        "dimension": "COLUMNS",
                        "startIndex": 7,
                        "endIndex": 8
                    },
                    "properties": {
                        "pixelSize": 150
                    },
                    "fields": "pixelSize"
                }
            },
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": tab_id,
                        "dimension": "COLUMNS",
                        "startIndex": 8,
                        "endIndex": 9
                    },
                    "properties": {
                        "pixelSize": 76
                    },
                    "fields": "pixelSize"
                }
            },
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": tab_id,
                        "dimension": "COLUMNS",
                        "startIndex": 9,
                        "endIndex": 10
                    },
                    "properties": {
                        "pixelSize": 350
                    },
                    "fields": "pixelSize"
                }
            },
        ],
        'includeSpreadsheetInResponse': False,
        'responseIncludeGridData': False
    }


def pvf_callNo_report_template(tab_id):
    """
    encodes properies of Google Sheet tab
    args:
        tab_id: string, tab (sheet id)
    returns:
        body: dictionary, request body
    """

    return {
        "requests": [
            {
                "repeatCell": {
                    "range": {
                        "sheetId": tab_id,
                        "startRowIndex": 0,
                        "endRowIndex": 1
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": {
                                "red": 0.64313725,
                                "green": 0.76078431,
                                "blue": 0.95686275
                            },
                            "horizontalAlignment": "CENTER",
                            "textFormat": {
                                "fontSize": 10,
                                "bold": True
                            }
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
                }
            },
            {
                'updateSheetProperties': {
                    'properties': {
                        'sheetId': tab_id,
                        'gridProperties': {
                            'frozenRowCount': 1
                        },
                    },
                    'fields': 'gridProperties.frozenRowCount'
                },
            },
            {
                "addConditionalFormatRule": {
                    "rule": {
                        "ranges": [
                            {
                                "sheetId": tab_id,
                                "startRowIndex": 1,
                                "startColumnIndex": 7,
                                "endColumnIndex": 8
                            }
                        ],
                        "booleanRule": {
                            "condition": {
                                "type": "TEXT_EQ",
                                "values": [
                                    {
                                        "userEnteredValue": "yes"
                                    }
                                ]
                            },
                            "format": {
                                'backgroundColor':
                                    {
                                        'red': 0.7176471,
                                        'green': 0.88235295,
                                        'blue': 0.8039216,
                                    }
                            }
                        }
                    },
                    "index": 0
                }
            },
            {
                "addConditionalFormatRule": {
                    "rule": {
                        "ranges": [
                            {
                                "sheetId": tab_id,
                                "startRowIndex": 1,
                                "startColumnIndex": 7,
                                "endColumnIndex": 8
                            }
                        ],
                        "booleanRule": {
                            "condition": {
                                "type": "TEXT_EQ",
                                "values": [
                                    {
                                        "userEnteredValue": "no"
                                    }
                                ]
                            },
                            "format": {
                                'backgroundColor':
                                    {
                                        'red': 0.95686275,
                                        'green': 0.78039217,
                                        'blue': 0.7647059,
                                    }
                            }
                        }
                    },
                    "index": 1
                }
            },
            {
                "setDataValidation": {
                    "range": {
                        "sheetId": tab_id,
                        "startRowIndex": 1,
                        "startColumnIndex": 7,
                        "endColumnIndex": 8,
                    },
                    "rule": {
                        "condition": {
                            "type": 'ONE_OF_LIST',
                            "values": [
                                {
                                    "userEnteredValue": 'yes'
                                },
                                {
                                    "userEnteredValue": 'no'
                                },
                            ]
                        },
                        "inputMessage": 'only yes,no permitted',
                        "strict": False,
                        "showCustomUi": True
                    }
                }
            },
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": tab_id,
                        "dimension": "COLUMNS",
                        "startIndex": 0,
                        "endIndex": 1
                    },
                    "properties": {
                        "pixelSize": 75
                    },
                    "fields": "pixelSize"
                }
            },
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": tab_id,
                        "dimension": "COLUMNS",
                        "startIndex": 1,
                        "endIndex": 2
                    },
                    "properties": {
                        "pixelSize": 100
                    },
                    "fields": "pixelSize"
                }
            },
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": tab_id,
                        "dimension": "COLUMNS",
                        "startIndex": 2,
                        "endIndex": 3
                    },
                    "properties": {
                        "pixelSize": 90
                    },
                    "fields": "pixelSize"
                }
            },
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": tab_id,
                        "dimension": "COLUMNS",
                        "startIndex": 3,
                        "endIndex": 4
                    },
                    "properties": {
                        "pixelSize": 82
                    },
                    "fields": "pixelSize"
                }
            },
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": tab_id,
                        "dimension": "COLUMNS",
                        "startIndex": 4,
                        "endIndex": 5
                    },
                    "properties": {
                        "pixelSize": 200
                    },
                    "fields": "pixelSize"
                }
            },
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": tab_id,
                        "dimension": "COLUMNS",
                        "startIndex": 5,
                        "endIndex": 6
                    },
                    "properties": {
                        "pixelSize": 200
                    },
                    "fields": "pixelSize"
                }
            },
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": tab_id,
                        "dimension": "COLUMNS",
                        "startIndex": 6,
                        "endIndex": 7
                    },
                    "properties": {
                        "pixelSize": 150
                    },
                    "fields": "pixelSize"
                }
            },
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": tab_id,
                        "dimension": "COLUMNS",
                        "startIndex": 7,
                        "endIndex": 8
                    },
                    "properties": {
                        "pixelSize": 70
                    },
                    "fields": "pixelSize"
                }
            },
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": tab_id,
                        "dimension": "COLUMNS",
                        "startIndex": 8,
                        "endIndex": 9
                    },
                    "properties": {
                        "pixelSize": 350
                    },
                    "fields": "pixelSize"
                }
            },
        ],
        'includeSpreadsheetInResponse': False,
        'responseIncludeGridData': False
    }


def bpl_pvf_dup_report_template(tab_id):

    return {
        "requests": [
            {
                "repeatCell": {
                    "range": {
                        "sheetId": tab_id,
                        "startRowIndex": 0,
                        "endRowIndex": 1
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": {
                                "red": 0.64313725,
                                "green": 0.76078431,
                                "blue": 0.95686275
                            },
                            "horizontalAlignment": "CENTER",
                            "textFormat": {
                                "fontSize": 10,
                                "bold": True
                            }
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
                }
            },
            {
                'updateSheetProperties': {
                    'properties': {
                        'sheetId': tab_id,
                        'gridProperties': {
                            'frozenRowCount': 1
                        },
                    },
                    'fields': 'gridProperties.frozenRowCount'
                },
            },
            {
                "addConditionalFormatRule": {
                    "rule": {
                        "ranges": [
                            {
                                "sheetId": tab_id,
                                "startRowIndex": 1,
                                "startColumnIndex": 6,
                                "endColumnIndex": 7
                            }
                        ],
                        "booleanRule": {
                            "condition": {
                                "type": "TEXT_EQ",
                                "values": [
                                    {
                                        "userEnteredValue": "yes"
                                    }
                                ]
                            },
                            "format": {
                                'backgroundColor':
                                    {
                                        'red': 0.7176471,
                                        'green': 0.88235295,
                                        'blue': 0.8039216,
                                    }
                            }
                        }
                    },
                    "index": 0
                }
            },
            {
                "addConditionalFormatRule": {
                    "rule": {
                        "ranges": [
                            {
                                "sheetId": tab_id,
                                "startRowIndex": 1,
                                "startColumnIndex": 6,
                                "endColumnIndex": 7
                            }
                        ],
                        "booleanRule": {
                            "condition": {
                                "type": "TEXT_EQ",
                                "values": [
                                    {
                                        "userEnteredValue": "no"
                                    }
                                ]
                            },
                            "format": {
                                'backgroundColor':
                                    {
                                        'red': 0.95686275,
                                        'green': 0.78039217,
                                        'blue': 0.7647059,
                                    }
                            }
                        }
                    },
                    "index": 1
                }
            },
            {
                "setDataValidation": {
                    "range": {
                        "sheetId": tab_id,
                        "startRowIndex": 1,
                        "startColumnIndex": 6,
                        "endColumnIndex": 7,
                    },
                    "rule": {
                        "condition": {
                            "type": 'ONE_OF_LIST',
                            "values": [
                                {
                                    "userEnteredValue": 'yes'
                                },
                                {
                                    "userEnteredValue": 'no'
                                },
                                {
                                    "userEnteredValue": 'no action'
                                },
                            ]
                        },
                        "inputMessage": 'only yes,no,no action permitted',
                        "strict": False,
                        "showCustomUi": True
                    }
                }
            },
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": tab_id,
                        "dimension": "COLUMNS",
                        "startIndex": 0,
                        "endIndex": 1
                    },
                    "properties": {
                        "pixelSize": 75
                    },
                    "fields": "pixelSize"
                }
            },
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": tab_id,
                        "dimension": "COLUMNS",
                        "startIndex": 1,
                        "endIndex": 2
                    },
                    "properties": {
                        "pixelSize": 53
                    },
                    "fields": "pixelSize"
                }
            },
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": tab_id,
                        "dimension": "COLUMNS",
                        "startIndex": 2,
                        "endIndex": 3
                    },
                    "properties": {
                        "pixelSize": 100
                    },
                    "fields": "pixelSize"
                }
            },
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": tab_id,
                        "dimension": "COLUMNS",
                        "startIndex": 3,
                        "endIndex": 4
                    },
                    "properties": {
                        "pixelSize": 90
                    },
                    "fields": "pixelSize"
                }
            },
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": tab_id,
                        "dimension": "COLUMNS",
                        "startIndex": 4,
                        "endIndex": 5
                    },
                    "properties": {
                        "pixelSize": 82
                    },
                    "fields": "pixelSize"
                }
            },
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": tab_id,
                        "dimension": "COLUMNS",
                        "startIndex": 5,
                        "endIndex": 6
                    },
                    "properties": {
                        "pixelSize": 250
                    },
                    "fields": "pixelSize"
                }
            },
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": tab_id,
                        "dimension": "COLUMNS",
                        "startIndex": 7,
                        "endIndex": 8
                    },
                    "properties": {
                        "pixelSize": 76
                    },
                    "fields": "pixelSize"
                }
            },
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": tab_id,
                        "dimension": "COLUMNS",
                        "startIndex": 8,
                        "endIndex": 9
                    },
                    "properties": {
                        "pixelSize": 350
                    },
                    "fields": "pixelSize"
                }
            },
        ],
        'includeSpreadsheetInResponse': False,
        'responseIncludeGridData': False
    }
