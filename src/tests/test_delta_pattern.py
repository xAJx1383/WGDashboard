import pytest

def delta_pattern_tracking(cur_total_receive, cur_total_sent, prev_total_receive, prev_total_sent, prev_cumu_receive, prev_cumu_sent):
    """Actual tracking logic extracted from WireguardConfiguration.py"""
    updates = {}
    total_receive = prev_total_receive
    total_sent = prev_total_sent
    
    # Delta Pattern for Sent
    if cur_total_sent < prev_total_sent:
        updates["cumu_sent"] = prev_cumu_sent + prev_total_sent
    
    # Delta Pattern for Receive
    if cur_total_receive < prev_total_receive:
        updates["cumu_receive"] = prev_cumu_receive + prev_total_receive
    
    if updates:
        updates["cumu_data"] = (updates.get("cumu_sent", prev_cumu_sent) + 
                               updates.get("cumu_receive", prev_cumu_receive))
    
    return cur_total_receive, cur_total_sent, updates

def test_integer_precision():
    """Verify that small byte increments are tracked accurately."""
    # Start with 100 GB in bytes
    start_bytes = 100 * 1024**3
    increment = 1024 # 1 KB
    
    prev_rx = start_bytes
    prev_tx = start_bytes
    prev_cumu_rx = 0
    prev_cumu_tx = 0
    
    cur_rx = start_bytes + increment
    cur_tx = start_bytes + increment
    
    new_rx, new_tx, updates = delta_pattern_tracking(cur_rx, cur_tx, prev_rx, prev_tx, prev_cumu_rx, prev_cumu_tx)
    
    assert new_rx == start_bytes + increment
    assert new_tx == start_bytes + increment
    assert updates == {}

def test_counter_reset_integer():
    """Verify counter reset logic with large integers."""
    prev_rx = 50 * 1024**3
    prev_tx = 30 * 1024**3
    prev_cumu_rx = 10 * 1024**3
    prev_cumu_tx = 5 * 1024**3
    
    # Interface restarted, counters reset to small values
    cur_rx = 1 * 1024**3
    cur_tx = 0.5 * 1024**3
    
    new_rx, new_tx, updates = delta_pattern_tracking(cur_rx, cur_tx, prev_rx, prev_tx, prev_cumu_rx, prev_cumu_tx)
    
    assert new_rx == 1 * 1024**3
    assert new_tx == 0.5 * 1024**3
    # cumulative = previous_cumulative + previous_total
    assert updates["cumu_receive"] == (10 + 50) * 1024**3
    assert updates["cumu_sent"] == (5 + 30) * 1024**3
    assert updates["cumu_data"] == (60 + 35) * 1024**3

from modules.Utilities import FormatBytes

def test_format_bytes():
    assert FormatBytes(0) == "0 B"
    assert FormatBytes(1024) == "1.0 KB"
    assert FormatBytes(1024**2) == "1.0 MB"
    assert FormatBytes(1024**3) == "1.0 GB"
    assert FormatBytes(1024**4) == "1.0 TB"
    assert FormatBytes(1536) == "1.5 KB"
