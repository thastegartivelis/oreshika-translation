import sys
import struct
import argparse

def get_string_end(data, start_addr, use_single_null):
    end = start_addr
    while end < len(data):
        if use_single_null:
            if end + 1 <= len(data) and data[end] == 0:
                break
        else:
            if end + 2 <= len(data) and data[end:end+2] in [b'\x00\x00', b'\xff\xff']:
                break
        end += 1
    return end

def deobfuscate_dummy_bytes(raw_bytes):
    """
    De-obfuscates strings matching the '..0' pattern where every second byte is 0x30 ('0').
    Example: b'72 30 67 30' -> b'72 67'
    """
    if len(raw_bytes) < 2:
        return raw_bytes
    
    # Check if every second byte is 0x30
    is_dummy = True
    for i in range(1, len(raw_bytes), 2):
        if raw_bytes[i] != 0x30:
            is_dummy = False
            break
    
    if is_dummy:
        # Reconstruct by taking only even-indexed bytes
        return raw_bytes[::2]
    return raw_bytes

def detect_and_decode(raw_bytes, filename):
    """
    Detects the encoding and decodes the byte string.
    Prioritizes ASCII/UTF-8 for _NA.mlb and _NAME.mlb files.
    """
    # Remove trailing nulls/0xff before processing
    trimmed_bytes = raw_bytes.rstrip(b'\x00\xff')
    if not trimmed_bytes:
        return ""

    # Handle de-obfuscation first
    processed_bytes = deobfuscate_dummy_bytes(trimmed_bytes)

    # Logic for metadata files
    if "_NA.mlb" in filename or "_NAME.mlb" in filename:
        # These are primarily ASCII/UTF-8
        for enc in ['ascii', 'utf-8']:
            try:
                return processed_bytes.decode(enc)
            except UnicodeDecodeError:
                continue
    
    # Default to UTF-16LE for standard files
    try:
        return processed_bytes.decode('utf-16le')
    except UnicodeDecodeError:
        # Final fallback
        try:
            return processed_bytes.decode('utf-8')
        except UnicodeDecodeError:
            return processed_bytes.decode('latin-1')


def read_mlb(path):
    try:
        with open(path, "rb") as f:
            data = f.read()
    except FileNotFoundError:
        print(f"Error: File not found at {path}")
        return
    except Exception as e:
        print(f"Error: {e}")
        return

    # Header: 4d 4c 54 (3 bytes)
    # Section count: 1 byte (offset 3)
    if len(data) < 4:
        print("Error: File too small to contain header.")
        return

    section_count = data[3]
    print(f"Section count: {section_count}")

    # Section locations block: 4 bytes each (starting at offset 4)
    # The header is 4 bytes (0-3). Locations start at 4.
    section_starts = []
    for i in range(section_count):
        idx = 4 + i * 4
        if idx + 4 <= len(data):
            start = struct.unpack("<I", data[idx : idx + 4])[0]
            section_starts.append(start)
        else:
            print(f"Warning: Could not read section {i} start location.")
    
    print(f"Section starts: {section_starts}")

    for i, start in enumerate(section_starts):
        print(f"\n--- Section {i} (Starts at {start}) ---")
        # Check if the start location is within bounds
        if start + 4 > len(data):
            print("Error: Section start is out of bounds.")
            continue

        # String information block: 4 bytes count of strings
        string_count = struct.unpack("<I", data[start : start + 4])[0]
        print(f"String count: {string_count}")
        
        # Addresses of strings: 4 bytes each
        addresses = []
        for j in range(string_count):
            addr_idx = start + 4 + j * 4
            if addr_idx + 4 <= len(data):
                addr = struct.unpack("<I", data[addr_idx : addr_idx + 4])[0]
                addresses.append(addr)
            else:
                print(f"Warning: Could not read address for string {j} in section {i}")
        
        print(f"Addresses: {addresses}")
        
        # Strings block
        for addr in addresses:
            if addr >= len(data):
                print(f"Error: Address {addr} is out of bounds.")
                continue
            
            end = addr
            while end < len(data):
                # Check for a null byte or 0xff 0xff
                if end + 1 <= len(data) and data[end] == 0:
                    break
                if end + 2 <= len(data) and data[end:end+2] == b'\xff\xff':
                    break
                end += 1

            
            string_data = data[addr:end]
            decoded_string = detect_and_decode(string_data, path)
            print(f"String at {addr}: {decoded_string}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract strings from .mlb files.")
    parser.add_argument("path", help="Path to the .mlb file.")
    args = parser.parse_args()

    read_mlb(args.path)
