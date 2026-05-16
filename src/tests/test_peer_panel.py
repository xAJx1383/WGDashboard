import pytest
import sys
import os
from unittest.mock import MagicMock
from flask import Flask

# Add src to sys.path to allow importing modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from peer_panel import get_peer_by_ip, peer_panel

def test_ip_identification():
    # Mock Peer objects
    peer1 = MagicMock()
    peer1.allowed_ip = "10.0.0.2/32"
    
    peer2 = MagicMock()
    peer2.allowed_ip = "10.0.0.3/32, fd00::2/128"

    # Mock WireguardConfiguration objects
    conf1 = MagicMock()
    conf1.getStatus.return_value = True
    conf1.Peers = [peer1, peer2]
    
    # Inactive configuration
    conf2 = MagicMock()
    conf2.getStatus.return_value = False
    peer3 = MagicMock()
    peer3.allowed_ip = "10.0.0.4/32"
    conf2.Peers = [peer3]

    configurations = {
        "wg0": conf1,
        "wg1": conf2
    }

    # Test 1: Exact IPv4 match
    assert get_peer_by_ip("10.0.0.2", configurations) == peer1

    # Test 2: IPv6 match in multiple allowed IPs
    assert get_peer_by_ip("fd00::2", configurations) == peer2

    # Test 3: No match
    assert get_peer_by_ip("10.0.0.5", configurations) is None

    # Test 4: Should not match peer in inactive configuration
    assert get_peer_by_ip("10.0.0.4", configurations) is None

def test_blueprint_isolation():
    app = Flask(__name__)
    app.register_blueprint(peer_panel, url_prefix='/peer')
    
    # Mock WGD in app.config
    peer1 = MagicMock()
    peer1.id = "peer1_pubkey"
    peer1.allowed_ip = "10.0.0.2/32"
    
    conf1 = MagicMock()
    conf1.getStatus.return_value = True
    conf1.Peers = [peer1]
    
    app.config['WGD'] = {"wg0": conf1}
    
    with app.test_client() as client:
        # 1. Access with known IP
        response = client.get('/peer/usage_check', environ_overrides={'REMOTE_ADDR': '10.0.0.2'})
        assert response.status_code == 200
        assert response.get_json() == {"status": "identified", "peer_id": "peer1_pubkey"}
        
        # 2. Access with unknown IP
        response = client.get('/peer/usage_check', environ_overrides={'REMOTE_ADDR': '10.0.0.5'})
        assert response.status_code == 403

def test_usage_route():
    app = Flask(__name__)
    app.register_blueprint(peer_panel, url_prefix='/peer')
    
    peer1 = MagicMock()
    peer1.id = "peer1_pubkey"
    peer1.name = "Test Peer"
    peer1.allowed_ip = "10.0.0.2/32"
    peer1.total_receive = 1024
    peer1.total_sent = 2048
    peer1.total_data = 3072
    peer1.status = "running"
    peer1.latest_handshake = "2 minutes ago"
    peer1.configuration.Name = "wg0"
    
    conf1 = MagicMock()
    conf1.getStatus.return_value = True
    conf1.Peers = [peer1]
    
    app.config['WGD'] = {"wg0": conf1}
    
    with app.test_client() as client:
        response = client.get('/peer/usage', environ_overrides={'REMOTE_ADDR': '10.0.0.2'})
        assert response.status_code == 200
        # Check if some key content is present in the rendered HTML
        html = response.get_data(as_text=True)
        assert "Test Peer" in html
        assert "peer1_pubkey" in html
        assert "1.0 KB" in html # 1024 bytes
        assert "2.0 KB" in html # 2048 bytes

def test_secondary_port_service():
    # Mocking necessary components to test startPeerPanelThread
    from unittest.mock import patch, MagicMock
    
    # We need to mock DashboardConfig BEFORE importing dashboard because dashboard.py 
    # executes code on import.
    mock_config_inst = MagicMock()
    def get_config_side_effect(section, key):
        if section == "PeerPanel":
            if key == "peer_panel_enable": return True, True
            if key == "peer_panel_port": return True, "10087"
            if key == "peer_panel_bind_address": return True, "127.0.0.1"
        if section == "Server" and key == "app_port": return True, "10086"
        if section == "Server" and key == "wg_conf_path": return True, "/tmp"
        if section == "Server" and key == "awg_conf_path": return True, "/tmp"
        return True, ""
        
    mock_config_inst.GetConfig.side_effect = get_config_side_effect
    
    with patch('modules.DashboardConfig.DashboardConfig', return_value=mock_config_inst), \
         patch('threading.Thread') as mock_thread:
        
        if 'dashboard' in sys.modules:
            del sys.modules['dashboard']
        import dashboard
        dashboard.DashboardConfig = mock_config_inst
        
        dashboard.startPeerPanelThread()
        
        # Ports are different (10087 vs 10086), so a thread should be started
        assert mock_thread.called
        # Check if the last thread started has daemon=True
        args, kwargs = mock_thread.call_args
        assert kwargs['daemon'] is True
