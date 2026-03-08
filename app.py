"""
SafeLink AI - Flask Backend Application
========================================

This is the main Flask web application that serves the SafeLink AI
threat detection dashboard and handles security scanning requests.

Features:
---------
1. Serves the web dashboard interface
2. Coordinates WiFi Evil Twin detection
3. Coordinates shoulder surfing detection
4. Returns real-time security alerts to the frontend

Routes:
-------
- GET  /       : Main dashboard page
- POST /scan   : Triggers security scans and returns results
"""

import os
from datetime import datetime, timezone

from flask import Flask, render_template, jsonify
from wifi_scanner import scan_wifi
from shoulder_detection import detect_shoulder_surfer

# Initialize Flask application
app = Flask(__name__)

# Configure Flask
app.config['SECRET_KEY'] = 'safelink-ai-hackathon-2026'


@app.route('/')
def index():
    """
    Main dashboard route.
    
    Renders the main HTML page with the threat detection interface.
    
    Returns:
        HTML: The dashboard template
    """
    print("[Flask] Loading SafeLink AI Dashboard...")
    return render_template('index.html')


@app.route('/scan', methods=['POST'])
def scan():
    """
    Security scan endpoint.
    
    This route triggers both security modules:
    1. WiFi Evil Twin detection
    2. Shoulder surfing detection
    
    Returns:
        JSON: Combined results from both security modules containing:
            - network_status: Status of WiFi scan ("safe", "suspicious", or "error")
            - network_message: Detailed WiFi scan message
            - networks: List of all detected networks [{"ssid": "...", "mac": "..."}]
            - suspicious_ssids: List of suspicious SSID names (if any)
            - connected_ap: Currently connected AP {"ssid": "...", "mac": "..."}
            - visual_status: Status of shoulder surfing scan ("safe", "risk", or "error")
            - visual_message: Detailed shoulder surfing message
    """
    print("\n" + "="*60)
    print("[Flask] Security scan initiated by user")
    print("="*60)
    
    # STEP 1: Run WiFi network scan
    print("\n[Flask] Starting WiFi Evil Twin detection...")
    network_result = scan_wifi()
    
    # STEP 2: Run shoulder surfing detection
    print("\n[Flask] Starting shoulder surfing detection...")
    visual_result = detect_shoulder_surfer()
    
    # STEP 3: Prepare response data
    response_data = {
        # Network security results - Real WiFi networks detected
        'network_status': network_result.get('status', 'error'),
        'network_message': network_result.get('message', 'Scan failed'),
        'networks': network_result.get('networks', []),  # List of {"ssid": "...", "mac": "..."}
        'suspicious_ssids': network_result.get('suspicious_ssids', []),
        'duplicate_ssids': network_result.get('duplicate_ssids', []),
        'mixed_vendor_ssids': network_result.get('mixed_vendor_ssids', []),
        'bssid_changed_ssids': network_result.get('bssid_changed_ssids', []),
        'signal_anomaly_ssids': network_result.get('signal_anomaly_ssids', []),
        'threat_scores': network_result.get('threat_scores', {}),
        'overall_threat_score': network_result.get('overall_threat_score', 0),
        'recent_live_networks': network_result.get('recent_live_networks', []),
        'recent_window_seconds': network_result.get('recent_window_seconds', 60),
        'scan_passes_used': network_result.get('scan_passes_used', 1),
        'scanned_at': datetime.now(timezone.utc).isoformat(),
        'connected_ap': network_result.get('connected_ap'),
        
        # Visual privacy results - Shoulder surfing detection
        'visual_status': visual_result.get('status', 'error'),
        'visual_message': visual_result.get('message', 'Detection failed')
    }
    
    # Log detailed results
    print("\n[Flask] Scan Results:")
    print(f"  Network Status: {response_data['network_status']}")
    print(f"  Total Networks Detected: {len(response_data['networks'])}")
    
    # Display detected networks in console
    if response_data['networks']:
        print("\n[Flask] Detected WiFi Networks:")
        for i, net in enumerate(response_data['networks'], 1):
            is_suspicious = net['ssid'] in response_data['suspicious_ssids']
            marker = " ⚠️ SUSPICIOUS" if is_suspicious else ""
            print(f"  {i}. {net['ssid']:<25} | MAC: {net['mac']}{marker}")
    
    if response_data['suspicious_ssids']:
        print(f"\n[Flask] ⚠️ Evil Twin Networks: {', '.join(response_data['suspicious_ssids'])}")
    
    print(f"\n[Flask] Visual Privacy Status: {response_data['visual_status']}")
    print("="*60 + "\n")
    
    # STEP 4: Return JSON response to frontend
    return jsonify(response_data)


@app.route('/health')
def health():
    """
    Health check endpoint for monitoring.
    
    Returns:
        JSON: Simple health status
    """
    return jsonify({
        'status': 'healthy',
        'service': 'SafeLink AI',
        'version': '1.0.0'
    })


@app.route('/api/networks')
def get_networks():
    """
    API endpoint to get current WiFi networks without full scan.
    
    Returns:
        JSON: Network scan results
    """
    print("\n[Flask] API request for network list")
    # Use multiple quick passes for live monitoring to reduce missed APs.
    # Slightly higher pass count improves reliability when nearby networks
    # appear/disappear quickly during channel hopping.
    network_result = scan_wifi(scan_passes=5, inter_pass_delay=0.35)
    network_result['scanned_at'] = datetime.now(timezone.utc).isoformat()
    network_result['scan_mode'] = 'live'
    return jsonify(network_result)


# Error handlers for better user experience
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    """
    Application entry point.
    
    Starts the Flask development server on:
    - Host: 127.0.0.1 (localhost)
    - Port: 5000
    - Debug mode: Enabled for development
    """
    # Flask debug mode starts a parent process and a child process.
    # Print the startup banner only in the reloader child process
    # to avoid duplicate banner output in the terminal.
    debug_mode = True
    is_reloader_child = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
    should_print_banner = (not debug_mode) or is_reloader_child

    if should_print_banner:
        print("\n" + "="*60)
        print("     SafeLink AI - Threat Detection System")
        print("="*60)
        print("\nStarting Flask server...")
        print("Server URL: http://127.0.0.1:5000")
        print("Dashboard: Open the URL in your browser")
        print("\nPress CTRL+C to stop the server")
        print("="*60 + "\n")
    
    # Start the Flask development server
    # debug=True enables auto-reload and detailed error messages
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=debug_mode
    )
