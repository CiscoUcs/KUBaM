#!/bin/bash
echo "Looking for iso image in /kubam/ directory"
if [ -d /kubam ]; then
  echo "Please rerun with -v <your ISO directory>/:/kubam"
  echo "See documentation at: http://kubam.io"
  exit 1
fi

if [ ! -e /kubam/*.iso ]; then
  echo "No ISO file found.  Please add a Linux ISO file to your directory."
  echo "The suffix of the file should be .iso"
  exit 1
fi

# run the installation script on the ISO file and start the web server. 
# start nginx  
  
