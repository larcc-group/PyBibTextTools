import os
import shutil
import sys
from html import unescape
import csv
import argparse
import unidecode
import random
sys.path.insert(0, "./pybtex/")
from pybtex.database import BibliographyData, Entry, BibliographyDataError
from pybtex.database import parse_file, parse_string


merged_count = 0

def merge_entry(original, novo):
    global merged_count
    merged = False

    year_out = int(str(original.rich_fields["year"]))
    year = int(str(novo.rich_fields["year"]))
    if year < year_out:
        original.fields["year"] = novo.fields["year"]
        merged = True

    for novo_key in novo.fields:
        if novo_key not in original.fields:
            original.fields[novo_key] = novo.fields[novo_key]
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
        merged_count += 1

    original.fields["source"] = original.fields["source"] + \
        ";" + novo.fields["source"]

    return original


def get_entry_DOI(entry):
    if "doi" in entry.fields:
        return str(entry.rich_fields["doi"]).replace("https://doi.org/", "")
    return ""


def get_entry_author(entry):
    author = ""
    if "author" in entry.persons:
        author = " and ".join(
            [
                "".join(p.last_names) + ", " + "".join(p.first_names)
                for p in entry.persons["author"]
            ]
        )
    return author


def get_entry_year(entry):
    year = ""
    if "year" in entry.fields:
        year = int(str(entry.rich_fields["year"]))
        if year == 0:
            year = ""
    return year


def get_entry_title(entry):
    title = ""
    if "title" in entry.fields:
        title = str(entry.rich_fields["title"])
    return title


def get_entry_publish(entry):
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


def get_entry_abstract(entry):
    abstract = ""
    if "abstract" in entry.fields:
        abstract = entry.fields["abstract"]
    if abstract != "":
        abstract = unescape(abstract).replace("\\%", "%")
    return abstract


def clear_string(x):
    return (
        x.lower()
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


def is_duplicated(entry_out, entry, verify_doi=False):
    if verify_doi:
        doi = get_entry_DOI(entry)
        if doi:
            doiOut = get_entry_DOI(entry_out)
            if doiOut and doi == doiOut:
                return True

    if clear_string(entry_out.fields["title"].lower()) == clear_string(
        entry.fields["title"].lower()
    ):
        year = int(str(entry.rich_fields["year"]))
        year_out = int(str(entry_out.rich_fields["year"]))
        diff = abs(year - year_out)
        if diff == 0:
            return True
        elif diff == 1 or diff == 2:
            try:
                last_name = unidecode.unidecode(
                    entry.persons["author"][0].last_names[0]
                ).lower()
            except:
                last_name = ""

            try:
                last_name_out = unidecode.unidecode(
                    entry_out.persons["author"][0].last_names[0]
                ).lower()
            except:
                last_name_out = ""

            try:
                first_name = unidecode.unidecode(
                    entry.persons["author"][0].firstNames[0]
                ).lower()
            except:
                first_name = ""

            try:
                first_name_out = unidecode.unidecode(
                    entry_out.persons["author"][0].firstNames[0]
                ).lower()
            except:
                first_name_out = ""

            if (
                last_name == last_name_out
                or last_name == first_name_out
                or last_name_out == first_name
            ):
                return True
    return False


def custom_parse_file(file_bib):
    print(file_bib, " " * 30)
    loop = True
    while loop:
        loop = False
        try:
            bib_data = parse_file(file_bib)
            return bib_data
        except BibliographyDataError as ex:
            repeated_key = ex.args[0].replace(
                "repeated bibliograhpy entry: ", "")

            if not os.path.isfile(file_bib + ".bkp"):
                shutil.copyfile(file_bib, file_bib + ".bkp")

            if repeated_key:
                with open(file_bib, "r") as file:
                    file_data = file.read()

                while file_data.find(repeated_key + ",") > -1:
                    new_key = repeated_key + "_" + str(random.randint(1, 101))
                    file_data = file_data.replace(
                        repeated_key + ",", new_key + ",", 1)

                    print(
                        file_bib + ": repeatedKey", repeated_key, "replaced by", new_key
                    )

                with open(file_bib, "w+") as file:
                    file.write(file_data)

                loop = True


def run(folder_path, file_list, file_name_out, exclude_list, log_process):
    global merged_count

    if log_process:
        f_removed = open(
            os.path.join(folder_path, "BibFilesMerge_removed.csv"),
            "w",
            encoding="utf-8",
        )
        csv_removed = csv.writer(
            f_removed, quotechar='"', quoting=csv.QUOTE_ALL)
        csv_removed.writerow(
            ["cause", "source", "key", "doi", "author", "year", "title", "publish"]
        )
        f_final = open(
            os.path.join(folder_path, "BibFilesMerge_final.csv"), "w", encoding="utf-8"
        )
        csv_final = csv.writer(f_final, quotechar='"', quoting=csv.QUOTE_ALL)
        csv_final.writerow(
            ["key", "source", "doi", "author", "year",
                "title", "publish", "abstract"]
        )

    file_name_path_out = os.path.join(folder_path, file_name_out)
    bib_data_out = BibliographyData()

    total = 0
    merged_count = 0
    without_author = 0
    without_year = 0
    without_jornal = 0
    duplicates = 0
    excluded_from_bib = 0

    bib_data_to_exclude = {}

    for bib_file_name in file_list:
        bib_data = custom_parse_file(bib_file_name)
        print(
            "-" * 3,
            bib_file_name + ":",
            len(bib_data.entries.values()),
            " " * 30,
        )

        for entry in bib_data.entries.values():
            total += 1

            doi = get_entry_DOI(entry)
            author = get_entry_author(entry)
            year = get_entry_year(entry)
            title = get_entry_title(entry)
            publish = get_entry_publish(entry)

            found_entry_to_exclude = False
            for bib_file_name_exclude in exclude_list:
                if bib_file_name_exclude not in bib_data_to_exclude:
                    bib_data = custom_parse_file(bib_file_name_exclude)
                    bib_data_to_exclude[
                        bib_file_name_exclude
                    ] = bib_data.entries.values()

                for entry_exclude in bib_data_to_exclude[bib_file_name_exclude]:
                    if is_duplicated(entry_exclude, entry):
                        excluded_from_bib += 1
                        found_entry_to_exclude = True
                        break

                if found_entry_to_exclude:
                    break

            if found_entry_to_exclude:
                continue

            if not author:
                without_author += 1
                if log_process:
                    # cause;source;key;doi;author;year;title;publish
                    csv_removed.writerow(
                        [
                            "no author",
                            bib_file_name,
                            entry.key,
                            doi,
                            author,
                            year,
                            title,
                            publish,
                        ]
                    )
            elif not year:
                without_year = without_year + 1
                if log_process:
                    # cause;source;key;doi;author;year;title;publish
                    csv_removed.writerow(
                        [
                            "no year",
                            bib_file_name,
                            entry.key,
                            doi,
                            author,
                            year,
                            title,
                            publish,
                        ]
                    )
            elif not publish:
                without_jornal = without_jornal + 1
                if log_process:
                    # cause;source;key;doi;author;year;title;publish
                    csv_removed.writerow(
                        [
                            "no journal",
                            bib_file_name,
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
                print("Key " + key + " " * 30 + "\r", end="", flush=True)

                entry.fields["source"] = bib_file_name
                old_entry = None

                for entry_out in bib_data_out.entries.values():
                    if is_duplicated(entry_out, entry, True):
                        old_entry = entry_out
                        break

                if old_entry != None:
                    duplicates += 1

                    if log_process:
                        # cause;source;key;doi;author;year;title;publish
                        csv_removed.writerow(
                            [
                                "duplicate of next",
                                bib_file_name,
                                entry.key,
                                doi,
                                author,
                                year,
                                title,
                                publish,
                            ]
                        )

                        doi = get_entry_DOI(old_entry)
                        author = get_entry_author(old_entry)
                        year = get_entry_year(old_entry)
                        title = get_entry_title(old_entry)
                        publish = get_entry_publish(old_entry)
                        csv_removed.writerow(
                            [
                                "duplicate of prev",
                                old_entry.fields["source"],
                                old_entry.key,
                                doi,
                                author,
                                year,
                                title,
                                publish,
                            ]
                        )

                    bib_data_out.entries[old_entry.key] = merge_entry(
                        old_entry, entry)
                else:
                    while key in bib_data_out.entries.keys():
                        key = key + "_a"
                    bib_data_out.entries[key] = entry

    print(" " * 50)
    print("Total:\t\t\t", total)

    print("No Author:\t\t", without_author)
    print("No Year:\t\t", without_year)
    print("No Publisher:\t\t", without_jornal)

    print("Duplicates:\t\t", duplicates)
    print("Merged:\t\t\t", merged_count)
    print("Excluded from bib:\t", excluded_from_bib)
    print("Final:\t\t\t", len(bib_data_out.entries))

    without_abstract_list = {i: 0 for i in file_list}
    without_abstract = 0
    for entry in bib_data_out.entries.values():
        if log_process:
            doi = get_entry_DOI(entry)
            author = get_entry_author(entry)
            year = get_entry_year(entry)
            title = get_entry_title(entry)
            publish = get_entry_publish(entry)
            abstract = get_entry_abstract(entry)

            # key;source;doi;author;year;title;publish;abstract
            csv_final.writerow(
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
            without_abstract = without_abstract + 1
            without_abstract_list[entry.fields["source"]] = (
                without_abstract_list[entry.fields["source"]] + 1
            )

    print("Without Abstract:\t", without_abstract, without_abstract_list)
    bib_data_out.to_file(file_name_path_out, bib_format="bibtex")

    if log_process:
        f_removed.close()
        f_final.close()


ap = argparse.ArgumentParser()
ap.add_argument("-p", "--folderPath", required=True,
                help="Bib files folder path")
ap.add_argument(
    "-f",
    "--fileList",
    nargs="*",
    required=False,
    help="bib file name list, e.g. -f IEEE.bib ACM.bib science.bib Springer.bib",
)
ap.add_argument("-o", "--fileNameOut", required=False,
                help="File name of merged file")
ap.add_argument(
    "-e",
    "--exclude",
    nargs="*",
    default=[],
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
