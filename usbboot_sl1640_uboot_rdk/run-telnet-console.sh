#!/bin/bash

USB_BOOT_BIN_PATH="./bin/linux/x86_64"

HOST_OS="$(uname -s)"
HOST_ARCH="$(uname -m)"


if [[ "${HOST_OS}" == "Darwin" ]]; then
	if [[ "${HOST_ARCH}" == "arm64" ]]; then
		USB_BOOT_BIN_PATH="./bin/mac/arm64"
	else
		USB_BOOT_BIN_PATH="./bin/mac/x86_64"
	fi
fi

# sudo required to access USB devices and semaphores
sudo ${USB_BOOT_BIN_PATH}/usb_boot 06CB 00B0 ./images/ 8141
