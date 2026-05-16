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
