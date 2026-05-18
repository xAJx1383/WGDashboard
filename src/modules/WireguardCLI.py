import subprocess
import threading

class WireguardCLI:
    _locks = {}
    _global_lock = threading.Lock()

    @staticmethod
    def run(command_list, timeout=10, input=None):
        """
        Executes a WireGuard command within an interface-specific lock to prevent race conditions
        while allowing different interfaces to run concurrently.
        """
        interface_name = None
        if len(command_list) >= 3:
            cmd_0 = str(command_list[0]).lower()
            if any(x in cmd_0 for x in ["wg", "awg"]):
                interface_name = command_list[2]

        if interface_name:
            with WireguardCLI._global_lock:
                if interface_name not in WireguardCLI._locks:
                    WireguardCLI._locks[interface_name] = threading.Lock()
                lock = WireguardCLI._locks[interface_name]
        else:
            lock = WireguardCLI._global_lock

        with lock:
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
