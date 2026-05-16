import pytest
import sqlalchemy
from sqlalchemy import Table, Column, String, Float, MetaData, create_engine, BigInteger
from src.modules.WireguardConfiguration import WireguardConfiguration
from src.modules.DashboardConfig import DashboardConfig
from unittest.mock import MagicMock

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
