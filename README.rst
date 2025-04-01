Synaptics Astra USB Tools
=========================

This repository contains the USB tools and drivers needed to flash images to the Synaptics Astra RDK boards.

USB Driver
----------

The ``Synaptics_WinUSB_Driver`` directory contains the Windows USB driver which is needed to communicate with a Synaptics Astra RDK board from a host PC using the USB interface.
Instructions for installing the USB driver can be found in the `Synaptics Astra Documentation <https://synaptics-astra.github.io/doc/v/1.6.0/linux/index.html#installing-the-winusb-driver-windows-only>`__.

Astra Update
------------

The ``astra-update`` tool replaces ``usbboot`` as the preferred tool for updating eMMC and SPI images on Astra Machina. Copy the eMMCimg or SPI image directory
to the usb-tool directory and run either ``update_emmc.bat`` or ``update_spi.bat`` on Windows or ``update_emmc.sh`` or ``update_spi.sh`` on Linux or Mac.
Instructions for using the tool can be found in the Synaptics Astra Documentation.

Previous versions of ``usbboot`` can be found on the `releases page <https://github.com/synaptics-astra/usb-tool/releases/>`__.
