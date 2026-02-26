import json
import subprocess
import time

with open('TopologiaMalha12/topologia.json') as f:
    routers = json.load(f)

processes = []
print("A iniciar a malha de 12 roteadores...")

for r in routers:
    cmd = f"python roteador.py -p 5000 -f TopologiaMalha12/{r['config_file']} --network {r['network']}"
    p = subprocess.Popen(cmd.split())
    processes.append(p)
    time.sleep(0.5)

print("Todos os roteadores iniciados. Prime Ctrl+C para encerrar.")

try:
    for p in processes:
        p.wait()
except KeyboardInterrupt:
    print("\nA encerrar a rede...")
    for p in processes:
        p.terminate()
