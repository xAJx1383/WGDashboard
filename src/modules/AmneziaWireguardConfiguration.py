"""
AmneziaWG Configuration
"""
import random, secrets, sqlalchemy, os, subprocess, re, uuid
from flask import current_app
from .PeerJobs import PeerJobs
from .AmneziaWGPeer import AmneziaWGPeer
from .PeerShareLinks import PeerShareLinks
from .Utilities import RegexMatch
from .WireguardConfiguration import WireguardConfiguration
from .DashboardWebHooks import DashboardWebHooks
from .WireguardCLI import WireguardCLI


class AmneziaWireguardConfiguration(WireguardConfiguration):
    def __init__(self, DashboardConfig,
                 AllPeerJobs: PeerJobs,
                 AllPeerShareLinks: PeerShareLinks,
                 DashboardWebHooks: DashboardWebHooks,
                 name: str = None, data: dict = None, backup: dict = None, startup: bool = False):
        self.Jc = 0
        self.Jmin = 0
        self.Jmax = 0
        self.S1 = 0
        self.S2 = 0
        self.H1 = 1
        self.H2 = 2
        self.H3 = 3
        self.H4 = 4

        super().__init__(DashboardConfig, AllPeerJobs, AllPeerShareLinks, DashboardWebHooks, name, data, backup, startup, wg=False)

    def toJson(self):
        self.Status = self.getStatus()
        return {
            "Status": self.Status,
            "Name": self.Name,
            "PrivateKey": self.PrivateKey,
            "PublicKey": self.PublicKey,
            "Address": self.Address,
            "ListenPort": self.ListenPort,
            "PreUp": self.PreUp,
            "PreDown": self.PreDown,
            "PostUp": self.PostUp,
            "PostDown": self.PostDown,
            "SaveConfig": self.SaveConfig,
            "Info": self.configurationInfo.model_dump(),
            "DataUsage": {
                "Total": sum(list(map(lambda x: x.cumu_data + x.total_data, self.Peers))),
                "Sent": sum(list(map(lambda x: x.cumu_sent + x.total_sent, self.Peers))),
                "Receive": sum(list(map(lambda x: x.cumu_receive + x.total_receive, self.Peers)))
            },
            "ConnectedPeers": len(list(filter(lambda x: x.status == "running", self.Peers))),
            "TotalPeers": len(self.Peers),
            "Protocol": self.Protocol,
            "Table": self.Table,
            "Jc": self.Jc,
            "Jmin": self.Jmin,
            "Jmax": self.Jmax,
            "S1": self.S1,
            "S2": self.S2,
            "H1": self.H1,
            "H2": self.H2,
            "H3": self.H3,
            "H4": self.H4
        }

    def createDatabase(self, dbName = None):
        if dbName is None:
            dbName = self.Name

        # Check if we need to migrate from Float (GB) to BigInteger (Bytes)
        inspector = sqlalchemy.inspect(self.engine)
        needs_migration = False
        migration_id = f'float_to_bigint_v1_{dbName}'
        migration_applied = False

        if inspector.has_table('wgd_migrations'):
            with self.engine.connect() as conn:
                res = conn.execute(sqlalchemy.text("SELECT id FROM wgd_migrations WHERE id = :id"), {"id": migration_id}).fetchone()
                if res:
                    migration_applied = True

        if not migration_applied and inspector.has_table(dbName):
            columns = inspector.get_columns(dbName)
            for col in columns:
                if col['name'] == 'total_receive' and isinstance(col['type'], sqlalchemy.Float):
                    needs_migration = True
                    break
        
        if needs_migration:
            current_app.logger.info(f"Migrating database {dbName} from Float (GB) to BigInteger (Bytes)")
            GB_TO_BYTES = 1024**3
            tables_to_migrate = [dbName, f'{dbName}_restrict_access', f'{dbName}_transfer', f'{dbName}_deleted']
            with self.engine.begin() as conn:
                for t in tables_to_migrate:
                    if inspector.has_table(t):
                        conn.execute(sqlalchemy.text(f"""
                            UPDATE "{t}" SET 
                                total_receive = CAST(total_receive * {GB_TO_BYTES} AS INTEGER),
                                total_sent = CAST(total_sent * {GB_TO_BYTES} AS INTEGER),
                                total_data = CAST(total_data * {GB_TO_BYTES} AS INTEGER),
                                cumu_receive = CAST(cumu_receive * {GB_TO_BYTES} AS INTEGER),
                                cumu_sent = CAST(cumu_sent * {GB_TO_BYTES} AS INTEGER),
                                cumu_data = CAST(cumu_data * {GB_TO_BYTES} AS INTEGER)
                        """))

        # Normalize potentially corrupted data (Task 2)
        if not migration_applied and inspector.has_table(dbName):
            current_app.logger.info(f"Checking for corrupted data in {dbName}")
            THRESHOLD = 1024**5 # 1 PB
            GB_TO_BYTES = 1024**3
            cols_to_fix = ['total_receive', 'total_sent', 'total_data', 'cumu_receive', 'cumu_sent', 'cumu_data']
            tables_to_check = [dbName, f'{dbName}_restrict_access', f'{dbName}_transfer', f'{dbName}_deleted']
            with self.engine.begin() as conn:
                for t in tables_to_check:
                    if inspector.has_table(t):
                        rows = conn.execute(sqlalchemy.text(f'SELECT * FROM "{t}"')).mappings().fetchall()
                        for row in rows:
                            updates = {}
                            for col in cols_to_fix:
                                if col in row and row[col] is not None and row[col] > THRESHOLD:
                                    val = row[col]
                                    while val > THRESHOLD:
                                        val //= GB_TO_BYTES
                                    updates[col] = val
                            if updates:
                                if 'id' in row:
                                    where_clause = 'id = :row_id'
                                    params = {**updates, "row_id": row['id']}
                                    if t.endswith('_transfer') and 'time' in row:
                                        where_clause += ' AND time = :row_time'
                                        params['row_time'] = row['time']
                                    conn.execute(sqlalchemy.text(f'UPDATE "{t}" SET ' + ', '.join([f'{k} = :{k}' for k in updates.keys()]) + f' WHERE {where_clause}'), params)

        self.peersTable = sqlalchemy.Table(
            dbName, self.metadata,
            sqlalchemy.Column('id', sqlalchemy.String(255), nullable=False, primary_key=True),
            sqlalchemy.Column('private_key', sqlalchemy.String(255)),
            sqlalchemy.Column('DNS', sqlalchemy.Text),
            sqlalchemy.Column('advanced_security', sqlalchemy.String(255)),
            sqlalchemy.Column('endpoint_allowed_ip', sqlalchemy.Text),
            sqlalchemy.Column('name', sqlalchemy.Text),
            sqlalchemy.Column('total_receive', sqlalchemy.BigInteger),
            sqlalchemy.Column('total_sent', sqlalchemy.BigInteger),
            sqlalchemy.Column('total_data', sqlalchemy.BigInteger),
            sqlalchemy.Column('endpoint', sqlalchemy.String(255)),
            sqlalchemy.Column('status', sqlalchemy.String(255)),
            sqlalchemy.Column('latest_handshake', sqlalchemy.String(255)),
            sqlalchemy.Column('allowed_ip', sqlalchemy.String(255)),
            sqlalchemy.Column('cumu_receive', sqlalchemy.BigInteger),
            sqlalchemy.Column('cumu_sent', sqlalchemy.BigInteger),
            sqlalchemy.Column('cumu_data', sqlalchemy.BigInteger),
            sqlalchemy.Column('mtu', sqlalchemy.Integer),
            sqlalchemy.Column('keepalive', sqlalchemy.Integer),
            sqlalchemy.Column('remote_endpoint', sqlalchemy.String(255)),
            sqlalchemy.Column('preshared_key', sqlalchemy.String(255)),
            extend_existing=True
        )
        self.peersRestrictedTable = sqlalchemy.Table(
            f'{dbName}_restrict_access', self.metadata,
            sqlalchemy.Column('id', sqlalchemy.String(255), nullable=False, primary_key=True),
            sqlalchemy.Column('private_key', sqlalchemy.String(255)),
            sqlalchemy.Column('DNS', sqlalchemy.Text),
            sqlalchemy.Column('advanced_security', sqlalchemy.String(255)),
            sqlalchemy.Column('endpoint_allowed_ip', sqlalchemy.Text),
            sqlalchemy.Column('name', sqlalchemy.Text),
            sqlalchemy.Column('total_receive', sqlalchemy.BigInteger),
            sqlalchemy.Column('total_sent', sqlalchemy.BigInteger),
            sqlalchemy.Column('total_data', sqlalchemy.BigInteger),
            sqlalchemy.Column('endpoint', sqlalchemy.String(255)),
            sqlalchemy.Column('status', sqlalchemy.String(255)),
            sqlalchemy.Column('latest_handshake', sqlalchemy.String(255)),
            sqlalchemy.Column('allowed_ip', sqlalchemy.String(255)),
            sqlalchemy.Column('cumu_receive', sqlalchemy.BigInteger),
            sqlalchemy.Column('cumu_sent', sqlalchemy.BigInteger),
            sqlalchemy.Column('cumu_data', sqlalchemy.BigInteger),
            sqlalchemy.Column('mtu', sqlalchemy.Integer),
            sqlalchemy.Column('keepalive', sqlalchemy.Integer),
            sqlalchemy.Column('remote_endpoint', sqlalchemy.String(255)),
            sqlalchemy.Column('preshared_key', sqlalchemy.String(255)),
            extend_existing=True
        )
        self.peersTransferTable = sqlalchemy.Table(
            f'{dbName}_transfer', self.metadata,
            sqlalchemy.Column('id', sqlalchemy.String(255), nullable=False),
            sqlalchemy.Column('total_receive', sqlalchemy.BigInteger),
            sqlalchemy.Column('total_sent', sqlalchemy.BigInteger),
            sqlalchemy.Column('total_data', sqlalchemy.BigInteger),
            sqlalchemy.Column('cumu_receive', sqlalchemy.BigInteger),
            sqlalchemy.Column('cumu_sent', sqlalchemy.BigInteger),
            sqlalchemy.Column('cumu_data', sqlalchemy.BigInteger),
            sqlalchemy.Column('time', (sqlalchemy.DATETIME if self.DashboardConfig.GetConfig("Database", "type")[1] == 'sqlite' else sqlalchemy.TIMESTAMP),
                              server_default=sqlalchemy.func.now()),
            extend_existing=True
        )
        self.peersDeletedTable = sqlalchemy.Table(
            f'{dbName}_deleted', self.metadata,
            sqlalchemy.Column('id', sqlalchemy.String(255), nullable=False),
            sqlalchemy.Column('private_key', sqlalchemy.String(255)),
            sqlalchemy.Column('DNS', sqlalchemy.Text),
            sqlalchemy.Column('advanced_security', sqlalchemy.String(255)),
            sqlalchemy.Column('endpoint_allowed_ip', sqlalchemy.Text),
            sqlalchemy.Column('name', sqlalchemy.Text),
            sqlalchemy.Column('total_receive', sqlalchemy.BigInteger),
            sqlalchemy.Column('total_sent', sqlalchemy.BigInteger),
            sqlalchemy.Column('total_data', sqlalchemy.BigInteger),
            sqlalchemy.Column('endpoint', sqlalchemy.String(255)),
            sqlalchemy.Column('status', sqlalchemy.String(255)),
            sqlalchemy.Column('latest_handshake', sqlalchemy.String(255)),
            sqlalchemy.Column('allowed_ip', sqlalchemy.String(255)),
            sqlalchemy.Column('cumu_receive', sqlalchemy.BigInteger),
            sqlalchemy.Column('cumu_sent', sqlalchemy.BigInteger),
            sqlalchemy.Column('cumu_data', sqlalchemy.BigInteger),
            sqlalchemy.Column('mtu', sqlalchemy.Integer),
            sqlalchemy.Column('keepalive', sqlalchemy.Integer),
            sqlalchemy.Column('remote_endpoint', sqlalchemy.String(255)),
            sqlalchemy.Column('preshared_key', sqlalchemy.String(255)),
            extend_existing=True
        )

        self.infoTable = sqlalchemy.Table(
            'ConfigurationsInfo', self.metadata,
            sqlalchemy.Column('ID', sqlalchemy.String(255), primary_key=True),
            sqlalchemy.Column('Info', sqlalchemy.Text),
            extend_existing=True
        )
        
        self.peersHistoryEndpointTable = sqlalchemy.Table(
            f'{dbName}_history_endpoint', self.metadata,
            sqlalchemy.Column('id', sqlalchemy.String(255), nullable=False),
            sqlalchemy.Column('endpoint', sqlalchemy.String(255), nullable=False),
            sqlalchemy.Column('time',
                              (sqlalchemy.DATETIME if self.DashboardConfig.GetConfig("Database", "type")[1] == 'sqlite' else sqlalchemy.TIMESTAMP)),
            extend_existing=True
        )

        self.migrationsTable = sqlalchemy.Table(
            'wgd_migrations', self.metadata,
            sqlalchemy.Column('id', sqlalchemy.String(255), primary_key=True),
            sqlalchemy.Column('applied_at', sqlalchemy.TIMESTAMP, server_default=sqlalchemy.func.now()),
            extend_existing=True
        )

        self.metadata.create_all(self.engine)

        if not migration_applied:
            with self.engine.begin() as conn:
                conn.execute(self.migrationsTable.insert().values(id=migration_id))


    def getPeers(self):
        self.Peers.clear()        
        if self.configurationFileChanged():
            with open(self.configPath, 'r') as configFile:
                p = []
                pCounter = -1
                content = configFile.read().split('\n')
                try:
                    if "[Peer]" not in content:
                        current_app.logger.info(f"{self.Name} config has no [Peer] section")
                        return

                    peerStarts = content.index("[Peer]")
                    content = content[peerStarts:]
                    for i in content:
                        if not RegexMatch("#(.*)", i) and not RegexMatch(";(.*)", i):
                            if i == "[Peer]":
                                pCounter += 1
                                p.append({})
                                p[pCounter]["name"] = ""
                            else:
                                if len(i) > 0:
                                    split = re.split(r'\s*=\s*', i, 1)
                                    if len(split) == 2:
                                        p[pCounter][split[0]] = split[1]

                        if RegexMatch("#Name# = (.*)", i):
                            split = re.split(r'\s*=\s*', i, 1)
                            if len(split) == 2:
                                p[pCounter]["name"] = split[1]
                    with self.engine.begin() as conn:
                        for i in p:
                            if "PublicKey" in i.keys():
                                tempPeer = conn.execute(self.peersTable.select().where(
                                    self.peersTable.columns.id == i['PublicKey']
                                )).mappings().fetchone()
                                if tempPeer is None:
                                    tempPeer = {
                                        "id": i['PublicKey'],
                                        "advanced_security": i.get('AdvancedSecurity', 'off'),
                                        "private_key": "",
                                        "DNS": self.DashboardConfig.GetConfig("Peers", "peer_global_DNS")[1],
                                        "endpoint_allowed_ip": self.DashboardConfig.GetConfig("Peers", "peer_endpoint_allowed_ip")[
                                            1],
                                        "name": i.get("name"),
                                        "total_receive": 0,
                                        "total_sent": 0,
                                        "total_data": 0,
                                        "endpoint": "N/A",
                                        "status": "stopped",
                                        "latest_handshake": "N/A",
                                        "allowed_ip": i.get("AllowedIPs", "N/A"),
                                        "cumu_receive": 0,
                                        "cumu_sent": 0,
                                        "cumu_data": 0,
                                        "mtu": self.DashboardConfig.GetConfig("Peers", "peer_mtu")[1],
                                        "keepalive": self.DashboardConfig.GetConfig("Peers", "peer_keep_alive")[1],
                                        "remote_endpoint": self.DashboardConfig.GetConfig("Peers", "remote_endpoint")[1],
                                        "preshared_key": i["PresharedKey"] if "PresharedKey" in i.keys() else ""
                                    }
                                    conn.execute(
                                        self.peersTable.insert().values(tempPeer)
                                    )
                                else:
                                    conn.execute(
                                        self.peersTable.update().values({
                                            "allowed_ip": i.get("AllowedIPs", "N/A")
                                        }).where(
                                            self.peersTable.columns.id == i['PublicKey']
                                        )
                                    )
                                self.Peers.append(AmneziaWGPeer(tempPeer, self))
                except Exception as e:
                    current_app.logger.error(f"{self.Name} getPeers() Error", e)
        else:
            with self.engine.connect() as conn:
                existingPeers = conn.execute(self.peersTable.select()).mappings().fetchall()
                for i in existingPeers:
                    self.Peers.append(AmneziaWGPeer(i, self))

    def addPeers(self, peers: list) -> tuple[bool, list, str]:
        result = {
            "message": None,
            "peers": []
        }
        try:
            with self.engine.begin() as conn:
                for i in peers:
                    newPeer = {
                        "id": i['id'],
                        "private_key": i['private_key'],
                        "DNS": i['DNS'],
                        "endpoint_allowed_ip": i['endpoint_allowed_ip'],
                        "name": i['name'],
                        "total_receive": 0,
                        "total_sent": 0,
                        "total_data": 0,
                        "endpoint": "N/A",
                        "status": "stopped",
                        "latest_handshake": "N/A",
                        "allowed_ip": i.get("allowed_ip", "N/A"),
                        "cumu_receive": 0,
                        "cumu_sent": 0,
                        "cumu_data": 0,
                        "mtu": i['mtu'],
                        "keepalive": i['keepalive'],
                        "remote_endpoint": self.DashboardConfig.GetConfig("Peers", "remote_endpoint")[1],
                        "preshared_key": i["preshared_key"],
                        "advanced_security": i['advanced_security']
                    }
                    conn.execute(
                        self.peersTable.insert().values(newPeer)
                    )
            for p in peers:
                presharedKeyExist = len(p['preshared_key']) > 0
                temp_psk_path = None
                if presharedKeyExist:
                    temp_psk_path = f".psk_{secrets.token_hex(16)}"
                    with open(temp_psk_path, "w") as f:
                        f.write(p['preshared_key'])

                try:
                    cmd = [self.Protocol, "set", self.Name, "peer", p['id'], "allowed-ips", p['allowed_ip'].replace(' ', '')]
                    cmd.extend(["preshared-key", temp_psk_path if temp_psk_path else "/dev/null"])
                    WireguardCLI.run(cmd, timeout=10)
                finally:
                    if temp_psk_path and os.path.exists(temp_psk_path):
                        os.remove(temp_psk_path)
            WireguardCLI.run([f"{self.Protocol}-quick", "save", self.Name], timeout=10)
            self.getPeers()
            for p in peers:
                p = self.searchPeer(p['id'])
                if p[0]:
                    result['peers'].append(p[1])
            self.DashboardWebHooks.RunWebHook("peer_created", {
                "configuration": self.Name,
                "peers": list(map(lambda k : k['id'], peers))
            })
        except Exception as e:
            current_app.logger.error("Add peers error", e)
            return False, [], str(e)
        return True, result['peers'], ""

    def getRestrictedPeers(self):
        self.RestrictedPeers = []
        with self.engine.connect() as conn:
            restricted = conn.execute(self.peersRestrictedTable.select()).mappings().fetchall()
            for i in restricted:
                self.RestrictedPeers.append(AmneziaWGPeer(i, self))