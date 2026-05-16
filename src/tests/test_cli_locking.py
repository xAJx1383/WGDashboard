import threading
import time
import pytest
import sys
import os

# Add src to sys.path to allow importing modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_cli_concurrency():
    """
    Test that WireguardCLI.run is indeed thread-safe and serializes execution.
    """
    try:
        from modules.WireguardCLI import WireguardCLI
    except ImportError:
        pytest.skip("WireguardCLI module not yet implemented")

    call_log = []
    lock = threading.Lock()

    def logged_run(command_list, timeout=10):
        # This will be called inside WireguardCLI.run (which should have its own lock)
        # But we want to simulate some work and record when it happens.
        # However, if we mock WireguardCLI.run, we are mocking the lock too unless we are careful.
        # The goal is to verify that WireguardCLI.run (the real one) uses its lock.
        pass

    # Instead of mocking the whole run, we might want to mock subprocess.check_output
    # which is what WireguardCLI.run will call.
    
    import subprocess
    
    def mocked_check_output(cmd, stderr=None, timeout=None, **kwargs):
        start_time = time.time()
        time.sleep(0.05)
        end_time = time.time()
        with lock:
            call_log.append((start_time, end_time))
        return b"mocked output"

    with threading.Lock(): # Just to make sure we can use locks
        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(subprocess, "check_output", mocked_check_output)
            
            threads = []
            for i in range(10):
                t = threading.Thread(target=WireguardCLI.run, args=(["wg", "show"],))
                threads.append(t)
                t.start()
            
            for t in threads:
                t.join()
                
    # Sort by start time
    call_log.sort(key=lambda x: x[0])
    
    # Verify no overlaps
    for i in range(len(call_log) - 1):
        # We allow a very small overlap due to timing precision if necessary, 
        # but with a real lock it should be strictly less than or equal.
        assert call_log[i][1] <= call_log[i+1][0], f"Overlap detected: {call_log[i]} and {call_log[i+1]}"
