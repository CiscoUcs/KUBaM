FROM python:2
MAINTAINER vallard@benincosa.com

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
# patch UCS Central
ADD patches/ucscsdk/ucscmeta.py /usr/lib/python2.7/site-packages/ucscsdk/
ADD patches/ucscsdk/ConfigRemoteResolveChildrenMeta.py /usr/lib/python2.7/site-packages/ucscsdk/methodmeta/
