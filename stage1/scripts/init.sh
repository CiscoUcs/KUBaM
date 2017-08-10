#!/bin/bash
echo "Looking for iso image in /kubam/ directory"
if [ ! -d /kubam ]; then
  echo "Please rerun with -v <your ISO directory>/:/kubam"
  echo "See documentation at: http://kubam.io"
  exit 1
fi

echo "Looking for the ISO file to extract."
if [ ! -e /kubam/*.iso ]; then
  echo "No ISO file found.  Please add a Linux ISO file to your directory."
  echo "The suffix of the file should be .iso"
  exit 1
fi
KUBAM_ROOT=/usr/share/nginx/html/kubam

# link to the web server directory.
if [ ! -d $KUBAM_ROOT ]
then 
  ln -sf /kubam $KUBAM_ROOT
fi

cd $KUBAM_ROOT
# osirrox is so rad!  
# thanks: https://stackoverflow.com/questions/22028795/is-it-possible-to-mount-an-iso-inside-a-docker-container
if [ ! -d isolinux ] 
then
  echo "Extracting isolinux file..."
  osirrox -prog kubam -indev ./*.iso -extract . isolinux
  echo "Finished extracting"
else
   echo "isolinux file exists."
fi
# extract the file in the kubam directory

# run the installation script on the ISO file and start the web server. 
# start nginx  
echo "starting web server"
/usr/sbin/nginx 
