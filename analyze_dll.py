#!/usr/bin/env python3
"""
DLL Analysis and Patcher Tool
Analyzes BestOrderflowUnlocker.dll and provides patching capabilities
"""

import struct
import re
from pathlib import Path

class DLLAnalyzer:
    def __init__(self, dll_path):
        self.dll_path = Path(dll_path)
        with open(self.dll_path, 'rb') as f:
            self.data = bytearray(f.read())
        
    def find_string(self, search_str):
        """Find a string in the DLL"""
        search_bytes = search_str.encode('utf-8')
        positions = []
        offset = 0
        while True:
            pos = self.data.find(search_bytes, offset)
            if pos == -1:
                break
            positions.append(pos)
            offset = pos + 1
        return positions
    
    def find_machine_id_references(self):
        """Find references to machine ID in the DLL"""
        patterns = [
            b'get_MachineId',
            b'MachineId',
            b'BadHwid',
            b'License',
            b'GetPhysicalAddress'
        ]
        
        results = {}
        for pattern in patterns:
            positions = []
            offset = 0
            while True:
                pos = self.data.find(pattern, offset)
                if pos == -1:
                    break
                positions.append(pos)
                offset = pos + 1
            if positions:
                results[pattern.decode('utf-8', errors='ignore')] = positions
        
        return results
    
    def extract_strings_around(self, position, before=50, after=50):
        """Extract readable strings around a position"""
        start = max(0, position - before)
        end = min(len(self.data), position + after)
        chunk = self.data[start:end]
        
        # Find printable strings
        strings = re.findall(b'[\x20-\x7e]{4,}', chunk)
        return [s.decode('utf-8', errors='ignore') for s in strings]
    
    def find_hex_patterns(self):
        """Find hex patterns that might be machine IDs or keys"""
        # Look for patterns like: XXXXX-XXXXX-XXXXX-XXXXX
        text = self.data.decode('utf-8', errors='ignore')
        machine_id_pattern = r'[0-9A-F]{5}-[0-9A-F]{5}-[0-9A-F]{5}-[0-9A-F]{5}'
        matches = re.findall(machine_id_pattern, text)
        return matches
    
    def patch_string(self, old_str, new_str, occurrence=0):
        """Replace a string in the DLL"""
        old_bytes = old_str.encode('utf-8')
        new_bytes = new_str.encode('utf-8')
        
        if len(new_bytes) > len(old_bytes):
            print(f"Warning: New string is longer than old string!")
            print(f"Old: {len(old_bytes)} bytes, New: {len(new_bytes)} bytes")
            return False
        
        # Pad with null bytes if shorter
        if len(new_bytes) < len(old_bytes):
            new_bytes = new_bytes + b'\x00' * (len(old_bytes) - len(new_bytes))
        
        positions = []
        offset = 0
        while True:
            pos = self.data.find(old_bytes, offset)
            if pos == -1:
                break
            positions.append(pos)
            offset = pos + 1
        
        if not positions:
            print(f"String not found: {old_str}")
            return False
        
        if occurrence >= len(positions):
            print(f"Occurrence {occurrence} not found (only {len(positions)} found)")
            return False
        
        patch_pos = positions[occurrence]
        print(f"Patching at offset 0x{patch_pos:08x}")
        self.data[patch_pos:patch_pos+len(new_bytes)] = new_bytes
        return True
    
    def save(self, output_path):
        """Save the modified DLL"""
        with open(output_path, 'wb') as f:
            f.write(self.data)
        print(f"Saved to: {output_path}")

def main():
    dll_path = "BestOrderflowUnlocker.dll"
    
    print("=" * 60)
    print("DLL ANALYZER - BestOrderflowUnlocker.dll")
    print("=" * 60)
    
    analyzer = DLLAnalyzer(dll_path)
    
    print("\n[*] Searching for Machine ID references...")
    refs = analyzer.find_machine_id_references()
    for key, positions in refs.items():
        print(f"\n'{key}' found at {len(positions)} location(s):")
        for i, pos in enumerate(positions[:5]):  # Show first 5
            print(f"  Offset 0x{pos:08x}")
            strings = analyzer.extract_strings_around(pos)
            if strings:
                print(f"    Context: {', '.join(strings[:3])}")
    
    print("\n[*] Searching for hex patterns (Machine ID format)...")
    patterns = analyzer.find_hex_patterns()
    if patterns:
        print(f"Found {len(patterns)} potential machine IDs:")
        for p in set(patterns):
            print(f"  {p}")
    else:
        print("  No hardcoded machine IDs found in readable strings")
    
    print("\n[*] Searching for the provided machine ID...")
    old_machine_id = "C6454-D375F-4D019-7F50C"
    positions = analyzer.find_string(old_machine_id)
    if positions:
        print(f"Found old machine ID at {len(positions)} location(s):")
        for pos in positions:
            print(f"  Offset 0x{pos:08x}")
    else:
        print("  Old machine ID not found as plaintext string")
        print("  (May be hashed, encoded, or stored in different format)")
    
    print("\n[*] Analyzing the provided key...")
    key = "32AD47B3C5B7AA135960994CCAACA29BF170D5AEAF47BF18543B7F578360FFA240724DF2B264B108720B603EA787B302603CE77EB4985DC401C0C66682FFAF3E"
    print(f"  Key length: {len(key)} characters ({len(key)//2} bytes)")
    print(f"  Key format: {'Hexadecimal' if all(c in '0123456789ABCDEFabcdef' for c in key) else 'Unknown'}")
    
    # Search for parts of the key
    key_parts = [key[i:i+32] for i in range(0, len(key), 32)]
    print("\n  Searching for key parts in DLL...")
    key_found = False
    for i, part in enumerate(key_parts):
        if analyzer.find_string(part):
            print(f"    Part {i+1} found: {part}")
            key_found = True
    
    if not key_found:
        print("    Key not found as plaintext in DLL")
    
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
