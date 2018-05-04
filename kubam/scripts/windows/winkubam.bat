@echo off
::This script is used to create customized Winpe and BCD for deployment of Windows Server
::This script was originally found in xCAT for windows:
::https://raw.githubusercontent.com/xcat2/xcat-core/master/KUBAM-server/share/xcat/netboot/windows/genimage.cmd
::This script requires that the ADK must be installed onto the Windows 
::This script can accept two parameters: 
::winkubam.bat [osversion] [kubamIP]
::Example:  .\winkubam.bat win2016 172.26.225.135


::get the arch from first param

set ARCH=amd64
set SUFFIX=64

::Configuration section
::the drive to use for holding the image
set defdrive=%SystemDrive%

::get the name of winpe
set WINPENAME=
set BOOTPATH=Boot

::location where Windows PE from ADK install is located
set adkpedir=%defdrive%\Program Files (x86)\Windows Kits\8.1\Assessment and Deployment Kit\Windows Preinstallation Environment
set oscdimg=%defdrive%\Program Files (x86)\Windows Kits\8.1\Assessment and Deployment Kit\Deployment Tools\amd64\Oscdimg
set WinPERoot=%adkpedir%
set OSCDImgRoot=%oscdimg%
set Path=C:\Program Files (x86)\Windows Kits\8.1\Assessment and Deployment Kit\Deployment Tools\amd64\DISM;%Path%
set Path=C:\Program Files (x86)\Windows Kits\8.1\Assessment and Deployment Kit\Windows Preinstallation Environment;%Path%
set Path=C:\Program Files (x86)\Windows Kits\8.1\Assessment and Deployment Kit\Deployment Tools\amd64\Oscdimg;%Path%

::clean the c:\winPE_amd64 and copy it from ADK
if exist %defdrive%\WinPE_%SUFFIX% rd %defdrive%\WinPE_%SUFFIX% /s /q
if exist %defdrive%\WinPE_KUBAM.iso del %defdrive%\WinPE_KUBAM.iso
set retpath=%cd%
cd /d "%adkpedir%"
call copype.cmd %ARCH% %defdrive%\WinPE_%SUFFIX%
cd /d %retpath%

bcdedit /createstore %defdrive%\WinPE_%SUFFIX%\media\Boot\BCD.%SUFFIX%
bcdedit /store %defdrive%\WinPE_%SUFFIX%\media\Boot\BCD.%SUFFIX%  /create {ramdiskoptions} /d "Ramdisk options"
bcdedit /store %defdrive%\WinPE_%SUFFIX%\media\Boot\BCD.%SUFFIX%  /set {ramdiskoptions} ramdisksdidevice boot
bcdedit /store %defdrive%\WinPE_%SUFFIX%\media\Boot\BCD.%SUFFIX%  /set {ramdiskoptions} ramdisksdipath \%BOOTPATH%\boot.sdi
for /f "Tokens=3" %%i in ('bcdedit /store %defdrive%\WinPE_%SUFFIX%\media\Boot\BCD.%SUFFIX% /create /d "KUBAM WinNB_%SUFFIX%" /application osloader') do set GUID=%%i
bcdedit /store %defdrive%\WinPE_%SUFFIX%\media\Boot\BCD.%SUFFIX%  /set %GUID% systemroot \Windows
bcdedit /store %defdrive%\WinPE_%SUFFIX%\media\Boot\BCD.%SUFFIX%  /set %GUID% detecthal Yes
bcdedit /store %defdrive%\WinPE_%SUFFIX%\media\Boot\BCD.%SUFFIX%  /set %GUID% winpe Yes
bcdedit /store %defdrive%\WinPE_%SUFFIX%\media\Boot\BCD.%SUFFIX%  /set %GUID% osdevice ramdisk=[boot]\%BOOTPATH%\WinPE_%SUFFIX%.wim,{ramdiskoptions}
bcdedit /store %defdrive%\WinPE_%SUFFIX%\media\Boot\BCD.%SUFFIX%  /set %GUID% device ramdisk=[boot]\%BOOTPATH%\WinPE_%SUFFIX%.wim,{ramdiskoptions}
bcdedit /store %defdrive%\WinPE_%SUFFIX%\media\Boot\BCD.%SUFFIX% /create {bootmgr} /d "KUBAM WinNB_%SUFFIX%"
bcdedit /store %defdrive%\WinPE_%SUFFIX%\media\Boot\BCD.%SUFFIX% /set {bootmgr} timeout 1
bcdedit /store %defdrive%\WinPE_%SUFFiX%\media\Boot\BCD.%SUFFIX% /set {bootmgr} displayorder %GUID%
bcdedit /store %defdrive%\WinPE_%SUFFIX%\media\Boot\BCD.%SUFFIX%
if [%ARCH%] EQU [x86] copy %defdrive%\WinPE_%SUFFIX%\media\Boot\BCD.%SUFFIX% %defdrive%\WinPE_%SUFFIX%\media\Boot\B32
if [%ARCH%] EQU [amd64]  copy %defdrive%\WinPE_%SUFFIX%\media\Boot\BCD.%SUFFIX% %defdrive%\WinPE_%SUFFIX%\media\Boot\BCD


dism /mount-image /imagefile:%defdrive%\WinPE_%SUFFIX%\media\Sources\boot.wim /index:1 /mountdir:%defdrive%\WinPE_%SUFFIX%\mount
cd /d %retpath%
copy startnet.cmd %defdrive%\WinPE_%SUFFIX%\mount\Windows\system32

dism /Image:%defdrive%\WinPE_%SUFFIX%\mount /add-package /packagepath:"%adkpedir%\amd64\WinPE_OCs\WinPE-WMI.cab"
dism /Image:%defdrive%\WinPE_%SUFFIX%\mount /add-package /packagepath:"%adkpedir%\amd64\WinPE_OCs\WinPE-Scripting.cab"
dism /Image:%defdrive%\WinPE_%SUFFIX%\mount /add-package /packagepath:"%adkpedir%\amd64\WinPE_OCs\WinPE-RNDIS.cab"
dism /Image:%defdrive%\WinPE_%SUFFIX%\mount /add-package /packagepath:"%adkpedir%\amd64\WinPE_OCs\WinPE-NetFX.cab"
dism /Image:%defdrive%\WinPE_%SUFFIX%\mount /add-package /packagepath:"%adkpedir%\amd64\WinPE_OCs\WinPE-PowerShell.cab"
dism /Image:%defdrive%\WinPE_%SUFFIX%\mount /add-package /packagepath:"%adkpedir%\amd64\WinPE_OCs\WinPE-DismCmdlets.cab"
dism /Image:%defdrive%\WinPE_%SUFFIX%\mount /add-package /packagepath:"%adkpedir%\amd64\WinPE_OCs\WinPE-StorageWMI.cab"
dism /Image:%defdrive%\WinPE_%SUFFIX%\mount /add-package /packagepath:"%adkpedir%\amd64\WinPE_OCs\WinPE-WDS-Tools.cab"
copy %defdrive%\WinPE_%SUFFIX%\mount\Windows\Boot\PXE\pxeboot.n12 %defdrive%\WinPE_%SUFFIX%\media\Boot\pxeboot.0
copy %defdrive%\WinPE_%SUFFIX%\mount\Windows\Boot\PXE\wdsmgfw.efi %defdrive%\WinPE_%SUFFIX%\media\Boot\wdsmgfw.efi
copy %defdrive%\WinPE_%SUFFIX%\mount\Windows\Boot\EFI\bootmgfw.efi %defdrive%\WinPE_%SUFFIX%\media\Boot\bootmgfw.efi
copy %defdrive%\WinPE_%SUFFIX%\mount\Windows\Boot\EFI\bootmgr.efi %defdrive%\WinPE_%SUFFIX%\media\Boot\bootmgr.efi
copy %defdrive%\WinPE_%SUFFIX%\mount\Windows\Boot\PXE\bootmgr.exe %defdrive%\WinPE_%SUFFIX%\media\
mkdir %defdrive%\WinPE_%SUFFIX%\media\dvd
copy "%oscdimg%\etfsboot.com" %defdrive%\WinPE_%SUFFIX%\media\dvd
copy "%oscdimg%\efisys_noprompt.bin" %defdrive%\WinPE_%SUFFIX%\media\dvd
rem for /r %defdrive%\drivers %%d in (*.inf) do dism /image:%defdrive%\WinPE_%SUFFIX%\mount /add-driver /driver:%%d 
if exist %defdrive%\drivers dism /image:%defdrive%\WinPE_%SUFFIX%\mount /add-driver /driver:%defdrive%\drivers /recurse
dism /Unmount-Wim /commit /mountdir:%defdrive%\WinPE_%SUFFIX%\mount
move %defdrive%\WinPE_%SUFFIX%\media\Sources\boot.wim %defdrive%\WinPE_%SUFFIX%\media\Boot\WinPE_%SUFFIX%.wim


echo Finished generating of winpe and BCD.
echo Generating ISO image.
MakeWinPEMedia.cmd /ISO %defdrive%\WinPE_64\ %defdrive%\WinPE_KUBAM.iso
echo "Upload %defdrive%\WinPE_KUBAM.iso into ~/kubam directory of KUBAM"

