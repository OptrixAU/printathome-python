from PIL import Image, ImageDraw, ImageFilter
import io
import os
import glob
import pathlib
import configparser
import argparse
import xmltodict
import math

def GenerateCutLines(img,wx,wy,ox,oy,nx,ny,sx,sy):
    draw = ImageDraw.Draw(img)
    for x in range(0,nx+1):
        ln = [(ox + (wx * x),0),(ox + (wx * x),sy)]        
        draw.line(ln,fill=(128,128,127),width=2)

    for y in range(0,ny+1):
        ln = [(0,oy + (wy * y)),(sx,oy + (wy * y))]
        draw.line(ln,fill=(128,128,127),width=2)

def Extract(origin, destination,extractor):
    if not os.path.exists(destination):
        os.mkdir(destination)

    backing = []

    with open(extractor) as fd:
        doc = xmltodict.parse(fd.read())
        capture = []

        for rct in doc['svg']['rect']:            
            capture.append((int(float(rct['@x'])),int(float(rct['@y'])),int(float(rct['@width'])),int(float(rct['@height']))))
            try:
                if rct['@fill'] == '#000000':
                    backing.append(len(capture)-1)
            except:
                backing.append(len(capture)-1)

    print("Found " + str(len(capture)) + " capture points in extractor SVG")

    backsequence = None
    backextract = extractor.replace(".svg","[back].svg")
    print("Checking For " + backextract)
    if os.path.exists(backextract):
        #The backing has an alternative distribution
        with open(backextract) as fd:
            print("Found alternative capture points for card back")
            backsequence = []
            doc = xmltodict.parse(fd.read())            

            for rct in doc['svg']['rect']:            
                backsequence.append((int(float(rct['@x'])),int(float(rct['@y'])),int(float(rct['@width'])),int(float(rct['@height']))))                

    #For every source image...
    imageno = 0
    backno = 0
    allfiles = glob.glob(origin + os.sep + "*.*")
    for file in allfiles:    
        extension = ''.join(pathlib.Path(file).suffixes)
        extension = extension.lower()
        if extension == ".jpg" or extension == ".jpeg" or extension == ".png":
            print("Extracting From " + file)
            src = Image.open(file)

            sequence = capture

            mod = ""
            idno = imageno
            ps = file.find('[back]')
            if ps > 0:                
                mod = "[back]"
                if backsequence is not None:
                    sequence = backsequence

            capno = 0
            for cap in sequence:
                
                if mod == "[back]":
                    idno = backno
                else:
                    idno = imageno

                if len(backing) > 0:
                    idno = imageno
                    mod=""
                    if capno in backing:
                        mod="[back]"
                        idno = backno                
                    
                croppiece = (cap[0],cap[1],cap[0] + cap[2],cap[1] + cap[3])
                mini = src.crop(croppiece)
                mini.load()
                mini.save(destination + os.sep + 'card' + str(idno).zfill(4) + mod + ".png")
                mini = None

                if mod == "[back]":
                    backno = backno + 1
                else:
                    imageno = imageno + 1

                capno = capno + 1
            src = None

#Prepare variables
cpath = os.getcwd()

#Calculate output paper size
paperwidth = 15
paperheight = 10

paperwidthin = 6
paperheightin = 4

#Options

#Place the images hard against the leading edge
fittoedge = False

#Mask the soft corners of the images
usemask = True

#Generate the cut SVG
gencut = True

#Draw cut lines
cutlines = False
borders = False

#Generate backs
genbacks = False

#Use overlap
overlap = False

#Distribute images
distribute = False

#Paper Options
bleed = 0


#Import arguments
parser = argparse.ArgumentParser(description='Prepares Print-At-Home Card Games for Printing',fromfile_prefix_chars="@")
parser.add_argument('name', default="*", help='The name of the card to process')
parser.add_argument('--backs',const=True, default=False, action='store_const', help='Produce card backs, even if no back information exists.')
parser.add_argument('--nobacks',const=True, default=False, action='store_const', help='Do not produce backs, even if there is back artwork available')
parser.add_argument('--nooverlap',const=False, default=True, action='store_const', help='Do not overlap cards, leaving unfilled space')
parser.add_argument('--cutlines',const=True, default=False, action='store_const', help='Draw cut lines onto the finished images')
parser.add_argument('--topedge',const=True, default=False, action='store_const', help='Place images at the top of the paper instead of the center')
parser.add_argument('--leftedge',const=True, default=False, action='store_const', help='Place images at the left of the paper instead of the center')
parser.add_argument('--nomask',const=False, default=True, action='store_const', help='Do not mask out unused parts of the image')
parser.add_argument('--distribute',const=True, default=False, action='store_const', help='Cards should not share any borders')
parser.add_argument('--borders',const=True, default=False, action='store_const', help='Draw square card borders')
parser.add_argument('--skipextract',const=True, default=False, action='store_const', help='Skip the extraction step')
parser.add_argument('--paper',default='4x6', nargs='?')
parser.add_argument('--paperwidth',default='', nargs='?')
parser.add_argument('--paperheight',default='', nargs='?')
parser.add_argument('--units',default='in', nargs='?')
parser.add_argument('--dpi',default='300', nargs='?')
parser.add_argument('--margin',default='0', nargs='?')
parser.add_argument('--landscape',const=True, default=False, action='store_const', help='Flip the named paper sizes 90 degrees')
parser.add_argument('--flipbacksx',const=True, default=False, action='store_const', help='Produce cards with backs on their longest axis')
parser.add_argument('--flipbacksy',const=True, default=False, action='store_const', help='Produce cards with backs on their shortest axis')
parser.add_argument('--flipmirror',const=False, default=True, action='store_const', help='Mirror the image when flipping')
parser.add_argument('--flipalt',const=True, default=False, action='store_const', help='Change the order of drawing cards with backs on the same image')
parser.add_argument('--backhreflect',const=True, default=False, action='store_const', help='Reflect the image on the back of the card (horizontally)')
parser.add_argument('--backvreflect',const=True, default=False, action='store_const', help='Reflect the image on the back of the card (vertically)')
parser.add_argument('--resize',default="no", help='Resize the card to fit onto the output paper')
parser.add_argument('--rotatecw',const=True, default=False, action='store_const', help='Rotate the final image clockwise 90 degrees')
parser.add_argument('--rotateacw',const=True, default=False, action='store_const', help='Rotate the final image anti-clockwise 90 degrees')
args = parser.parse_args()



#genbacks = args.backs
cutlines = args.cutlines
overlap = args.nooverlap
usemask = args.nomask
borders = args.borders

#Translate paper names
if args.paper == '4x6' or args.paper == '6x4':
    paperwidthin = 6
    paperheightin = 4

if args.paper == 'letter':
    paperwidthin = 8.5
    paperheightin = 11

if args.paper == 'legal':
    paperwidthin = 8.5
    paperheightin = 14

if args.paper == 'A0':
    paperwidthin = 33.11
    paperheightin = 46.811

if args.paper == 'A1':
    paperwidthin = 23.386
    paperheightin = 33.110

if args.paper == 'A2':
    paperwidthin = 16.535
    paperheightin = 23.386

if args.paper == 'A3':
    paperwidthin = 11.693
    paperheightin = 16.535

if args.paper == 'A4':
    paperwidthin = 8.268
    paperheightin = 11.693

if args.paper == 'A5':
    paperwidthin = 5.827
    paperheightin = 8.268

if args.landscape == True:
    dd = paperwidthin
    paperwidthin = paperheightin
    paperheightin = dd

#Read specified paper sizing
if args.units != '':    
    unitmult = 1

    if args.units == 'cm':
        unitmult = 2.54

    if args.units == 'px':
        unitmult = 1/float(args.dpi)

    if args.paperwidth != '':
        paperwidthin = int(int(args.paperwidth) * unitmult)
        paperheightin = int(int(args.paperheight) * unitmult)

#Output quality
dpi = int(args.dpi)

bleed = int(args.margin)

#Final resolution
pw = int(dpi * paperwidthin)
ph = int(dpi * paperheightin)

if args.units == 'px':
    pw = int(args.paperwidth)
    ph = int(args.paperheight)

#Create a list of folders in this directory
dirs = os.listdir(cpath)

for folder in dirs:

    if args.name != "*":
        if folder != args.name:
            continue
        
    images = []
    cardbacks = {}
    
    mask = None
    back = None

    #Only process directories...
    if not os.path.isdir(cpath + os.sep + folder):
        pass

    extracting = False
    outputfolder = folder

    #Look for a card extractor...
    extfile = cpath + os.sep + folder + os.sep + "extractor.svg"
    if os.path.exists(extfile):
        print("Using Extraction Template To Find Individual Cards")
        oldfolder = folder
        folder = folder + os.sep + "extracted"
        if args.skipextract == False:
            Extract(oldfolder,folder,extfile)
            extracting = True
        print("Card Extraction Complete!")
    
    #Grab a list of files in the active directory    
    allfiles = glob.glob(cpath + os.sep + folder + os.sep + "*.*")
    for file in allfiles:    
        extension = ''.join(pathlib.Path(file).suffixes)
        extension = extension.lower()
        if extension == ".jpg" or extension == ".jpeg" or extension == ".png":
            if file.lower().find("mask" + extension) >= 0:
                mask=file
                continue

            if file.lower().find("back" + extension) >= 0:
                genbacks = True
                back=file
                continue

            ps = file.find('[back]')
            if ps > 0:
                genbacks = True
                cardbacks[file.replace('[back]','')] = file
                continue
            
            images.append(file)        

    #Skip if there were no images
    if len(images) == 0:
        continue

    #If they've demanded no backs, don't draw them.
    if args.nobacks == True:
        genbacks = False

    if args.backs == True:
        genbacks = True

    #Take a look at the size of the images...
    sample = images[0]
    im = Image.open(sample)
    srcsize = im.size
    ar = float(im.size[0]) / float(im.size[1])
    
    print(folder + " images are " + str(im.size[0]) + "x" + str(im.size[1]) + " with ratio of " + str(ar))

    #Overlap Amounts
    olt = 0
    olb = 0
    olr = 0
    oll = 0

    config = None
    
    #Is there a config file for this deck?
    if os.path.exists(cpath + os.sep + folder + os.sep + "deck.ini"):        
        config = configparser.ConfigParser()
        config.read(cpath + os.sep + folder + os.sep + "deck.ini")

        if overlap == True:
            try:
                oll = int(config['OVERLAP']['left'])
                olr = int(config['OVERLAP']['right'])
                olt = int(config['OVERLAP']['top'])
                olb = int(config['OVERLAP']['bottom'])
            except:
                pass            
    
        srcsize = (srcsize[0] - (oll + olr),srcsize[1] - (olt + olb))
    
    #Check for special card instructions...
    touched = []
    for cd in images:
        nm = pathlib.Path(cd).stem.lower()
        if nm not in touched:
            try:
                touched.append(nm)
                repeats = int(config['COUNTS'][nm])-1
                #print("Repeating " + nm + " " + str(repeats) + " times!")
                if repeats >= 1:
                    for n in range(0,repeats):
                        images.append(cd)
            except:
                pass            

    print("Fitting Cards to " + str(pw) + ", " + str(ph) + " paper")
        
    #Figure out the ideal fit...
    ppw = pw
    pph = ph

    ppw -= bleed*2
    pph -= bleed*2
    
    if args.flipbacksx == True:        
        srcsize = (int(srcsize[0] * 2),srcsize[1])
        
    if args.flipbacksy == True:        
        srcsize = (srcsize[0],int(srcsize[1] * 2))
    
    #Vertical fit
    vfitx = int(ppw / srcsize[0])
    vfity = int(pph / srcsize[1])
    vfit = vfitx * vfity

    #Horizontal fit
    hfitx = int(ppw / srcsize[1])
    hfity = int(pph / srcsize[0])
    hfit = hfitx * hfity

    #Assume vertical
    fit = vfit
    fitx = vfitx
    fity = vfity

    flipped = False

    #Switch to horizontal if required
    if args.resize == "no":
        if hfit > vfit:        
            sz = pw
            pw = ph
            ph = sz
            fit = hfit
            fitx = hfity
            fity = hfitx
            sz = ppw
            ppw = pph
            pph = sz
            flipped = True

    #Do I need to resize the incoming images?
    if args.resize != "no":
        fit = 1
        fitx = 1
        fity = 1

        print("Adjusting Source Size to Fit To Page")
        srcsize = (ppw,pph)

    #Show final paper fit details...
    print(folder + " can fit " + str(fit) + " items ( " + str(fitx) + "x" + str(fity) + " ) on a " + str(pw) + "x" + str(ph) + " canvas.")
    if fit == 0:
        print("Unable to process - item does not fit on the selected paper size.")
        continue
    
    #Calculate image offsets...
    printwidth = fitx * srcsize[0]
    printheight = fity * srcsize[1]

    offsetx = 0
    #Center on X axis...
    if args.leftedge == False:
        offsetx = int((ppw - printwidth)/ 2)

    offsety = 0
    #Center on Y axis...
    if args.topedge == False:
        offsety = int((pph - printheight)/ 2)

    offsetx += bleed
    offsety += bleed    

    #Prepare masking images
    whiteimage = Image.new('RGBA',(im.size[0],im.size[1]),(255, 255, 255, 255))
    if mask is not None:
        maskimage = Image.open(mask).convert(mode='L')
        if args.resize != "no":
            maskimage.resize((ppw,pph),Image.BICUBIC)

    #Generate fronts for all of the cards...
    imageno = 1
    imageindex = 0
    img = Image.new('RGBA',(pw,ph),(255, 255,255,255))
    backimage = None
    if genbacks == True:
        backimg = Image.new('RGBA',(pw,ph),(255, 255,255,255))
        try:
            backimage = Image.open(back)
        except:
            pass

    print("Creating Card Images..." + str(len(images)) + " Items")
    if mask is not None and usemask == True:
        print("Using Mask")

    #These cards shouldn't touch one-another - spread them out a bit.
    gapx = 0
    gapy = 0
    if args.distribute == True:
        print("Calculating Distribution...")

        thispage = len(images) - imageno
        pwidth = printwidth
        pheight = printheight

        if thispage < fity:
            pheight = thispage * srcsize[1]
        if thispage < fit:
            pwidth = srcsize[0] * int(math.floor(thispage / fity)+1)
        
        gapx = int((pw - pwidth) / (fitx))
        offsetx = int(bleed + (gapx / 2))
        
        gapy = int((ph - pheight) / (fity))
        offsety = int(bleed + (gapy / 2))

        print("Page = " + str(pw) + ", " + str(ph))
        print("Paper = " + str(printwidth) + ", " + str(printheight))
        print("Gap = " + str(gapx) + ", " + str(gapy))
        print("Offset = " + str(offsetx) + ", " + str(offsety))

    #Prepare SVG file..
    svg = '<?xml version="1.0" encoding="utf-8"?>' + "\r\n"
    svg = svg + '<svg version="1.1" id="Layer_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px"' + "\r\n"
    svg = svg + '   viewBox="0 0 ' + str(pw) + ' ' + str(ph) + '" enable-background="new 0 0 ' + str(pw) + ' ' + str(ph) + '" xml:space="preserve">' + "\r\n"

    #Grap SVG cut template
    svgcontent = ""
    svgfilename = cpath + os.sep + folder + os.sep + "mask.svg"
    if os.path.exists(svgfilename):
        fl = open(svgfilename,"r")
        svgcontent = fl.read()
        fl.close()
    else:
        if args.distribute == True:
            #If we are distributing, we can prooduce cut SVGs.
            svgcontent = "<rect x=\"0\" y=\"0\" width=\"" + str(srcsize[0]) + "\" height=\"" + str(srcsize[1]) + "\" fill=\"black\"/>"

    #Start generating images
    while imageindex <= len(images)-1:        
        for x in range(0,fitx):
            for y in range(0,fity):                
                if imageindex >= len(images):
                    break

                #Open the image
                imx = Image.open(images[imageindex])
                if args.resize != "no":                    
                    imx = imx.resize((ppw,pph),Image.BICUBIC)

                #Determine draw location
                target = (int(offsetx + (x*srcsize[0])) + (gapx * x) - oll,int(offsety + (y*srcsize[1])) + (gapy * y) - olt)
                targetb = None

                #Resized cards should be drawn from top-left
                if args.resize != "no":
                    target = (bleed,bleed)

                #If drawings fronts AND backs, halve the axis (since we doubled it earlier)
                if args.flipbacksx:
                    targetb = (target[0] + int(srcsize[0]/2),target[1])
                if args.flipbacksy:
                    targetb = (target[0],target[1] + int(srcsize[1] / 2))

                if args.flipalt == True:
                    tg = target
                    target = targetb
                    targetb = tg

                #Draw the image
                if mask is not None and usemask == True:
                    #With a mask
                    imm = Image.composite(imx,whiteimage,maskimage)
                    img.paste(imm,target,maskimage)
                    imm = None                
                else:
                    #Wihout a mask
                    img.paste(imx,target)

                #Calculate the border
                bdr = [int(offsetx + (x*srcsize[0])) + (gapx * x) - oll,int(offsety + (y*srcsize[1])) + (gapy * y) - olt,srcsize[0],srcsize[1]]

                if borders == True:
                    #print("Drawing Border")                    
                    draw = ImageDraw.Draw(img)
                    draw.rectangle(bdr,outline=(128,128,127),width=2)

                if genbacks == True:
                    #If generating card backs, add the back image here too.

                    #We need to flip the Y axis for backs
                    if args.distribute == True:
                        #For some reason, the distributed version needs an extra fudge along the x-offset
                        mtarget = (backimg.size[0] - (int(offsetx + ((x+1)*srcsize[0])) + (gapx * (x+1)) - oll) + (offsetx*2),int(offsety + (y*srcsize[1])) + (gapy * y) - olt)
                    else:
                        mtarget = (backimg.size[0] - (int(offsetx + ((x+1)*srcsize[0])) + (gapx * (x+1)) - oll),int(offsety + (y*srcsize[1])) + (gapy * y) - olt)                    
                    
                    thisbackimage = backimage
                    #Check if there is a specific back for this card
                    if images[imageindex] in cardbacks:                        
                        thisbackimage = Image.open(cardbacks[images[imageindex]])

                    #Resized cards should be drawn from top-left
                    if thisbackimage is not None and args.resize != "no":                        
                        thisbackimage = thisbackimage.resize((ppw,pph),Image.BICUBIC)
                        mtarget = (bleed,bleed)

                    #If no back is available, use the original image.
                    if thisbackimage is None:
                        thisbackimage = imx

                    if args.backhreflect == True:
                        thisbackimage = thisbackimage.transpose(Image.FLIP_LEFT_RIGHT)
                    if args.backvreflect == True:
                        thisbackimage = thisbackimage.transpose(Image.FLIP_TOP_BOTTOM)

                    if thisbackimage is not None:                        
                        if mask is not None and usemask == True:
                            #Draw with masking
                            imm = Image.composite(thisbackimage,whiteimage,maskimage)
                            backimg.paste(imm,mtarget,maskimage)                        
                            imm = None                
                        else:
                            #Draw without masking
                            backimg.paste(thisbackimage,mtarget)

                    if borders == True:
                        drawback = ImageDraw.Draw(backimg)
                        drawback.rectangle(bdr,outline=(128,128,127),width=2)

                    thisbackimage = None

                #This is for drawing backs on the SAME PAGE as fronts
                if targetb is not None:
                    thisbackimage = backimage

                    #Check if there is a specific back for this card.
                    if images[imageindex] in cardbacks:                        
                        thisbackimage = Image.open(cardbacks[images[imageindex]])

                    #If no back is available, use the original image.
                    if thisbackimage is None:
                        thisbackimage = imx
                        if args.flipmirror == True:
                            if args.flipbacksx == True:
                                thisbackimage = imx.transpose(Image.FLIP_LEFT_RIGHT)
                            if args.flipbacksy == True:
                                thisbackimage = imx.transpose(Image.FLIP_TOP_BOTTOM)
                                                
                    if mask is not None and usemask == True:
                        #Draw with masking
                        imm = Image.composite(thisbackimage,whiteimage,maskimage)
                        img.paste(imm,targetb,maskimage)
                        imm = None                
                    else:
                        #Draw without masking
                        img.paste(thisbackimage,targetb)

                #Add to SVG cut template
                if svgcontent != '':
                    svgx = target[0]
                    svgy = target[1]
                    svg += '<g transform="translate(' + str(svgx) + ' ' + str(svgy) + ')">' + svgcontent + '</g>'

                #All done, move onto the next card
                imx = None                    
                imageindex = imageindex + 1                
                pass

        if cutlines == True:
            GenerateCutLines(img,srcsize[0],srcsize[1],offsetx,offsety,fitx,fity,pw,ph)

        #Saving Image File
        img.save(outputfolder + '_front_' + str(imageno) + ".png")

        if genbacks == True:
            #Save backing file
            if cutlines == True:
                GenerateCutLines(backimg,srcsize[0],srcsize[1],offsetx,offsety,fitx,fity,pw,ph)            
            backimg.save(outputfolder + '_back_' + str(imageno) + ".png")

        #Saving SVG file
        svg = svg + "</svg>"
        if svgcontent != '':
            svfile = open(outputfolder + '_cut_' + str(imageno) + ".svg","w")
            svfile.write(svg)
            svfile.close()

        #Clearing images & Resetting for Next Pass
        imageno = imageno + 1        
        img = None
        img = Image.new('RGBA',(pw,ph),color=(255, 255, 255, 255))

        if genbacks == True:
            backimg = None
            backimg = Image.new('RGBA',(pw,ph),(255, 255,255,255))

        svg = '<?xml version="1.0" encoding="utf-8"?>' + "\r\n"
        svg = svg + '<svg version="1.1" id="Layer_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px"' + "\r\n"
        svg = svg + '   viewBox="0 0 ' + str(pw) + ' ' + str(ph) + '" enable-background="new 0 0 ' + str(pw) + ' ' + str(ph) + '" xml:space="preserve">' + "\r\n"
        
        
