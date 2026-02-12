# BestOrderflowUnlocker.dll Analysis & Tools

## Overview

This directory contains analysis tools and documentation for understanding the protection mechanism in `BestOrderflowUnlocker.dll` and how to work with machine ID/hardware ID binding.

## Key Finding

The license key `32AD47B3C5B7AA135960994CCAACA29BF170D5AEAF47BF18543B7F578360FFA240724DF2B264B108720B603EA787B302603CE77EB4985DC401C0C66682FFAF3E` is **server-signed** and cannot be regenerated locally for a new machine ID. 

**Machine ID detected**: `C6454-D375F-4D019-7F50C`  
**HWID Hash (SHA1)**: `A7E773DBADCA5494A137CCDCDA48843DDC2EFD64`

## Files

### Documentation
- **[DLL_ANALYSIS.md](DLL_ANALYSIS.md)** - Complete technical analysis of the DLL protection mechanism
- **[SOLUTION_GUIDE.md](SOLUTION_GUIDE.md)** - Step-by-step guide with multiple solution options
- **README_DLL_TOOLS.md** - This file

### Tools
- **[analyze_dll.py](analyze_dll.py)** - Binary analysis tool to find strings and offsets in the DLL
- **[generate_license.py](generate_license.py)** - License file generator (creates Base64-encoded JSON)
- **[machine_id_patcher.py](machine_id_patcher.py)** - Comprehensive analysis and patching utility

### Generated Files
- **license.txt** - Base64-encoded license file (example for original machine ID)
- **license_readable.json** - Human-readable JSON version of the license
- **dll_strings.txt** - Extracted strings from the DLL

## Quick Start

### 1. Analyze the DLL
```bash
python3 analyze_dll.py
```

### 2. Generate License File
```bash
# Interactive mode
python3 generate_license.py

# With specific machine ID
python3 generate_license.py "XXXXX-XXXXX-XXXXX-XXXXX"
```

### 3. Review Solutions
Read [SOLUTION_GUIDE.md](SOLUTION_GUIDE.md) for complete instructions on:
- Contacting the vendor (recommended)
- MAC address spoofing
- DLL patching with dnSpy

## Protection Details

### How It Works
1. DLL reads license file from disk (Base64-encoded JSON)
2. Extracts stored machine ID and license key
3. Computes current machine's HWID from network adapter MAC addresses
4. Compares with stored machine ID
5. Validates key (likely with remote server)
6. Returns status: Success, BadHwid, SerialUnknown, etc.

### Hardware ID Generation
```
MAC Address → Normalize (uppercase, no separators) → SHA1 Hash → HWID
```

Example:
- Machine ID: `C6454-D375F-4D019-7F50C`
- Normalized: `C6454D375F4D0197F50C`
- SHA1: `A7E773DBADCA5494A137CCDCDA48843DDC2EFD64`

### License File Format
```json
{
  "MachineId": "C6454-D375F-4D019-7F50C",
  "HardwareHash": "A7E773DBADCA5494A137CCDCDA48843DDC2EFD64",
  "LicenseKey": "32AD47B3...",
  "Status": "Success",
  "ExpiryDate": "2099-12-31",
  "MaxBuild": "999999",
  "IssuedDate": "2024-01-01"
}
```
This JSON is then Base64-encoded and stored in a file.

## Recommended Approach

**For a new machine**, the best approach is:

1. **Contact the vendor** - Request a legitimate license transfer or new key
2. **If legitimate use** - The vendor should provide a new key for your new machine ID
3. **If vendor unresponsive** - Consider the DLL patching method (see SOLUTION_GUIDE.md)

## Important Notes

⚠️ **Legal Notice**: These tools are for:
- Educational and research purposes
- Security analysis
- Legitimate backup and recovery
- Authorized testing

Using these tools to bypass licensing without authorization may violate:
- EULA/Terms of Service
- DMCA (USA) anti-circumvention laws
- Computer Fraud and Abuse Act
- Copyright law

## Technical Support

### Finding License Files
Common locations:
```
Windows:
  %APPDATA%\NinjaTrader 8\
  %LOCALAPPDATA%\NinjaTrader 8\
  {DLL Directory}\
  
Registry:
  HKEY_CURRENT_USER\Software\NinjaTrader
```

### Debugging
Use Process Monitor (Sysinternals) to trace file access:
1. Filter: Process = NinjaTrader.exe
2. Filter: Operation = ReadFile
3. Look for license-related file reads

## References

- NinjaTrader Platform: https://ninjatrader.com
- dnSpy (.NET Decompiler): https://github.com/dnSpy/dnSpy
- Process Monitor: https://learn.microsoft.com/en-us/sysinternals/downloads/procmon

---

**Analysis Date**: February 12, 2026  
**DLL Version**: 17.0.0.0  
**Target Platform**: NinjaTrader 8.1.2.0
