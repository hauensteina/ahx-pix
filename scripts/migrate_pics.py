#!/usr/bin/env python

'''
Migrate pictures from hauenstein.nine.ch to ahx-pics bucket on S3
AHN, Jan 2023
'''

import sys,os,re
from os.path import dirname
sys.path.append( f'{dirname(__file__)}/..')

import argparse
from pdb import set_trace as BP

from mod_ahx_pix import helpers 

def usage(printmsg=False):
    name = os.path.basename( __file__)
    msg = f'''
    Name:
      {name}: Migrate pictures from hauenstein.nine.ch to ahx-pics bucket on S3
    Synopsis:
      python {name} --folder <folder>
    Example:
      python {name} --folder pics

--
''' 
    if printmsg:
        print(msg)
        exit(1)
    else:
        return msg

def main():
    if len(sys.argv) == 1: usage(True)
    parser = argparse.ArgumentParser(usage=usage())
    parser.add_argument( "--folder", required=True)
    args = parser.parse_args()
    run(args.folder)

def run(folder):
    fnames = []
    for currentpath, folders, files in os.walk(folder):
        for f in files:
            if not '.DS_STORE' in f.upper(): 
                fnames.append( os.path.join(currentpath, f))
    #fnames = fnames[:100]
    helpers.s3_upload_files(fnames)

if __name__ == '__main__':
  main()

