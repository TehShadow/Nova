import psutil
import subprocess
import time

class SystemStats:
    def get_cpu_usage(self):
        return f"CPU usage is at {psutil.cpu_percent()}%."

    def get_memory_usage(self):
        mem = psutil.virtual_memory()
        used = mem.used // (1024 ** 2)
        total = mem.total // (1024 ** 2)
        return f"Memory usage: {mem.percent}% ({used}MB used of {total}MB)."

    def get_disk_usage(self):
        disk = psutil.disk_usage('/')
        return f"Disk usage: {disk.percent}% used on root partition."

    def get_uptime(self):
        uptime = time.time() - psutil.boot_time()
        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)
        return f"System uptime: {hours} hours and {minutes} minutes."

    def get_cpu_temp(self):
        try:
            output = subprocess.check_output(["sensors"]).decode()
            lines = output.splitlines()
            for line in lines:
                if "Package id 0" in line or "Tdie" in line:
                    temp = line.split(":")[1].strip().split(" ")[0]
                    return f"CPU temperature is {temp}."
            return "Could not find CPU temperature."
        except Exception as e:
            return f"Error getting CPU temperature: {e}"

    def get_gpu_temp(self):
        try:
            output = subprocess.check_output(["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader,nounits"]).decode().strip()
            return f"GPU temperature is {output}°C."
        except FileNotFoundError:
            return "nvidia-smi not found. Are NVIDIA drivers installed?"
        except Exception as e:
            return f"Error getting GPU temperature: {e}"

    def get_gpu_usage(self):
        try:
            output = subprocess.check_output(["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"]).decode().strip()
            return f"GPU usage is at {output}%."
        except FileNotFoundError:
            return "nvidia-smi not found. Are NVIDIA drivers installed?"
        except Exception as e:
            return f"Error getting GPU usage: {e}"
