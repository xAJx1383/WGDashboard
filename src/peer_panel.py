from flask import Blueprint, request, abort, g, jsonify, send_from_directory
from modules.Utilities import IsIPInSubnet, FormatBytes
import os

peer_panel = Blueprint('peer_panel', __name__,
                       static_folder=os.path.abspath('./static/dist/WGDashboardPeerPanel'),
                       static_url_path='/static')

def get_peer_by_ip(remote_addr, wireguard_configurations):
    """
    Identifies a WireGuard peer based on its internal VPN IP address.
    Returns (peer, configuration_name) tuple.
    """
    for config_name, config in wireguard_configurations.items():
        # Only check active configurations
        if config.getStatus():
            for peer in config.Peers:
                # Peer allowed_ip can be a comma-separated list of subnets
                allowed_ips = [ip.strip() for ip in peer.allowed_ip.split(",")]
                for subnet in allowed_ips:
                    if IsIPInSubnet(remote_addr, subnet):
                        return peer, config_name
    return None, None

@peer_panel.before_request
def restrict_to_peers():
    """
    Isolation hook: verifies the requester is a known WireGuard peer.
    Allows static assets through without auth check.
    """
    # Allow static assets through
    if request.path.startswith('/static/') or request.path.startswith('/peer/static/'):
        return

    from flask import current_app
    WGD = current_app.config.get('WGD')
    if not WGD:
        abort(500, description="WireGuard configurations not initialized")
        
    peer, config_name = get_peer_by_ip(request.remote_addr, WGD)
    if not peer:
        abort(403, description="Access denied: Unknown Peer IP")
    
    g.current_peer = peer
    g.current_config_name = config_name

@peer_panel.route('/')
def index():
    """
    Serves the Vue SPA index.html
    """
    dist_dir = os.path.abspath('./static/dist/WGDashboardPeerPanel')
    return send_from_directory(dist_dir, 'index.html')

@peer_panel.route('/api/status', methods=['GET'])
def api_status():
    """
    Returns the current peer's identification info and usage data.
    """
    peer = g.current_peer
    
    total_receive = getattr(peer, 'total_receive', 0) + getattr(peer, 'cumu_receive', 0)
    total_sent = getattr(peer, 'total_sent', 0) + getattr(peer, 'cumu_sent', 0)
    total_data = total_receive + total_sent
    
    return jsonify({
        "status": True,
        "data": {
            "peer": {
                "id": peer.id,
                "name": getattr(peer, 'name', '') or 'Unnamed Peer',
                "allowed_ip": peer.allowed_ip,
                "endpoint": getattr(peer, 'endpoint', ''),
                "status": getattr(peer, 'status', 'stopped'),
                "latest_handshake": getattr(peer, 'latest_handshake', 'No Handshake'),
                "total_receive": total_receive,
                "total_sent": total_sent,
                "total_data": total_data,
                "total_receive_formatted": FormatBytes(total_receive),
                "total_sent_formatted": FormatBytes(total_sent),
                "total_data_formatted": FormatBytes(total_data),
                "restricted": getattr(peer, 'restricted', False),
            },
            "configuration": g.current_config_name
        }
    })

@peer_panel.route('/api/jobs', methods=['GET'])
def api_jobs():
    """
    Returns the current peer's active jobs in human-readable format.
    """
    from flask import current_app
    peer = g.current_peer
    config_name = g.current_config_name
    
    WGD = current_app.config.get('WGD')
    config = WGD.get(config_name) if WGD else None
    
    jobs = []
    if config and hasattr(config, 'AllPeerJobs'):
        peer_jobs = config.AllPeerJobs.searchJob(config_name, peer.id)
        for job in peer_jobs:
            # Build human-readable description
            field_labels = {
                'total_receive': 'Total Downloaded',
                'total_sent': 'Total Uploaded',
                'total_data': 'Total Data Usage',
            }
            operator_labels = {
                'lgt': 'exceeds',
                'lst': 'is below',
                'eq': 'equals',
                'neq': 'does not equal',
            }
            action_labels = {
                'restrict': 'Restrict Access',
                'delete': 'Remove Peer',
                'reset_total_data_usage': 'Reset Data & Restart',
            }
            
            field_label = field_labels.get(job.Field, job.Field)
            operator_label = operator_labels.get(job.Operator, job.Operator)
            action_label = action_labels.get(job.Action, job.Action)
            
            # Format value based on field type
            if job.Field in ['total_receive', 'total_sent', 'total_data']:
                value_display = f"{job.Value} GB"
            else:
                value_display = job.Value
            
            jobs.append({
                "id": job.JobID,
                "field": job.Field,
                "field_label": field_label,
                "operator": job.Operator,
                "operator_label": operator_label,
                "value": job.Value,
                "value_display": value_display,
                "action": job.Action,
                "action_label": action_label,
                "description": f"When {field_label} {operator_label} {value_display} → {action_label}",
                "created": str(job.CreationDate) if job.CreationDate else None,
            })
    
    return jsonify({
        "status": True,
        "data": jobs
    })

@peer_panel.route('/usage_check', methods=['GET'])
def usage_check():
    """
    Test route to verify peer identification.
    """
    return {"status": "identified", "peer_id": g.current_peer.id}
