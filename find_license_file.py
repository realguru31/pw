#!/usr/bin/env python3
"""
License File Finder and Tester
Helps identify where the DLL expects the license file
"""

import os
import base64
import json
from pathlib import Path

def create_license_file(machine_id, license_key, output_path):
    """Create a license file"""
    license_data = {
        'MachineId': machine_id,
        'HardwareHash': 'A7E773DBADCA5494A137CCDCDA48843DDC2EFD64',
        'LicenseKey': license_key,
        'Status': 'Success',
        'ExpiryDate': '2099-12-31',
        'MaxBuild': '999999',
        'IssuedDate': '2024-01-01'
    }
    
    json_str = json.dumps(license_data, indent=2)
    encoded = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
    
    with open(output_path, 'w') as f:
        f.write(encoded)
    
    print(f"✓ Created: {output_path}")
    return output_path

def get_likely_locations():
    """Get list of likely file locations"""
    locations = []
    
    # Windows paths
    if os.name == 'nt':
        appdata = os.environ.get('APPDATA', '')
        localappdata = os.environ.get('LOCALAPPDATA', '')
        userprofile = os.environ.get('USERPROFILE', '')
        
        base_dirs = [
            os.path.join(appdata, 'NinjaTrader 8'),
            os.path.join(appdata, 'NinjaTrader'),
            os.path.join(localappdata, 'NinjaTrader 8'),
            os.path.join(localappdata, 'NinjaTrader'),
            os.path.join(userprofile, 'Documents', 'NinjaTrader 8'),
            os.path.join(userprofile, 'Documents', 'NinjaTrader'),
            'C:\\Program Files\\NinjaTrader 8\\bin\\Custom',
            'C:\\Program Files (x86)\\NinjaTrader 8\\bin\\Custom',
        ]
    else:
        # Linux/Mac (for testing)
        home = os.path.expanduser('~')
        base_dirs = [
            os.path.join(home, '.ninjatrader'),
            os.path.join(home, '.config', 'ninjatrader'),
            '.'
        ]
    
    # Add current directory
    base_dirs.append('.')
    
    # Common filenames
    filenames = [
        'license.dat',
        'hwid.dat',
        'machine.id',
        'activation.dat',
        'license.txt',
        '.license',
        'BestOrderflow.lic',
        'BestOrderflowUnlocker.lic',
        'orderflow.lic',
        'key.dat',
    ]
    
    for base_dir in base_dirs:
        if os.path.exists(base_dir):
            for filename in filenames:
                full_path = os.path.join(base_dir, filename)
                locations.append(full_path)
    
    return locations

def main():
    print("=" * 70)
    print("LICENSE FILE FINDER AND CREATOR")
    print("=" * 70)
    
    # Known working values
    machine_id = "C6454-D375F-4D019-7F50C"
    license_key = "32AD47B3C5B7AA135960994CCAACA29BF170D5AEAF47BF18543B7F578360FFA240724DF2B264B108720B603EA787B302603CE77EB4985DC401C0C66682FFAF3E"
    
    print("\n⚠️  IMPORTANT NOTICE:")
    print("=" * 70)
    print("""
Just creating a license file with the OLD machine ID will NOT work
on a NEW machine because:

1. DLL reads YOUR CURRENT hardware (MAC addresses)
2. Compares with machine ID in file
3. If they don't match → BadHwid error

TO MAKE IT WORK, you need to ALSO:
- Patch the DLL (recommended - see dll_patcher_concept.py), OR
- Spoof your MAC address to match the old machine

See IMPORTANT_LICENSE_FILE_INFO.md for full explanation.
""")
    
    print("\n" + "=" * 70)
    print("GENERATING TEST LICENSE FILES")
    print("=" * 70)
    
    locations = get_likely_locations()
    
    print(f"\nFound {len(locations)} possible locations to test:")
    print("\nCreating test files in likely locations...\n")
    
    created = []
    for location in locations:
        try:
            # Create directory if needed
            directory = os.path.dirname(location)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
            
            create_license_file(machine_id, license_key, location)
            created.append(location)
        except Exception as e:
            print(f"✗ Could not create {location}: {e}")
    
    print(f"\n✓ Successfully created {len(created)} test files")
    
    print("\n" + "=" * 70)
    print("NEXT STEPS")
    print("=" * 70)
    print("""
1. LAUNCH NINJATRADER:
   - Start NinjaTrader with the BestOrderflowUnlocker addon
   - Check if it loads without errors

2. CHECK ERROR MESSAGES:
   - If you see "BadHwid" error → License file was found!
   - This confirms the file location is correct
   - But validation failed (expected - different hardware)

3. IF NO ERRORS AND IT WORKS:
   - Congratulations! You found the right location
   - The DLL accepted the file

4. IF STILL GETTING LICENSE ERRORS:
   - The filename/location might be different
   - Use Process Monitor to see actual file reads:
     a) Download: https://learn.microsoft.com/sysinternals/procmon
     b) Run as Administrator
     c) Filter: Process = NinjaTrader.exe, Operation = ReadFile
     d) Launch NinjaTrader
     e) Check which files it tries to read

5. TO FIX BADHWID ERROR:
   - Option A: Patch the DLL (see dll_patcher_concept.py)
   - Option B: Change your MAC address to match old machine
   - Option C: Contact vendor for legitimate license

6. CLEANUP (if you want to remove test files):
   - Delete the files from the locations listed above
""")
    
    print("\n" + "=" * 70)
    print("CREATED FILES LIST")
    print("=" * 70)
    for path in created:
        print(f"  {path}")
    
    print("\n💡 TIP: If NinjaTrader shows 'BadHwid', that means it FOUND")
    print("   the license file but your hardware doesn't match!")
    print("   → Solution: Patch the DLL to skip the hardware check")

if __name__ == "__main__":
    main()
