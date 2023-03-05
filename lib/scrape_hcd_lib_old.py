import datetime
from datetime import timedelta
import json

import requests

HCD_QUERY_URL = "https://wabi-us-gov-iowa-api.analysis.usgovcloudapi.net/public/reports/querydata"

HCD_HTML_PAGE_URL = "https://app.powerbigov.us/view?r=eyJrIjoiZTk1YTg5NzAtYmI2ZC00NDllLTgxMDktMmE0ZWM3ODE1ZGE2IiwidCI6IjJiODI4NjQ2LWIwMzctNGZlNy04NDE1LWU5MzVjZDM0Y2Y5NiJ9"

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "PostmanRuntime/7.29.2",
    "Accept-Encoding": "gzip, deflate, br",
    "X-PowerBI-ResourceKey": "e95a8970-bb6d-449e-8109-2a4ec7815da6",
    "ActivityID": "c0e77b96-9382-6ac7-2741-efcd3db86b27",
    "RequestID": "e3b9c2aa-b228-305a-ce0a-ed8f22734393",
}
params = {"synchronous": "true"}

################################################################################################
# scrape section 1: element statuses
################################################################################################


def OLD__scrape_element_statuses():
    # load and format request payload, borrowing how HCD's web dashboard requests data
    with open("lib/scrape_hcd/request_body.json", "r") as f:
        data = json.dumps(json.load(f), indent=4, sort_keys=True)

    # request page 1
    response = requests.post(HCD_QUERY_URL, data=data, headers=HEADERS, params=params)
    jsonResp = json.loads(response.content)

    if response.status_code != 200:
        raise Exception("HCD request did not return data")

    # load mappings
    first100CityNames = jsonResp["results"][0]["result"]["data"]["dsr"]["DS"][0]["ValueDicts"]["D2"]
    fifthCycleCodes = jsonResp["results"][0]["result"]["data"]["dsr"]["DS"][0]["ValueDicts"]["D0"]
    sixthCycleCodes = jsonResp["results"][0]["result"]["data"]["dsr"]["DS"][0]["ValueDicts"]["D1"]

    # set up transform loop
    tableRows = []
    counter = 0

    respList = jsonResp["results"][0]["result"]["data"]["dsr"]["DS"][0]["PH"][0]["DM0"]

    for x in respList[0:-1]:  # ignore the last element because it shows up in 2nd page
        if counter < 100:
            x["CityName"] = first100CityNames[counter]
        else:
            x["CityName"] = x["C"][-1]

        if "R" in x:
            # R is a compression trick when row N is similar to row N-1.
            # The key R is a bitfield representing which fields to re-use from the previous row. eg an R of 25
            # corresponds to bits 1, 8 and 16 => for the first, fourth, and fifth fields, copy the previous row.
            if x["R"] == 1:
                x["FifthCycleStatus"] = tableRows[counter - 1]["5thCycle"]
                x["SixthCycleStatus"] = sixthCycleCodes[x["C"][0]]
            elif x["R"] == 2:
                x["FifthCycleStatus"] = fifthCycleCodes[x["C"][0]]
                x["SixthCycleStatus"] = tableRows[counter - 1]["6thCycle"]
            elif x["R"] == 3:
                x["FifthCycleStatus"] = tableRows[counter - 1]["5thCycle"]
                x["SixthCycleStatus"] = tableRows[counter - 1]["6thCycle"]
        else:  # R is blank, so no borrowing from row N-1.
            x["FifthCycleStatus"] = fifthCycleCodes[x["C"][0]]
            x["SixthCycleStatus"] = sixthCycleCodes[x["C"][1]]

        # print(row.CityName + ': ' + row['5thCycle'] + ' | ' + row['6thCycle'])
        # elementStatusTable.create({'jurisdiction':row.CityName, '5thCycle':row['5thCycle'], '6thCycle':row['6thCycle']})
        row = {"jurisdiction": x["CityName"], "5thCycle": x["FifthCycleStatus"], "6thCycle": x["SixthCycleStatus"]}
        tableRows.append(row)
        counter += 1

    # request page 2
    with open("lib/scrape_hcd/request_body_paginate.json", "r") as f:
        dataPaginate = json.dumps(json.load(f), indent=4, sort_keys=True)

    responsePaginate = requests.post(HCD_QUERY_URL, data=dataPaginate, headers=HEADERS, params=params)
    jsonRespPaginate = json.loads(responsePaginate.content)

    if responsePaginate.status_code != 200:
        raise Exception("HCD pagination request did not return data")

    # with open('HCD_response_paginate.json', 'w') as json_file:
    #   json.dump(jsonRespPaginate, json_file)

    # paginated map - the mapping is different!!!
    respListPaginate = jsonRespPaginate["results"][0]["result"]["data"]["dsr"]["DS"][0]["PH"][0]["DM0"]
    fifthCycleCodesPaginated = jsonRespPaginate["results"][0]["result"]["data"]["dsr"]["DS"][0]["ValueDicts"]["D0"]
    sixthCycleCodesPaginated = jsonRespPaginate["results"][0]["result"]["data"]["dsr"]["DS"][0]["ValueDicts"]["D1"]
    first100CityNamesPaginate = jsonRespPaginate["results"][0]["result"]["data"]["dsr"]["DS"][0]["ValueDicts"][
        "D2"
    ]

    nameCounter = 0
    for x in respListPaginate:
        x["CityName"] = first100CityNamesPaginate[nameCounter]
        if "R" in x:
            if x["R"] == 1:
                x["FifthCycleStatus"] = tableRows[counter - 1]["5thCycle"]
                x["SixthCycleStatus"] = sixthCycleCodesPaginated[x["C"][0]]
            elif x["R"] == 2:
                x["FifthCycleStatus"] = fifthCycleCodesPaginated[x["C"][0]]
                x["SixthCycleStatus"] = tableRows[counter - 1]["6thCycle"]
            elif x["R"] == 3:
                x["FifthCycleStatus"] = tableRows[counter - 1]["5thCycle"]
                x["SixthCycleStatus"] = tableRows[counter - 1]["6thCycle"]
        else:  # R is blank
            x["FifthCycleStatus"] = fifthCycleCodesPaginated[x["C"][0]]
            x["SixthCycleStatus"] = sixthCycleCodesPaginated[x["C"][1]]

        row = {"jurisdiction": x["CityName"], "5thCycle": x["FifthCycleStatus"], "6thCycle": x["SixthCycleStatus"]}
        # print(row.CityName + ': ' + row['5thCycle'] + ' | ' + row['6thCycle'])
        # elementStatusTable.create({'jurisdiction':row.CityName, '5thCycle':row['5thCycle'], '6thCycle':row['6thCycle']})
        tableRows.append(row)
        counter += 1
        nameCounter += 1
    return tableRows


################################################################################################
# scrape section 2: elements under review
################################################################################################


def OLD__scrape_elements_under_review():
    with open("lib/scrape_hcd/review_request_body.json", "r") as f:
        reviewData = json.dumps(json.load(f), indent=4, sort_keys=True)

    reviewResponse = requests.post(HCD_QUERY_URL, data=reviewData, headers=HEADERS, params=params)
    reviewJsonResp = json.loads(reviewResponse.content)

    # store response for debugging
    # with open('HCD_review_response.json', 'w') as json_file:
    #  json.dump(reviewJsonResp, json_file)

    reviewCityNames = reviewJsonResp["results"][0]["result"]["data"]["dsr"]["DS"][0]["ValueDicts"]["D0"]
    reviewStatus = reviewJsonResp["results"][0]["result"]["data"]["dsr"]["DS"][0]["ValueDicts"]["D2"]
    reviewCycle = reviewJsonResp["results"][0]["result"]["data"]["dsr"]["DS"][0]["ValueDicts"]["D1"]
    reviewRespList = reviewJsonResp["results"][0]["result"]["data"]["dsr"]["DS"][0]["PH"][0]["DM0"]
    reviewTableRows = []
    counter = 0

    # date fields are encoded as msecs since epoch
    epoch = datetime.datetime.utcfromtimestamp(0)  # TODO: use record's time stamp directly?

    for x in reviewRespList:
        x["cityName"] = reviewCityNames[counter]
        if "R" in x:  # R means run-length-encoding, when row N is similar to row N-1
            if x["R"] == 4:  # no borrowing, but different spacing from 1st item (?)
                x["type"] = reviewStatus[x["C"][2]]
                rdate = timedelta(seconds=x["C"][1] / 1000) + epoch
                x["receivedDate"] = rdate.strftime("%Y-%m-%d")
                fdate = timedelta(seconds=x["C"][3] / 1000) + epoch
                x["finalDueDate"] = fdate.strftime("%Y-%m-%d")
            elif x["R"] == 6:  # change final date date
                x["type"] = reviewStatus[x["C"][1]]
                fdate = timedelta(seconds=x["C"][2] / 1000) + epoch
                x["finalDueDate"] = fdate.strftime("%Y-%m-%d")
                x["receivedDate"] = reviewTableRows[counter - 1]["receivedDate"]
            elif x["R"] == 12:  # change both dates
                x["type"] = reviewTableRows[counter - 1]["type"]
                rdate = timedelta(seconds=x["C"][1] / 1000) + epoch
                x["receivedDate"] = rdate.strftime("%Y-%m-%d")
                fdate = timedelta(seconds=x["C"][2] / 1000) + epoch
                x["finalDueDate"] = fdate.strftime("%Y-%m-%d")
            elif x["R"] == 20:  # change received date and status
                x["type"] = reviewStatus[x["C"][2]]
                rdate = timedelta(seconds=x["C"][1] / 1000) + epoch
                x["receivedDate"] = rdate.strftime("%Y-%m-%d")
                x["finalDueDate"] = reviewTableRows[counter - 1]["finalDueDate"]
            elif x["R"] == 22:  # change status
                x["type"] = reviewStatus[x["C"][1]]
                x["finalDueDate"] = reviewTableRows[counter - 1]["finalDueDate"]
                x["receivedDate"] = reviewTableRows[counter - 1]["receivedDate"]
            elif x["R"] == 28:  # change received date
                rdate = timedelta(seconds=x["C"][1] / 1000) + epoch
                x["receivedDate"] = rdate.strftime("%Y-%m-%d")
                x["type"] = reviewTableRows[counter - 1]["type"]
                x["finalDueDate"] = reviewTableRows[counter - 1]["finalDueDate"]
            elif x["R"] == 30:  # no changes
                x["type"] = reviewTableRows[counter - 1]["type"]
                x["receivedDate"] = reviewTableRows[counter - 1]["receivedDate"]
                x["finalDueDate"] = reviewTableRows[counter - 1]["finalDueDate"]
        else:
            x["type"] = reviewStatus[x["C"][2]]
            rdate = timedelta(seconds=x["C"][1] / 1000) + epoch
            x["receivedDate"] = rdate.strftime("%Y-%m-%d")
            fdate = timedelta(seconds=x["C"][4] / 1000) + epoch
            x["finalDueDate"] = fdate.strftime("%Y-%m-%d")

        # print(row.cityName + ': ' + row.reviewStatus  + ' | ' + row['receivedDate']+ ' | ' + row.finalDueDate)
        # reviewTable.create({'jurisdiction':row.cityName, 'type':row.reviewStatus, 'receivedDate':row['receivedDate'], 'finalDueDate':row.finalDueDate})
        row = {
            "jurisdiction": x["cityName"],
            "type": x["type"],
            "receivedDate": x["receivedDate"],
            "finalDueDate": x["finalDueDate"],
        }
        reviewTableRows.append(row)
        counter += 1
    return reviewTableRows
