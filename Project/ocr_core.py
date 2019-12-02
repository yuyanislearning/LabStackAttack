try:
    from PIL import Image
except ImportError:
    import Image
import pytesseract
from pdf2image import convert_from_path, convert_from_bytes
from pdf2image.exceptions import (
    PDFInfoNotInstalledError,
    PDFPageCountError,
    PDFSyntaxError
)
import sys
import matplotlib.pyplot as plt
import re
from datetime import datetime
import matplotlib.dates as mdates
from PIL import ImageEnhance

#filename = sys.argv[1]
search_term = sys.argv[1]
filenames = []
with open("filenames.txt") as f:
    filenames = [line.strip() for line in f]



def ocr_core(filenames, search_term):
    """
    This function will handle the core OCR processing of images."""
    if search_term == 'cbc':
        cbc_search()
        return None, None

    pages, content, result, time = [], [], [], []
    for filename in filenames:
        images = convert_from_path('RE__my_data/' + filename)
        t = find_time(images)
        for i in range(len(images)):
            # convert to grey scale 
            images[i] = images[i].convert('L')
            # contrast the image
            enhancer = ImageEnhance.Contrast(images[i])
            images[i] = enhancer.enhance(2)
            text = pytesseract.image_to_string(images[i]).lower()
            text = text.splitlines()
            a = get_content(text, search_term)
            if a[0]:
                c, r = a[1],a[2]
        pages.append(i+1)
        content.append(c)
        result.append(r)
        time.append(t)
    # plotting
    fig, ax = plt.subplots()
    ax.plot(time, result)
    fig.autofmt_xdate()
    style = dict(size=10, color='gray')
    for i in range(len(pages)):
        ax.text(time[i], result[i][0], pages[i][0], **style)
    ax.fmt_xdata = mdates.DateFormatter('%Y-%m-%d')
    ax.set_title('time series of ' + search_term)
   
    plt.savefig("test.png", dpi=480)
    return (pages, content)  

def cbc_search():
    '''search for cbc'''
    search_terms = ['white blood cell count','red blood cell count', 'hemoglobin','hematocrit','platelet count, auto']
    # initialize
    d = {}
    time = []
    for search_term in search_terms:
        d[search_term] = []
    for filename in filenames:
        images = convert_from_path('RE__my_data/' + filename)
        # finnd time
        t = find_time(images)
        time.append(t)
        for image in images:
            text = pytesseract.image_to_string(image).lower()
            text = text.splitlines()
            for search_term in search_terms:
                a = get_content(text, search_term)
                # if found, search for next
                if a[0]:
                    c, r = a[1], a[2]
                    d[search_term].append(r)
                    continue
                

    # create table
    with open("test.tsv",'w') as fw:
        # header
        for i in range(len(d['hemoglobin'])):
            fw.write("\t%s"%(str(time[i])))
        fw.write("\n")
        for search_term in search_terms:
            fw.write(search_term)
            for r in d[search_term]:
                fw.write("\t%s"%(str(r)))
            fw.write("\n")

    return None




def get_content(text, search_term):
    '''get the pages that the search term occur, content is the line that include search term
    result is the test result of the search lab'''
    for line in text:
        if search_term in line:
            con = re.findall("%s ([0-9\.]*)"%(search_term), line)
            if len(con) == 0: 
                continue
            content=line
            result=float(con[0])
            return [1, content, result]
    return [0]

def find_time(images):
    '''find time in one images, only consider the first appearence'''
    for i in range(len(images)):
        text = pytesseract.image_to_string(images[i])
        text = text.splitlines()
        for line in text:
            time = re.findall("[0-9]+\/[0-9]+\/[0-9]+", line)
            if len(time) == 0:
                continue
            else:
                break
        if len(time) != 0:
            break
    if len(time) == 0:
        raise Exception('no time info in the document!')
    else:
        time = datetime.strptime(time[0],'%m/%d/%Y').date()
    return time
        
        



pages, content = ocr_core(filenames, search_term)
if search_term!='cbc':
    print("pages that included the search term:", pages)
    print("contents:")
    for c in content:
        print(c)
#print(ocr_core('Examples/Wellness-5-Test-Panel-Results.pdf'))
