"""
SafeLink AI - WiFi Evil Twin Threat Scoring Module
==================================================

This module implements a threat scoring model for WiFi Evil Twin detection.

Scoring rules (per SSID):
- Duplicate SSID (multiple BSSIDs)         : +40
- Different vendor prefix under same SSID  : +30
- New BSSID not seen before                : +20
- Large signal strength anomaly            : +10

Score classification:
- 0 to 30   -> SAFE
- 31 to 60  -> SUSPICIOUS
- > 60      -> POSSIBLE EVIL TWIN
"""

import json
import os
import re
import subprocess
import threading
import time
from difflib import SequenceMatcher

HISTORY_FILE_PATH = os.path.join(os.path.dirname(__file__), "wifi_history.json")
HISTORY_LOCK = threading.Lock()
RECENT_SIGHTINGS_LOCK = threading.Lock()
RECENT_SIGHTINGS_WINDOW_SECONDS = 60

# In-memory history: {ssid: set([bssid1, bssid2, ...])}
SSID_BSSID_HISTORY = {}
# In-memory short-term cache: {(ssid, bssid): {"ssid":..., "mac":..., "signal":..., "last_seen":...}}
RECENT_SIGHTINGS = {}


def _is_hidden_ssid(ssid):
    """Return True if SSID is a hidden-network placeholder."""
    return ssid.startswith("[Hidden SSID #")


def _get_vendor_prefix(bssid):
    """Return vendor prefix (OUI = first 3 bytes) from a MAC/BSSID."""
    parts = bssid.strip().upper().split(":")
    if len(parts) < 3:
        return ""
    return ":".join(parts[:3])


def _score_to_status(score):
    """
    Map numeric threat score to readable risk level.
    """

    if score <= 20:
        return "safe", "LOW RISK"

    if score <= 50:
        return "suspicious", "MEDIUM RISK"

    if score <= 80:
        return "risk", "HIGH RISK"

    return "risk", "CRITICAL (EVIL TWIN)"

def _ssid_similarity(a, b):
        """Return similarity between two SSID names."""
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _update_recent_sightings(networks):
    """Update short-term live sightings cache from current scan."""
    now_ts = time.time()

    with RECENT_SIGHTINGS_LOCK:
        for network in networks:
            ssid = str(network.get("ssid", "")).strip()
            bssid = str(network.get("mac", "")).strip().upper()
            if not ssid or not bssid:
                continue

            RECENT_SIGHTINGS[(ssid, bssid)] = {
                "ssid": ssid,
                "mac": bssid,
                "signal": network.get("signal"),
                "last_seen": now_ts,
            }

        # Cleanup old sightings to keep cache bounded.
        stale_keys = [
            key
            for key, value in RECENT_SIGHTINGS.items()
            if (now_ts - value.get("last_seen", 0)) > RECENT_SIGHTINGS_WINDOW_SECONDS
        ]
        for key in stale_keys:
            RECENT_SIGHTINGS.pop(key, None)


def _get_recent_live_networks(window_seconds=None):
    """Return networks seen recently within a short rolling time window."""
    if window_seconds is None:
        window_seconds = RECENT_SIGHTINGS_WINDOW_SECONDS

    now_ts = time.time()
    recent_networks = []

    with RECENT_SIGHTINGS_LOCK:
        for value in RECENT_SIGHTINGS.values():
            if (now_ts - value.get("last_seen", 0)) <= window_seconds:
                recent_networks.append(
                    {
                        "ssid": value.get("ssid"),
                        "mac": value.get("mac"),
                        "signal": value.get("signal"),
                    }
                )

    return recent_networks


def _has_signal_anomaly(signals):
    """
    Detect large signal anomaly from current scan.

    Uses spread between strongest and weakest AP signal for the same SSID.
    """
    if len(signals) < 2:
        return False
    return (max(signals) - min(signals)) >= 35


def _load_history_from_disk():
    """Load SSID/BSSID history from JSON file if available."""
    if not os.path.exists(HISTORY_FILE_PATH):
        return

    try:
        with open(HISTORY_FILE_PATH, "r", encoding="utf-8") as history_file:
            data = json.load(history_file)

        if not isinstance(data, dict):
            return

        with HISTORY_LOCK:
            SSID_BSSID_HISTORY.clear()
            for ssid, bssids in data.items():
                if not isinstance(ssid, str) or not isinstance(bssids, list):
                    continue
                normalized = {
                    str(bssid).strip().upper()
                    for bssid in bssids
                    if isinstance(bssid, str) and bssid.strip()
                }
                if normalized:
                    SSID_BSSID_HISTORY[ssid] = normalized

        print(f"[WiFi Scanner] Loaded persisted history for {len(SSID_BSSID_HISTORY)} SSID(s)")
    except Exception as error:
        print(f"[WiFi Scanner] Failed to load history: {type(error).__name__}")


def _save_history_to_disk():
    """Persist current SSID/BSSID history to JSON file."""
    try:
        with HISTORY_LOCK:
            serializable = {
                ssid: sorted(list(bssids))
                for ssid, bssids in SSID_BSSID_HISTORY.items()
            }

        tmp_path = HISTORY_FILE_PATH + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as history_file:
            json.dump(serializable, history_file, indent=2, sort_keys=True)

        os.replace(tmp_path, HISTORY_FILE_PATH)
    except Exception as error:
        print(f"[WiFi Scanner] Failed to save history: {type(error).__name__}")


def _parse_networks_from_output(output_text):
    """
    Parse `netsh wlan show networks mode=bssid` output.

    Returns list of dicts with keys:
    - ssid
    - mac
    - signal (int percentage when available)
    """
    networks = []
    current_ssid = None
    current_entry = None

    for raw_line in output_text.split("\n"):
        line = raw_line.strip()

        ssid_match = re.search(r"^\s*SSID\s+(\d+)\s*:\s*(.*)$", line, re.IGNORECASE)
        if ssid_match:
            ssid_index = ssid_match.group(1).strip()
            ssid_name = ssid_match.group(2).strip()
            current_ssid = ssid_name if ssid_name else f"[Hidden SSID #{ssid_index}]"
            current_entry = None
            continue

        bssid_match = re.search(r"BSSID\s+\d+\s+:\s*([0-9a-fA-F:]{17})", line, re.IGNORECASE)
        if bssid_match and current_ssid:
            current_entry = {
                "ssid": current_ssid,
                "mac": bssid_match.group(1).strip().upper(),
                "signal": None,
            }
            networks.append(current_entry)
            continue

        signal_match = re.search(r"^Signal\s*:\s*(\d+)%$", line, re.IGNORECASE)
        if signal_match and current_entry is not None:
            current_entry["signal"] = int(signal_match.group(1))

    return networks


def _group_networks_by_ssid(networks):
                
    """Group scanned entries by SSID and enrich with derived fields."""
    grouped = {}

    for network in networks:
        ssid = str(network.get("ssid", "")).strip()
        bssid = str(network.get("mac", "")).strip().upper()
        signal = network.get("signal")

        if not ssid or not bssid:
            continue

        if ssid not in grouped:
            grouped[ssid] = {
                "entries": [],
                "bssids": set(),
                "vendors": set(),
                "signals": [],
            }

        grouped[ssid]["entries"].append(network)
        grouped[ssid]["bssids"].add(bssid)

        vendor_prefix = _get_vendor_prefix(bssid)
        if vendor_prefix:
            grouped[ssid]["vendors"].add(vendor_prefix)

        if isinstance(signal, int):
            grouped[ssid]["signals"].append(signal)
        similar_ssids = []
        ssid_list = list(grouped.keys())
        for i in range(len(ssid_list)):
            for j in range(i + 1, len(ssid_list)):
              s1 = ssid_list[i]
              s2 = ssid_list[j]
              sim = _ssid_similarity(s1, s2)
              if sim > 0.75 and s1 != s2:
                 similar_ssids.append((s1, s2))

    return grouped, similar_ssids


def _get_connected_access_point():
    """Return currently connected AP (SSID + BSSID), if available."""
    try:
        output = subprocess.check_output(
            "netsh wlan show interfaces",
            shell=True,
            stderr=subprocess.STDOUT,
        ).decode("utf-8", errors="ignore")

        connected_ssid = None
        connected_bssid = None

        for raw_line in output.split("\n"):
            line = raw_line.strip()

            ssid_match = re.search(r"^SSID\s*:\s*(.+)$", line, re.IGNORECASE)
            if ssid_match:
                candidate = ssid_match.group(1).strip()
                if candidate and candidate.lower() != "name":
                    connected_ssid = candidate
                continue

            bssid_match = re.search(
                r"^AP\s+BSSID\s*:\s*([0-9a-fA-F:]{17})$", line, re.IGNORECASE
            )
            if bssid_match:
                connected_bssid = bssid_match.group(1).strip().upper()

        if connected_ssid and connected_bssid:
            return {"ssid": connected_ssid, "mac": connected_bssid}
    except Exception:
        pass

    return None


def scan_wifi_networks(scan_passes=1, inter_pass_delay=0.25):
    """Run one or more quick netsh scans and merge results."""
    try:
        scan_passes = int(scan_passes)
    except Exception:
        scan_passes = 1

    if scan_passes < 1:
        scan_passes = 1

    networks_by_key = {}

    for pass_index in range(scan_passes):
        print(
            f"[WiFi Scanner] Running command: netsh wlan show networks mode=bssid "
            f"(pass {pass_index + 1}/{scan_passes})"
        )

        output = subprocess.check_output(
            "netsh wlan show networks mode=bssid",
            shell=True,
            stderr=subprocess.STDOUT,
        ).decode("utf-8", errors="ignore")

        parsed_pass_networks = _parse_networks_from_output(output)
        print(
            f"[WiFi Scanner] Pass {pass_index + 1}: "
            f"{len(parsed_pass_networks)} access points detected"
        )

        for network in parsed_pass_networks:
            key = (network["ssid"], network["mac"])
            # Keep strongest observed signal across passes for this AP.
            if key in networks_by_key:
                old_signal = networks_by_key[key].get("signal")
                new_signal = network.get("signal")
                if isinstance(new_signal, int) and (
                    not isinstance(old_signal, int) or new_signal > old_signal
                ):
                    networks_by_key[key]["signal"] = new_signal
            else:
                networks_by_key[key] = network

        if pass_index < (scan_passes - 1):
            time.sleep(inter_pass_delay)

    return list(networks_by_key.values())


def detect_evil_twin(networks):
    """
    Return SSIDs where multiple vendor prefixes are found under same SSID.

    This identifies stronger Evil Twin signals than simple duplicate SSID checks.
    """
    grouped = _group_networks_by_ssid(networks)
    suspicious = []

    for ssid, data in grouped.items():
        if _is_hidden_ssid(ssid):
            continue
        if len(data["bssids"]) > 1 and len(data["vendors"]) > 1:
            suspicious.append(ssid)

    return sorted(suspicious)


def check_bssid_history(networks):
    """
    Detect known SSIDs where new BSSID(s) appear and update persistent history.

    Returns:
        dict[str, set[str]]: map of SSID -> newly seen BSSID(s)
    """
    grouped, similar_ssids = _group_networks_by_ssid(networks)
    new_bssid_map = {}

    with HISTORY_LOCK:
        for ssid, data in grouped.items():
            if _is_hidden_ssid(ssid):
                continue

            current_bssids = set(data["bssids"])
            known_bssids = SSID_BSSID_HISTORY.get(ssid, set())

            if known_bssids:
                new_bssids = current_bssids - known_bssids
                if new_bssids:
                    print(f"[ALERT] Possible Evil Twin Detected (BSSID changed): {ssid}")
                    print(f"[ALERT] Previously known BSSIDs: {sorted(known_bssids)}")
                    print(f"[ALERT] New observed BSSID(s): {sorted(new_bssids)}")
                    new_bssid_map[ssid] = new_bssids

            if ssid not in SSID_BSSID_HISTORY:
                SSID_BSSID_HISTORY[ssid] = set()
            SSID_BSSID_HISTORY[ssid].update(current_bssids)

    _save_history_to_disk()
    return new_bssid_map


def _calculate_threat_score_for_ssid(ssid, data, new_bssids, similar_ssids):
    """Calculate threat score and explain which rules contributed."""
    score = 0
    reasons = []
    # Check for SSID similarity (possible evil twin)
    for s1, s2 in similar_ssids:
        if ssid == s1 or ssid == s2:
            score += 40
            reasons.append(f"Similar SSID detected: {s1} ↔ {s2}")
        
    ap_count = len(data["bssids"])
    vendor_count = len(data["vendors"])
    is_multi_ap = ap_count > 1
    has_mixed_vendor = vendor_count > 1
    # Detect legitimate multi-AP enterprise networks
    if is_multi_ap and not has_mixed_vendor:
        reasons.append("Multiple legitimate access points detected")

    # Duplicate SSID points are applied only when multiple vendor prefixes exist.
    # Same-vendor multi-AP is typically legitimate enterprise/campus deployment.
    if is_multi_ap and has_mixed_vendor:
        score += 40
        reasons.append("Duplicate SSID (+40)")

    if is_multi_ap and not has_mixed_vendor:
        reasons.append("Enterprise multi-AP (same vendor prefix, no penalty)")

    if has_mixed_vendor:
        score += 30
        reasons.append("Different vendor prefix (+30)")

    if new_bssids:
        score += 20
        reasons.append("New BSSID not seen before (+20)")

    # Signal spread is noisy in multi-AP deployments; score anomaly only when
    # mixed vendors are also present.
    signal_anomaly_detected = _has_signal_anomaly(data["signals"])
    signal_anomaly_scored = signal_anomaly_detected and has_mixed_vendor
    if signal_anomaly_scored:
        score += 10
        reasons.append("Large signal strength anomaly (+10)")

    api_status, label = _score_to_status(score)

    print(f"Network: {ssid}")
    print(f"Access Points: {ap_count}")
    print(f"Threat Score: {score}")
    print(f"Status: {label}")
    if reasons:
        print(f"Reasons: {', '.join(reasons)}")
    else:
        print("Reasons: None")
    print("-" * 60)

    return {
        "score": score,
        "api_status": api_status,
        "label": label,
        "ap_count": ap_count,
        "vendor_prefixes": sorted(list(data["vendors"])),
        "reasons": reasons,
        "has_signal_anomaly": signal_anomaly_scored,
        "signal_anomaly_detected": signal_anomaly_detected,
    }


def scan_wifi(scan_passes=1, inter_pass_delay=0.25):
    """Main function used by Flask app endpoints."""
    print("[WiFi Scanner] Initiating WiFi network threat scoring...")

    try:
        networks = scan_wifi_networks(
            scan_passes=scan_passes,
            inter_pass_delay=inter_pass_delay,
        )

        _update_recent_sightings(networks)
        recent_live_networks = _get_recent_live_networks()

        connected_ap = _get_connected_access_point()

        if not networks:
            return {
                "status": "error",
                "message": "No WiFi networks found. Ensure WiFi is enabled and in range.",
                "networks": [],
                "suspicious_ssids": [],
                "duplicate_ssids": [],
                "mixed_vendor_ssids": [],
                "bssid_changed_ssids": [],
                "signal_anomaly_ssids": [],
                "threat_scores": {},
                "overall_threat_score": 0,
                "recent_live_networks": recent_live_networks,
                "recent_window_seconds": RECENT_SIGHTINGS_WINDOW_SECONDS,
                "connected_ap": connected_ap,
                "scan_passes_used": scan_passes,
            }

        grouped, similar_ssids = _group_networks_by_ssid(networks)
        new_bssid_map = check_bssid_history(networks)

        threat_scores = {}
        duplicate_ssids = []
        mixed_vendor_ssids = []
        bssid_changed_ssids = []
        signal_anomaly_ssids = []

        for ssid in sorted(grouped.keys()):
            if _is_hidden_ssid(ssid):
                continue

            data = grouped[ssid]
            new_bssids = new_bssid_map.get(ssid, set())
            ssid_result = _calculate_threat_score_for_ssid(ssid, data, new_bssids, similar_ssids)
            threat_scores[ssid] = ssid_result

            if len(data["bssids"]) > 1 and len(data["vendors"]) > 1:
                duplicate_ssids.append(ssid)
            if len(data["vendors"]) > 1:
                mixed_vendor_ssids.append(ssid)
            if new_bssids:
                bssid_changed_ssids.append(ssid)
            if ssid_result["has_signal_anomaly"]:
                signal_anomaly_ssids.append(ssid)

        per_ssid_scores = [details["score"] for details in threat_scores.values()]
        overall_threat_score = max(per_ssid_scores) if per_ssid_scores else 0
        wifi_safety_score = max(0, 100 - overall_threat_score)
        status, overall_label = _score_to_status(overall_threat_score)
        
        # Determine safest network (consider threat score + signal strength)
        recommended_network = None
        if threat_scores:
            recommended_network = min(
                threat_scores,
                key=lambda ssid: (
                    threat_scores[ssid]["score"],  # lowest threat first
                    -max(grouped[ssid]["signals"]) if grouped[ssid]["signals"] else 0
                    )
                )

        suspicious_ssids = [
            ssid for ssid, details in threat_scores.items() if details["score"] > 30
        ]

        message = (
            f"Threat scoring complete for {len(threat_scores)} SSID(s). "
            f"Highest score: {overall_threat_score} ({overall_label})."
        )

        return {
            "status": status,
            "message": message,
            "networks": networks,
            "recommended_network": recommended_network,
            "wifi_safety_score": wifi_safety_score,
            "suspicious_ssids": sorted(suspicious_ssids),
            "duplicate_ssids": sorted(duplicate_ssids),
            "mixed_vendor_ssids": sorted(mixed_vendor_ssids),
            "bssid_changed_ssids": sorted(bssid_changed_ssids),
            "signal_anomaly_ssids": sorted(signal_anomaly_ssids),
            "threat_scores": threat_scores,
            "overall_threat_score": overall_threat_score,
            "recent_live_networks": recent_live_networks,
            "recent_window_seconds": RECENT_SIGHTINGS_WINDOW_SECONDS,
            "connected_ap": connected_ap,
            "scan_passes_used": scan_passes,
            "similar_ssid_pairs": similar_ssids
        }

    except subprocess.CalledProcessError as error:
        print(f"[WiFi Scanner] Command execution failed: {error}")
        return {
            "status": "error",
            "message": "Unable to scan WiFi networks. Ensure Windows WiFi services are active.",
            "networks": [],
            "suspicious_ssids": [],
            "duplicate_ssids": [],
            "mixed_vendor_ssids": [],
            "bssid_changed_ssids": [],
            "signal_anomaly_ssids": [],
            "similar_ssid_pairs": [],
            "threat_scores": {},
            "overall_threat_score": 0,
            "recent_live_networks": [],
            "recent_window_seconds": RECENT_SIGHTINGS_WINDOW_SECONDS,
            "connected_ap": None,
            "scan_passes_used": scan_passes,
        }

    except FileNotFoundError:
        print("[WiFi Scanner] netsh command not found")
        return {
            "status": "error",
            "message": "The 'netsh' command is not available. This scanner requires Windows.",
            "networks": [],
            "suspicious_ssids": [],
            "duplicate_ssids": [],
            "mixed_vendor_ssids": [],
            "bssid_changed_ssids": [],
            "signal_anomaly_ssids": [],
            "similar_ssid_pairs": [],
            "threat_scores": {},
            "overall_threat_score": 0,
            "recent_live_networks": [],
            "recent_window_seconds": RECENT_SIGHTINGS_WINDOW_SECONDS,
            "connected_ap": None,
            "scan_passes_used": scan_passes,
        }

    except Exception as error:
        print(f"[WiFi Scanner] Unexpected error: {type(error).__name__}: {error}")
        return {
            "status": "error",
            "message": f"Unexpected error during WiFi scanning: {type(error).__name__}",
            "networks": [],
            "suspicious_ssids": [],
            "duplicate_ssids": [],
            "mixed_vendor_ssids": [],
            "bssid_changed_ssids": [],
            "signal_anomaly_ssids": [],
            "threat_scores": {},
            "overall_threat_score": 0,
            "recent_live_networks": [],
            "recent_window_seconds": RECENT_SIGHTINGS_WINDOW_SECONDS,
            "connected_ap": None,
            "scan_passes_used": scan_passes,
        }


# Load persisted history when module is imported.
_load_history_from_disk()


if __name__ == "__main__":
    print("=" * 70)
    print("SafeLink AI - WiFi Threat Scoring Test")
    print("=" * 70)

    result = scan_wifi(scan_passes=1)

    print("\n" + "=" * 70)
    print("SCAN RESULTS")
    print("=" * 70)
    print(f"Status: {result.get('status', 'unknown').upper()}")
    print(f"Overall Threat Score: {result.get('overall_threat_score', 0)}")
    print(f"Message: {result.get('message', '')}")

    if result.get("connected_ap"):
        connected = result["connected_ap"]
        print(f"Connected AP: {connected['ssid']} | {connected['mac']}")

    print("\n" + "=" * 70)
    print("Test Complete")
    print("=" * 70)