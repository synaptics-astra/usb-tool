#!/bin/bash

ASTRA_UPDATE_BIN_PATH="./bin/linux/x86_64"

HOST_OS="$(uname -s)"
HOST_ARCH="$(uname -m)"


if [[ "${HOST_OS}" == "Darwin" ]]; then
	if [[ "${HOST_ARCH}" == "arm64" ]]; then
		ASTRA_UPDATE_BIN_PATH="./bin/mac/arm64"
	else
		ASTRA_UPDATE_BIN_PATH="./bin/mac/x86_64"
	fi
fi

# sudo required to access USB devices
sudo ${ASTRA_UPDATE_BIN_PATH}/astra-update