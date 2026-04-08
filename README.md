# USB Boot Utility — User Guide

This guide describes how to use the USB Boot Tool CLI to load bootloader, System Manager, and A-Core images, as well as flash eMMC partitions onto the sl2610 device.

> [!IMPORTANT]
> This tool is only for SL261x.
> For SL16x0 see https://github.com/synaptics-astra/usb-tool/tree/main.

---

## Table of Contents

- [1. Overview](#1-overview)
- [2. Prerequisites](#2-prerequisites)
  - [2.1 Software Requirements](#21-software-requirements)
  - [2.2 Python Packages](#22-python-packages)
- [3. Script Invocation Format](#3-script-invocation-format)
- [4. Supported Operations (`--op`)](#4-supported-operations---op)
- [5. Operation Details & Usage](#5-operation-details--usage)
  - [5.1 Run SPK](#51-run-spk-mandatory-first-step)
  - [5.2 Read Bootloader Version](#52-read-bootloader-version)
  - [5.3 Read System Manager (SM) Version](#53-read-system-manager-sm-version)
  - [5.4 Run System Manager (SM)](#54-run-system-manager-sm)
  - [5.5 Run A-Core Software](#55-run-a-core-software)
  - [5.6 DDR Type Selection (`--ddr-type`)](#56-ddr-type-selection---ddr-type)
- [6. eMMC Flashing Service](#6-emmc-flashing-service)
  - [6.1 Required Directory Structure](#61-required-directory-structure)
  - [6.2 Flash All Partitions](#62-flash-all-partitions)
  - [6.3 Flash Only System Manager](#63-flash-only-system-manager)
- [7. Running on WSL (Windows)](#7-running-on-wsl-windows)
  - [7.1 Additional Prerequisites](#71-additional-prerequisites)
  - [7.2 USB CDC VID:PID Reference](#72-usb-cdc-vidpid-reference)
  - [7.3 Flashing Workflow Overview](#73-flashing-workflow-overview)
  - [7.4 Step-by-Step: Bind & Flash](#74-step-by-step-bind--flash)
  - [7.5 Quick Reference — Command Sequence](#75-quick-reference--command-sequence)
  - [7.6 Important Notes](#76-important-notes)

---

## 1. Overview

The USB Boot Utility is a Python-based command-line tool used for:

- Loading keys and SPK
- Running M52 Bootloader
- Running System Manager (SM) firmware
- Running A-Core software
- Flashing eMMC (GPT, Boot partitions, and User partitions)

The tool communicates with the target over USB CDC (Serial) and supports automatic port detection based on VID/PID.

---

## 2. Prerequisites

### 2.1 Software Requirements

- Python 3.13 or later

### 2.2 Python Packages

```bash
pip install pyserial
```

---

## 3. Script Invocation Format

```bash
python usb_boot_tool.py --op <operation> [additional arguments]
```

> **Note:** The USB boot tool auto-detects the USB CDC port.

---

## 4. Supported Operations (`--op`)

| Operation    | Description                          |
|--------------|--------------------------------------|
| `run-spk`    | Upload keys, SPK, and M52 bootloader |
| `version-bl` | Read M52 Bootloader version          |
| `version-sm` | Read System Manager version          |
| `run-sm`     | Load and run System Manager firmware |
| `run-acore`  | Load and run A-Core software         |
| `emmc`       | Flash eMMC (GPT + partitions)        |

---

## 5. Operation Details & Usage

### 5.1 Run SPK

Uploads the following files:

```bash
python usb_boot_tool.py --op run-spk
```

- `key.bin`
- `spk.bin`
- `m52bl.bin`

---

### 5.2 Read Bootloader Version

```bash
python usb_boot_tool.py --op version-bl
```

**Internal flow:**

1. Runs SPK
2. Queries Bootloader version

---

### 5.3 Read System Manager (SM) Version

**Required argument:** `--sm`

```bash
python usb_boot_tool.py --op version-sm –sm <path to sysmgr.subimg.gz>
```

**Internal flow:**

1. Run SPK
2. Run SM
3. Query SM version

---

### 5.4 Run System Manager (SM)

**Required argument:** `--sm`

```bash
python usb_boot_tool.py --op run-sm --sm <path_to_sysmgr.subimg>
```

**Example:**

```bash
python usb_boot_tool.py --op run-sm --sm sysmgr.subimg
```

**Internal flow:**

1. Run SPK
2. Run SM

---

### 5.5 Run A-Core Software

**Required arguments:** `--bl`, `--tzk`, and `--sm`

```bash
python usb_boot_tool.py --op run-acore \
--sm <path_to_sysmgr.subimg> \
--bl <path_to_bl.subimg> \
--tzk <path_to_tzk.subimg>
```

**Example:**

```bash
python usb_boot_tool.py --op run-acore --sm sysmgr.subimg.gz --bl bl.subimg --tzk tzk.subimg
```

**Simplified example using `--ddr-type` (recommended):**

```bash
python usb_boot_tool.py --op run-acore --ddr-type ddr4
```

See [Section 5.6](#56-ddr-type-selection---ddr-type) for details.

**Internal flow:**

1. Run SPK
2. Run SM
3. Load BL → Execute
4. Load TZK → Execute

---

### 5.6 DDR Type Selection (`--ddr-type`)

The `--ddr-type` argument automatically resolves `sysmgr.subimg`, `bl.subimg`, `tzk.subimg`, and `m52bl.bin` from the corresponding DDR-specific subfolder, eliminating the need to pass individual file paths.

| `--ddr-type` value | Folder used |
|---|---|
| `ddr3` | `USB_BOOT_TOOL_DDR3/` |
| `ddr4` | `USB_BOOT_TOOL_DDR4/` |
| `ddr4-1x16` | `USB_BOOT_TOOL_DDR4_1x16/` |
| `lpddr4` | `USB_BOOT_TOOL_LPDDR4/` |

**Usage:**

```bash
python usb_boot_tool.py --op run-acore --ddr-type <ddr_type>
```

**Example:**

```bash
python usb_boot_tool.py --op run-acore --ddr-type lpddr4
```

> **Note:** `--ddr-type` can be combined with any operation that uses SM, BL, TZK, or M52BL files (e.g. `run-sm`, `version-sm`, `run-acore`). Individual file path arguments (`--sm`, `--bl`, `--tzk`, `--m52bl`) can still be provided alongside `--ddr-type` to override specific files.

---

## 6. eMMC Flashing Service

### 6.1 Required Directory Structure

The image directory must contain:

```
eMMCimg/
├── emmc_part_list
├── emmc_image_list
├── gpt.bin
└── *.subimg.gz
```

> **Note:** The eMMC flash service requires [5.4 Run System Manager](#54-run-system-manager-sm) to be executed beforehand.

---

### 6.2 Flash All Partitions

```bash
python usb_boot_tool.py --op emmc --img-dir <path_to_eMMCimg>
```

**Internal flow:**

1. Parses `emmc_part_list`
2. Parses `emmc_image_list`

**Automatically flashes:**

- GPT
- Boot partitions (`b1`, `b2`)
- User partitions (`sd1`, `sd2`, ...)

> **Note:** To flash a specific partition, keep only the corresponding partition info in `emmc_image_list`.

---

### 6.3 Flash Only System Manager

**Required arguments:** `--sm` and `--sm-image`

```bash
python usb_boot_tool.py --op emmc-sm \
--sm <path to USB sysmgr.subimg.gz> \
--sm-image <path to sysmgr.subimg.gz to be flashed>
```

**Example:**

```bash
python usb_boot_tool.py --op emmc-sm --sm sysmgr.subimg.gz --sm-image sysmgr.subimg.gz
```

---

## 7. Running on WSL (Windows)

When running the USB Boot Tool inside WSL, the USB CDC device must be forwarded from Windows into the Linux environment using `usbipd`. The device re-enumerates at different stages of flashing, so the bind and attach steps must be repeated accordingly.

### 7.1 Additional Prerequisites

| Requirement | Notes |
|---|---|
| **usbipd-win** installed on Windows | Required to forward USB devices to WSL |
| **WSL** set up and running | Ubuntu or any compatible distro |
| **Python 3** and **pyserial** available in WSL | Must be accessible from the WSL terminal |

> **Tip:** To verify usbipd is installed, run `usbipd --version` in a Windows terminal.

---

### 7.2 USB CDC VID:PID Reference

The device presents different USB identities at different flashing stages:

| Stage | VID | PID | Description |
|---|---|---|---|
| Initial Boot & BL Flash | `0x06CB` | `0x019E` | Device in bootloader mode (used for SPK, BL, keys upload) |
| After SM Flash | `0xCAFE` | `0x4002` | System Manager (SM) is running |

---

### 7.3 Flashing Workflow Overview

```
[Device in BL mode]
       │
       ▼
 Step 1: Bind & Attach 0x06CB:0x019E  (Admin Windows Terminal)
       │
       ▼
 Step 2: Flash SPK  →  python usb_boot_tool.py --op run-spk
       │
       ▼
 Step 3: Device re-enumerates as 0x06CB:0x019E (M52BL CDC)
         Bind & Attach again
       │
       ▼
 Step 4: Flash SM   →  python usb_boot_tool.py --op run-sm --sm <path>
       │
       ▼
 Step 5: Device re-enumerates as 0xCAFE:0x4002 (SM CDC)
         Bind & Attach
       │
       ▼
 Step 6: Flash eMMC →  python usb_boot_tool.py --op emmc --img-dir <path>
```

---

### 7.4 Step-by-Step: Bind & Flash

#### Step 1 — Identify the USB Device (BL Flash CDC)

Open a **Windows Terminal as Administrator** and list connected USB devices:

```powershell
usbipd list
```

Look for the device with VID:PID `06CB:019E`. Note its `BUSID` (e.g., `2-4`).

---

#### Step 2 — Bind the BL Flash CDC

Still in the **Administrator Windows Terminal**:

```powershell
usbipd bind --busid <bus_id> --force
```

> **Note:** `--force` is required to override any existing driver binding.

---

#### Step 3 — Attach the Device to WSL

Open a **second Windows Terminal** (no admin required) and attach the bound device:

```powershell
usbipd attach --wsl --busid <bus_id>
```

Verify the device is visible inside WSL:

```bash
# Run inside WSL
lsusb | grep "06cb"
```

---

#### Step 4 — Flash the SPK Image

```bash
python usb_boot_tool.py --op run-spk
```

**Expected output:**
```
Uploading key.bin...
Uploading spk.bin...
Uploading m52bl.bin...
SPK/BL upload complete!
```

---

#### Step 5 — Re-bind & Attach M52BL CDC

After the SPK flash, the device re-enumerates (still as `0x06CB:0x019E`, now as M52BL CDC). Repeat bind and attach:

```powershell
# In Admin Windows Terminal
usbipd bind --busid <bus_id> --force

# In second Windows Terminal
usbipd attach --wsl --busid <bus_id>
```

> **Check:** Run `usbipd list` again if the `BUSID` has changed after re-enumeration.

---

#### Step 6 — Flash the System Manager (SM) Image

Back in WSL, run:

```bash
python usb_boot_tool.py --op run-sm --sm <path_to_sysmgr.subimg>
```

**Example:**

```bash
python usb_boot_tool.py --op run-sm --sm default_images/default_sysmgr.subimg
```

**Expected output:**
```
Waiting for SM CDC to enumerate...
SM CDC detected - uploading/flashing SM...
SM flash complete!
[SM Flashing] SUCCESS!
```

---

#### Step 7 — Bind & Attach the SM CDC

Once SM is running, the device enumerates as `0xCAFE:0x4002`. Run `usbipd list` to find the new `BUSID`, then:

```powershell
# In Admin Windows Terminal
usbipd bind --busid <new_bus_id> --force

# In second Windows Terminal
usbipd attach --wsl --busid <new_bus_id>
```

---

#### Step 8 — Flash eMMC

```bash
python usb_boot_tool.py --op emmc --img-dir <path_to_eMMC_image_directory>
```

**Example:**

```bash
python usb_boot_tool.py --op emmc --img-dir /home/user/images/eMMCimg/
```

---

### 7.5 Quick Reference — Command Sequence

```powershell
# [Admin Windows Terminal]
usbipd list                              # Find BUSID for 06CB:019E
usbipd bind --busid <bus_id> --force

# [Second Windows Terminal]
usbipd attach --wsl --busid <bus_id>
```

```bash
# [WSL Terminal] — from Image_flashing/SL2610/
python usb_boot_tool.py --op run-spk
```

```powershell
# [Admin Windows Terminal] — after SPK flash (device re-enumerates)
usbipd bind --busid <bus_id> --force

# [Second Windows Terminal]
usbipd attach --wsl --busid <bus_id>
```

```bash
# [WSL Terminal]
python usb_boot_tool.py --op run-sm --sm <path_to_sysmgr.subimg>
```

```powershell
# [Admin Windows Terminal] — after SM flash (device now 0xCAFE:0x4002)
usbipd list                              # Find new BUSID
usbipd bind --busid <new_bus_id> --force

# [Second Windows Terminal]
usbipd attach --wsl --busid <new_bus_id>
```

```bash
# [WSL Terminal]
python usb_boot_tool.py --op emmc --img-dir <path_to_eMMC_image_directory>
```

---

### 7.6 Important Notes

- All `usbipd bind` commands **must be run in a Windows Terminal with Administrator privileges**.
- `usbipd attach` does **not** require admin and can be run in a regular Windows Terminal.
- After flashing is complete, **unbind the USB ports** to restore normal Windows usage:
  ```powershell
  usbipd unbind --busid <bus_id>
  ```