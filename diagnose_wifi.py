"""
WiFi Diagnosis Script
=====================
This script will help identify why WiFi scanning is failing.
"""

import subprocess
import platform
import re

print("=" * 70)
print("WiFi Scanner Diagnostic Tool")
print("=" * 70)

# Check 1: Operating System
print("\n[CHECK 1] Operating System")
print("-" * 70)
os_name = platform.system()
print(f"OS: {os_name}")
if os_name == 'Windows':
    print("✅ Windows detected - netsh command should be available")
else:
    print(f"❌ Not Windows - netsh command not available on {os_name}")

# Check 2: Run netsh command and capture output
print("\n[CHECK 2] Running netsh command")
print("-" * 70)
print("Command: netsh wlan show networks mode=bssid")
print()

try:
    result = subprocess.run(
        ['netsh', 'wlan', 'show', 'networks', 'mode=bssid'],
        capture_output=True,
        text=True,
        timeout=15
    )
    
    print(f"Return Code: {result.returncode}")
    print(f"Output Length: {len(result.stdout)} characters")
    print(f"Error Length: {len(result.stderr)} characters")
    
    if result.returncode != 0:
        print("\n❌ Command failed!")
        print("\nError Output:")
        print(result.stderr)
    else:
        print("\n✅ Command succeeded!")
        print("\nRaw Output:")
        print("=" * 70)
        print(result.stdout)
        print("=" * 70)
        
        # Check 3: Parse the output
        print("\n[CHECK 3] Parsing WiFi networks")
        print("-" * 70)
        
        networks = []
        current_ssid = None
        
        for line in result.stdout.split('\n'):
            line = line.strip()
            
            # Look for SSID
            ssid_match = re.search(r'SSID \d+ : (.+)', line)
            if ssid_match:
                current_ssid = ssid_match.group(1).strip()
                if current_ssid == '':
                    current_ssid = None
                    print(f"Found: [Hidden Network]")
                else:
                    print(f"Found SSID: {current_ssid}")
                continue
            
            # Look for BSSID
            bssid_match = re.search(r'BSSID \d+ : ([0-9a-fA-F:]{17})', line)
            if bssid_match and current_ssid:
                bssid = bssid_match.group(1).strip().upper()
                networks.append((current_ssid, bssid))
                print(f"  -> BSSID: {bssid}")
        
        print(f"\n✅ Successfully parsed {len(networks)} network entries")
        
        if networks:
            print("\n[CHECK 4] Network Summary")
            print("-" * 70)
            unique_ssids = set()
            for ssid, bssid in networks:
                if ssid not in unique_ssids:
                    unique_ssids.add(ssid)
                    print(f"📡 {ssid}")
            print(f"\nTotal unique SSIDs: {len(unique_ssids)}")
            print(f"Total access points: {len(networks)}")
        else:
            print("\n❌ No networks found in output")
            print("Possible reasons:")
            print("  • WiFi is disabled")
            print("  • No networks in range")
            print("  • Regex pattern not matching output format")

except FileNotFoundError:
    print("❌ 'netsh' command not found")
    print("This system may not support netsh")
except subprocess.TimeoutExpired:
    print("❌ Command timed out after 15 seconds")
except Exception as e:
    print(f"❌ Error: {e}")
    print(f"Error type: {type(e).__name__}")

print("\n" + "=" * 70)
print("Diagnosis Complete")
print("=" * 70)
