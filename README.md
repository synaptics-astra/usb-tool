# USB Boot Utility for SL261x

## Overview

The USB Boot Utility is a Python-based command-line tool used for:

-   Loading keys and SPK

-   Running M52 Bootloader

-   Running System Manager (SM) firmware

-   Running A-Core software

-   Flashing eMMC (GPT, Boot partitions, and User partitions)

The tool communicates with the target over USB CDC (Serial) and supports
automatic port detection based on VID/PID.

## Prerequisites

#### Software Requirements

-   Python 3.13 or later

#### Python packages:

-   *pip install pyserial*

## Script Invocation Format

python usb_boot_tool.py \--op \<operation\> \[additional arguments\]

> **Note:** The usb boot tool auto-detects the USB CDC port.

## Supported Operations (\--op)

| Operation   | Description                                   |
|------------|-----------------------------------------------|
| run-spk    | Upload keys, SPK, and M52 bootloader           |
| version-bl| Read M52 Bootloader version                   |
| version-sm| Read System Manager version                   |
| run-sm     | Load and run System Manager firmware           |
| run-acore  | Load and run A-Core software                  |
| emmc       | Flash eMMC (GPT + partitions)                 |

## Operation Details & Usage

### Run SPK (Mandatory First Step)

#### **Uploads:**

-   key.bin

-   spk.bin

-   m52bl.bin

### 

### Read Bootloader Version

#### **Internal flow:**

1.  Runs SPK

2.  Queries Bootloader version

### Read System Manager (SM) Version

#### **Internal flow:**

1.  Run SPK

2.  Run SM

3.  Query SM version

### Run System Manager (SM)

Required argument: \--sm

#### **Example:**

python usb_boot_tool.py \--op run-sm \--sm sysmgr.subimg

### Run A-Core Software

Required arguments: \--bl, \--tzk and --sm

#### **Example:**

python usb_boot_tool.py \--op run-acore \--sm sysmgr.subimg\--bl
bl.subimg \--tzk tzk.subimg

#### **Internal flow:**

1.  Run SPK

2.  Run SM

3.  Load BL → Execute

4.  Load TZK → Execute

## eMMC Flashing Service

### Required Directory Structure

The image directory must contain:

eMMCimg/

├── emmc_part_list

├── emmc_image_list

├── gpt.bin

├── \*.subimg.gz

### Flash All Partitions:

1.  Parses emmc_part_list

2.  Parses emmc_image_list

#### **Automatically flashes:**

-   GPT

-   Boot partitions (b1, b2)

-   User partitions (sd1, sd2, ...)
