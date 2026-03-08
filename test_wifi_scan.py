"""
Quick Test Script for WiFi Scanning
====================================

Run this to verify WiFi scanning is working on your system.
This will show you exactly what networks are being detected.
"""

from wifi_scanner import get_real_wifi_networks, scan_wifi

print("=" * 70)
print("WiFi Scanner Test - Testing Live Network Detection")
print("=" * 70)

print("\n[TEST] Step 1: Testing raw network scan...")
print("-" * 70)

networks = get_real_wifi_networks()

if networks is None:
    print("\n❌ FAILED: WiFi scan returned no data")
    print("\nTroubleshooting steps:")
    print("1. Make sure WiFi is enabled on your computer")
    print("2. Check that you're on Windows")
    print("3. Try running: netsh wlan show networks mode=bssid")
    print("   in Command Prompt to verify WiFi is working")
else:
    print(f"\n✅ SUCCESS: Found {len(networks)} network access points")
    print("\nDetected Networks:")
    print("-" * 70)
    for i, (ssid, bssid) in enumerate(networks, 1):
        print(f"{i}. SSID: {ssid:<30} | MAC: {bssid}")

print("\n" + "=" * 70)
print("[TEST] Step 2: Testing Evil Twin detection...")
print("-" * 70)

result = scan_wifi()
print(f"\nStatus: {result['status']}")
print(f"Message: {result['message']}")

print("\n" + "=" * 70)
print("Test Complete!")
print("=" * 70)
