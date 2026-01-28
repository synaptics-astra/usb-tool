#!/usr/bin/env python3
"""
USB boot utility for SM, A-core and eMMC flashing.
"""

import sys
import os
import time
import struct
import serial
import serial.tools.list_ports
import binascii
import uuid
import gzip
import shutil
import argparse
import tempfile
from typing import Optional, List, Iterable, Tuple, Union
from serial.tools import list_ports

# Serial Defaults
DEFAULT_BAUD            = 230400
DEFAULT_TIMEOUT         = 2.0
EMMC_OP_TIMEOUT         = 240.0

# Protocol Constants
HOST_SYNC1              = 0x5B
HOST_SYNC2              = 0x5A
OP_HEADER_SIZE          = 32
HOST_HDR_SIZE           = 8

# Service IDs
SERVICE_ID_BOOT         = 0x33
HOST_API_SERVICE_ID     = 0xD

# Opcodes
OPCODE_VERSION          = 0x0A
OPCODE_RUN_IMG          = 0x0B
OPCODE_EXEC_0C          = 0x0C
OPCODE_EMMC_OP          = 0x0F
OPCODE_UPLOAD           = 0x12

# Host API Opcodes
HOST_API_OPCODE_GENERIC = 0x12
HOST_API_OPCODE_EMMC    = 0x0F
HOST_API_OPCODE_VERSION = 0x0A
HOST_API_OPCODE_EXEC    = 0x0C

# Memory Addresses
ADDR_SM_LOAD            = 0xB4A00000
ADDR_AC_LOAD            = 0xBA100000

# Image Types
IMG_TYPE_BL             = 0x00020017
IMG_TYPE_TZK            = 0x00020014
IMG_TYPE_SM             = 0x00000012
IMG_TYPE_GPT            = 0x10
IMG_TYPE_OPTEE          = 0x00020014
IMG_TYPE_GENERIC        = 0x00000000

# Sizes
BLOCK_SIZE              = 512
MB_SIZE                 = 1024 * 1024
CHUNK_SIZE_MB           = 32
LARGE_FILE_THRESHOLD_MB = 100
STREAM_CHUNK_SIZE       = 3 * 1024 * 1024 

# GPT Constants
PART_ENTRIES            = 128
PART_ENTRY_SIZE         = 128
GPT_TABLE_SIZE          = 0x4000
GPT_HEADER_SIZE         = 92
GPT_REVISION            = 0x00010000
DISK_GUID               = uuid.uuid4()
PART_TYPE_GUID          = uuid.UUID("EBD0A0A2-B9E5-4433-87C0-68B6B72699C7")

# CONSTANT FOR SMART ARGS
USE_DEFAULT             = "USE_DEFAULT_FILENAME"

# USB CDC Definitions
USB_CDC_SPK             = 0
USB_CDC_M52BL           = 0
USB_CDC_SM              = 1
usb_cdc_port_default    = [[(0x06CB, 0x019E)], [(0xCAFE, 0x4002)]]

def _log(level, msg):
    print(f"[{level}] {msg}")

def log_info(msg):  _log("INFO", msg)
def log_error(msg): _log("ERROR", msg)
def log_warn(msg):  _log("WARN", msg)

def crc32(data): return binascii.crc32(data) & 0xFFFFFFFF

def _normalize_id_list(ids: Optional[Iterable[Union[int, str]]]) -> Optional[List[int]]:
    """Normalize a list of IDs that may be given as ints or hex strings to a list of ints."""
    if ids is None:
        return None
    normalized: List[int] = []
    for v in ids:
        if isinstance(v, int):
            normalized.append(v)
        elif isinstance(v, str):
            s = v.strip().lower()
            if s.startswith("0x"):
                normalized.append(int(s, 16))
            else:
                try:
                    normalized.append(int(s, 16))
                except ValueError:
                    normalized.append(int(s, 10))
        else:
            raise TypeError(f"Unsupported ID type: {type(v)}")
    return normalized

def find_cdc_port(
    vid: Optional[int] = None,
    pid: Optional[int] = None,
    serial_number: Optional[str] = None,
    wait_seconds: float = 0,
    poll_interval: float = 0.5,
    vids: Optional[Iterable[Union[int, str]]] = None,
    pids: Optional[Iterable[Union[int, str]]] = None,
    vid_pid_pairs: Optional[Iterable[Tuple[Union[int, str], Union[int, str]]]] = None,
) -> Optional[str]:
    """Find a USB CDC serial port with advanced filtering."""
    vids_n = _normalize_id_list(vids)
    pids_n = _normalize_id_list(pids)
    pairs_n: Optional[List[Tuple[int, int]]] = None
    if vid_pid_pairs:
        pairs_n = []
        for v, p in vid_pid_pairs:
            vn = _normalize_id_list([v])[0]
            pn = _normalize_id_list([p])[0]
            pairs_n.append((vn, pn))

    if vid is not None:
        vids_n = (vids_n or []) + [vid]
    if pid is not None:
        pids_n = (pids_n or []) + [pid]

    deadline = time.time() + max(0, wait_seconds)
    while True:
        candidates: List[str] = []
        for port in list_ports.comports():
            p_vid = getattr(port, 'vid', None)
            p_pid = getattr(port, 'pid', None)
            p_sn  = getattr(port, 'serial_number', None)
            p_dev = port.device

            if serial_number is not None and p_sn != serial_number:
                continue
            if pairs_n:
                if (p_vid, p_pid) not in pairs_n:
                    continue
            if vids_n and p_vid not in vids_n:
                continue
            if pids_n and p_pid not in pids_n:
                continue

            # Heuristic fallback
            if not (serial_number or pairs_n or vids_n or pids_n):
                name = (p_dev or "").lower()
                if not (name.startswith('com') or 'ttyacm' in name or 'ttyusb' in name or 'usbmodem' in name):
                    continue
            candidates.append(p_dev)

        if candidates:
            return candidates[0]

        if time.time() >= deadline:
            return None
        time.sleep(poll_interval)

def auto_detect_usb_cdc_port(vid_pid_pairs: Optional[Iterable[Tuple[Union[int, str], Union[int, str]]]]):
    """Wrapper to detect port and print status."""
    pairs_n = []
    if vid_pid_pairs:
        for v, p in vid_pid_pairs:
            vn = _normalize_id_list([v])[0]
            pn = _normalize_id_list([p])[0]
            pairs_n.append((vn, pn))
            formatted = ", ".join(f"VID:0x{vid:04X}, PID:0x{pid:04X}" for vid, pid in pairs_n)
            print(f"Auto-detecting {formatted} serial port...")
    else:
        print("Auto-detecting serial port...")

    detected = find_cdc_port(vid_pid_pairs=vid_pid_pairs, wait_seconds=10)
    print("Syna USB CDC port detected:", detected)
    if detected:
        return detected
    else:
        return None

def pack_spk_cmd(ser, op, payload):
    """Pack and send SPK command."""
    header = struct.pack("<BBBBIIIIIII", 0x5B, 0x5A, 0x33, op, len(payload), 0, 0,0,0,0,0)
    ser.write(header + payload)
    resp = ser.read(HOST_HDR_SIZE)
    if len(resp) != 8:
        print(" ERROR: No or incomplete response")
        return False
    _, _, srv, opc, rc0, rc1, rc2, rc3 = resp
    rc = rc0 | (rc1<<8) | (rc2<<16) | (rc3<<24)
    if rc != 0:
        print(" Transfer returned error")
        return False
    return True

def upload_file(ser_port, op, ser_baud, input_file):
    """Uploader for SPK/Keys."""
    size = os.path.getsize(input_file)
    with open(input_file, "rb") as f, serial.Serial(ser_port, ser_baud, timeout=2) as ser:
        start = time.time()
        payload = f.read()
        ok = pack_spk_cmd(ser, op, payload)
        if not ok:
            print("\n Upload stopped due to error\n")
            return
        elapsed = time.time() - start
        speed = size / 1024 / 1024 / elapsed
        print(f" ✔  {os.path.basename(input_file)} UPLOADED ({elapsed:.2f}s @ {speed:.2f}MB/s)")

def gunzip_if_needed(path):
    if path.endswith(".gz"):
        # Remove .gz
        dst = path[:-3]
        log_info(f"Auto-Decompressing {os.path.basename(path)} -> {os.path.basename(dst)}")
        try:
            with gzip.open(path, "rb") as f_in, open(dst, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        except Exception as e:
            log_error(f"Failed to decompress {path}: {e}")
            return path
        return dst
    return path

def resolve_file_path(path):
    if not path: return None
    clean_path = os.path.abspath(path)

    if clean_path.endswith(".gz"):
        if os.path.exists(clean_path):
            return gunzip_if_needed(clean_path)
    else:
        gz_candidate = clean_path + ".gz"
        if os.path.exists(gz_candidate):
            return gunzip_if_needed(gz_candidate)

    if os.path.exists(clean_path):
        return clean_path

    return None

def print_progress(iteration, total, prefix='', suffix='', decimals=1, length=40, fill='#'):
    if total == 0: return
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    if iteration == total:
        sys.stdout.write(f'\r{prefix} |{bar}| {percent}% {suffix}\n')
    else:
        sys.stdout.write(f'\r{prefix} |{bar}| {percent}% {suffix}')
    sys.stdout.flush()

def parse_image_list_to_map(path):
    """Parses emmc_image_list into a map."""
    action_map = {}
    if os.path.exists(path):
        with open(path, "r") as f:
            for line in f:
                parts = [x.strip() for x in line.strip().split(",")]
                if len(parts) >= 2 and not line.strip().startswith("#"):
                    filename = parts[0]
                    target   = parts[1].lower()

                    if "rootfs_s.subimg" in filename:
                        filename = "rootfs.subimg.gz"

                    if target not in action_map:
                        action_map[target] = []

                    if filename not in action_map[target]:
                        action_map[target].append(filename)

    return action_map

def get_image_type_from_name(part_name):
    """Derives the Image Type ID based on partition name patterns."""
    name = part_name.lower()

    if "sysmgr" in name: return IMG_TYPE_SM
    if "bl" in name and "m52" not in name: return IMG_TYPE_BL
    if "tzk" in name: return IMG_TYPE_OPTEE

    if any(x in name for x in ["key", "boot", "firmware", "rootfs", "home"]): 
        return IMG_TYPE_GPT

    return IMG_TYPE_GPT

def uuid_to_gpt_bytes(u):
    b = u.bytes
    return b[0:4][::-1] + b[4:6][::-1] + b[6:8][::-1] + b[8:]

def build_protective_mbr():
    mbr = bytearray(512)
    entry = struct.pack("<B3sB3sII", 0x00, b"\x00\x02\x00", 0xEE, b"\xFF\xFF\xFF", 1, 0xFFFFFFFF)
    mbr[0x1BE:0x1BE+16] = entry
    mbr[510] = 0x55; mbr[511] = 0xAA
    return bytes(mbr)

def build_partition_entry(name, start_lba, end_lba):
    part_guid = uuid.uuid4()
    entry = bytearray(PART_ENTRY_SIZE)
    entry[0:16] = uuid_to_gpt_bytes(PART_TYPE_GUID)
    entry[16:32] = uuid_to_gpt_bytes(part_guid)
    entry[32:40] = struct.pack("<Q", start_lba)
    entry[40:48] = struct.pack("<Q", end_lba)
    entry[48:56] = struct.pack("<Q", 0)
    name_utf16 = name.encode("utf-16le")[:72]
    entry[56:56+len(name_utf16)] = name_utf16
    return bytes(entry)

def parse_emmc_part_list(path):
    parts = []
    if not os.path.exists(path):
        raise FileNotFoundError(f"Partition list not found: {path}")
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"): continue
            fields = [x.strip() for x in line.split(",") if x.strip()]
            if len(fields) < 3:
                ws = line.split()
                if len(ws) >= 3: fields = ws[:3]
                else: continue
            name = fields[0]
            start_mb = int(fields[1], 0)
            size_mb = int(fields[2], 0)
            if size_mb == 0: continue
            parts.append((name, start_mb, size_mb))
    return parts

def build_gpt_primary(part_desc_list):
    part_bytes = bytearray(PART_ENTRIES * PART_ENTRY_SIZE)
    previous_end_lba = 0
    max_used_lba = 0
    LBAS_PER_MB = MB_SIZE // BLOCK_SIZE

    for idx, (name, start_mb, size_mb) in enumerate(part_desc_list):
        if start_mb > 0: start_lba = start_mb * LBAS_PER_MB
        else: start_lba = previous_end_lba + 1
        size_lbas = size_mb * LBAS_PER_MB
        end_lba = start_lba + size_lbas - 1
        previous_end_lba = end_lba
        entry_bin = build_partition_entry(name, start_lba, end_lba)
        part_bytes[idx*PART_ENTRY_SIZE : (idx+1)*PART_ENTRY_SIZE] = entry_bin
        if end_lba > max_used_lba: max_used_lba = end_lba

    part_array_crc = crc32(part_bytes)
    header = bytearray(512)
    struct.pack_into("<8sI I I I", header, 0, b"EFI PART", GPT_REVISION, GPT_HEADER_SIZE, 0, 0)
    struct.pack_into("<Q Q Q Q", header, 24, 1, 0, 34, max_used_lba)
    header[56:72] = uuid_to_gpt_bytes(DISK_GUID)
    struct.pack_into("<Q I I I", header, 72, 2, PART_ENTRIES, PART_ENTRY_SIZE, part_array_crc)
    hdr_crc = crc32(header[:GPT_HEADER_SIZE])
    struct.pack_into("<I", header, 16, hdr_crc)
    part_bytes += b"\x00" * (GPT_TABLE_SIZE - len(part_bytes))
    return build_protective_mbr() + header + part_bytes, GPT_TABLE_SIZE // BLOCK_SIZE

class DeviceHandler:
    def __init__(self, port, baud, raw_mode=False):
        self.port = port
        self.baud = baud
        self.ser = None
        self.raw_mode = raw_mode

    def __enter__(self):
        self.ser = serial.Serial(self.port, self.baud, timeout=DEFAULT_TIMEOUT)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.ser: self.ser.close()

    def _build_host_header(self, service_id, opcode, payload_len):
        third = (service_id & 0x3F)
        return struct.pack("<BBBB I", HOST_SYNC1, HOST_SYNC2, third, opcode, payload_len)

    def _build_op_header(self, service_id, opcode, addr=0, img_type=0, is_last=0, num_words=0):
        return struct.pack("<BBBB I I I I I I I",
            HOST_SYNC1, HOST_SYNC2, service_id, opcode, 0, num_words, 0, addr, img_type, 1 if is_last else 0, 0)

    def send_packet(self, service_id, opcode, payload=b"", host_opcode=None, addr=0, img_type=0, is_last=False, timeout=None, num_words=None):
        
        pad = (4 - (len(payload) % 4)) % 4
        payload_padded = payload + (b'\xFF' * pad)
        
        if num_words is None:
            final_num_words = len(payload_padded) // 4
        else:
            final_num_words = num_words

        inner_hdr = self._build_op_header(service_id, opcode, addr, img_type, is_last, final_num_words)
        inner_packet = inner_hdr + payload_padded

        final_packet = inner_packet
        if not self.raw_mode:
            if host_opcode is None: host_opcode = HOST_API_OPCODE_GENERIC
            host_hdr = self._build_host_header(HOST_API_SERVICE_ID, host_opcode, len(inner_packet))
            final_packet = host_hdr + inner_packet

        if timeout:
            old_timeout = self.ser.timeout
            self.ser.timeout = timeout
            
        self.ser.write(final_packet)
        self.ser.flush()

        resp_hdr = self.ser.read(HOST_HDR_SIZE)
        if timeout: self.ser.timeout = old_timeout

        if len(resp_hdr) != 8:
            return None

        if resp_hdr[0] != HOST_SYNC1 or resp_hdr[1] != HOST_SYNC2:
            return None

        rc = -1
        if self.raw_mode:
            rc = struct.unpack("<I", resp_hdr[4:8])[0]
        else:
            data_len = struct.unpack("<I", resp_hdr[4:8])[0]
            if data_len > 0:
                payload = self.ser.read(data_len)
                if len(payload) == data_len and data_len >= 4:
                     rc = struct.unpack("<I", payload[:4])[0]
            else:
                rc = 0 
        return rc

def send_emmc_cmd_manual(dev, subcmd, param1, param2, timeout=DEFAULT_TIMEOUT, delay_sec=0.1):
    dev.ser.reset_input_buffer()

    inner_hdr = struct.pack("<BBBB I I I I I I I",
        HOST_SYNC1, HOST_SYNC2, SERVICE_ID_BOOT, OPCODE_EMMC_OP, 0, subcmd, param1, param2, 0, 0, 0)
    
    packet = inner_hdr
    if not dev.raw_mode:
         host_hdr = dev._build_host_header(HOST_API_SERVICE_ID, HOST_API_OPCODE_EMMC, len(inner_hdr))
         packet = host_hdr + inner_hdr

    if timeout:
        old_timeout = dev.ser.timeout
        dev.ser.timeout = timeout
    dev.ser.write(packet)
    dev.ser.flush()
    resp_hdr = dev.ser.read(HOST_HDR_SIZE)
    if timeout: dev.ser.timeout = old_timeout

    if len(resp_hdr) != 8:
        log_error("Timeout waiting for response header")
        return -1
    if resp_hdr[0] != HOST_SYNC1 or resp_hdr[1] != HOST_SYNC2:
        log_error("Invalid Sync Bytes in response")
        return -1

    rc = -1
    if dev.raw_mode:
        rc = struct.unpack("<I", resp_hdr[4:8])[0]
    else:
        data_len = struct.unpack("<I", resp_hdr[4:8])[0]
        if data_len > 0:
            payload = dev.ser.read(data_len)
            if len(payload) >= 4:
                 rc = struct.unpack("<I", payload[:4])[0]
    
    if delay_sec > 0:
        time.sleep(delay_sec)
    return rc

def op_upload_file(dev, file_path, addr, img_type=IMG_TYPE_GENERIC, chunk_size=None):
    size = os.path.getsize(file_path)
    filename = os.path.basename(file_path)

    if chunk_size is None: chunk_size = STREAM_CHUNK_SIZE
    
    log_info(f"Upload {filename} ({size} bytes) to 0x{addr:X}...")

    rc = dev.send_packet(SERVICE_ID_BOOT, OPCODE_UPLOAD, payload=b"", 
                         host_opcode=HOST_API_OPCODE_GENERIC,
                         addr=addr, img_type=img_type, 
                         is_last=0,
                         num_words=size)
    
    if rc is None:
        log_error("Setup Failed: No response from Firmware (Timeout).")
        return False
    if rc != 0:
        log_error(f"Setup Failed. FW returned RC=0x{rc:X}")
        return False

    t_start = time.perf_counter()
    with open(file_path, "rb") as f:
        sent = 0
        print_progress(0, size, prefix='Tx:', suffix='Complete', length=40)
        
        while True:
            chunk = f.read(chunk_size)
            if not chunk: break

            dev.ser.write(chunk)
            dev.ser.flush()
            
            sent += len(chunk)
            print_progress(sent, size, prefix='Tx:', suffix='Complete', length=40)

    sys.stdout.write('\n')

    log_info("Data sent. Waiting for verification...")
    
    try:
        old_timeout = dev.ser.timeout
        dev.ser.timeout = 20.0 
        
        resp_hdr = dev.ser.read(8)
        dev.ser.timeout = old_timeout

        if len(resp_hdr) != 8:
            log_error("Timeout waiting for Final ACK")
            return False
        
        if resp_hdr[0] != HOST_SYNC1 or resp_hdr[1] != HOST_SYNC2:
            log_error(f"Invalid Sync in Final ACK: {binascii.hexlify(resp_hdr)}")
            return False

        final_rc = -1
        
        if dev.raw_mode:
            final_rc = struct.unpack("<I", resp_hdr[4:8])[0]
        else:
            data_len = struct.unpack("<I", resp_hdr[4:8])[0]
            if data_len > 0:
                payload = dev.ser.read(data_len)
                if len(payload) >= 4:
                    final_rc = struct.unpack("<I", payload[:4])[0]
            else:
                final_rc = 0 
        
        if final_rc != 0:
            log_error(f"Final FW Verification Failed. RC=0x{final_rc:X}")
            return False

    except Exception as e:
        log_error(f"Exception during final ACK read: {e}")
        return False

    duration = time.perf_counter() - t_start
    log_info(f"Upload Done: {duration:.4f}s ({size/1024/duration:.2f} KB/s)")
    return True


def op_upload_and_flash_chunked(dev, file_path, start_lba, img_type=IMG_TYPE_GENERIC, chunk_size_mb=CHUNK_SIZE_MB):
    file_size = os.path.getsize(file_path)
    chunk_size_bytes = chunk_size_mb * MB_SIZE

    log_info(
        f"CHUNKED MODE: {os.path.basename(file_path)} "
        f"({file_size / MB_SIZE:.2f} MB) in {chunk_size_mb}MB chunks"
    )

    total_blocks_written = 0
    current_lba = start_lba

    with open(file_path, "rb") as f:
        chunk_num = 1
        while True:
            chunk_data = f.read(chunk_size_bytes)
            if not chunk_data:
                break

            pad_len = (-len(chunk_data)) % BLOCK_SIZE
            if pad_len:
                chunk_data += b"\x00" * pad_len

            chunk_blocks = len(chunk_data) // BLOCK_SIZE

            log_info(
                f"  Chunk {chunk_num}: {chunk_blocks} blocks "
                f"@ LBA 0x{current_lba:X}"
            )

            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write(chunk_data)
                tmp_path = tmp.name

            if not op_upload_file(dev, tmp_path, ADDR_AC_LOAD, img_type):
                log_error("Chunk upload failed")
                os.remove(tmp_path)
                return 0

            if send_emmc_cmd_manual(dev, 5, current_lba, chunk_blocks, timeout=EMMC_OP_TIMEOUT, delay_sec=0.1) != 0:
                log_error("Chunk ERASE failed")
                os.remove(tmp_path)
                return 0

            if send_emmc_cmd_manual(dev, 4, current_lba, chunk_blocks, timeout=EMMC_OP_TIMEOUT, delay_sec=0.1) != 0:
                log_error("Chunk WRITE failed")
                os.remove(tmp_path)
                return 0

            if send_emmc_cmd_manual(dev, 3, current_lba, chunk_blocks, timeout=EMMC_OP_TIMEOUT, delay_sec=0.1) != 0:
                log_error("Chunk READ failed")
                os.remove(tmp_path)
                return 0

            os.remove(tmp_path)

            current_lba += chunk_blocks
            total_blocks_written += chunk_blocks
            chunk_num += 1

    return total_blocks_written

def do_run_spk(args):
    """Run SPK"""
    if not args.port:
        cdc_port = auto_detect_usb_cdc_port(vid_pid_pairs=usb_cdc_port_default[USB_CDC_SPK])
    else:
        cdc_port = args.port

    if not cdc_port:
        log_error("SPK Port not found")
        return

    fpath = resolve_file_path(args.keys)
    if not fpath:
        log_error(f"File not found: {args.keys}")
        return
    upload_file(cdc_port, 0x1, args.baud, fpath)

    fpath = resolve_file_path(args.spk)
    if not fpath:
        log_error(f"File not found: {args.spk}")
        return
    upload_file(cdc_port, 0x2, args.baud, fpath)

    fpath = resolve_file_path(args.m52bl)
    if not fpath:
        log_error(f"File not found: {args.m52bl}")
        return
    upload_file(cdc_port, 0x4, args.baud, fpath)

def do_version_bl(args):
    cdc_port = args.port
    if not cdc_port:
        cdc_port = auto_detect_usb_cdc_port(vid_pid_pairs=usb_cdc_port_default[USB_CDC_M52BL])

    if not cdc_port:
        log_error("Port not found for M52BL")
        return

    with DeviceHandler(cdc_port, args.baud, raw_mode=True) as dev:
        op0a_hdr = dev._build_op_header(SERVICE_ID_BOOT, OPCODE_VERSION)
        dev.ser.write(op0a_hdr)
        time.sleep(0.2)
        resp_hdr = dev.ser.read(HOST_HDR_SIZE)
        if len(resp_hdr) != 8: return
        more = dev.ser.read(4)
        full_resp = resp_hdr + more
        ver = struct.unpack("<I", full_resp[4:8])[0]
        major = (ver >> 16) & 0xFFFF
        minor = ver & 0xFFFF

        print(f"BL Version: {major}.{minor}")

def do_version_sm(args):
    cdc_port = args.port
    if not cdc_port:
        cdc_port = auto_detect_usb_cdc_port(vid_pid_pairs=usb_cdc_port_default[USB_CDC_SM])

    if not cdc_port:
        log_error("Port not found for SM")
        return

    with DeviceHandler(cdc_port, args.baud, raw_mode=False) as dev:
        op0a_hdr = dev._build_op_header(SERVICE_ID_BOOT, OPCODE_VERSION)
        host_hdr = dev._build_host_header(HOST_API_SERVICE_ID, HOST_API_OPCODE_VERSION, len(op0a_hdr))
        dev.ser.write(host_hdr + op0a_hdr)
        time.sleep(0.2)
        resp_hdr = dev.ser.read(HOST_HDR_SIZE)
        if len(resp_hdr) != 8: return
        dlen = struct.unpack("<I", resp_hdr[4:8])[0]
        payload = dev.ser.read(dlen)
        if len(payload) >= 4:
            ver = struct.unpack("<I", payload[0:4])[0]
            major = (ver >> 16) & 0xFFFF
            minor = ver & 0xFFFF
            print(f"SM Version: {major}.{minor}")

def do_run_sm(args):
    cdc_port = args.port
    if not cdc_port:
        cdc_port = auto_detect_usb_cdc_port(vid_pid_pairs=usb_cdc_port_default[USB_CDC_M52BL])

    if not cdc_port:
        log_error("Port not found for Run-SM")
        return

    if not args.sm or args.sm == USE_DEFAULT:
        log_error("Run SM requires explicit path: --sm <path>")
        return

    fpath = resolve_file_path(args.sm)
    if not fpath:
        log_error(f"File not found: {args.sm}")
        return

    with DeviceHandler(cdc_port, args.baud, raw_mode=True) as dev:
        if op_upload_file(dev, fpath, ADDR_SM_LOAD, IMG_TYPE_SM):
            log_info("Sending RUN (0x0B)...")
            dev.send_packet(SERVICE_ID_BOOT, OPCODE_RUN_IMG, addr=ADDR_SM_LOAD)

def do_run_acore(args):
    cdc_port = args.port
    if not cdc_port:
        cdc_port = auto_detect_usb_cdc_port(vid_pid_pairs=usb_cdc_port_default[USB_CDC_SM])

    if not cdc_port:
        log_error("Port not found for Run-Acore")
        return

    if not args.bl or not args.tzk or args.bl == USE_DEFAULT or args.tzk == USE_DEFAULT:
        log_error("Run A-Core requires explicit paths: --bl <path> --tzk <path>")
        return

    bl_path = resolve_file_path(args.bl)
    tzk_path = resolve_file_path(args.tzk)

    if not bl_path: log_error(f"BL Not Found: {args.bl}"); return
    if not tzk_path: log_error(f"TZK Not Found: {args.tzk}"); return

    with DeviceHandler(cdc_port, args.baud, raw_mode=False) as dev:
        if not op_upload_file(dev, bl_path, ADDR_AC_LOAD, IMG_TYPE_BL): return
        dev.send_packet(SERVICE_ID_BOOT, OPCODE_EXEC_0C, host_opcode=HOST_API_OPCODE_EXEC)
        if not op_upload_file(dev, tzk_path, ADDR_AC_LOAD, IMG_TYPE_TZK): return
        dev.send_packet(SERVICE_ID_BOOT, OPCODE_EXEC_0C, host_opcode=HOST_API_OPCODE_EXEC)
        log_info("A-Core Sequence Complete.")

def do_emmc(args):
    cdc_port = args.port
    if not cdc_port:
        cdc_port = auto_detect_usb_cdc_port(vid_pid_pairs=usb_cdc_port_default[USB_CDC_SM])

    if not cdc_port:
        log_error("Port not found for EMMC")
        return

    if not args.img_dir:
        log_error("Requires --img-dir <folder>")
        return

    folder = args.img_dir
    part_list_path = os.path.join(folder, "emmc_part_list")
    img_list_path  = os.path.join(folder, "emmc_image_list")

    try: parts = parse_emmc_part_list(part_list_path)
    except Exception as e: log_error(str(e)); return

    file_defined_map = parse_image_list_to_map(img_list_path)
    if not file_defined_map:
        log_error("emmc_image_list missing or empty")
        return

    ops_map = file_defined_map

    log_info("--- PHASE A: FLASHING GPT ---")
    gpt_bin, table_lbas = build_gpt_primary(parts)
    gpt_path = os.path.join(folder, "gpt.bin")
    with open(gpt_path, "wb") as f: f.write(gpt_bin)

    LBAS_PER_MB = MB_SIZE // BLOCK_SIZE

    with DeviceHandler(cdc_port, args.baud, raw_mode=False) as dev:
        if op_upload_file(dev, gpt_path, ADDR_AC_LOAD, IMG_TYPE_GPT):
            gpt_len_bytes = len(gpt_bin)
            gpt_blocks = (gpt_len_bytes + BLOCK_SIZE - 1) // BLOCK_SIZE
            send_emmc_cmd_manual(dev, 0, 0, 0, delay_sec=0.1)
            send_emmc_cmd_manual(dev, 2, 0, 0, delay_sec=0.1)
            send_emmc_cmd_manual(dev, 5, 0, gpt_blocks, timeout=EMMC_OP_TIMEOUT, delay_sec=0.1)
            send_emmc_cmd_manual(dev, 4, 0, gpt_blocks, timeout=EMMC_OP_TIMEOUT, delay_sec=0.1)
            send_emmc_cmd_manual(dev, 3, 0, gpt_blocks, timeout=EMMC_OP_TIMEOUT, delay_sec=0.1)
            log_info("GPT Flashed.")

        for boot_id in [1, 2]:
            key = f"b{boot_id}"
            if key in ops_map:
                for fname in ops_map[key]:
                    p_path = resolve_file_path(os.path.join(folder, fname))
                    if p_path:
                        fsize = os.path.getsize(p_path)
                        fblks = (fsize + BLOCK_SIZE - 1) // BLOCK_SIZE
                        log_info(f"[{key}] Flashing {fname} to Boot{boot_id}...")
                        if op_upload_file(dev, p_path, ADDR_AC_LOAD, IMG_TYPE_GPT):
                            send_emmc_cmd_manual(dev, 0, 0, 0, delay_sec=0.2)
                            send_emmc_cmd_manual(dev, 2, boot_id, 0, delay_sec=12.0)
                            send_emmc_cmd_manual(dev, 5, 0, fblks, timeout=EMMC_OP_TIMEOUT, delay_sec=3.0)
                            send_emmc_cmd_manual(dev, 4, 0, fblks, timeout=EMMC_OP_TIMEOUT, delay_sec=7.0)
                            send_emmc_cmd_manual(dev, 3, 0, fblks, timeout=EMMC_OP_TIMEOUT, delay_sec=0.0)
                            log_info(f"[{key}] Done.")

        prev_end = 0

        for idx, (name, start_mb, size_mb) in enumerate(parts):
            if start_mb > 0: start_lba = start_mb * LBAS_PER_MB
            else: start_lba = prev_end + 1
            size_lbas = size_mb * LBAS_PER_MB
            end_lba = start_lba + size_lbas - 1
            prev_end = end_lba

            target_id = f"sd{idx + 1}"

            if target_id in ops_map:
                files_to_process = ops_map[target_id]
                current_offset = 0

                for fname in files_to_process:
                    if fname.lower() == "format":
                        continue

                    if fname.lower() == "erase":
                        log_info(f"[{target_id}] Erasing {name}...")
                        send_emmc_cmd_manual(dev, 0, 0, 0, delay_sec=0.1)
                        send_emmc_cmd_manual(dev, 2, 0, 0, delay_sec=0.1)
                        send_emmc_cmd_manual(dev, 5, start_lba, size_lbas, timeout=EMMC_OP_TIMEOUT, delay_sec=0.1)
                        continue

                    clean_file = resolve_file_path(os.path.join(folder, fname))

                    if clean_file:
                        fsize = os.path.getsize(clean_file)
                        fblks = (fsize + BLOCK_SIZE - 1) // BLOCK_SIZE
                        fsize_mb = fsize / MB_SIZE

                        itype = get_image_type_from_name(name)
                        target_lba = start_lba + current_offset

                        if target_lba + fblks - 1 > end_lba:
                            log_error(f"[{target_id}] {fname} overflows {name}")
                            continue

                        log_info(f"[{target_id}] Flashing {fname} -> {name} (Type: 0x{itype:X}, Size: {fsize_mb:.2f} MB)")
                        time.sleep(0.1)

                        use_chunked = fsize_mb > LARGE_FILE_THRESHOLD_MB

                        send_emmc_cmd_manual(dev, 0, 0, 0, delay_sec=0.1)
                        send_emmc_cmd_manual(dev, 2, 0, 0, delay_sec=0.1)

                        if use_chunked:
                            log_info(f"  Using CHUNKED mode (file > {LARGE_FILE_THRESHOLD_MB}MB) with {CHUNK_SIZE_MB}MB Chunks")
                            written = op_upload_and_flash_chunked(dev, clean_file, target_lba, itype, CHUNK_SIZE_MB)

                            if not written:
                                log_error(f"[{target_id}] Chunked flash failed")
                                return

                            written_blocks = fblks if written is True else int(written)
                            log_info(f"[{target_id}] Chunked flash complete.")
                            current_offset += written_blocks
                        else:
                            if op_upload_file(dev, clean_file, ADDR_AC_LOAD, itype):
                                send_emmc_cmd_manual(dev, 5, target_lba, fblks, timeout=EMMC_OP_TIMEOUT, delay_sec=0.1) # ERASE (Redundant but safe)
                                send_emmc_cmd_manual(dev, 4, target_lba, fblks, timeout=EMMC_OP_TIMEOUT, delay_sec=0.1) # WRITE
                                send_emmc_cmd_manual(dev, 3, target_lba, fblks, timeout=EMMC_OP_TIMEOUT, delay_sec=0.1) # READ
                                log_info(f"[{target_id}] Flashed.")
                                current_offset += fblks
                            else:
                                log_error(f"[{target_id}] Upload failed for {fname}")
                                return

                    else:
                        if "home" in name: pass
                        else: log_error(f"[{target_id}] File {fname} not found")

        log_info("=== ALL OPERATIONS COMPLETE ===")

def update_sm_image(args):
    clean_file = resolve_file_path(args.sm_image)
    # EMMC usually happens after A-Core is running or in SM mode
    cdc_port = args.port
    if not cdc_port:
        cdc_port = auto_detect_usb_cdc_port(vid_pid_pairs=usb_cdc_port_default[USB_CDC_SM])

    if not cdc_port:
        log_error("Port not found for EMMC")
        return False

    LBAS_PER_MB = MB_SIZE // BLOCK_SIZE
    target_lba = 98304
    fsize = os.path.getsize(clean_file)
    fblks = (fsize + BLOCK_SIZE - 1) // BLOCK_SIZE
    itype = IMG_TYPE_SM

    with DeviceHandler(cdc_port, args.baud, raw_mode=False) as dev:
        send_emmc_cmd_manual(dev, 0, 0, 0, delay_sec=0.1)   # INIT
        send_emmc_cmd_manual(dev, 2, 0, 0, delay_sec=0.1)   # SWITCH to user
        # Normal upload for smaller files
        if op_upload_file(dev, clean_file, ADDR_AC_LOAD, itype):
            send_emmc_cmd_manual(dev, 5, target_lba, fblks, timeout=EMMC_OP_TIMEOUT, delay_sec=0.1) # ERASE
            send_emmc_cmd_manual(dev, 4, target_lba, fblks, timeout=EMMC_OP_TIMEOUT, delay_sec=0.1) # WRITE
            send_emmc_cmd_manual(dev, 3, target_lba, fblks, timeout=EMMC_OP_TIMEOUT, delay_sec=0.1) # READ
            log_info("=== SM FLASH OPERATION COMPLETED ===")
            return True
        else:
            log_error(f"Upload failed")
            return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--op", required=True, choices=["version-bl", "version-sm", "run-spk", "run-sm", "run-acore", "emmc", "emmc-sm"])
    parser.add_argument("--port", help="Serial Port (Leave empty for Auto-Detect)")
    parser.add_argument("--baud", type=int, default=DEFAULT_BAUD)
    parser.add_argument("--img-dir", help="Directory for eMMC images")

    parser.add_argument("--spk", default="spk.bin", help="SynaPROT SPK image file")
    parser.add_argument("--keys", default="key.bin", help="SynaPROT keys file")
    parser.add_argument("--m52bl", default="m52bl.bin", help="M52 Bootloader image file input")

    parser.add_argument("--sm", nargs='?', const=USE_DEFAULT, help="SysMgr Path or Flag")
    parser.add_argument("--bl", nargs='?', const=USE_DEFAULT, help="Bootloader Path or Flag")
    parser.add_argument("--tzk", nargs='?', const=USE_DEFAULT, help="TZK Path or Flag")
    parser.add_argument("--sm-image", nargs='?', const=USE_DEFAULT, help="SysMgr Path to Flash")
    
    args = parser.parse_args()

    if args.op == "run-spk":
        do_run_spk(args)
    elif args.op == "version-bl":
        do_run_spk(args)
        time.sleep(2)
        do_version_bl(args)
    elif args.op == "version-sm":
        do_run_spk(args)
        time.sleep(2)
        do_run_sm(args)
        time.sleep(2)
        do_version_sm(args)
    elif args.op == "run-sm":
        do_run_spk(args)
        time.sleep(2)
        do_run_sm(args)
    elif args.op == "run-acore":
        do_run_spk(args)
        time.sleep(2)
        do_run_sm(args)
        time.sleep(2)
        do_run_acore(args)
    elif args.op == "emmc": 
        do_emmc(args)
    elif args.op == "emmc-sm":
        do_run_spk(args)
        time.sleep(2)
        do_run_sm(args)
        time.sleep(2)
        update_sm_image(args)

if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt: pass
    except Exception as e: log_error(f"{e}")