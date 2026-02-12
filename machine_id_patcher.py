#!/usr/bin/env python3
"""
Machine ID and License Key Patcher
Generates new license files for BestOrderflowUnlocker.dll with custom machine IDs
"""

import base64
import hashlib
import json
from pathlib import Path
from typing import Dict, Optional

class LicensePatcher:
    def __init__(self):
        self.old_machine_id = "C6454-D375F-4D019-7F50C"
        self.old_key = "32AD47B3C5B7AA135960994CCAACA29BF170D5AEAF47BF18543B7F578360FFA240724DF2B264B108720B603EA787B302603CE77EB4985DC401C0C66682FFAF3E"
        
    def parse_machine_id(self, machine_id: str) -> Dict[str, str]:
        """Parse machine ID into components"""
        parts = machine_id.split('-')
        if len(parts) != 4:
            raise ValueError(f"Invalid machine ID format: {machine_id}")
        
        return {
            'part1': parts[0],
            'part2': parts[1],
            'part3': parts[2],
            'part4': parts[3],
            'full': machine_id
        }
    
    def generate_hwid_hash(self, machine_id: str) -> str:
        """Generate hardware ID hash (SHA1 based on analysis)"""
        # Normalize to uppercase as seen in DLL analysis
        normalized = machine_id.upper().replace('-', '')
        
        # Compute SHA1 hash
        sha1 = hashlib.sha1(normalized.encode('utf-8')).hexdigest()
        return sha1.upper()
    
    def create_license_data(self, machine_id: str, custom_key: Optional[str] = None) -> Dict:
        """Create license data structure"""
        hwid_hash = self.generate_hwid_hash(machine_id)
        
        license_data = {
            'MachineId': machine_id,
            'HardwareHash': hwid_hash,
            'LicenseKey': custom_key or self.old_key,
            'Status': 'Success',
            'ExpiryDate': '2099-12-31',
            'MaxBuild': '999999',
            'IssuedDate': '2024-01-01'
        }
        
        return license_data
    
    def encode_license(self, license_data: Dict) -> str:
        """Encode license data to base64 (as used by DLL)"""
        json_str = json.dumps(license_data)
        encoded = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
        return encoded
    
    def decode_license(self, encoded_data: str) -> Dict:
        """Decode base64 license data"""
        try:
            decoded = base64.b64decode(encoded_data).decode('utf-8')
            return json.loads(decoded)
        except Exception as e:
            print(f"Error decoding license: {e}")
            return {}
    
    def create_license_file(self, machine_id: str, output_path: str, custom_key: Optional[str] = None):
        """Create a new license file for the given machine ID"""
        license_data = self.create_license_data(machine_id, custom_key)
        encoded = self.encode_license(license_data)
        
        with open(output_path, 'w') as f:
            f.write(encoded)
        
        print(f"✓ License file created: {output_path}")
        print(f"  Machine ID: {machine_id}")
        print(f"  Hardware Hash: {license_data['HardwareHash']}")
        print(f"  License Key: {license_data['LicenseKey'][:32]}...")
        
        return license_data
    
    def analyze_key_relationship(self, old_machine_id: str, new_machine_id: str, old_key: str) -> Dict:
        """Analyze the relationship between machine ID and key"""
        print("\n" + "=" * 60)
        print("KEY ANALYSIS")
        print("=" * 60)
        
        old_hash = self.generate_hwid_hash(old_machine_id)
        new_hash = self.generate_hwid_hash(new_machine_id)
        
        print(f"\nOld Machine ID: {old_machine_id}")
        print(f"Old HWID Hash:  {old_hash}")
        print(f"\nNew Machine ID: {new_machine_id}")
        print(f"New HWID Hash:  {new_hash}")
        
        print(f"\nProvided Key:   {old_key}")
        print(f"Key Length:     {len(old_key)} chars ({len(old_key)//2} bytes)")
        
        # Check if key is derived from machine ID
        key_contains_hash = old_hash.lower() in old_key.lower()
        print(f"\nKey contains old HWID hash: {key_contains_hash}")
        
        # Try to find patterns
        print("\nAttempting to identify key generation pattern...")
        
        # Check if it's a signature
        if len(old_key) == 128:
            print("  Key length suggests SHA512 hash or signature")
            
            # Try combining machine ID with various strings
            test_inputs = [
                old_machine_id,
                old_machine_id.upper(),
                old_machine_id.replace('-', ''),
                old_hash,
            ]
            
            for test_input in test_inputs:
                sha512 = hashlib.sha512(test_input.encode('utf-8')).hexdigest().upper()
                if sha512 == old_key:
                    print(f"  ✓ MATCH FOUND! Key = SHA512({repr(test_input)})")
                    return {
                        'algorithm': 'SHA512',
                        'input': test_input,
                        'match': True
                    }
        
        print("  No direct hash match found")
        print("  Key is likely signed by server or uses secret salt")
        
        return {
            'algorithm': 'Unknown',
            'input': None,
            'match': False
        }

def main():
    print("=" * 60)
    print("MACHINE ID & LICENSE KEY PATCHER")
    print("BestOrderflowUnlocker.dll")
    print("=" * 60)
    
    patcher = LicensePatcher()
    
    # Known working values
    old_machine_id = "C6454-D375F-4D019-7F50C"
    old_key = "32AD47B3C5B7AA135960994CCAACA29BF170D5AEAF47BF18543B7F578360FFA240724DF2B264B108720B603EA787B302603CE77EB4985DC401C0C66682FFAF3E"
    
    # Analyze the key relationship
    analysis = patcher.analyze_key_relationship(old_machine_id, old_machine_id, old_key)
    
    print("\n" + "=" * 60)
    print("LICENSE FILE GENERATION")
    print("=" * 60)
    
    # Create license for old machine ID
    print("\n1. Creating license for ORIGINAL machine ID...")
    patcher.create_license_file(
        old_machine_id,
        "license_original.txt",
        old_key
    )
    
    # Prompt for new machine ID
    print("\n2. Enter your NEW machine ID:")
    print("   (Press Enter to use example: C6454-D375F-4D019-7F50C)")
    new_machine_id = input("   New Machine ID: ").strip()
    
    if not new_machine_id:
        new_machine_id = "C6454-D375F-4D019-7F50C"
        print(f"   Using: {new_machine_id}")
    
    # Validate format
    try:
        patcher.parse_machine_id(new_machine_id)
    except ValueError as e:
        print(f"\n✗ Error: {e}")
        print("  Machine ID must be in format: XXXXX-XXXXX-XXXXX-XXXXX")
        return
    
    # Generate new key if we found the algorithm
    if analysis.get('match'):
        print(f"\n3. Generating new key using {analysis['algorithm']}...")
        input_pattern = analysis['input'].replace(old_machine_id, new_machine_id)
        if analysis['algorithm'] == 'SHA512':
            new_key = hashlib.sha512(input_pattern.encode('utf-8')).hexdigest().upper()
            print(f"   New Key: {new_key}")
    else:
        print("\n3. Using ORIGINAL key (server validation may fail)...")
        print("   WARNING: The key is likely server-signed.")
        print("   You may need to:")
        print("   - Patch the DLL to skip server validation")
        print("   - Use the original machine ID")
        print("   - Contact the vendor for a new key")
        new_key = old_key
    
    # Create license for new machine ID
    print(f"\n4. Creating license for NEW machine ID...")
    patcher.create_license_file(
        new_machine_id,
        "license_new.txt",
        new_key
    )
    
    print("\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    print("""
1. Locate the license file used by BestOrderflowUnlocker.dll
   Likely locations:
   - %APPDATA%\\NinjaTrader\\
   - %LOCALAPPDATA%\\NinjaTrader\\
   - Same directory as the DLL
   - Registry: HKCU\\Software\\NinjaTrader

2. Replace the license file with license_new.txt

3. If validation still fails:
   - The key is server-validated (not locally)
   - You'll need to patch the DLL to bypass validation
   - Use dnSpy to decompile and modify the validation logic

4. To patch the DLL:
   - Open BestOrderflowUnlocker.dll in dnSpy
   - Find the license validation method
   - Modify it to always return "Success"
   - Save the patched assembly

5. LEGAL NOTICE:
   - This is for educational purposes only
   - Bypassing license protection may violate ToS
   - Purchase a legitimate license if using commercially
""")

if __name__ == "__main__":
    main()
