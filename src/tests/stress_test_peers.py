import sys
import os
import time
import unittest
import tempfile
from unittest.mock import MagicMock, patch

# Mock flask before importing modules that use it
mock_flask = MagicMock()
sys.modules['flask'] = mock_flask
mock_flask.current_app = MagicMock()

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now we can import it
from modules.WireguardConfiguration import WireguardConfiguration

class StressTestPeers(unittest.TestCase):
    @patch('modules.DashboardConfig.DashboardConfig')
    @patch('modules.PeerJobs.PeerJobs')
    @patch('modules.PeerShareLinks.PeerShareLinks')
    @patch('modules.DashboardWebHooks.DashboardWebHooks')
    @patch('modules.WireguardCLI.WireguardCLI.run')
    def test_performance_500_peers(self, mock_wg_run, mock_webhooks, mock_sharelinks, mock_jobs, mock_config):
        # Setup mocks
        tmp_dir = tempfile.gettempdir()
        mock_config.GetConfig.side_effect = lambda s, k: (True, "sqlite") if s == "Database" and k == "type" else (True, tmp_dir)
        
        # Mock WireguardConfiguration methods that touch filesystem or DB in ways we want to avoid or control
        with patch.object(WireguardConfiguration, '_WireguardConfiguration__parseConfigurationFile', return_value=None), \
             patch.object(WireguardConfiguration, 'getStatus', return_value=True), \
             patch.object(WireguardConfiguration, 'readConfigurationInfo', return_value=None), \
             patch.object(WireguardConfiguration, 'initConfigurationInfo', return_value=None), \
             patch.object(WireguardConfiguration, 'createDatabase', return_value=None), \
             patch.object(WireguardConfiguration, '_WireguardConfiguration__initPeersList', return_value=None), \
             patch.object(WireguardConfiguration, '_WireguardConfiguration__dumpDatabase', return_value=[]), \
             patch('os.path.exists', return_value=True), \
             patch('os.mkdir', return_value=None):
            
            # Initialize WireguardConfiguration
            wgc = WireguardConfiguration(mock_config, mock_jobs, mock_sharelinks, mock_webhooks, name="test_wg0")
            wgc.Peers = []
            wgc.Protocol = "wg"
            wgc.Name = "test_wg0"
            
            # Setup engine and metadata for in-memory sqlite
            import sqlalchemy as db
            wgc.engine = db.create_engine('sqlite:///:memory:')
            wgc.metadata = db.MetaData()
            
            # Manually create the peers table
            wgc.peersTable = db.Table(
                wgc.Name, wgc.metadata,
                db.Column('id', db.String(255), primary_key=True),
                db.Column('total_receive', db.BigInteger, default=0),
                db.Column('total_sent', db.BigInteger, default=0),
                db.Column('total_data', db.BigInteger, default=0),
                db.Column('cumu_receive', db.BigInteger, default=0),
                db.Column('cumu_sent', db.BigInteger, default=0),
                db.Column('cumu_data', db.BigInteger, default=0),
                db.Column('status', db.String(255)),
                db.Column('latest_handshake', db.String(255)),
                db.Column('endpoint', db.String(255)),
                extend_existing=True
            )
            wgc.metadata.create_all(wgc.engine)

            # Populate with 500 peers
            peer_count = 500
            peers_data = []
            dump_lines = ["public_key\tpreshared_key\tendpoint\tallowed_ips\tlatest_handshake\ttransfer_rx\ttransfer_tx\tpersistent_keepalive"]
            
            now_ts = int(time.time())
            for i in range(peer_count):
                pk = f"peer_pubkey_{i:03d}="
                peers_data.append({
                    "id": pk,
                    "total_receive": 0,
                    "total_sent": 0,
                    "total_data": 0,
                    "cumu_receive": 0,
                    "cumu_sent": 0,
                    "cumu_data": 0,
                    "status": "stopped",
                    "latest_handshake": "No Handshake",
                    "endpoint": "N/A"
                })
                # Simulated wg show dump line:
                # public_key, preshared_key, endpoint, allowed_ips, latest_handshake, transfer_rx, transfer_tx, persistent_keepalive
                dump_lines.append(f"{pk}\t(none)\t1.2.3.4:1234\t10.0.0.{i}/32\t{now_ts}\t{1000 * i}\t{2000 * i}\t21")

            with wgc.engine.begin() as conn:
                conn.execute(wgc.peersTable.insert(), peers_data)

            # Mock wg show dump output
            mock_wg_run.return_value = "\n".join(dump_lines).encode('utf-8')

            # Measure performance
            start_time = time.time()
            wgc.updatePeersData()
            end_time = time.time()

            duration = end_time - start_time
            print(f"\nPerformance for {peer_count} peers: {duration:.4f} seconds")
            
            self.assertLess(duration, 10, "Update took too long (expected < 10s)")
            
            # Verify data was updated
            with wgc.engine.connect() as conn:
                res = conn.execute(wgc.peersTable.select().where(wgc.peersTable.c.id == "peer_pubkey_499=")).mappings().fetchone()
                self.assertEqual(res['total_receive'], 1000 * 499)
                self.assertEqual(res['total_sent'], 2000 * 499)
                self.assertEqual(res['status'], "running")

if __name__ == '__main__':
    unittest.main()
