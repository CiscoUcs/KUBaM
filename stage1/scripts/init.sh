#!/bin/bash
echo "Looking for iso image in /kubam/ directory"
if [ ! -d /kubam ]; then
  echo "Please rerun with -v <your ISO directory>/:/kubam"
  echo "See documentation at: http://kubam.io"
  exit 1
fi

echo "Looking for the ISO file to extract."
F=$(ls /kubam/*.iso 2>/dev/null | head -1)
if [[ F = "" ]]; then
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
if [ ! -d centos7.3 ] 
then
  echo "Extracting centos 7.3 ISO..."
  osirrox -prog kubam -indev ./*.iso -extract . centos7.3
  echo "Finished extracting"
else
   echo "centos7.3 directory exists."
fi
# extract the file in the kubam directory

if [ ! -d stage1 ]
then
  echo "Making installation image."
  mkdir -p stage1
  cp -a centos7.3/isolinux stage1/
  cp -a centos7.3/.discinfo stage1/isolinux/
  cp -a centos7.3/LiveOS stage1/isolinux/
  cp -a centos7.3/images/  stage1/isolinux/
  cp /usr/share/kubam/stage1/centos7.3/isolinux.cfg stage1/isolinux/
fi

if [ ! -e centos7.3-boot.iso ]
then 
  echo "Compressing Installation image."
  mkisofs -o $KUBAM_ROOT/centos7.3-boot.iso -b isolinux.bin \
  -c boot.cat -no-emul-boot -V 'CentOS 7 x86_64' \
  -boot-load-size 4 -boot-info-table -r -J -v -T stage1/isolinux
fi


# run the installation script on the ISO file and start the web server. 
# start nginx  
echo "starting web server"
/usr/sbin/nginx 
