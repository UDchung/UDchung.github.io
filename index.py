import os
import json
import datetime
from operator import itemgetter
from itertools import groupby

BITMAP_FOLDER = "bitmaps"

displays = {}
dests = {}
miscDisplays = []
invalid = []


#####################
# utility functions #
#####################

def uncapitalizeLast(rtnum: str):
    """
    Uncapitalize the last alphabetical characters.
    """
    # if rtnum only has digits, return immediately
    if rtnum.isnumeric():
        return rtnum

    numIndex = -1

    # iterate each character,
    # get index of last numeric character
    for index, char in enumerate(rtnum):
        if char.isnumeric():
            numIndex = index

    # if there is numeric and it is not the last character,
    # uncapitalize chars after that index
    if 0 <= numIndex < len(rtnum)-1:
        rtnum = rtnum[:numIndex+1] + rtnum[numIndex+1:].lower()

    return rtnum


def getNumeric(rtnum: str):
    """
    Get initial numeric portion of route number.

    Returns the starting index of numeric portion, and the numeric portion itself in integer.
    If no numeric portion found, -1 is returned for both values.
    """
    numeric = ""
    start = -1

    # iterate each character
    for index, char in enumerate(rtnum):
        # for 1st occurence of number, set start
        # for all occurence, append to string
        if ord("0") <= ord(char) <= ord("9"):
            if start < 0:
                start = index
            numeric += char
        # if end of number, break immediately
        elif start >= 0:
            break

    if numeric == "":
        numeric = "-1"

    return start, int(numeric)


################
# main portion #
################

folder = os.path.join(os.getcwd(), BITMAP_FOLDER)

for (root, dirs, files) in os.walk(folder, topdown=True):
    # continue if not main directory
    if root != folder:
        continue

    # iterate filenames list
    for file in files:
        # get file format
        split = file.split(".")

        # if not bmp, continue next file
        if split[1] != "bmp":
            continue

        # get fields
        bla = split[0].split("_")
        if len(bla) != 3:
            # misc displays
            miscDisplays.append(file)
            continue

        # if contain 3 fields, route displays
        #   unpack fields
        route, dest, info = bla

        route = uncapitalizeLast(route)

        # 1st field = route
        if displays.get(route) is None:
            displays[route] = {}

        # 2nd field = dest
        if displays[route].get(dest) is None:
            displays[route][dest] = {}

        # 3rd field contains sequence/version/pages
        #   if last digit not number, add to invalid
        if not ord("0") <= ord(info[-1]) <= ord("9"):
            invalid.append(file)
            continue

        # first digit denotes sequence
        # last digit denotes pages
        # intermediate "o"s denotes version,
        #   other character denotes special versions
        sequence = info[0]
        page = info[-1]
        versionString = info[1:-1]

        if len(versionString) == 0 or \
                versionString == "o"*len(versionString):
            version = str(len(versionString))
        else:
            # first character of version denotes special versions
            version = versionString[0] + str(len(versionString)-1)

        # add to displays dictionary
        if displays[route][dest].get(sequence) is None:
            displays[route][dest][sequence] = {}

        if displays[route][dest][sequence].get(version) is None:
            displays[route][dest][sequence][version] = 0

        displays[route][dest][sequence][version] += 1

        # add to dest dictionary
        if dests.get(dest) is None:
            dests[dest] = []

        if route not in dests[dest]:
            dests[dest].append(route)

# sort by route key
group = {key: [] for key in [
    "numeric",
    "alphabet",
    "Others"
]}

# iterate routes
#   step 1: group by start index of numeric character (0 / 1 / >=2 or none)
keys = list(displays.keys())
for routeNum in keys:
    start, num = getNumeric(routeNum)
    if start == 0:
        group["numeric"].append((num, routeNum))
    elif start == 1:
        group["alphabet"].append((num, routeNum))
    else:
        group["Others"].append((num, routeNum))

#   step 2: for pure numeric, sort by numeric portion, then by complete rtnum
#               then it is splitted by groups of 100 (0-99, 100-199, etc)
#               before adding to keylist
#           else, sort by complete rtnum only,
#               then whole group is added to keylist
keylist = {}
for key, value in group.items():
    if key == "numeric":
        value.sort()
        # group by 100, set key as (0-99)
        for numberKey, group in groupby(value, key=lambda num: num[0]//100):
            groupItems = [routeNum for num, routeNum in group]
            groupKey = f"{groupItems[0]}-{groupItems[-1]}"
            keylist[groupKey] = groupItems
    else:
        value.sort(key=itemgetter(1))
        if key == "alphabet":
            # group by 1st char, set key as (A10-A29)
            for numberKey, group in groupby(value, key=lambda num: num[1][0]):
                groupItems = [routeNum for num, routeNum in group]
                groupKey = f"{groupItems[0]}-{groupItems[-1]}"
                keylist[groupKey] = groupItems
        else:
            # append rtNum part of whole group to keylist
            keylist[key] = [routeNum for num, routeNum in value]

# now keys is sorted the way we want,
# rebuild display dictionary by the order in [keys]
sortedDisplays = {}
for group, rtnumList in keylist.items():
    sortedDisplays[group] = {}
    for rtnum in rtnumList:
        sortedDisplays[group][rtnum] = displays[rtnum]

displays = sortedDisplays.copy()
displays
sortedDisplays.clear()

timestamp = str(datetime.datetime.now().isoformat(sep=" ", timespec="seconds"))

# dump to json
with open("indexDump.json", "w", encoding="utf-8") as dumpFile:
    dump = {
        "timestamp": timestamp,
        "displays": displays,
        "dests": dests,
        "miscDisplays": miscDisplays,
        "invalid": invalid
    }
    json.dump(dump, dumpFile, ensure_ascii=False, indent="\t")


# iterate for each group
markdown = []

for group, displaysGroup in displays.items():
    htmlFilename = f"index_{group}.html"
    title = f"{group} ({timestamp})"

    markdown.append(f"- [{group.upper()}]({htmlFilename})")

    with open(htmlFilename, "w", encoding="utf-8") as html:
        html.write("\n".join([
            "<!DOCTYPE html>",
            "<html lang=\"en\">",
            "",
            "<head>",
            "\t<meta charset=\"UTF-8\">",
            "\t<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">",
            "\t<link rel=\"stylesheet\" href=\"style.css\">",
            f"\t<title>{title}</title>",
            "</head>",
            "",
            "<body>",
            "\t<table>",
            "\t\t<thead>",
            "\t\t\t<tr>",
            "\t\t\t\t<th>路綫</th>",
            "\t\t\t\t<th>方向</th>",
            "\t\t\t\t<th>次序</th>",
            "\t\t\t\t<th>顯示</th>",
            "\t\t\t</tr>",
            "\t\t</thead>",
            "\t\t<tbody>",
        ]))

        tableCellClass = ["route", "dest", "seq", "files"]
        tableCells = []
        rowSpans = []
        for route, routeDest in displaysGroup.items():
            for dest, destSeq in routeDest.items():
                for seq, verCount in destSeq.items():
                    files = ""

                    for ver, count in verCount.items():
                        try:
                            version = int(ver)+1
                            versionHead = len(verCount)-int(ver)
                        except ValueError:
                            version = ver[:-1]
                            versionHead = version
                        else:
                            version = "o"*(version-1)

                        files += "<div>"
                        files += f"<h1>Version {versionHead}</h1>"
                        for fileIndex in range(count):
                            filename = f"{route.upper()}_{dest}_{seq}{version}{fileIndex}.bmp"
                            files += f"<div><span><p>Page</p><h2>{fileIndex+1}</h2></span>"
                            files += f"<span><img src=\"{BITMAP_FOLDER}\\{filename}\"></span></div>"
                        files += "</div>"

                    tableCells.append([
                            route,
                            dest,
                            seq,
                            files
                        ])
                    rowSpans.append([1, 1, 1])

            # look for each col, if the cell above has same value
            for x in range(len(rowSpans[0])):
                for y in range(len(tableCells)-1, 0, -1):
                    # print(x,y)
                    #  current (1 ~ n)     above (0 ~ n-1)
                    if tableCells[y][x] == tableCells[y-1][x]:
                        # set to empty string
                        tableCells[y][x] = ""
                        # add rowSpan to above, unset self
                        rowSpans[y-1][x] += rowSpans[y][x]
                        rowSpans[y][x] = 0

            # make into html rows
            for y, tableRow in enumerate(tableCells):
                tr = ""
                tr += "\t\t\t<tr>"
                # for each cell, dont write rowSpan if doesnt exist
                for x, cell in enumerate(tableRow):
                    # has rowSpan
                    cellClass = tableCellClass[x]
                    if cellClass == "dest":
                        cell = cell.replace("-", "<br>-")

                    if x < len(rowSpans[0]):
                        rowspan = rowSpans[y][x]
                        if rowspan > 1:
                            tr += ("<td class=\"%s\" rowspan=\"%d\">%s</td>" % (cellClass, rowSpans[y][x], cell))
                        elif rowspan == 1:
                            tr += ("<td class=\"%s\">%s</td>" % (cellClass, cell))
                        # rowspan = 0, dont write <td> at all
                    else:
                        tr += ("<td class=\"%s\">%s</td>" % (cellClass, cell))

                tr += ("</tr>")
                # print("\n".join(tr))

                html.write("\n")
                html.write(tr)

            tableCells.clear()
            rowSpans.clear()

        html.write("\n")
        html.write("\n".join([
            "\t\t</tbody>",
            "\t</table>",
            "</body>"
        ]))

print("\n".join(markdown))

