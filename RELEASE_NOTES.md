# Astra Update Release Notes

## v2.0.3

* Fix order of image file and address in NAND flash command
* Support U-Boot 2025 commands with SL16x0

## v2.0.2

* Add support for SL2610 to generate_boot_manifest.py
* Print out which boot image was selected in AstraDeviceManager::Update()
* Add support for 512MB memory layouts

  https://github.com/synaptics-astra/astra-update/releases/tag/v2.0.2

## v2.0.1

* Coralboard and SPI Flash Improvements

  https://github.com/synaptics-astra/astra-update/releases/tag/v2.0.1

## v2.0.0

* Fix errors found when compiling with newer versions of GCC
* Add SL26XX (SL261x) device support with CDC transport and eMMC update

  https://github.com/synaptics-astra/astra-update/releases/tag/v2.0.0

## v1.1.0

* Improve error handling and optimize libusb calls

  https://github.com/synaptics-astra/astra-update/releases/tag/v1.1.0

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