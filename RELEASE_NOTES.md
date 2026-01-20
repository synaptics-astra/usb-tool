# Astra Update Release Notes

## v1.0.6

* Fix incorrectly reporting an error when the final operation is erase or format

https://github.com/synaptics-astra/astra-update/releases/tag/v1.0.6

## v1.0.5

* Support Multiple Instances of AstraDeviceManager
* Check if the boot-images option is set in astra-boot to prevent exception
* Add DDR Type Parameter for Images
* Call notify_all on m_writeCompleteCV when the USB device closes

https://github.com/synaptics-astra/astra-update/releases/tag/v1.0.5

## v1.0.4

* Make reset after successful update user configurable 

https://github.com/synaptics-astra/astra-update/releases/tag/v1.0.4

## v1.0.3

* Add support for multiple SPI images
* Minor Fixes

https://github.com/synaptics-astra/astra-update/releases/tag/v1.0.3

## v1.0.2

* Fix libusb_exit() on Windows
* Check if a device is already in use in Windows specific device detection

https://github.com/synaptics-astra/astra-update/releases/tag/v1.0.2

## v1.0.1

* Add option to filter USB devices based on the port.
* Fix issue when update fails when boot image contains linux files.

https://github.com/synaptics-astra/astra-update/releases/tag/v1.0.1

## v1.0.0

Initial release of astra-update and astra-boot USB utilities.