# PyBibTextTools

* SpringerCsv2Bib 
* GetAbstract
* BibFilesMerge


## Dependencies

Run this command to install the dependencies:
* pip install -r requirements.txt

## SpringerCsv2Bib

Convert Springer CSV file to Bibtext file

### Run

```console
foo@bar:~$ python SpringerCsv2Bib.py -h
usage: SpringerCsv2Bib.py [-h] -c CSVFILENAME -b BIBFILENAME

optional arguments:
  -h, --help            show this help message and exit
  -c CSVFILENAME, --csvFileName CSVFILENAME
                        CSV file name
  -b BIBFILENAME, --bibFileName BIBFILENAME
                        BibText file name
```

### Example

```console
foo@bar:~$ python SpringerCsv2Bib.py -c "Springer.csv" -b "Springer.bib"

File founded: Springer.csv
Processed: 590
Removid without author: 5
Total Final: 585
Saved file: Springer.bib
```

## GetAbstract

This tools get abstract on digital library, its a Magver function, not official.

Obs 1: ACM need use limit parameter, because ACM blocks if you get many abstracts same time.

Obs 2: In my case, I use proxy, because I access in my house by proxy of my university.

### Run

```console
foo@bar:~$ python GetAbstract.py -h
usage: GetAbstract.py [-h] -d {springer,acm,ieee} -f BIBFILENAME [-p PROXY]
                      [-l LIMIT]

optional arguments:
  -h, --help            show this help message and exit
  -d {springer,acm,ieee}, --database {springer,acm,ieee}
                        select database
  -f BIBFILENAME, --bibFileName BIBFILENAME
                        Springer bibFile name
  -p PROXY, --proxy PROXY
                        internet proxy, ex:
                        https://john:password123@palmas.pucrs.br:4001
  -l LIMIT, --limit LIMIT
                        abstract load limit
```

### Example

```console
foo@bar:~$ python GetAbstract.py -d acm -f "ACM.bib" -l 10 -p https://peter:mypass@palmas.pucrs.br:4001

Had Abstract: 85
Url errors: 0
Loaded Abstract: 10
Total Entries: 585
Limit to process: 10
Processed: 95
Left: 490
```

or

```console
foo@bar:~$ python GetAbstract.py -d springer -f "Springer.bib"

Had Abstract: 85
Url errors: 0
Loaded Abstract: 10
Total Entries: 585
Limit to process: 10
Processed: 95
Left: 490
```

## BibFilesMerge

Merge BibTex files and:
- remove duplicate entries 
- in some cases merge information before removing duplicates
- remove entries that not have:
    - author or
    - title or
    - year or
    - journal name or conference name

This tool has been tested with these digital library files:
- ACM Digital Library
- IEEE Xplore
- Scopus
- SpringerLink
- ScienceDirect - ElsevierWeb of Science
- Web of Science (thanks [@dineiar](https://github.com/dineiar) for this)

### Run

```console
foo@bar:~$ python BibFilesMerge.py -h
usage: BibFilesMerge.py [-h] -p FOLDERPATH [-f [FILELIST [FILELIST ...]]]
                        [-o FILENAMEOUT] [-l]

optional arguments:
  -h, --help            show this help message and exit
  -p FOLDERPATH, --folderPath FOLDERPATH
                        Bib files folder path
  -f [FILELIST [FILELIST ...]], --fileList [FILELIST [FILELIST ...]]
                        bib file name list, e.g. -files IEEE.bib ACM.bib
                        science.bib Springer.bib
  -o FILENAMEOUT, --fileNameOut FILENAMEOUT
                        File name of merged file
  -l, --logProcess      Log processing to csv files
```

### Example

```console
foo@bar:~$ python BibFilesMerge.py -p <OUTPUT_FOLDER> -o MyFile.bib -f IEEE.bib ACM.bib science.bib Springer.bib scopus.bib -l

Total: 3253
without Author: 65
without Year: 0
without Jornal or conference or booktitle: 76
Duplicates: 842, merged: 833
Final: 2270
Without abstract: 746
```

The two CSV files created on `<OUTPUT_FOLDER>` by the `-l` switch are:
- `BibFilesMerge_removed.csv`, with columns cause, source, key, doi, author, year, title and publish
- cause is one of: no author, no year, no journal, duplicate of next or duplicate of prev
- `BibFilesMerge_final.csv`, with columns key, doi, author, year, title, publish and abstract

### Load Bib File Error

Sometimes errors occur while reading the bib file. In this case, note at the end of the error line of the bib file. Then edit the bib file and adjust the error. For example:

```console
foo@bar:~$ python BibFilesMerge.py -p "results" -f IEEE.bib ACM.bib science.bib Springer.bib -o "MyFile.bib"

-p  results
-o  MyFile.bib
-f  ['IEEE.bib', 'ACM.bib', 'science.bib', 'Springer.bib']
IEEE.bib
ACM.bib
science.bib
Traceback (most recent call last):
  File "BibFilesMerge.py", line 146, in <module>
    run(args["folderPath"], args["fileList"], args["fileNameOut"])
  File "BibFilesMerge.py", line 63, in run
    bibData = parse_file(os.path.join(folderPath,bibFileName))
  File "./pybtex\pybtex\database\__init__.py", line 865, in parse_file
    return parser.parse_file(file)
  File "./pybtex\pybtex\database\input\__init__.py", line 54, in parse_file
    self.parse_stream(f)
  File "./pybtex\pybtex\database\input\bibtex.py", line 410, in parse_stream
    return self.parse_string(text)
  File "./pybtex\pybtex\database\input\bibtex.py", line 397, in parse_string
    for entry in entry_iterator:
  File "./pybtex\pybtex\database\input\bibtex.py", line 191, in parse_bibliography
    self.handle_error(error)
  File "./pybtex\pybtex\database\input\bibtex.py", line 383, in handle_error
    report_error(error)
  File "./pybtex\pybtex\errors.py", line 78, in report_error
    raise exception
  File "./pybtex\pybtex\database\input\bibtex.py", line 189, in parse_bibliography
    yield tuple(self.parse_command())
  File "./pybtex\pybtex\database\input\bibtex.py", line 222, in parse_command
    self.handle_error(error)
  File "./pybtex\pybtex\database\input\bibtex.py", line 383, in handle_error
    report_error(error)
  File "./pybtex\pybtex\errors.py", line 78, in report_error
    raise exception
  File "./pybtex\pybtex\database\input\bibtex.py", line 220, in parse_command
    self.required([body_end])
  File "./pybtex\pybtex\scanner.py", line 120, in required
    raise TokenRequired(description, self)
pybtex.scanner.TokenRequired: syntax error in line 2264: '}' expected
```

**Bib file Content in line 2264**:

> 2264 note = "Special issue on Assistive Computer Vision and Robotics - "Assistive Solutions for Mobility, Communication and HMI" ",

**just fix it to**: 

> 2264 note = "Special issue on Assistive Computer Vision and Robotics - Assistive Solutions for Mobility, Communication and HMI",
