:: OSVER and KUBAM are veriables added by winkubam.bat 
start /min cmd
echo Initializing KUBAM WinPE please wait.
wpeinit
:: Get information somehow from file in the C:\ drive of the IP address for this node. 
set "File2Read=c:\network.txt"
setlocal EnableExtensions EnableDelayedExpansion
for /f "delims=" %%a in ('Type "%File2Read%"') do (
  set /a count+=1
  set "Line[!count!]=%%a
)
echo Setting IP address of node...
netsh interface ip set address eth0 static !Line[1]! !Line[2]! !Line[3]!
:noping
ping -n 1 %KUBAM% 2> NUL | find "TTL=" > NUL || goto :noping
md \kubam
echo "Waiting for successful mount of \\%KUBAM%\kubam (if this hangs, check that samba is running. See: https://ciscoucs.github.io/site/kubam/configure/windows2.html)"
:nomount
net use i: \\%KUBAM%\kubam || goto :nomount
echo Successfully mounted \\172.28.225.135\install, moving on to execute remote script
if exist  c:\autounattend.xml copy c:\autounattend.xml x:\kubam\autounattend.xml
if not exist x:\kubam\autounattend.xml echo I could not find my autoinst file
if not exist x:\kubam\autounattend.xml pause
i:\%OSVER%\setup /unattend:x:\kubam\autounattend.xml /noreboot
wpeutil reboot
:end
