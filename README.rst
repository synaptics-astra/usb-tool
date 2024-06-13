Synaptics Astra USB Tools
=========================

This repository contains the USB tools and drivers needed to flash images to the Synaptics Astra RDK boards.

USB Driver
----------

The ``Synaptics_WinUSB_Driver`` directory contains the Windows USB driver which is needed to communicate with a Synaptics Astra RDK board from a host PC using the USB interface.
Instructions for installing the USB driver can be found in the `Synaptics Astra Documentation <https://synaptics-astra.github.io/doc/v/1.0.0/linux/index.html#installing-the-winusb-driver-windows-only>`__.

USBBoot
-------

The ``usbboot_sl16xx_uboot`` directories contain the tools used to flash images onto Synaptics Astra RDK boards. Each version of the RDK contain's its own tool so
please ensure you use the correct tool for the version of the RDK you have. Instructions for using the tool can be found  in the 
`Synaptics Astra Documentation <https://synaptics-astra.github.io/doc/v/1.0.0/linux/index.html#running-the-usb-boot-tool>`__.
