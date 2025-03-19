@echo off
setlocal

:: Define the directories to check
set "SL1620=sl1620"
set "SL1640=sl1640"
set "SL1680=sl1680"

:: Check for existence of directories
if exist "%SL1620%" (
    echo SL1620 SPI image exists...
    .\bin\win\astra-update -f "%SL1620%"
    exit /b
)

if exist "%SL1640%" (
    echo SL1640 SPI image exists...
    .\bin\win\astra-update -f "%SL1640%"
    exit /b
)

if exist "%SL1680%" (
    echo SL1680 SPI image exists...
    .\bin\win\astra-update -f "%SL1680%"
    exit /b
)

echo No SPI images detected. Download an image from https://github.com/synaptics-astra/spi-u-boot
exit /b

