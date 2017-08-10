FROM centos
MAINTAINER vallard@benincosa.com
# get NGINX server. 
RUN rpm -Uvh http://nginx.org/packages/centos/7/noarch/RPMS/nginx-release-centos-7-0.el7.ngx.noarch.rpm && \
    yum -y install nginx mkisofs pykickstart
ADD files/nginx.conf /etc/nginx.conf
ADD scripts/* /usr/bin/
EXPOSE 80

