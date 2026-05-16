import pytest

def calculate_updates(cur_total_receive, cur_total_sent, prev_total_receive, prev_total_sent, prev_cumu_receive, prev_cumu_sent):
    updates = {}
    total_receive = prev_total_receive
    total_sent = prev_total_sent
    
    if cur_total_sent < prev_total_sent:
        updates["cumu_sent"] = prev_cumu_sent + prev_total_sent
        total_sent = cur_total_sent
    else:
        total_sent = cur_total_sent

    if cur_total_receive < prev_total_receive:
        updates["cumu_receive"] = prev_cumu_receive + prev_total_receive
        total_receive = cur_total_receive
    else:
        total_receive = cur_total_receive
        
    if updates:
        updates["cumu_data"] = (updates.get("cumu_sent", prev_cumu_sent) + 
                               updates.get("cumu_receive", prev_cumu_receive))
    
    return total_receive, total_sent, updates

def test_no_reset():
    prev_total_rx = 10.0
    prev_total_tx = 20.0
    prev_cumu_rx = 5.0
    prev_cumu_tx = 8.0
    
    cur_total_rx = 12.0
    cur_total_tx = 25.0
    
    new_rx, new_tx, updates = calculate_updates(cur_total_rx, cur_total_tx, prev_total_rx, prev_total_tx, prev_cumu_rx, prev_cumu_tx)
    
    assert new_rx == 12.0
    assert new_tx == 25.0
    assert updates == {}

def test_rx_reset():
    prev_total_rx = 10.0
    prev_total_tx = 20.0
    prev_cumu_rx = 5.0
    prev_cumu_tx = 8.0
    
    cur_total_rx = 2.0
    cur_total_tx = 25.0
    
    new_rx, new_tx, updates = calculate_updates(cur_total_rx, cur_total_tx, prev_total_rx, prev_total_tx, prev_cumu_rx, prev_cumu_tx)
    
    assert new_rx == 2.0
    assert new_tx == 25.0
    assert updates["cumu_receive"] == 15.0
    assert "cumu_sent" not in updates
    assert updates["cumu_data"] == 15.0 + 8.0

def test_both_reset():
    prev_total_rx = 10.0
    prev_total_tx = 20.0
    prev_cumu_rx = 5.0
    prev_cumu_tx = 8.0
    
    cur_total_rx = 2.0
    cur_total_tx = 3.0
    
    new_rx, new_tx, updates = calculate_updates(cur_total_rx, cur_total_tx, prev_total_rx, prev_total_tx, prev_cumu_rx, prev_cumu_tx)
    
    assert new_rx == 2.0
    assert new_tx == 3.0
    assert updates["cumu_receive"] == 15.0
    assert updates["cumu_sent"] == 28.0
    assert updates["cumu_data"] == 15.0 + 28.0
