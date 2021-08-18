import os
import csv
import json
from dateutil import parser
import operator
import datetime
from bs4 import BeautifulSoup
from inscriptis import get_text
from texttable import Texttable
# Given a CSS Rule, and a blob of HTML, return the blob of HTML that matches


def css_filter(css_filter, html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    html_block = ""
    for item in soup.select(css_filter, separator=""):
        html_block += str(item)

    return html_block + "\n"


def get_data(html_content):
    """
    parses sorted data out of html content and adds parsed values if possible
    """
    soup = BeautifulSoup(html_content, "html.parser")
    tables = soup.findAll('table')
    data = []

    # strip whitespace, replace some unicode weirdness and replace all tab characters
    # because we will ouptut to tsv eventually
    def strip_text(d):
        return d.get_text().strip().replace(u'\xa0', ' ').replace('\t', ' ')

    for table in tables:
        headers = [strip_text(x) for x in table.findAll("th")]
        table_data = [headers + ["ArrivalParsed", "DepartureParsed"]]
        rows = []
        for row in table.findAll('tr'):
            rowdata = [strip_text(x)
                       for x in row.findAll("td")]
            if len(rowdata) == 0:
                continue
            if rowdata[0] == '':
                rowdata[0] = 'Old'
            try:
                startdt = parser.parse(rowdata[3] + " " + rowdata[4])
                enddt = parser.parse(rowdata[3] + " " + rowdata[5])
                rowdata.append(startdt)
                rowdata.append(enddt)
            except Exception as e:
                print(e)
            rows.append(rowdata)
        # sort rows by ASC(Status) -> ASC(Suburb) -> DESC(ArrivalParsed)
        # ASC ArrivalParsed, ignore exceptions if rows dont have 6th element
        try:
            rows.sort(key=operator.itemgetter(6), reverse=True)
        except Exception:
            pass
        # and by status -> suburb
        rows.sort(key=operator.itemgetter(0, 1))
        table_data.extend(rows)
        data.append(table_data)
    return data


def json_serial(obj):
    """JSON serializer for datetime objects not serializable by default json code"""

    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    raise TypeError("Type %s not serializable" % type(obj))


if __name__ == "__main__":

    with open('locations.html') as f:
        contents = f.read()
        print(contents)

    # Remove downloaded HTML file
    os.remove('locations.html')

    # Skip the headers/footers
    page_content = css_filter("#TOCScannableArea", contents)

    # Get the text-only representation of the HTML
    page_content_text = get_text(page_content)

    # Output to locations.txt for commit
    with open('locations.txt', 'w') as txtoutput:
        txtoutput.write(page_content_text)

    # get data for structured output
    data = get_data(contents)

    tablenames = ["CloseContact", "CasualContact", "MonitorForSymptoms"]
    # tsv, because data has comma characters in it.
    for i, table in enumerate(data):
        with open(f"{tablenames[i]}.tsv", 'w') as csvfile:
            writer = csv.writer(csvfile, delimiter="\t")
            writer.writerows(table)
    # json
    for i, table in enumerate(data):
        headers = table[0]
        json_table = [{headers[i]: v for i, v in enumerate(row)}
                      for row in table[1:]]
        with open(f"{tablenames[i]}.json", 'w') as jsonfile:
            jsonfile.write(json.dumps(json_table, indent=4, sort_keys=True, default=json_serial))

    # texttable
    for i, table in enumerate(data):
        text_table = Texttable(max_width=200)
        text_table.add_rows(table)
        with open(f"{tablenames[i]}.txt", 'w') as tablefile:
            tablefile.write(text_table.draw())
