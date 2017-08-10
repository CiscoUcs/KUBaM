FROM centos
MAINTAINER vallard@benincosa.com
# get NGINX server. 
RUN rpm -Uvh http://nginx.org/packages/centos/7/noarch/RPMS/nginx-release-centos-7-0.el7.ngx.noarch.rpm && \
    yum -y install nginx mkisofs pykickstart
RUN rpm -Uvh http://ftp.tu-chemnitz.de/pub/linux/dag/redhat/el7/en/x86_64/rpmforge/RPMS/rpmforge-release-0.5.3-1.el7.rf.x86_64.rpm
RUN yum -y install xorriso
ADD files/nginx.conf /etc/nginx/nginx.conf
ADD scripts/* /usr/bin/
RUN ln -sf /dev/stdout /var/log/nginx/access.log 
RUN ln -sf /dev/stderr /var/log/nginx/error.log
EXPOSE 80
CMD ["/bin/bash", "/usr/bin/init.sh"]
