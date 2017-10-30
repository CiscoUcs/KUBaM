#!/bin/bash

KUBAM_ROOT=/usr/share/nginx/html/kubam

# link to the web server directory.
if [ ! -d $KUBAM_ROOT ]
then
  ln -sf /kubam $KUBAM_ROOT
fi


# start application
echo "starting kubam app server"
python /app/app.py &

# run the installation script on the ISO file and start the web server. 
# start nginx  
echo "starting web server"
/usr/sbin/nginx 
