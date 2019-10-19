from PIL import Image, ImageDraw, ImageFilter
import io
import os
import glob
import pathlib
import configparser
import argparse

def GenerateCutLines(img,wx,wy,ox,oy,nx,ny,sx,sy):
    draw = ImageDraw.Draw(img)
    for x in range(0,nx+1):
        ln = [(ox + (wx * x),0),(ox + (wx * x),sy)]        
        draw.line(ln,fill=(128,128,127),width=2)

    for y in range(0,ny+1):
        ln = [(0,oy + (wy * y)),(sx,oy + (wy * y))]
        draw.line(ln,fill=(128,128,127),width=2)

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

#Generate backs
genbacks = False

#Use overlap
overlap = False

#Distribute images
distribute = False

#Import arguments
parser = argparse.ArgumentParser(description='Prepares Print-At-Home Card Games for Printing')
parser.add_argument('--backs',const=True, default=False, action='store_const', help='Produce card backs as well as fronts')
parser.add_argument('--nooverlap',const=False, default=True, action='store_const', help='Do not overlap cards, leaving unfilled space')
parser.add_argument('--cutlines',const=True, default=False, action='store_const', help='Draw cut lines onto the finished images')
parser.add_argument('--topedge',const=True, default=False, action='store_const', help='Place images at the top of the paper instead of the center')
parser.add_argument('--leftedge',const=True, default=False, action='store_const', help='Place images at the left of the paper instead of the center')
parser.add_argument('--nomask',const=False, default=True, action='store_const', help='Do not mask out unused parts of the image')
parser.add_argument('--distribute',const=False, default=True, action='store_const', help='Cards should not share any borders')
parser.add_argument('--paper',default='4x6', nargs='?')
parser.add_argument('--paperwidth',default='', nargs='?')
parser.add_argument('--paperheight',default='', nargs='?')
parser.add_argument('--units',default='in', nargs='?')
parser.add_argument('--dpi',default='300', nargs='?')
parser.add_argument('--landscape',const=True, default=False, action='store_const', help='Flip the named paper sizes 90 degrees')
args = parser.parse_args()

genbacks = args.backs
cutlines = args.cutlines
overlap = args.nooverlap
#fittoedge = args.onedge
usemask = args.nomask

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
        unitmult = float(args.dpi)

    if args.paperwidth != '':
        paperwidthin = int(int(args.paperwidth) * unitmult)
        paperheightin = int(int(args.paperheight) * unitmult)

#Output quality
dpi = int(args.dpi)

#Final resolution
pw = int(dpi * paperwidthin)
ph = int(dpi * paperheightin)

#Create a list of folders in this directory
dirs = os.listdir(cpath)

for folder in dirs:
    images = []
    
    mask = None
    back = None

    #Only process directories...
    if not os.path.isdir(cpath + os.sep + folder):
        pass
    
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
                back=file
                continue
            
            images.append(file)        

    #Skip if there were no images
    if len(images) == 0:
        continue    

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
        
    #Figure out the ideal fit...
    
    #Vertical fit
    vfitx = int(pw / srcsize[0])
    vfity = int(ph / srcsize[1])
    vfit = vfitx * vfity

    #Horizontal fit
    hfitx = int(pw / srcsize[1])
    hfity = int(ph / srcsize[0])
    hfit = hfitx * hfity

    #Assume vertical
    fit = vfit
    fitx = vfitx
    fity = vfity

    flipped = False

    #Switch to horizontal if required
    if hfit > vfit:        
        sz = pw
        pw = ph
        ph = sz
        fit = hfit
        fitx = hfity
        fity = hfitx
        flipped = True

    #Show final paper fit details...
    print(folder + " can fit " + str(fit) + " items on a " + str(pw) + "x" + str(ph) + " canvas.")
    
    #Calculate image offsets...
    printwidth = fitx * srcsize[0]
    printheight = fity * srcsize[1]

    offsetx = 0
    #Center on X axis...
    if args.leftedge == False:
        offsetx = (pw - printwidth)/ 2

    offsety = 0
    #Center on Y axis...
    if args.topedge == False:
        offsety = (ph - printheight)/ 2    

    #Prepare masking images
    whiteimage = Image.new('RGBA',(im.size[0],im.size[1]),(255, 255, 255, 255))
    if mask is not None:
        maskimage = Image.open(mask).convert(mode='L')

    #If no back image was found, don't generate backs.
    if back is None:
        args.genbacks = False

    #Generate fronts for all of the cards...
    imageno = 1
    imageindex = 0
    img = Image.new('RGBA',(pw,ph),(255, 255,255,255))
    if genbacks == True:
        backimg = Image.new('RGBA',(pw,ph),(255, 255,255,255))
        backimage = Image.open(back)

    print("Creating Card Images..." + str(len(images)) + " Items")
    if mask is not None and usemask == True:
        print("Using Mask")

    #These cards shouldn't touch one-another - spread them out a bit.
    gapx = 0
    gapy = 0
    if distribute == True:
        gapx = (offsetx * 0.8) / (fitx-1)
        offsetx = offsetx * 0.2
        
        gapy = (offsety * 0.8) / (fity-1)
        offsety = offsety * 0.2    

    #Prepare SVG file..
    svg = '<?xml version="1.0" encoding="utf-8"?>' + "\r\n"
    svg = svg + '<svg version="1.1" id="Layer_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px"' + "\r\n"
    svg = svg + '   viewBox="0 0 ' + str(pw) + ' ' + str(ph) + '" enable-background="new 0 0 ' + str(pw) + ' ' + str(ph) + '" xml:space="preserve">' + "\r\n"

    svgcontent = ""
    svgfilename = cpath + os.sep + folder + os.sep + "mask.svg"
    if os.path.exists(svgfilename):
        fl = open(svgfilename,"r")
        svgcontent = fl.read()
        fl.close()

    #Start generating images
    while imageindex <= len(images)-1:        
        for x in range(0,fitx):
            for y in range(0,fity):                
                if imageindex >= len(images):
                    break
                                
                imx = Image.open(images[imageindex])
                target = (int(offsetx + (x*srcsize[0])) + (gapx * x) - oll,int(offsety + (y*srcsize[1])) + (gapy * y) - olt)

                #If we are using the mask, mask the image here.
                if mask is not None and usemask == True:                    
                    imm = Image.composite(imx,whiteimage,maskimage)
                    img.paste(imm,target,maskimage)
                    imm = None                
                else:
                    img.paste(imx,target)

                if genbacks == True:
                    #If generating card backs, add the back image here too.
                    backimg.paste(backimage,target)

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
        img.save(folder + '_front_' + str(imageno) + ".png")
        print("Generated File " + folder + '_front_' + str(imageno) + ".png")        

        if genbacks == True:
            #Save backing file
            if cutlines == True:
                GenerateCutLines(backimg,srcsize[0],srcsize[1],offsetx,offsety,fitx,fity,pw,ph)            
            backimg.save(folder + '_back_' + str(imageno) + ".png")

        #Saving SVG file
        svg = svg + "</svg>"
        svfile = open(folder + '_cut_' + str(imageno) + ".svg","w")
        svfile.write(svg)
        svfile.close()

        #Clearing images
        imageno = imageno + 1        
        img = None
        img = Image.new('RGBA',(pw,ph),color=(255, 255, 255, 255))

        if genbacks == True:
            backimg = None
            backimg = Image.new('RGBA',(pw,ph),(255, 255,255,255))

        svg = '<?xml version="1.0" encoding="utf-8"?>' + "\r\n"
        svg = svg + '<svg version="1.1" id="Layer_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px"' + "\r\n"
        svg = svg + '   viewBox="0 0 ' + str(pw) + ' ' + str(ph) + '" enable-background="new 0 0 ' + str(pw) + ' ' + str(ph) + '" xml:space="preserve">' + "\r\n"
        
        
