#!/usr/bin/env python

# /********************************************************************
# Filename: ahx-pix/main.py
# Author: AHN
# Creation Date: Jan 2023
# **********************************************************************/
#
# A simple image viewer
# See https://www.youtube.com/watch?v=9HcxHDS2w1s (Web Dev Simplified)

from pdb import set_trace as BP
from mod_ahx_pix import app

#----------------------------
if __name__ == '__main__':
    app.run( host='0.0.0.0', port=8000, debug=True)
    # If you want to run with gunicorn:
    # $ gunicorn app:app -w 1 -b 0.0.0.0:8000 --reload --timeout 1000
