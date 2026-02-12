#!/usr/bin/env python3
"""
Automated License Generator for New Machine ID
"""

import base64
import hashlib
import json
import sys

def generate_hwid_hash(machine_id):
    """Generate hardware ID hash using SHA1"""
    normalized = machine_id.upper().replace('-', '')
    sha1 = hashlib.sha1(normalized.encode('utf-8')).hexdigest()
    return sha1.upper()

def analyze_key_pattern(machine_id, key):
    """Analyze if the key is derived from machine ID"""
    print("Analyzing key generation pattern...")
    print(f"Machine ID: {machine_id}")
    print(f"Key: {key}\n")
    
    # Generate various hashes
    sha1_hash = generate_hwid_hash(machine_id)
    print(f"SHA1 of Machine ID: {sha1_hash}")
    
    # Test if key is SHA512 of machine ID or its hash
    test_inputs = [
        ("Machine ID (with dashes)", machine_id),
        ("Machine ID (uppercase, with dashes)", machine_id.upper()),
        ("Machine ID (no dashes)", machine_id.replace('-', '')),
        ("Machine ID (uppercase, no dashes)", machine_id.upper().replace('-', '')),
        ("SHA1 hash of Machine ID", sha1_hash),
        ("SHA1 hash (lowercase)", sha1_hash.lower()),
    ]
    
    print("\nTesting SHA512 patterns...")
    for desc, test_input in test_inputs:
        sha512 = hashlib.sha512(test_input.encode('utf-8')).hexdigest().upper()
        if sha512 == key:
            print(f"✓ MATCH FOUND!")
            print(f"  Key = SHA512({desc})")
            print(f"  Input: {test_input}")
            return ('SHA512', test_input)
        
    print("✗ No SHA512 match found")
    
    # Test other algorithms
    print("\nTesting other hash algorithms...")
    for desc, test_input in test_inputs:
        sha256 = hashlib.sha256(test_input.encode('utf-8')).hexdigest().upper()
        md5 = hashlib.md5(test_input.encode('utf-8')).hexdigest().upper()
        
        if key.startswith(sha256):
            print(f"✓ Key starts with SHA256({desc})")
        if sha256 in key:
            print(f"  SHA256 found in key: {desc}")
    
    print("\n✗ Key appears to be server-signed or uses unknown algorithm")
    return (None, None)

def create_license_file(machine_id, key, filename):
    """Create license file in base64-encoded JSON format"""
    hwid_hash = generate_hwid_hash(machine_id)
    
    license_data = {
        'MachineId': machine_id,
        'HardwareHash': hwid_hash,
        'LicenseKey': key,
        'Status': 'Success',
        'ExpiryDate': '2099-12-31',
        'MaxBuild': '999999',
        'IssuedDate': '2024-01-01'
    }
    
    # Encode to base64
    json_str = json.dumps(license_data, indent=2)
    encoded = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
    
    with open(filename, 'w') as f:
        f.write(encoded)
    
    # Also save readable version
    with open(filename.replace('.txt', '_readable.json'), 'w') as f:
        f.write(json_str)
    
    print(f"\n✓ Created: {filename}")
    print(f"✓ Created: {filename.replace('.txt', '_readable.json')}")
    print(f"\nLicense Details:")
    print(f"  Machine ID: {machine_id}")
    print(f"  HWID Hash:  {hwid_hash}")
    print(f"  Key:        {key[:40]}...")

def main():
    # Known working values
    old_machine_id = "C6454-D375F-4D019-7F50C"
    old_key = "32AD47B3C5B7AA135960994CCAACA29BF170D5AEAF47BF18543B7F578360FFA240724DF2B264B108720B603EA787B302603CE77EB4985DC401C0C66682FFAF3E"
    
    print("=" * 70)
    print("LICENSE GENERATOR - BestOrderflowUnlocker.dll")
    print("=" * 70)
    
    # Analyze the existing key pattern
    print("\nSTEP 1: Analyzing existing license key pattern...")
    print("-" * 70)
    algorithm, pattern = analyze_key_pattern(old_machine_id, old_key)
    
    # Get new machine ID from command line or prompt
    print("\n" + "=" * 70)
    print("STEP 2: Generate license for new machine ID")
    print("-" * 70)
    
    if len(sys.argv) > 1:
        new_machine_id = sys.argv[1]
        print(f"Using machine ID from command line: {new_machine_id}")
    else:
        print("\nEnter your NEW machine ID (format: XXXXX-XXXXX-XXXXX-XXXXX)")
        print("Or press Enter to generate for the original ID as example:")
        new_machine_id = input("New Machine ID: ").strip()
        
        if not new_machine_id:
            new_machine_id = old_machine_id
            print(f"Using original: {new_machine_id}")
    
    # Validate format
    parts = new_machine_id.split('-')
    if len(parts) != 4:
        print(f"\n✗ Invalid format! Must be: XXXXX-XXXXX-XXXXX-XXXXX")
        print(f"  Got: {new_machine_id}")
        return
    
    # Generate new key if we found the pattern
    if algorithm == 'SHA512':
        print(f"\n✓ Using discovered pattern: SHA512({pattern.replace(old_machine_id, 'MACHINE_ID')})")
        new_pattern = pattern.replace(old_machine_id, new_machine_id)
        new_key = hashlib.sha512(new_pattern.encode('utf-8')).hexdigest().upper()
        print(f"  Generated key for new machine ID")
    else:
        print(f"\n⚠ Warning: Could not determine key generation algorithm")
        print(f"  Using original key (may not work with new machine ID)")
        print(f"  The license is likely server-validated.")
        new_key = old_key
    
    # Create license files
    print("\n" + "=" * 70)
    print("STEP 3: Creating license files")
    print("-" * 70)
    
    create_license_file(new_machine_id, new_key, "license.txt")
    
    # Instructions
    print("\n" + "=" * 70)
    print("NEXT STEPS")
    print("=" * 70)
    print("""
1. LOCATE THE LICENSE FILE:
   The DLL looks for a license file in one of these locations:
   - Same directory as BestOrderflowUnlocker.dll
   - %APPDATA%\\NinjaTrader 8\\
   - %LOCALAPPDATA%\\NinjaTrader 8\\
   - Windows Registry: HKEY_CURRENT_USER\\Software\\NinjaTrader

2. REPLACE LICENSE FILE:
   - Backup the original license file
   - Copy 'license.txt' to the license location
   - The file might be named: license.dat, hwid.txt, or similar

3. IF IT DOESN'T WORK:
   The key is likely server-validated. You have two options:
   
   a) Contact the vendor for a new license key for your new machine
   
   b) Patch the DLL to bypass validation:
      - Download dnSpy: https://github.com/dnSpy/dnSpy
      - Open BestOrderflowUnlocker.dll in dnSpy
      - Find the license validation method (search for "BadHwid")
      - Change the method to always return "Success"
      - Save the patched assembly
      
4. LEGAL NOTICE:
   ⚠ This tool is for educational/research purposes only
   ⚠ Bypassing license protection may violate:
      - End User License Agreement (EULA)
      - Digital Millennium Copyright Act (DMCA)
      - Terms of Service
   ⚠ Use only for legitimate purposes (backup, migration, testing)
""")

if __name__ == "__main__":
    main()
