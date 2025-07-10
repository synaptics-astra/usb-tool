#!/bin/sh

ASTRA_UPDATE_BIN_PATH="./bin/linux/x86_64"

HOST_OS="$(uname -s)"
HOST_ARCH="$(uname -m)"


if [ "${HOST_OS}" = "Darwin" ]; then
	if [ "${HOST_ARCH}" = "arm64" ]; then
		ASTRA_UPDATE_BIN_PATH="./bin/mac/arm64"
	else
		ASTRA_UPDATE_BIN_PATH="./bin/mac/x86_64"
	fi
fi

SPI_IMAGE_PATH=""

if [ -d "sl1680" ]; then
    SPI_IMAGE_PATH="sl1680"
elif [ -d "sl1640" ]; then
    SPI_IMAGE_PATH="sl1640";
elif [ -d "sl1620" ]; then
    SPI_IMAGE_PATH="sl1620"
fi

if [ -n "${SPI_IMAGE_PATH}" ]; then
    # sudo required to access USB devices
    sudo ${ASTRA_UPDATE_BIN_PATH}/astra-update -f ${SPI_IMAGE_PATH}
else
    echo "No SPI images detected. Download an image from https://github.com/synaptics-astra/spi-u-boot"
fi
