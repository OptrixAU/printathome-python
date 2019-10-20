# Print At Home

This tool allows you to prepare print-at-home card games for a personal use on your choice of paper size and with formatting that suits your method of production.

![alt text](https://github.com/OptrixAU/printathome-python/blob/master/Sample.jpg?raw=true)

## Status

This is in very early development, but may be functional for some limited uses

## Installation 

First, ensure you have Python 2.7 or above installed (this script was developed on Python 3.7, but should be backwards compatible)

Next, install the Pillow module.

```
pip install pillow
```

Then, create a directory to copy the python script into.

## Usage

Then, create a sub-directory under where you installed your script file. There is a **Sample** directory provided that illustrates this.

This should include all of your images for a single deck of cards.

There are three special files that can be located inside the directory....

**Deck.ini** includes instructions for how much overlap may occur in your cards. 

**Mask.svg** is an SVG fragment (ie. it does not contain the actual <svg> element, nor the XML header) containing a SVG masking shape for a cutting device.

**Mask.[image extension]** A greyscale or black-and-white mask image that are optionally applied to cards when they are printed - simulates what a cutter would normally do.

**Back.[image extension]** Used for the back of the card.


## Examples

The following command examples create cards under different circumstances

```
python printathome.py --nooverlap --nomask --paper A4
```

Place your cards onto A4 paper, for use with a cutting machine. These cards will not touch borders, so your cutting machine won't struggle with overlaps. No mask will be used, so you won't get white edges where your cutter and printer are mis-aligned.

```
python printathome.py -cutlines --paper 4x6
```

Place your cards onto 4x6 paper for printing at a photo lab. The cards borders will touch, reducing the amount of manual cutting. Thin cut guide-lines will appear on your image.

## INI Settings

The deck INI file can currently contain the following sections...

```
[OVERLAP]
left = 37
right = 37
top = 37
bottom = 37

[COUNTS]
CardD=4
```

**Overlap** describes how much whitespace is present in the image / mask. 

**Counts** lets you tell the converter to print multiple copies of a card. 

## Special File Names

The following file names & file name components have special meanings...

__Back.[extension]__ - The back of the card deck.

__*CardName*[back].[extension]__ - The back of one specific card.

