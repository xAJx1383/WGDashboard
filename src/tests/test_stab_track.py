import pytest
import sqlalchemy
from sqlalchemy import Table, Column, String, MetaData, create_engine, BigInteger, Float
from modules.WireguardConfiguration import WireguardConfiguration
from modules.DashboardConfig import DashboardConfig
from unittest.mock import MagicMock
import os

def test_biginteger_schema():
    """Verify that traffic columns use BigInteger."""
    metadata = MetaData()
    engine = create_engine("sqlite:///:memory:")
    
    # Mocking necessary components for WireguardConfiguration
    mock_db_config = MagicMock(spec=DashboardConfig)
    mock_db_config.GetConfig.side_effect = lambda section, key: (True, "sqlite") if section == "Database" else (True, "test_path")
    
    # We want to check the schema defined in createDatabase
    # Since createDatabase uses self.metadata, we can check it after calling it.
    
    class MockWGConfig(WireguardConfiguration):
        def __init__(self):
            self.Name = "test_wg"
            self.metadata = MetaData()
            self.engine = engine
            self.DashboardConfig = mock_db_config
            self.createDatabase()

    wg = MockWGConfig()
    
    for table_name in [wg.Name, f"{wg.Name}_restrict_access", f"{wg.Name}_transfer", f"{wg.Name}_deleted"]:
        table = wg.metadata.tables[table_name]
        assert isinstance(table.c.total_receive.type, BigInteger)
        assert isinstance(table.c.total_sent.type, BigInteger)
        assert isinstance(table.c.total_data.type, BigInteger)
        assert isinstance(table.c.cumu_receive.type, BigInteger)
        assert isinstance(table.c.cumu_sent.type, BigInteger)
        assert isinstance(table.c.cumu_data.type, BigInteger)

def test_migration_logic():
    """Verify raw SQL migration from Float GB to BigInteger Bytes."""
    engine = create_engine("sqlite:///:memory:")
    metadata = MetaData()
    
    # Create old schema table
    test_table = Table(
        'peer', metadata,
        Column('id', String, primary_key=True),
        Column('total_receive', Float),
        Column('total_sent', Float),
        Column('cumu_receive', Float),
        Column('cumu_sent', Float)
    )
    metadata.create_all(engine)
    
    # Insert float GB data
    with engine.begin() as conn:
        conn.execute(test_table.insert().values(
            id="peer1",
            total_receive=1.5, # 1.5 GB
            total_sent=0.5,    # 0.5 GB
            cumu_receive=10.0, # 10 GB
            cumu_sent=5.0      # 5 GB
        ))
    
    # Migration SQL
    GB_TO_BYTES = 1024**3
    migration_sql = f"""
    UPDATE peer SET 
        total_receive = CAST(total_receive * {GB_TO_BYTES} AS INTEGER),
        total_sent = CAST(total_sent * {GB_TO_BYTES} AS INTEGER),
        cumu_receive = CAST(cumu_receive * {GB_TO_BYTES} AS INTEGER),
        cumu_sent = CAST(cumu_sent * {GB_TO_BYTES} AS INTEGER)
    """
    
    with engine.begin() as conn:
        conn.execute(sqlalchemy.text(migration_sql))
        
    # Verify results
    with engine.connect() as conn:
        row = conn.execute(sqlalchemy.text("SELECT * FROM peer")).mappings().fetchone()
        assert row['total_receive'] == 1.5 * GB_TO_BYTES
        assert row['total_sent'] == 0.5 * GB_TO_BYTES
        assert row['cumu_receive'] == 10.0 * GB_TO_BYTES
        assert row['cumu_sent'] == 5.0 * GB_TO_BYTES

def test_atomic_peer_management(monkeypatch):
    """Verify that peer management uses wg set and wg-quick save without restarts."""
    from modules.WireguardCLI import WireguardCLI
    from modules.Utilities import GenerateWireguardPrivateKey, GenerateWireguardPublicKey
    
    # Generate valid keys
    status, private_key = GenerateWireguardPrivateKey()
    status, real_public_key = GenerateWireguardPublicKey(private_key)
    
    commands_run = []
    def mock_run(cmd, timeout=10, input=None):
        commands_run.append(" ".join(cmd))
        if "pubkey" in cmd:
            return real_public_key.encode()
        if "set" in cmd:
            return b""
        if "save" in cmd:
            return f"wg showconf {cmd[2]}".encode()
        return b""

    monkeypatch.setattr(WireguardCLI, "run", mock_run)
    
    # Mock Configuration
    mock_config = MagicMock()
    mock_config.getStatus.return_value = True
    mock_config.Protocol = "wg"
    mock_config.Name = "test_wg"
    mock_config.engine = create_engine("sqlite:///:memory:")
    mock_config.peersTable = Table('peers', MetaData(), 
                                   Column('id', String, primary_key=True),
                                   Column('name', String),
                                   Column('private_key', String),
                                   Column('DNS', String),
                                   Column('endpoint_allowed_ip', String),
                                   Column('mtu', sqlalchemy.Integer),
                                   Column('keepalive', sqlalchemy.Integer),
                                   Column('preshared_key', String))
    mock_config.peersTable.create(mock_config.engine)
    mock_config.getPeersList.return_value = []
    
    from modules.Peer import Peer
    peer_data = {
        "id": real_public_key, "private_key": private_key, "DNS": "1.1.1.1",
        "endpoint_allowed_ip": "0.0.0.0/0", "name": "peer1",
        "total_receive": 0, "total_sent": 0, "total_data": 0,
        "endpoint": "N/A", "status": "stopped", "latest_handshake": "N/A",
        "allowed_ip": "10.0.0.2/32", "cumu_receive": 0, "cumu_sent": 0,
        "cumu_data": 0, "mtu": 1420, "keepalive": 25, "remote_endpoint": "1.2.3.4",
        "preshared_key": ""
    }
    peer = Peer(peer_data, mock_config)
    
    # Call updatePeer
    status, msg = peer.updatePeer("new_name", private_key, "", "1.1.1.1", "10.0.0.2/32", "0.0.0.0/0", 1420, 25)
    
    assert status is True, f"updatePeer failed: {msg}"
    # Verify commands
    assert any(f"wg set test_wg peer {real_public_key}" in cmd for cmd in commands_run)
    assert any("wg-quick save test_wg" in cmd for cmd in commands_run)
    assert not any("wg-quick down" in cmd for cmd in commands_run)
    assert not any("wg-quick up" in cmd for cmd in commands_run)

def test_graceful_shutdown(monkeypatch):
    """Verify that atexit handler flushes usage data for all configurations."""
    from modules.DashboardConfig import DashboardConfig
    monkeypatch.setattr(DashboardConfig, "GetConfig", lambda *args, **kwargs: (True, "/tmp"))
    
    # Mock InitWireguardConfigurationsList before importing dashboard
    import modules.WireguardConfiguration as wc
    monkeypatch.setattr(wc, "WireguardConfiguration", MagicMock)
    
    import dashboard
    monkeypatch.setattr(dashboard, "InitWireguardConfigurationsList", lambda *args, **kwargs: None)
    
    mock_config = MagicMock()
    mock_config.getStatus.return_value = True
    
    # Inject mock configuration
    monkeypatch.setattr(dashboard, "WireguardConfigurations", {"wg0": mock_config})
    
    # Call flush
    dashboard.flush_usage_on_shutdown()
    
    # Verify updatePeersData was called
    mock_config.updatePeersData.assert_called_once()
