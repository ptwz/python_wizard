#!/usr/bin/env python
import re
import os
from pywizard.userSettings import settings
from pywizard.tools import BitPacker
from pywizard.Processor import Processor
from pywizard.Buffer import Buffer
import logging

'''
Command line application for processing WAV files into LPC data
for use with TMS5220 (emulators)
'''

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("-u", "--unvoicedThreshold",
    help="Unvoiced frame threshold",
    action="store",
    default=0.3,
    type=float)
parser.add_argument("-w", "--windowWidth",
    help="Window width in frames",
    action="store",
    default=2,
    type=int)
parser.add_argument("-U", "--normalizeUnvoicedRMS",
    help="Normalize unvoiced frame RMS",
    action="store_true")
parser.add_argument("-V", "--normalizeVoicedRMS",
    help="Normalize voiced frame RMS",
    action="store_true")
parser.add_argument("-S", "--includeExplicitStopFrame",
    help="Create explicit stop frame (needed e.g. for Talkie)",
    action="store_true")
parser.add_argument("-p", "--preEmphasis",
    help="Pre emphasize sound to improve quality of translation",
    action="store_true")
parser.add_argument("-a", "--preEmphasisAlpha",
    help="Emphasis coefficient",
    type=float,
    default=-0.9373)
parser.add_argument("-d", "--debug",
    help="Enable (lots) of debug output",
    action="store_true")
parser.add_argument("-r", "--pitchRange",
    help="Comma separated range of available voice pitch in Hz. Default: 50,500",
    default="50,500")
parser.add_argument("-F", "--frameRate",
    default=25,
    type=int)
parser.add_argument("-m", "--subMultipleThreshold",
    help="sub-multiple threshold",
    default=0.9,
    type=float)
parser.add_argument("-f", "--outputFormat",
    help="Output file format",
    choices=["arduino", "C", "hex"],
    default="hex")
parser.add_argument("filename",
    help="File name of a .wav file to be processed",
    action="store")


args = parser.parse_args()

settings.import_from_argparse(args)
if args.debug:
    logging.basicConfig(level=logging.DEBUG)
    print vars(args)
    print settings.__dict__
b=Buffer.fromWave(args.filename)
x=Processor(b)

result = BitPacker.pack(x.frames)

new_varname = os.path.basename(args.filename)
new_varname = os.path.splitext(new_varname)[0]

if re.match("^[^A-Za-z_]", new_varname):
    new_varname = "_"+new_varname

print result.replace("FILENAME", new_varname)
