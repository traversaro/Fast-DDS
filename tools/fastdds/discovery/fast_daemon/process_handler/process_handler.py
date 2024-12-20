import os
import signal
import subprocess
import threading

class ProcessHandler:
    def __init__(self):
        self.processes = {}  # Dictionary to store process information
        self.command = None
        self.index = 0
        self._lock = threading.RLock()

    def __del__(self):
        # Ensure all processes are stopped when the object is deleted
        with self._lock:
            for domain in list(self.processes.keys()):
                self.stop_process(domain, 1)

    def _get_signal(self, sig: int):
        if sig == 0:
            return signal.SIGINT
        elif sig == 1:
            return signal.SIGTERM
        elif sig == 2:
            return signal.SIGKILL

    def run_process_nb(self, domain: int, command: str):
        """ Used for starting new servers. Commands 'start' and 'auto'."""
        with self._lock:
            if domain in self.processes:
                return f"Discovery server for Domain '{domain}' is already running."
            # Start a new subprocess in a non-blocking way
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)
            self.processes[domain] = process
            return f"Server for Domain ID '{domain}' started."

    def run_process_b(self, domain: int, command: str, check_server: bool):
        """ Used for modyfing running servers. Commands 'list', 'add', 'set'."""
        with self._lock:
            if check_server and domain not in self.processes:
                return f"Discovery server for Domain '{domain}' is not running."

            # Run the process in a blocking way (list, add, set)
            try:
                result = subprocess.run(command,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        text=True,
                                        check=True)
                return result.stdout
            except subprocess.CalledProcessError as e:
                return e.stdout

    def stop_process(self, domain: int, sig: int):
        with self._lock:
            process = self.processes.get(domain)
            if not process:
                return f"Discovery Server for Domain ID '{domain}' not running."

            # Send signal to terminate the process group
            os.killpg(os.getpgid(process.pid), self._get_signal(sig))
            process.wait()
            del self.processes[domain]
            return f"Discovery Server for Domain ID '{domain}' stopped."

    def list_processes(self):
        with self._lock:
            return {domain: proc.pid for domain, proc in self.processes.items()}

    def stop_all_processes(self, sig: int):
        ret = ''
        with self._lock:
            for domain in list(self.processes.keys()):
                ret += self.stop_process(domain, sig)
                ret += '\n'
        return ret
