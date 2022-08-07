import gc
import os
import textwrap
from glob import glob

import PyPDF2
from reportlab.lib.colors import black
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.pdfgen.canvas import Canvas

import codecs
import os
import re
import sys
import pypdftk

from PyPDF2 import PdfFileMerger, PdfFileReader
from pdfrw import PdfReader, PdfWriter


dirs = []
folders = []
pdfs = []
dirFiles = []
files = []

class config():
    SORT = True


def log(msg):
    if msg[:-1] != '\n':
        msg = msg + '\n'
    f = open("pdfbook.log", 'a')
    f.write(msg)
    f.close()
    return


# returns a list of directories and filenames of pdf files without ".pdf" extension
# filenames are appended with "*"
def listdirs(basedir, ignore):
    cf = config()
    for it in os.scandir(basedir):
        if it.is_dir():
            dirs.append(str(it.path))
            folders.append(str(it.path))
            dirfiles = os.listdir(it)
            if cf.SORT:
                dirfiles.sort()
                log("sorting")
                log(str(dirfiles))
            for file in dirfiles:
                if len(file) >= 4 and file[-4:] == ".pdf":
                    #ignore is so that you can prepend a file with some sorting chars that dont get shown TODO fix this
                    pdfs.append(str(it.path) + '/' + str(file[ignore:]))
                    dirs.append(str(it.path) + "/" + str(file[ignore:-4]) + "*")
                    #print(str(it.path) + "/" + str(file))
            listdirs(it, ignore)

    return dirs


# makes a TOC for all pdf files in a directory sructure
def makeBook(args):
    cf = config()
    startdir = str(os.getcwd())
    datadir = str(os.getcwd())


    PAGEWIDTH = 95  # total characers to build each line
    MAXDEPTH = 7  # max depth to build TOC
    INDENT = 2  # num chars to indent each level
    PDFCOMPRESS = False
    VERBOSE = False
    DEBUG = False
    IGNORE = 0
    DOCTITLE = ""

    if len(args) > 1:
        for a in args[1:]:
            if a[0] == '-':
                if 'c' in a:
                    PDFCOMPRESS = True
                if 'v' in a:
                    VERBOSE = True
                if 'd' in a:
                    DEBUG = True
                if 's' in a:
                    cf.SORT = True

            else:
                opt = a.split('=')
                if len(opt) == 2:
                    if opt[0] == 'startdir':
                        startdir = opt[1]
                    if opt[0] == 'pagewidth':
                        PAGEWIDTH = int(opt[1])
                    if opt[0] == 'maxdepth':
                        MAXDEPTH = int(opt[1])
                    if opt[0] == 'indent':
                        INDENT = int(opt[1])
                    if opt[0] == 'ignore':
                        IGNORE = int(opt[1])
                    if opt[0] == 'doctitle':
                        DOCTITLE = str(opt[1])


    log('DEBUG : ' + str(DEBUG))
    log('VERBOSE : ' + str(VERBOSE))
    log('PDFCOMPRESS : ' + str(PDFCOMPRESS))
    log('startdir : ' + startdir)
    log('datadir : ' + datadir)
    log('pagewidth : ' + str(PAGEWIDTH))
    log('maxdepth : ' + str(MAXDEPTH))
    log('indent : ' + str(INDENT))
    log('sort : ' + str(cf.SORT))
    log('ignore : ' + str(IGNORE))
    log('doctitle : ' + str(DOCTITLE))

    #startdir = "/home/gareth/Documents/HAZAR 2022/"
    # file = PdfFileWriter()
    tocpages = 1  # count of number of toc pages

    merger = PdfWriter()
    merger.addpages(PdfReader(datadir+"/cover.pdf").pages)
    tocpages = tocpages + len(PdfReader(datadir+"/cover.pdf").pages)

    pagecount = 1
    stack = []
    c = startdir  # '/home/gareth/Downloads/'
    listdir = []
    tmpDirs = listdirs(startdir, IGNORE)
    if DEBUG:
        print("PDFs Found")
        print("==========")
        for p in pdfs:
            print(p)

        print("Folders Found")
        print("=============")
        for f in folders:
            print(f)

    lines = []
    y = 10
    mycanvas = Canvas(datadir + '/toc.pdf', pagesize=A4)
    mycanvas.setFont("Courier", 8)
    mycanvas.setFillColor(black)
    if tmpDirs:
        d = (tmpDirs[0].replace(c, '')).split('/')  # setup working variables
        depth = len(d)
        startCount = depth - 1
        count = depth
        lastDepth = depth - 1
        oldpagenum = 1

        bbb = open(datadir + "/b.txt", "w")
        bbb.write('+"TOC"|0\n')
        for z in tmpDirs:
            x = z
            altEntry = ''
            oldpagenum = pagecount
            if z[-1:] == '*':
                q = "'" + z.replace('*', '.pdf') + "'"
                x = str(z.replace('*', '.pdf'))
                txtf = str(z.replace('*', '.txt'))
                if os.path.exists(txtf):
                    log('Found alternate title file : ' + txtf)
                    f = open(txtf, 'r')
                    altEntry = f.readline().replace('\n','')
                    log("AltEntry found as : "+altEntry)
                    f.close()
                if PDFCOMPRESS:
                    pypdftk.uncompress(q, "./tmp.pdf")
                    pypdftk.compress("./tmp.pdf", q)
                #w = q.replace("'","")
                #z = w.replace(" ","\ ")
                #fieldList = pypdftk.dump_data_fields(z)
                #q = q
                if DEBUG:
                    print("READING:" + x)
                pdf = PdfReader(x)
                oldpagenum = pagecount
                pagecount = pagecount + len(pdf.pages)
            l = z.replace(c, '')  # strip off directory info above the selected dir
            line = ""
            d = l.split('/')
            depth = len(d)
            delta = depth - lastDepth
            if altEntry:
                entry = altEntry + '*'
            else:
                entry = str(d[-1:][0])
            # strip out dir or filename for toc entry
            if delta > 0:  # datadir + '/toc.pdf' # deeper nesting
                for pp in range(abs(delta)):
                    stack.append(1)
                count = 1
            if delta < 0:  # shallower nesting
                for pp in range(abs(delta)):
                    count = stack.pop()
                count = stack.pop()
                stack.append(count + 1)
            if delta == 0:  # same depth
                count = stack.pop()
                stack.append(count + 1)
            bbb.write(str('+'))
            for level in range(depth - 1):  # make indent
                bbb.write(str('+'))
                for i in range(INDENT):
                    line = line + " "
            for level in range(depth):
                line = line + str(stack[level])  # add level number
                if depth - level > 1:  # add "." if not last level
                    line = line + "."

            count = count + 1  # inc count
            if entry[-1:] != "*":
                line = line + " " + entry
                titlepage = line
                for fill in range(PAGEWIDTH - len(line)):  # fill in blanks to mke line width
                    line = line + " "
                # insert page
                pagecount = pagecount + 1
            if entry[-1:] == "*":
                for fill in range(PAGEWIDTH - len(line) - len(entry) - 1):  # fill in blanks to mke line width
                    line = line + " "
                line = line + " " + entry
            lastDepth = depth
            bbb.write(str('"' + str(entry).replace("*", "") + '"' + "|" + str(oldpagenum) + "\n"))
            line = line + '{:>5}'.format(str(oldpagenum + tocpages + 1))  # TODO this is too early
            if (depth <= MAXDEPTH):  # only show if less than max depth
                if DEBUG:
                    print(line)
                lines.append(line.replace("*", ""))
                wrapper = textwrap.TextWrapper(width=100)
                text = wrapper.wrap(text=line)
                for textline in text:
                    mycanvas.drawString(0.75 * inch, y * inch, str(textline))
                    y = y - 0.15
                if y < 2.0:
                    y = 10.0
                    mycanvas.showPage()
                    mycanvas.setFont("Courier", 8)
                    mycanvas.setFillColor(black)
                    tocpages = tocpages + 1

        bbb.close()
    mycanvas.save()

    merger.addpages(PdfReader(datadir + "/toc.pdf").pages)
    for l in tmpDirs:
        d = l.replace('*', '.pdf').split('/')
        entry = str(d[-1:][0])

        if l[-1:] != '*':
            canvas = Canvas(datadir + '/blankpage.pdf', pagesize=A4)
            canvas.setFont("Courier", 20)
            canvas.setFillColor(black)
            wrapper = textwrap.TextWrapper(width=40)
            text = wrapper.wrap(text=entry)
            y = 10.0
            for textline in text:
                canvas.drawString(0.75 * inch, y * inch, str(textline).replace("*", ""))
                canvas.bookmarkPage(str(textline).replace("*", ""))
                # canvas.showPage()
                canvas.addOutlineEntry(str(textline).replace("*", ""), str(textline).replace("*", ""), level=0)
                y = y - 0.3
            # Save the PDF file

            canvas.save()

        x = datadir + "/blankpage.pdf"
        if l[-1:] == '*':
            x = l.replace('*', '.pdf')
        pdf = PdfReader(x)
        # pdf = PdfReader(x).pages
        print(str(len(pdf.pages)) + " : ", x)
        merger.addpages(pdf.pages)

    merger.write(datadir + "/book.pdf")
    gc.collect()

    pdfMark = open("pdfmark.txt","w")
    for pn in range(2, pagecount+tocpages):
        pageNumPdfMark1 = "[ /SrcPg XXXX /Q 0 /Rect [ 5 5 72 20 ] /Color [1 1 1] /Contents (Page XXXX) /DA (/Helv 10 Tf) /BS << /W 0 >> /Subtype /FreeText /ANN pdfmark".replace("XXXX", str(pn))
        pageNumPdfMark2 = "[ /SrcPg XXXX /Q 0 /Rect [ 100 5 500 20 ] /Color [1 1 1] /Contents (ZZZZ) /DA (/Helv 10 Tf) /BS << /W 0 >> /Subtype /FreeText /ANN pdfmark".replace("XXXX", str(pn)).replace("ZZZZ", DOCTITLE)
        pdfMark.write(pageNumPdfMark1 + "\n")
        pdfMark.write(pageNumPdfMark2 + "\n")

    pdfMark.close()


    print("Bookmarking - be patient")
    tree = get_bookmarks_tree(tocpages, datadir + "/b.txt")
    add_bookmarks(datadir + "/book.pdf", tree, datadir + "/out.pdf")

    print("Adding page numbers with ghostscript")

    os.system("gs -o final.pdf -sDEVICE=pdfwrite -dPDFSETTINGS=/prepress out.pdf pdfmark.txt")

    print("Finished - final.pdf")


def add_bookmarks(pdf_in_filename, bookmarks_tree, pdf_out_filename=None):
    """Add bookmarks to existing PDF files
    Home:
        https://github.com/RussellLuo/pdfbookmarker
    Some useful references:
        [1] http://pybrary.net/pyPdf/
        [2] http://stackoverflow.com/questions/18855907/adding-bookmarks-using-pypdf2
        [3] http://stackoverflow.com/questions/3009935/looking-for-a-good-python-tree-data-structure
    """
    pdf_in = PdfFileReader(pdf_in_filename)

    # merge `pdf_in` into `pdf_out`, using PyPDF2.PdfFileMerger()
    pdf_out = PdfFileMerger()
    pdf_out.append(pdf_in, import_bookmarks=False)

    # copy/preserve existing document info
    doc_info = pdf_in.getDocumentInfo()
    if doc_info:
        pdf_out.addMetadata(doc_info)

    def crawl_tree(tree, parent):
        for title, page_num, subtree in tree:
            current = pdf_out.addBookmark(title, page_num, parent)  # add parent bookmark
            if subtree:
                crawl_tree(subtree, current)

    crawl_tree(bookmarks_tree, None)    # add bookmarks into `pdf_out` by crawling `bookmarks_tree`


    # get `pdf_out_filename` if it's not specified
    if not pdf_out_filename:
        name_parts = os.path.splitext(pdf_in_filename)
        pdf_out_filename = name_parts[0] + '-new' + name_parts[1]

    # write all data to the given file
    pdf_out.write(pdf_out_filename)
    pdf_out.close()

    return pdf_out_filename


def get_bookmarks_tree(offset, bookmarks_filename):
    """Get bookmarks tree from TEXT-format file
    Bookmarks tree structure:
        #>>> get_bookmarks_tree('sample_bookmarks.txt')
        [(u'Foreword', 0, []), (u'Chapter 1: Introduction', 1, [(u'1.1 Python', 1, [(u'1.1.1 Basic syntax', 1, []), (u'1.1.2 Hello world', 2, [])]), (u'1.2 Exercises', 3, [])]), (u'Chapter 2: Conclusion', 4, [])]
    The above test result may be more readable in the following format:
        [
            (u'Foreword', 0, []),
            (u'Chapter 1: Introduction', 1,
                [
                    (u'1.1 Python', 1,
                        [
                            (u'1.1.1 Basic syntax', 1, []),
                            (u'1.1.2 Hello world', 2, [])
                        ]
                    ),
                    (u'1.2 Exercises', 3, [])
                ]
            ),
            (u'Chapter 2: Conclusion', 4, [])
        ]
    Thanks Stefan, who share us a perfect solution for Python tree.
    See http://stackoverflow.com/questions/3009935/looking-for-a-good-python-tree-data-structure
    Since dictionary in Python is unordered, I use list instead now.
    Also thanks Caicono, who inspiring me that it's not a bad idea to record bookmark titles and page numbers by hand.
    See here: http://www.caicono.cn/wordpress/2010/01/%E6%80%9D%E8%80%83%E5%85%85%E5%88%86%E5%86%8D%E8%A1%8C%E5%8A%A8-python%E8%AF%95%E6%B0%B4%E8%AE%B0.html
    And I think it's the only solution for scan version PDFs to be processed automatically.
    """

    # bookmarks tree
    tree = []

    # the latest nodes (the old node will be replaced by a new one if they have the same level)
    #
    # each item (key, value) in dictionary represents a node
    # `key`: the level of the node
    # `value`: the children list of the node
    latest_nodes = {0: tree}

    prev_level = 0
    for line in codecs.open(bookmarks_filename, 'r', encoding='utf-8'):
        line = line.strip()
        if line.startswith('//'):
            try:
                offset = int(line[2:])
            except ValueError:
                pass
            continue
        res = re.match(r'(\+*)\s*?"([^"]+)"\s*\|\s*(\d+)', line)
        if res:
            pluses, title, page_num = res.groups()
            cur_level = len(pluses)  # plus count stands for level
            cur_node = (title, int(page_num) - 1 + offset, [])

            if not (0 < cur_level <= prev_level + 1):
                raise Exception('plus (+) count is invalid here: %s' % line)
            else:
                # append the current node into its parent node (with the level `cur_level` - 1)
                latest_nodes[cur_level - 1].append(cur_node)

            latest_nodes[cur_level] = cur_node[2]
            prev_level = cur_level

    return tree


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    if os.path.exists("pdfbook.log"):
        os.remove("pdfbook.log")
    makeBook(sys.argv)
