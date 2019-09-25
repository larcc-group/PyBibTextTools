#!/usr/bin/env python3

import os
import sys

sys.path.insert(0, "./pybtex/")

from pybtex.database import parse_file, parse_string
from pybtex.database import BibliographyData, Entry, BibliographyDataError
import random
import unidecode
import argparse
import csv
from html import unescape


mergedCount = 0


def mergeEntry(original, novo):
    global mergedCount
    merged = False

    yearOut = int(str(original.rich_fields["year"]))
    year2 = int(str(novo.rich_fields["year"]))
    if year2 < yearOut:
        original.fields["year"] = novo.fields["year"]
        merged = True

    for novoKey in novo.fields:
        if novoKey not in original.fields:
            original.fields[novoKey] = novo.fields[novoKey]
            merged = True

    abs1 = ""
    abs2 = ""
    if "abstract" in original.fields:
        abs1 = original.fields["abstract"]
    if "abstract" in novo.fields:
        abs2 = novo.fields["abstract"]
    if len(abs2) > len(abs1):
        original.fields["abstract"] = novo.fields["abstract"]
        merged = True

    if merged:
        mergedCount += 1

    original.fields["source"] = original.fields["source"] + ";" + novo.fields["source"]

    return original


def getEntryDOIStr(entry):
    if "doi" in entry.fields:
        return str(entry.rich_fields["doi"]).replace("https://doi.org/", "")
    return ""


def getEntryAuthorStr(entry):
    author = ""
    if "author" in entry.persons:
        author = " and ".join(
            [
                "".join(p.last_names) + ", " + "".join(p.first_names)
                for p in entry.persons["author"]
            ]
        )
    return author


def getEntryYearStr(entry):
    year = ""
    if "year" in entry.fields:
        year = int(str(entry.rich_fields["year"]))
        if year == 0:
            year = ""
    return year


def getEntryTitleStr(entry):
    title = ""
    if "title" in entry.fields:
        title = str(entry.rich_fields["title"])
    return title


def getEntryPublishStr(entry):
    publish = ""
    if "journal" in entry.fields:
        publish = str(entry.rich_fields["journal"])
    elif "journaltitle" in entry.fields:
        publish = str(entry.rich_fields["journaltitle"])
    elif "booktitle" in entry.fields:
        publish = str(entry.rich_fields["booktitle"])
    elif "howpublished" in entry.fields:
        publish = str(entry.rich_fields["howpublished"])
    elif "type" in entry.fields:
        publish = str(entry.rich_fields["type"])
    elif "url" in entry.fields:
        publish = "URL {}".format(entry.fields["url"])
    elif "crossref" in entry.fields:
        publish = entry.fields["crossref"].replace("_", " ")
        publish = capwords(publish)
    elif "publisher" in entry.fields:
        publish = str(entry.rich_fields["publisher"])
    elif "arxivId" in entry.fields:
        publish = "arXiv"
    return publish


def getEntryAbstractStr(entry):
    abstract = ""
    if "abstract" in entry.fields:
        abstract = entry.fields["abstract"]
    if abstract != "":
        abstract = unescape(abstract).replace("\\%", "%")
    return abstract


def cleanStringToCompare(xStr):
    return (
        xStr.lower()
        .replace(" ", "")
        .replace(".", "")
        .replace(",", "")
        .replace("-", "")
        .replace(":", "")
        .replace("/", "")
        .replace("\\", "")
        .replace("'", "")
        .replace("`", "")
    )


def isDuplicated(entryOut, entry, verify_doi=False):
    if verify_doi:
        doi = getEntryDOIStr(entry)
        if doi:
            doiOut = getEntryDOIStr(entryOut)
            if doiOut and doi == doiOut:
                return True

    if cleanStringToCompare(entryOut.fields["title"].lower()) == cleanStringToCompare(
        entry.fields["title"].lower()
    ):
        year = int(str(entry.rich_fields["year"]))
        yearOut = int(str(entryOut.rich_fields["year"]))
        diff = abs(year - yearOut)
        if diff == 0:
            return True
        elif diff == 1 or diff == 2:
            try:
                lastname = unidecode.unidecode(
                    entry.persons["author"][0].last_names[0]
                ).lower()
            except:
                lastname = ""

            try:
                lastNameOut = unidecode.unidecode(
                    entryOut.persons["author"][0].last_names[0]
                ).lower()
            except:
                lastNameOut = ""

            try:
                firstName = unidecode.unidecode(
                    entry.persons["author"][0].firstNames[0]
                ).lower()
            except:
                firstName = ""

            try:
                firstNameOut = unidecode.unidecode(
                    entryOut.persons["author"][0].firstNames[0]
                ).lower()
            except:
                firstNameOut = ""

            if (
                lastname == lastNameOut
                or lastname == firstNameOut
                or lastNameOut == firstName
            ):
                return True
    return False


def run(folderPath, fileList, fileNameOut, excludeList, logProcess):
    global mergedCount

    if logProcess:
        fRemoved = open(
            os.path.join(folderPath, "BibFilesMerge_removed.csv"), "w", encoding="utf-8"
        )
        csvRemoved = csv.writer(fRemoved, delimiter=";", quotechar='"')
        csvRemoved.writerow(
            ["cause", "source", "key", "doi", "author", "year", "title", "publish"]
        )
        fFinal = open(
            os.path.join(folderPath, "BibFilesMerge_final.csv"), "w", encoding="utf-8"
        )
        csvFinal = csv.writer(fFinal, delimiter=";", quotechar='"')
        csvFinal.writerow(
            ["key", "source", "doi", "author", "year", "title", "publish", "abstract"]
        )

    fileNamePathOut = os.path.join(folderPath, fileNameOut)

    bibDataOut = BibliographyData()

    total = 0
    mergedCount = 0
    withoutAuthor = 0
    withoutYear = 0
    withoutJornal = 0
    duplicates = 0
    excludedFromBib = 0

    bibDatoToExclude = {}

    for bibFileName in fileList:
        with open(bibFileName, "r") as bibFile:
            fileData = bibFile.read()

        loop = True
        while loop:
            loop = False
            try:
                bibData = parse_string(fileData, None)
                print(
                    bibFileName + ":",
                    len(bibData.entries.values()),
                    "                                             ",
                )

                for entry in bibData.entries.values():
                    total += 1

                    doi = getEntryDOIStr(entry)
                    author = getEntryAuthorStr(entry)
                    year = getEntryYearStr(entry)
                    title = getEntryTitleStr(entry)
                    publish = getEntryPublishStr(entry)

                    foundEntryToExclude = False
                    for bibFileName in excludeList:
                        if bibFileName not in bibDatoToExclude:
                            bibData = parse_file(bibFileName)
                            bibDatoToExclude[bibFileName] = bibData.entries.values()

                        for entryExclude in bibDatoToExclude[bibFileName]:
                            if isDuplicated(entryExclude, entry):
                                excludedFromBib += 1
                                foundEntryToExclude = True
                                break

                        if foundEntryToExclude:
                            break

                    if foundEntryToExclude:
                        continue

                    if not author:
                        withoutAuthor += 1
                        if logProcess:
                            # cause;source;key;doi;author;year;title;publish
                            csvRemoved.writerow(
                                [
                                    "no author",
                                    bibFileName,
                                    entry.key,
                                    doi,
                                    author,
                                    year,
                                    title,
                                    publish,
                                ]
                            )
                    elif not year:
                        withoutYear = withoutYear + 1
                        if logProcess:
                            # cause;source;key;doi;author;year;title;publish
                            csvRemoved.writerow(
                                [
                                    "no year",
                                    bibFileName,
                                    entry.key,
                                    doi,
                                    author,
                                    year,
                                    title,
                                    publish,
                                ]
                            )
                    elif not publish:
                        withoutJornal = withoutJornal + 1
                        if logProcess:
                            # cause;source;key;doi;author;year;title;publish
                            csvRemoved.writerow(
                                [
                                    "no journal",
                                    bibFileName,
                                    entry.key,
                                    doi,
                                    author,
                                    year,
                                    title,
                                    publish,
                                ]
                            )
                    else:
                        key = entry.key.lower()
                        print(
                            "Key " + key + "                        \r",
                            end="",
                            flush=True,
                        )

                        entry.fields["source"] = bibFileName
                        oldEntry = None

                        for entryOut in bibDataOut.entries.values():
                            if isDuplicated(entryOut, entry, True):
                                oldEntry = entryOut
                                break

                        if oldEntry != None:
                            duplicates += 1

                            if logProcess:
                                # cause;source;key;doi;author;year;title;publish
                                csvRemoved.writerow(
                                    [
                                        "duplicate of next",
                                        bibFileName,
                                        entry.key,
                                        doi,
                                        author,
                                        year,
                                        title,
                                        publish,
                                    ]
                                )

                                doi = getEntryDOIStr(oldEntry)
                                author = getEntryAuthorStr(oldEntry)
                                year = getEntryYearStr(oldEntry)
                                title = getEntryTitleStr(oldEntry)
                                publish = getEntryPublishStr(oldEntry)
                                csvRemoved.writerow(
                                    [
                                        "duplicate of prev",
                                        oldEntry.fields["source"],
                                        oldEntry.key,
                                        doi,
                                        author,
                                        year,
                                        title,
                                        publish,
                                    ]
                                )

                            bibDataOut.entries[oldEntry.key] = mergeEntry(
                                oldEntry, entry
                            )
                        else:
                            while key in bibDataOut.entries.keys():
                                key = key + "_a"
                            bibDataOut.entries[key] = entry
            except BibliographyDataError as ex:
                repeatedKey = ex.args[0].replace("repeated bibliograhpy entry: ", "")

                if repeatedKey != None and repeatedKey:
                    newKeyFirst = repeatedKey + "_" + str(random.randint(1, 101))
                    fileData = fileData.replace(repeatedKey + ",", newKeyFirst + ",", 1)
                    newKeySecond = repeatedKey + "_" + str(random.randint(1, 101))
                    fileData = fileData.replace(
                        repeatedKey + ",", newKeySecond + ",", 1
                    )

                    print(
                        bibFileName + ": repeatedKey",
                        repeatedKey,
                        "replaced by",
                        newKeyFirst,
                        "and",
                        newKeySecond,
                    )

                    loop = True

                    with open(
                        os.path.join(
                            os.path.dirname(os.path.abspath(bibFileName)),
                            "fix_" + os.path.basename(bibFileName),
                        ),
                        "w+",
                    ) as bibFile:
                        bibFile.write(fileData)

    print("                                                     ")
    print("Total:\t\t\t", total)

    print("No Author:\t\t", withoutAuthor)
    print("No Year:\t\t", withoutYear)
    print("No Publisher:\t\t", withoutJornal)

    print("Duplicates:\t\t", duplicates)
    print("Merged:\t\t\t", mergedCount)
    print("Excluded from bib:\t", excludedFromBib)
    print("Final:\t\t\t", len(bibDataOut.entries))

    withoutAbstractList = {i: 0 for i in fileList}
    withoutAbstract = 0
    for entry in bibDataOut.entries.values():
        if logProcess:
            doi = getEntryDOIStr(entry)
            author = getEntryAuthorStr(entry)
            year = getEntryYearStr(entry)
            title = getEntryTitleStr(entry)
            publish = getEntryPublishStr(entry)
            abstract = getEntryAbstractStr(entry)

            # key;source;doi;author;year;title;publish;abstract
            csvFinal.writerow(
                [
                    entry.key,
                    entry.fields["source"],
                    doi,
                    author,
                    year,
                    title,
                    publish,
                    abstract,
                ]
            )

        if not "abstract" in entry.fields:
            withoutAbstract = withoutAbstract + 1
            withoutAbstractList[entry.fields["source"]] = (
                withoutAbstractList[entry.fields["source"]] + 1
            )

    print("without Abstract:\t", withoutAbstract, withoutAbstractList)
    bibDataOut.to_file(fileNamePathOut)

    if logProcess:
        fRemoved.close()
        fFinal.close()


ap = argparse.ArgumentParser()
ap.add_argument("-p", "--folderPath", required=True, help="Bib files folder path")
ap.add_argument(
    "-f",
    "--fileList",
    nargs="*",
    required=False,
    help="bib file name list, e.g. -f IEEE.bib ACM.bib science.bib Springer.bib",
)
ap.add_argument("-o", "--fileNameOut", required=False, help="File name of merged file")
ap.add_argument(
    "-e",
    "--exclude",
    nargs="*",
    required=False,
    help=" bib with entries to be removed from others, e.g. -e FirstExecution.bib SecondExecution.bib",
)
ap.add_argument(
    "-l",
    "--logProcess",
    required=False,
    help="Log processing to CSV files",
    action="store_true",
)

args = vars(ap.parse_args())

print("--folderPath\t", args["folderPath"])
print("--fileNameOut\t", args["fileNameOut"])
print("--fileList\t", args["fileList"])
print("--exclude\t", args["exclude"])
print("--logProcess\t", args["logProcess"])
print("")

run(
    args["folderPath"],
    args["fileList"],
    args["fileNameOut"],
    args["exclude"],
    args["logProcess"],
)
