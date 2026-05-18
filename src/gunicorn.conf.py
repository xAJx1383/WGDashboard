import dashboard
from datetime import datetime
global sqldb, cursor, DashboardConfig, WireguardConfigurations, AllPeerJobs, JobLogger, Dash
app_host, app_port = dashboard.gunicornConfig()
date = datetime.today().strftime('%Y_%m_%d_%H_%M_%S')

def post_worker_init(worker):
    dashboard.startThreads()
    dashboard.DashboardPlugins.startThreads()

worker_class = 'gthread'
workers = 1
threads = 8
bind = f"{app_host}:{app_port}"
daemon = True
pidfile = './gunicorn.pid'
wsgi_app = "dashboard:app"
accesslog = f"./log/access_{date}.log"
loglevel = "info"
capture_output = True
errorlog = f"./log/error_{date}.log"
pythonpath = "., ./modules"

print(f"[Gunicorn] WGDashboard w/ Gunicorn will be running on {bind}", flush=True)
print(f"[Gunicorn] Access log file is at {accesslog}", flush=True)
print(f"[Gunicorn] Error log file is at {errorlog}", flush=True)

# Also print Peer Panel status
try:
    from modules.DashboardConfig import DashboardConfig as DC
    dc = DC()
    _, peer_panel_enable = dc.GetConfig("PeerPanel", "peer_panel_enable")
    _, peer_panel_port = dc.GetConfig("PeerPanel", "peer_panel_port")
    _, app_port_cfg = dc.GetConfig("Server", "app_port")
    if peer_panel_enable:
        if str(peer_panel_port) == str(app_port_cfg):
            print(f"[Gunicorn] Peer Panel is enabled on the same port as dashboard ({app_port_cfg}) at /peer/", flush=True)
        else:
            print(f"[Gunicorn] Peer Panel is enabled and running on port {peer_panel_port}", flush=True)
    else:
        print("[Gunicorn] Peer Panel is disabled", flush=True)
except Exception as e:
    print(f"[Gunicorn] Could not determine Peer Panel status: {e}", flush=True)
