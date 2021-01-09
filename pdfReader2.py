from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfpage import PDFTextExtractionNotAllowed
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice
from pdfminer.layout import LAParams, LTTextLine
from pdfminer.converter import PDFPageAggregator
import pdfminer

import os
import csv
import re

directory = r"C:\Users\Student\Desktop\currentSets"
os.chdir(directory)

global pageNum

# csvname="outputscrape.csv"

# resets

# print (extracted_text.encode("utf-8"))
def writeCSV(row_text, csvname):  # list
    """writes 1 row to csv
    Args:
        row_text (list): comma separated list representing the features to record
        csvname (string): csv filename
    """
    # global csvname
    # print(row_text)
    csvWriter = csv.writer(open("output/" + csvname, "a", encoding="utf-8"), lineterminator='\n')
    csvWriter.writerow(row_text)


def parsePDFs(directory):
    """parses each pdf in the specified directory and writes to csv output file
    Args:
        directory (string): working directory
    Raises:
        PDFTextExtractionNotAllowed: if document does not allow text extraction
    """
    with open("output/guesses.csv", "w", encoding="utf-8") as fil:
        fil.write("filename, score, text\n")
    for filename in os.listdir(directory):
        if filename.endswith(".pdf"):
            csvfilename = filename[0:-4] + ".csv"
            with open("output/" + filename[0:-4] + ".csv", "w", encoding="utf-8") as f:
                # writes header
                f.write(
                    "filename,x0,y0,x1,y1,width,height,charWidth, charHeight,hasNum, numNum, dash,decimal,numChar,"
                    "regex,score,text,drawing_no,page_no\n")

            # Create a PDF parser object associated with the file object.
            fp = open(directory + filename, 'rb')  # read pdfs
            parser = PDFParser(fp)

            # Create a PDF document object that stores the document structure.
            # Password for initialization as 2nd parameter
            document = PDFDocument(parser)

            # Check if the document allows text extraction. If not, abort.
            if not document.is_extractable:
                raise PDFTextExtractionNotAllowed

            # Create a PDF resource manager object that stores shared resources.
            rsrcmgr = PDFResourceManager()

            # Create a PDF device object.
            device = PDFDevice(rsrcmgr)

            # BEGIN LAYOUT ANALYSIS
            # Set parameters for analysis.
            laparams = LAParams()

            # Create a PDF page aggregator object.
            device = PDFPageAggregator(rsrcmgr, laparams=laparams)

            # Create a PDF interpreter object.
            interpreter = PDFPageInterpreter(rsrcmgr, device)

            global pageNum
            pageNum = 0

            # loop over all pages in the document
            for page in PDFPage.create_pages(document):
                # increase the page number for each page
                pageNum += 1
                # read the page into a layout object
                interpreter.process_page(page)  # doesn't return anything
                layout = device.get_result()
                # width of page , print(layout.width)
                # print(type(layout))

                # extract text from this object
                # parse_obj(layout)
                ratio = 0.25
                text, score = find_drawing_num(layout, get_region(layout, ratio), csvfilename)
                writeCSV([filename, str(score), str(text)], "guesses.csv")
                print(score, text)

            # close the pdf file
            fp.close()
        else:
            continue
    # Open a PDF file.
    # fp = open('drawings/3.pdf', 'rb')


def find_drawing_num(pdf_node, bbox, filename):
    """Recursive function to find drawing number based on a scoring system dependent on attributes by recursing through the pdf tree
       until we get to a text line
    Args:
        pdf_node (object): pdfminer object
        bbox (tuple): Bounding coordinates of the region of interest (x0,y0); not to be confused with bbox,
                     the inherent attribute of pdfminer objects that specifies the bounding region of a textline.
        filename (string): csv filename to output pdf text
    Returns:
        tuple: containing the score of the text and the text itself
    """
    score = 0
    text = ''
    # returns the drawing number guess and the score
    if isinstance(pdf_node, LTTextLine):

        # attributes list for 1 row to be recorded in csv
        att = get_attrib(pdf_node, filename[0:-4] + ".pdf")
        # character count
        score = getScore(pdf_node)
        text = getText(pdf_node)

        # write to csvs here
        writeCSV(att, filename)  # raw data, filename here refers to the csv filename, not pdf filename

        # filename, regex, score, text
        # att = [filename[0:-4]+".pdf", str(int(isRegEx(pdf_node))), str(score), str(text)]
        # list of guesses from each page compiled to a csv, based on highest score

        return text, score

    elif in_region(pdf_node, bbox):
        if hasattr(pdf_node, "_objs"):
            for child in pdf_node._objs:
                new_text, new_score = find_drawing_num(child, bbox, filename)
                if new_score >= score:
                    score = new_score
                    text = new_text
    return text, score


def get_region(pdf_node, ratio):
    """Specifies the area of interest in the pdf. For example if a pdf is 1000 x 1000 pixels, a ratio of 0.5 would provide the bottom
       right corner (1/4 of the page area)
    Args:
        pdf_node (object): pdfminer object, layout should be passed in here to cover the entire pdf page
        ratio (double): ratio of the x and y coordinates of interest
    Returns:
        [type]: [description]
    """
    w = pdf_node.width
    h = pdf_node.height
    return ((1 - ratio) * w, (ratio) * h)


def in_region(pdf_node, bbox):
    """Determines if the textline is in the area of interest (AOI) (ex: bottom 8th of the page).
    Args:
        pdf_node (object): pdfminer object
        bbox (tuple): area of interest (x0,y0)
    Returns:
        boolean: if in AOI
    """
    if (pdf_node.x1) >= bbox[0]:
        if (pdf_node.y0) <= bbox[1]:
            return True
    return False


def getText(pdf_node):
    """Formats text to get rid of new line at the end
    Args:
        pdf_node (object): pdfminer object, should pass in a pdf.LTTextLine obj to read text lines.
    Returns:
        formatted text
    """
    return pdf_node.get_text().replace('\n', '')


def hasDecimal(pdf_node):
    """Determines if decimal is present in text
    Args:
        pdf_node (object): pdfminer object, should pass in a pdf.LTTextLine obj to read text lines.
    Returns:
        boolean : if has decimal in text
    """
    if "." in pdf_node.get_text():
        return True
    return False


def hasDash(pdf_node):
    """Determines if dash is present in text
    Args:
        pdf_node (object): pdfminer object, should pass in a pdf.LTTextLine obj to read text lines.
    Returns:
        boolean : if has dash in text
    """
    if "-" in pdf_node.get_text():
        return True
    return False


def hasNumber(pdf_node):
    """Determines if digits are present in text
    Args:
        pdf_node (object): pdfminer object, should pass in a pdf.LTTextLine obj to read text lines.
    Returns:
        boolean : if has digit in text
    """
    return any(char.isdigit() for char in pdf_node.get_text())


def getNumNum(pdf_node):
    """Returns number of digits present in text
    Args:
        pdf_node (object): pdfminer object, should pass in a pdf.LTTextLine obj to read text lines.
    Returns:
        int : number of digits in text
    """
    count = 0
    for char in pdf_node.get_text():
        if char.isdigit():
            count += 1
    return count

def getNumChar(pdf_node):
    # checks for newline at end of textline
    if (pdf_node._objs[-1].get_text() == "\n"):
        numChar = len(pdf_node._objs) - 1
    else:
        numChar = len(pdf_node._objs)
    return numChar

def get_attrib(pdf_node, filename):
    """returns list with information on the text represented by pdf_node
    Args:
        pdf_node (object): pdfminer object, should pass in a pdf.LTTextLine obj to read text lines.
        filename (string): pdf file name
    Returns:
        list: [filename,x0,y0,x1,y1,width,height,charWidth, charHeight,hasNum, numNum, dash,decimal,numChar,regex, score,text]
    """
    # returns list with order of attributes
    # filename,x0,y0,x1,y1,width,height,charWidth, charHeight,hasNum, numNum, dash,decimal,numChar,regex, score,text

    # # checks for newline at end of textline
    # if (pdf_node._objs[-1].get_text() == "\n"):
    #     numChar = len(pdf_node._objs) - 1
    # else:
    #     numChar = len(pdf_node._objs)
    hasNum = ""
    numNum = ""

    text = getText(pdf_node)
    score = getScore(pdf_node)
    # does textline have a number? If so, set to 1 and record number of digits as numNum
    if hasNumber(pdf_node):
        hasNum = "1"
        numNum = str(getNumNum(pdf_node))
    else:
        hasNum = "0"
        numNum = "0"

        # filename,x0,y0,x1,y1,width,height,charWidth, charHeight,hasNum, numNum, dash,decimal,numChar,regex, score,text
    att = [str(filename), str(pdf_node.x0), str(pdf_node.y0), str(pdf_node.x1), \
           str(pdf_node.y1), str(pdf_node.width), str(pdf_node.height), \
           str(pdf_node._objs[0].width), str(pdf_node._objs[0].height), hasNum, numNum, str(int(hasDash(pdf_node))), \
           str(int(hasDecimal(pdf_node))), getNumChar(pdf_node), str(int(isRegEx(pdf_node))), score, text, "0", str(pageNum)]

    return att


def isRegEx(pdf_node):
    """returns if satisfies regex
    Args:
        pdf_node (object): pdfminer object
    Returns:
        bool:
    """
    pattern = r"\b[a-zA-Z]{1,3}[1-9]{0,3}\s?[.-]?\s?[0-9]{1,4}[.-_]?[a-zA-Z0-9]{1,3}\b(?<!\d\d\d\d\d)"
    reg = re.compile(pattern)
    if reg.search(pdf_node.get_text()):
        return True
    return False


def getScore(pdf_node):
    """score for text to determine probability of being the drawing number
    Args:
        pdf_node (object): pdfminer object. Should pass in LTTextLIne
    Returns:
        double: score
    """
    #factor = 1

    # if isRegEx(pdf_node):
    #     factor = 10
    #score = factor * (10 * pdf_node._objs[0].height + 5 * (pdf_node.x0 - pdf_node.y0))  # first character's height
    score = (-6.227*pdf_node.x0) + (24.07*pdf_node.y0) + (6.737*pdf_node.x1) + (-24.07*pdf_node.y1) + \
            (24.07*pdf_node._objs[0].height) + (-37.7*int(hasNumber(pdf_node))) + (-44.04*getNumNum(pdf_node)) + \
            (424.3*int(hasDash(pdf_node))) + (1059*int(hasDecimal(pdf_node))) + (-49*getNumChar(pdf_node)) + \
            (5009*int(isRegEx(pdf_node)))
    # exit()
    return score


if __name__ == "__main__":
    parsePDFs("drawings/")

# location
# char height
# decimal
# has decimal
#