import subprocess
import threading

class WireguardCLI:
    _lock = threading.Lock()

    @staticmethod
    def run(command_list, timeout=10, input=None):
        """
        Executes a WireGuard command within a global lock to prevent race conditions.
        """
        with WireguardCLI._lock:
            try:
                # We use check_output to match the behavior of the existing code.
                # It raises CalledProcessError on non-zero exit codes.
                return subprocess.check_output(command_list, stderr=subprocess.STDOUT, timeout=timeout, input=input)
            except subprocess.CalledProcessError as e:
                # Re-raise to let callers handle it if they need to, 
                # but it matches the current behavior where they catch it.
                raise e
            except subprocess.TimeoutExpired as e:
                raise e
