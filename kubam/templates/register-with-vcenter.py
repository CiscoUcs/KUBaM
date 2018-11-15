import sys,re,os,urllib,base64,syslog,socket
import urllib.request as request
import ssl

# used for unverified SSL/TLS certs. Insecure, not good for public.
ssl._create_default_https_context = ssl._create_unverified_context

## Variables that need to be filled out for different environments ##
# URL of vcenter, just the IP address
vcenter = "10.93.140.100"

# Data center
#cluster = "<datacenter>/host/<cluster>"
cluster = "Lucky Lab (LK02)/host/SandyBridge"

# vCenter credentials
user = "administrator@vsphere.local"
password = "Cisco.123"

# host ESXi credentials
host_username = "root"
host_password = "Cisco.123"

url = "https://" + vcenter + "/mob/?moid=SearchIndex&method=findByInventoryPath"


passman = request.HTTPPasswordMgrWithDefaultRealm()
passman.add_password(None,url, user, password)
authhandler = request.HTTPBasicAuthHandler(passman)
opener = request.build_opener(authhandler)
request.install_opener(opener)
#cont = ssl._create_unverified_context()
#ssl._create_default_https_context = ssl._create_unverified_context()
req = request.Request(url)
#cont = ssl._create_unverified_context()
#page = request.urlopen(req, context=context)
page = request.urlopen(req)
page_content = page.read().decode('utf-8')
#print(page_content)

reg = re.compile('name="vmware-session-nonce" type="hidden" value="?([^\s^"]+)"')
nonce = reg.search(page_content).group(1)

headers = page.info()
cookie = headers.get("Set-Cookie")

params = {'vmware-session-nonce':nonce,'inventoryPath':cluster}
e_params = urllib.parse.urlencode(params)
#print(e_params)
bin_data = e_params.encode('utf8')
req = request.Request(url, bin_data, headers={"Cookie":cookie})
page = request.urlopen(req)
page_content = page.read().decode('utf-8')
#print(page_content)

clusterMoRef = re.search('domain-c[0-9]*',page_content)
if clusterMoRef:
	print("Found cluster: " + cluster)
else:
	opener.close()
	sys.exit(1)

# cert stuff
cmd = "openssl x509 -sha1 -in /etc/vmware/ssl/rui.crt -noout -fingerprint"
tmp = os.popen(cmd)
tmp_sha1 = tmp.readline()
tmp.close()
s1 = re.split('=',tmp_sha1)
s2 = s1[1]
s3 = re.split('\n', s2)
sha1 = s3[0]

if sha1:
	print("Hash: ", sha1)
else:
	opener.close()
	sys.exit(1)

xml = '<spec xsi:type="HostConnectSpec"><hostName>%hostname</hostName><sslThumbprint>%sha</sslThumbprint><userName>%user</userName><password>%pass</password><force>1</force></spec>'
 
# Code to extract IP Address to perform DNS lookup to add FQDN to vCenter
hostip = socket.gethostbyname(socket.gethostname())

if hostip:
	print("IP address of host: ", hostip.strip())
else:
	opener.close()
	sys.exit(1)

# could add logic to do DNS lookup, but no dns in our environment. 

xml = xml.replace("%hostname",hostip)
xml = xml.replace("%sha",sha1)
xml = xml.replace("%user",host_username)
xml = xml.replace("%pass",host_password)
print(xml)
# now join to vcenter cluster
try: 
	url = "https://" + vcenter + "/mob/?moid=" + clusterMoRef.group() + "&method=addHost"
	params = {'vmware-session-nonce':nonce,'spec':xml,'asConnected':'1','resourcePool':'','license':''}
	e_params = urllib.parse.urlencode(params)
	bin_data = e_params.encode('utf8')
	req = request.Request(url, bin_data, headers={"Cookie":cookie})
	page = request.urlopen(req).read()
except IOError as e:
	opener.close()
	print("Couldn't join cluster", e)
	sys.exit(1)
else:
	print("Joined vcenter cluster!")
	url = "https://" + vcenter + "/mob/?moid=SessionManager&method=logout"
	params = {'vmware-session-nonce':nonce}
	e_params = urllib.parse.urlencode(params)
	bin_data = e_params.encode('utf8')
	req = request.Request(url, bin_data, headers={"Cookie":cookie})
	page = request.urlopen(req).read()
	sys.exit(0)
