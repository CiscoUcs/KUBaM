#!/bin/bash
# start application
echo "starting kubam app server"
python /app/app.py &

# run the installation script on the ISO file and start the web server. 
# start nginx  
echo "starting web server"
/usr/sbin/nginx 
