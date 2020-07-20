import os
import sys
import argparse
import re
from urllib.request import Request, urlopen
from html.parser import HTMLParser
import urllib.request
import unidecode
sys.path.insert(0, "./pybtex/")
from pybtex.database import BibliographyData, Entry
from pybtex.database import parse_file


def run(database, bib_file_name, proxy, limit):
    print("=========================================")
    print("DATABASE ", database, limit)
    print("=========================================")

    if not os.path.isfile(bib_file_name):
        print("File not found: ", bib_file_name)
        return

    bib_data = parse_file(bib_file_name)

    processed = 0
    url_error = 0
    had_abstract = 0
    get_abstract = 0
    without_acm_id = 0

    for entry in bib_data.entries.values():
        processed = processed + 1

        print(processed, entry.key + ": ", end="", flush=True)

        if "abstract" in entry.fields.keys():
            had_abstract = had_abstract + 1
            print("had abstract")

        elif database == "acm" and not "acmid" in entry.fields.keys():
            without_acm_id = without_acm_id + 1

        else:

            if database == "springer":
                site = entry.fields["url"]
                if site.find("chapter") != -1:
                    site = "http://link.springer.com/chapter/"
                else:
                    site = "http://link.springer.com/article/"

                site = site + entry.key

            elif database == "acm":
                site = "https://dl.acm.org/tab_abstract.cfm?id=" + \
                    entry.fields["acmid"]

            elif database == "ieee":
                site = "https://ieeexplore.ieee.org/document/" + entry.key + "/"

            try:
                if not proxy == None:
                    # Use proxy.
                    proxy_handler = urllib.request.ProxyHandler(
                        {"https": proxy})
                    opener = urllib.request.build_opener(proxy_handler)
                    urllib.request.install_opener(opener)

                req = Request(site, headers={"User-Agent": "Mozilla/5.0"})
                html = urlopen(req).read()
                html_text = html.decode("utf-8")

                if database == "springer":
                    inicio = html_text.find(
                        '<strong class="EmphasisTypeBold ">Abstract.</strong>'
                    )
                    if inicio == -1:
                        inicio = html_text.find(
                            '<h2 class="Heading">Abstract</h2>')
                    if inicio == -1:
                        inicio = html_text.find(
                            '<h2 class="Heading">Abstract.</h2>')
                    if inicio == -1:
                        inicio = html_text.find("Abstract")

                    html_text = html_text[inicio:]

                    inicio = html_text.find("<p ")
                    if inicio > -1 and inicio < 50:
                        html_text = html_text[inicio:]

                    final = html_text.find("</section>")
                    subhtml_text = html_text[0:final]

                    texto = re.sub("<.*?>", "", subhtml_text)

                elif database == "acm":
                    texto = re.sub("<.*?>", "", html_text)

                elif database == "ieee":
                    inicio = html_text.find('"abstract":')
                    subtexto = texto[inicio:]
                    abstract_split = subtexto.split('"')
                    if len(abstract_split) >= 3:
                        texto = abstract_split[3]

                if texto == "":
                    print("Abstract not found")
                else:
                    print("Loaded")
                    entry.fields["abstract"] = texto

                entry.fields["url"] = site
                if database == "springer":
                    entry.fields["doi"] = entry.key

                bib_data.entries[entry.key] = entry
                get_abstract = get_abstract + 1

            except:
                print("url error ", sys.exc_info())
                url_error = url_error + 1

            if get_abstract >= limit:
                break

    print("")
    print("Had Abstract: ", had_abstract)
    print("Url errors ", url_error)
    if without_acm_id > 0:
        print("Without ACM id: ", without_acm_id)

    print("Loaded Abstract: ", get_abstract)
    print("Total Entries: ", len(bib_data.entries))
    print("Limit to process: ", limit)
    print("Processed: ", processed)
    if processed < len(bib_data.entries):
        print("Left: ", len(bib_data.entries) - processed)

    bib_data.to_file(bib_file_name, bib_format="bibtex")


ap = argparse.ArgumentParser()
ap.add_argument(
    "-d",
    "--database",
    choices=["springer", "acm", "ieee"],
    required=True,
    help="select database",
)
ap.add_argument("-f", "--bibFileName", required=True,
                help="Springer bibFile name")

ap.add_argument(
    "-p",
    "--proxy",
    required=False,
    help="internet proxy, ex: https://john:password123@palmas.pucrs.br:4001",
)
ap.add_argument(
    "-l", "--limit", required=False, help="abstract load limit", default=9999, type=int
)

args = vars(ap.parse_args())

run(args["database"], args["bibFileName"], args["proxy"], args["limit"])
