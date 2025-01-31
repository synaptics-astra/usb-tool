# Astra U-Boot 2019.10 Release notes for Dolphin, Platypus and Myna2 RDK boards

## 1. Information

Based on U-Boot mainline version: U-Boot-2019.10

## 2. Change Log
### U-Boot-2019.10-Astra-v1.2.0
enable usb console and uEnv.txt

### U-Boot-2019.10-Astra-v1.1.1
General:

	- Update keys for OPTEE

### U-Boot-2019.10-Astra-v1.1.0
Fastboot:

	- Add "oem run" to support all U-Boot commands
	- Add "flash ram" to download files into memory

General:

	- Support eMMC quick fill while upgrading sparse images

### U-Boot-2019.10-Astra-v1.0.1
mmc:

	- Update eMMC & SDIO HW settings to work on all Astra board versions
	- Add flag to force eMMC & SDIO to low speed

General:

	- SL1640: Fix environment saving issue on SPI flash

### U-Boot-2019.10-Astra-v1.0.0
General:

	- Support USB2.0 device
	- Support USB3.0 host
	- Support Ethernet
	- Support SPI Flash
	- Support eMMC
		- Support HS400 mode
		- Boot Linux with SU-Boot
	- Support SD card
		- Support SDR104 mode
		- Boot Linux with SU-Boot
	- Support Image upgrading
		- Support eMMC image upgrading in USB U-Boot, SPI U-Boot and SU-Boot
			- USB U-Boot:  image via TFTP and USB slave (connect to PC)
			- SPI U-Boot: image via TFTP and USB Host (connect to USB Disk)
			- SU-Boot: image via TFTP and USB Host (connect to USB Disk)
		- Support sparse image slices
	- Support optee TA loading
	- Support fastboot via UDP and USB2.0 (SPI U-Boot and SU-Boot)
		- Supported commands:  reboot, flash

## 3. Known issues
### 3.1 Some USB disks can't be recognized in 1st probe
fix: run command: "setenv usb_pgood_delay 1000;", can save on SPI U-Boot and SU-Boot by "saveenv"

### 3.2 Some customer designed boards can't work with eMMC/SDIO high speed
fix: run command: "setenv force_mmc_low_speed 1; setenv force_sd_low_speed 1;", can save on SPI U-Boot and SU-Boot by "saveenv"
**This fix only works from v1.0.1**
