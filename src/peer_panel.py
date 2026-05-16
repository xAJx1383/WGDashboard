from flask import Blueprint, request, abort, g, render_template
from modules.Utilities import IsIPInSubnet, FormatBytes

peer_panel = Blueprint('peer_panel', __name__, template_folder='../static/dist/WGDashboardPeerPanel')

def get_peer_by_ip(remote_addr, wireguard_configurations):
    """
    Identifies a WireGuard peer based on its internal VPN IP address.
    """
    for config in wireguard_configurations.values():
        # Only check active configurations
        if config.getStatus():
            for peer in config.Peers:
                # Peer allowed_ip can be a comma-separated list of subnets
                allowed_ips = [ip.strip() for ip in peer.allowed_ip.split(",")]
                for subnet in allowed_ips:
                    if IsIPInSubnet(remote_addr, subnet):
                        return peer
    return None

@peer_panel.before_request
def restrict_to_peers():
    """
    Isolation hook: verifies the requester is a known WireGuard peer.
    """
    # wireguard_configurations is stored in current_app.config or passed via g
    # Based on src/dashboard.py, it's usually in a global or passed around.
    # Looking at how routes access it in dashboard.py might help.
    from flask import current_app
    WGD = current_app.config.get('WGD')
    if not WGD:
        abort(500, description="WireGuard configurations not initialized")
        
    peer = get_peer_by_ip(request.remote_addr, WGD)
    if not peer:
        abort(403, description="Access denied: Unknown Peer IP")
    
    g.current_peer = peer

@peer_panel.route('/usage_check', methods=['GET'])
def usage_check():
    """
    Test route to verify peer identification.
    """
    return {"status": "identified", "peer_id": g.current_peer.id}

@peer_panel.route('/usage', methods=['GET'])
def usage():
    """
    Renders the peer usage panel.
    """
    return render_template('panel.html', peer=g.current_peer, format_bytes=FormatBytes)
