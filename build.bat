
set path=C:\Python312\;C:\Python312\scripts;%path%
pyinstaller copis_all.spec --noconfirm
xcopy dist\compose\* dist\copisclient\ /E
xcopy dist\pose_img_linker\* dist\copisclient\ /E
del dist\compose /s /q
rmdir dist\compose /s /q
del dist\pose_img_linker /s /q
rmdir dist\pose_img_linker /s /q

del dist\copisclient\client\copis.ini  /q
del dist\copisclient\client\db\copis.db /q
del dist\copisclient\client\profiles\*  /q