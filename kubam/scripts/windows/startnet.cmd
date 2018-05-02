@echo off
start /min cmd
echo Initializing, please wait.
FOR /F "tokens=*" %%A IN ('wmic csproduct get uuid /Format:list ^| FIND "="') DO SET %%A
echo REGEDIT4 >> duiduuid.reg
echo. >> duiduuid.reg
echo [HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\services\TCPIP6\Parameters] >> duiduuid.reg
echo "Dhcpv6DUID"=hex:00,04,%uuid:~0,2%,%uuid:~2,2%,%uuid:~4,2%,%uuid:~6,2%,%uuid:~9,2%,%uuid:~11,2%,%uuid:~14,2%,%uuid:~16,2%,%uuid:~19,2%,%uuid:~21,2%,%uuid:~24,2%,%uuid:~26,2%,%uuid:~28,2%,%uuid:~30,2%,%uuid:~32,2%,%uuid:~34,2% >> duiduuid.reg
echo. >> duiduuid.reg
regedit /s duiduuid.reg
for /f "delims=" %%a in ('wmic cdrom get drive ^| find ":"') do set optdrive=%%a
if not defined optdrive GOTO :netboot
set optdrive=%optdrive: =%
if not exist %optdrive%\dvdboot.cmd GOTO :netboot
call %optdrive%\dvdboot.cmd
goto :end
:netboot
wpeinit
:: Get information somehow from file in the C:\ drive of the IP address for this node. 
set "File2Read=c:\network.txt"
setlocal EnableExtensions EnableDelayedExpansion
for /f "delims=" %%a in ('Type "%File2Read%"') do (
  set /a count+=1
  set "Line[!count!]=%%a
)
netsh interface ip set address eth0 static !Line[1]! !Line[2]! !Line[3]!
:noping
ping -n 1 172.28.225.135 2> NUL | find "TTL=" > NUL || goto :noping
md \kubam
echo Waiting for successful mount of \\%KUBAM%\install (if this hangs, check that samba is running)
:nomount
::net use i: \\%KBAM%\kubam || goto :nomount
net use i: \\172.28.225.135\kubam || goto :nomount
echo Successfully mounted \\%KUBAM%\install, moving on to execute remote script
if exist  c:\autounattend.xml copy c:\autounattend.xml x:\kubam\autounattend.xml
if not exist x:\kubam\autounattend.xml echo I could not find my autoinst file
if not exist x:\kubam\autounattend.xml pause
i:\win2012r2\setup /unattend:x:\kubam\autounattend.xml /noreboot
::wpeutil reboot
:end
