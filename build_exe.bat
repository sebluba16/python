@echo off
pip install pillow pyinstaller
pyinstaller --onefile --name show_3mf show_3mf.py
echo.
echo Executable : dist\show_3mf.exe
