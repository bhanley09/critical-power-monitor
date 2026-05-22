import subprocess
import time

subprocess.Popen(["python", "simulator/simulator.py"])

time.sleep(3)

subprocess.run([
    "gunicorn",
    "dashboard.app:server",
    "--bind",
    "0.0.0.0:10000"
])