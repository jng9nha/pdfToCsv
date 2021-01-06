# authors: Dennis Chiappetta and Jen Gulley
# uses PyMuPDF library
import re
import fitz
import csv
import Conversion1

def pdfToCSV(file):
    """
    main function for creating csv file from pdf
    :param file: the pdf file to open and convert to csv
    :return: none; creates csv file with the same as the pdf file
    """
    # create csv file
    csvFile = open("csvFile.csv", 'w')

    # get the csv filename from the pdf filename
    csvFilename = file[0:-3]
    csvFilename = csvFilename + "csv"

    # make header for csv
    header = "page_number,x0,y0,x1,y1,text,page_drawing_no\n"
    csvFile.write(header)
    csvFile.close()

    # open the pdf
    pdf_file = fitz.open(file)

    pageSizeList = []

    # for loop going into each page
    for pageNumber, page in enumerate(pdf_file.pages(), start=1):
        csvFile = open("csvFile.csv", 'a', encoding='utf-8')
        # makes in textpage
        text = page.getTextPage()
        # call to method in library that gets all necessary information
        text1 = text.extractBLOCKS()
        print(text1)
        # call to method in library that gets all images (raster PDFs?)
        text2 = page.getImageList()
        # goes through the list of items in text1 because text1 is list of lists
        # svg = page.getSVGimage(matrix=fitz.Identity).encode('utf-8')
        pagesize = page.MediaBoxSize
        pageSizeList.append(pagesize)
        # print(pageSizeList)
        pageSize = page.MediaBoxSize
        xSize = pageSize.x
        ySize = pageSize.y
        if text1 == []:
            text1 = Conversion1.rasterToPDF(page)
        for each in text1:
            # reformats text
            eachText = str(each[4]).replace("\n", " ").replace("\"", "'""'")
            # write to csv with call to regex
            csvFile.write((str(pageNumber) + "," + str(each[0]) + "," + str(each[1]) + "," + str(each[2]) + "," +
                           str(each[3]) + ","
                      + "\"" + eachText + "\"" + "," + coordMatch(each[0], each[1], xSize, ySize, eachText) + "\n"))
        for piece in text2:
            # insert raster to vector method here
            print(str(pageNumber) + ": ")
            print(piece)
            csvFile.write(str(pageNumber) + "," + str(piece[0]) + "," + str(piece[1]) + "," + str(piece[2]) + "," +
                    str(piece[3]) + ",image: " + str(piece[7]) + "\n")
        csvFile.close()

    # call to getPageLoc() function to determine location of drawing page numbers
    NoLoc = getPageLoc(dict)
    NoLoc = NoLoc[0:4]

    # locList = []
    # for pageNumber, page in enumerate(pdf_file.pages(), start=1):
    #     if page.getTextbox(NoLoc) != "":
    #         locList.append(page.getTextbox(NoLoc))
    # print(locList)

    # add a new column to the csv called page_drawing_no which tells you whether the drawing number
    # is the drawing number of the page
    myCsv = csv.reader(open("csvFile.csv", encoding='utf-8'))
    csvFileFinal = open(csvFilename, 'w', encoding='utf-8')
    row0 = next(myCsv)
    # header for the new column
    row0.append("contains_drawing_no\n")
    row0 = listToString(row0)
    csvFileFinal.write(row0)
    # for loop to go through each row in original csv and add a new column in updated csv
    for row in myCsv:
        x = float(row[1])
        y = float(row[2])
        rowText = row[3]
        row[5] = "\"" + row[5] + "\""
        row.append(drawingNo(row[5]) + "\n")
        rowString = listToString(row)
        csvFileFinal.write(rowString)
    csvFileFinal.close()

# global dictionary for finding drawing number on each page
dict = {}

# regex function
# param text - s
# param value2 -
# return
def drawingNo(text):
    """
    regex function to find all drawing numbers
    :param text: string to be searched for drawing number
    :param value2: list containing x0, y0, x1, y1, text, block_no, block_type of the text block
    :return: boolean as a string; returns true if the text contains a drawing number, false otherwise
    """
    # starting value of boolean
    boolean = False
    for each in drawingNoList:
        if each in text:
            boolean = True
    return str(boolean)
    # # regex pattern
    # pattern = r"\b[a-zA-Z]{1,3}[1-9]{0,3}\s?[.-]?\s?[0-9]{1,4}[.-]?[a-zA-Z0-9]{1,3}\b(?<!\d\d\d\d\d)"
    # pattern2 = r"([a-zA-Z]{1,3} *-*\.* *[0-9(\.*)(a-z*A-Z*)]{1,5}( *))"
    # reg = re.compile(pattern)
    # # look for regex match
    # if reg.search(text):
    #     # if there is a match change boolean
    #     boolean = True
    #     if value2[0]+value2[1] not in dict:
    #         dict[value2[0]+value2[1]] = [value2[0], value2[1], value2[2], value2[3], 1]
    #     else:
    #         val = dict[value2[0]+value2[1]]
    #         number = val[4] + 1
    #         newList = [value2[0], value2[1], value2[2], value2[3], number]
    #         dict[value2[0]+value2[1]] = newList
    # # return the result of the boolean as a string for csv
    # return str(boolean)

def getPageLoc(z):
    """
    takes in the dictionary created by the regex function and returns the value at the key that has the highest count
    :param z: dictionary with key being the x0 coordinate and value being a list
    :return: returns a list containing x0, y0, x1, y1, count (count is how many times the x0 coordinate showed up)
    """
  # For finding the page number by location
    x = [10, 10, 10, 10, 0]
    for key in z:
        part = z[key]
        if x[4] <= part[4]:
            x = dict[key]
 #   print(x)
    return x

drawingNoList = []

def coordMatch(x, y, xSize, ySize, text):
    """
    takes in x and y coordinates and determines if they match the x and y coordinates of interest
    :param x: float, x coordinate
    :param y: float, y coordinate
    :param NoLoc: list containing coordinates of interest
    :return: boolean as a string; returns true if the coordinates match, false otherwise
    """
    pattern = r"\b[a-zA-Z]{1,3}[1-9]{0,3}\s?[.-]?\s?[0-9]{1,4}[.-_]?[a-zA-Z0-9]{1,3}\b(?<!\d\d\d\d\d)"
    reg = re.compile(pattern)
    boolean = False
    if x > xSize-300 and y > ySize-300:
        # x > xSize-300 and
        if reg.search(text):
            boolean = True
            text = text.replace(" ", "")
            drawingNoList.append(text)
            #print(drawingNoList)
    return str(boolean)

def listToString(listToConvert):
    """
    takes in a list and converts it to a string separated by commas
    :param listToConvert: list to be converted
    :return: string separated by commas
    """
    s = ""
    for each in listToConvert:
        s = s + each + ","
    s = s[0:-1]
    return s

pdfToCSV("vol-6.1.001-15-052-3.1-000-location-plan.pdf")
# pdfToCSV("out.pdf")
# pdfToCSV("2 Story Architectural Dwgs.pdf")
# 20170814_PVL-Bid-Set-1P1-19.pdf
# vol-6.1.001-15-052-3.1-000-location-plan.pdf
# 0E82B492-A386-409F-B491-5B337A37002C.pdf

# To Do:
# 1.) fix regex
# 2.) come up with another way to find page drawing number (1 page or diff loc)
# 3.) change key to be x + y coordinates or something
# 4.) raster to vector