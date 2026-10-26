Synaptics Astra USB Tools
=========================

This repository contains the USB tools and drivers needed to flash images to the Synaptics Astra RDK boards.

.. note::

  The Synaptics Coralboard™ Google I/O Edition requires the `astra-update-v2.0.3 <https://github.com/synaptics-astra/usb-tool/releases/tag/astra-update-v2.0.3>`__
  version of the`usb-tool in order to boot. Newer versions of ``usb-tool`` only support the Synaptics Coralboard SL currently available for purchase.

USB Driver
----------

The ``Synaptics_WinUSB_Driver`` directory contains the Windows USB driver which is needed to communicate with a Synaptics Astra SL16x0 RDK board from a host PC using the USB interface.
Instructions for installing the USB driver can be found in the `Synaptics Astra Documentation <https://synaptics-astra.github.io/doc/v/latest/linux/index.html#installing-winusb-for-sl16x0-on-windows>`__.

SL261x requires the ``Google USB Driver`` to communicate with a Synaptics Astra SL261x RDK board from a host PC using the USB interface.
Instructions for installing the USB driver can be found in the `Synaptics Astra Documentation <https://synaptics-astra.github.io/doc/v/latest/linux/index.html#installing-the-google-usb-driver-for-sl2610-on-windows>`__.

Astra Update
------------

The ``astra-update`` tool replaces ``usbboot`` as the preferred tool for updating eMMC and SPI images on Astra Machina. Copy the eMMCimg or SPI image directory
to the usb-tool directory and run either ``update_emmc.bat`` or ``update_spi.bat`` on Windows or ``update_emmc.sh`` or ``update_spi.sh`` on Linux or Mac.
Instructions for using the tool can be found in the Synaptics Astra Documentation.

The ``astra-update`` source code repository and detailed documentation can be found at the `Astra Update Source Repository <https://github.com/synaptics-astra/astra-update>`__.

Previous versions of ``usbboot`` can be found on the `releases page <https://github.com/synaptics-astra/usb-tool/releases/>`__.
