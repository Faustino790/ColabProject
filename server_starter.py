#!/usr/bin/env python3
# SERVER STARTER

import os
import re
import json
import subprocess
from google.colab import drive

# Step 1: Create update.sh script
def CRD():
    script_content = """#!/bin/bash
b='\033[1m'
r='\E[31m'
g='\E[32m'
c='\E[36m'
endc='\E[0m'
enda='\033[0m'

printf "\n\n$c$b    Software Updating... $endc$enda" >&2
if sudo apt-get update &> /dev/null
then
    printf "\r$g$b    Latest Software Installed.. $endc$enda\n" >&2
else
    printf "\r$r$b    Error Occurred $endc$enda\n" >&2
    exit
fi
"""
    with open('update.sh', 'w') as script:
        script.write(script_content)

    os.system("chmod +x update.sh")
    os.system("./update.sh")

CRD()

# Step 2: Mount Google Drive
try:
    drive.mount('/content/drive')
except Exception as e:
    print(f"❌ Google Drive mount failed or wasn't authorized: {e}")
    print("The server can't run without Drive access — re-run the cell and complete the sign-in prompt.")
    raise SystemExit(1)

# __Step 3: Change Directory__
os.makedirs("/content/drive/My Drive/Colab-Notebooks/minecraft-server", exist_ok=True)
os.chdir("/content/drive/My Drive/Colab-Notebooks/minecraft-server")

# Step 4: Install neofetch to show system info
os.system("sudo apt install neofetch -y &> /dev/null")
os.system("neofetch")

# Step 5: Load or create colabconfig
if os.path.isfile("colabconfig.json"):
  with open("colabconfig.json") as f:
    try:
        colabconfig = json.load(f)
    except json.JSONDecodeError:
        colabconfig = {}  # If file is broken
else:
    colabconfig = {}  # File doesn't exist yet — start fresh

# Set default keys if missing
if "server_type" not in colabconfig:
    colabconfig["server_type"] = "paper"
if "server_version" not in colabconfig:
    colabconfig["server_version"] = "1.20.11"

# Save back updated config
with open("colabconfig.json", "w") as f:
    json.dump(colabconfig, f)

# Step 6: Install Java (with proper version parsing)
server_version = colabconfig["server_version"]
try:
    version_tuple = tuple(int(p) for p in re.findall(r'\d+', server_version)[:3])
    if not version_tuple:
        raise ValueError
except ValueError:
    print(f"⚠ Couldn't parse server_version '{server_version}' — assuming 1.20.11.")
    version_tuple = (1, 20, 11)

if colabconfig["server_type"] == "forge" and version_tuple < (1, 17):
    target_java = "15"
else:
    target_java = "21"

os.system(f'sudo apt-get install openjdk-{target_java}-jre-headless -y &> /dev/null && echo "OpenJDK {target_java} installed."')

# Step 7: Java version check
java_version_output = subprocess.run(["java", "-version"], stderr=subprocess.PIPE, text=True)
print(java_version_output.stderr)

if target_java in java_version_output.stderr:
    print(f"✅ OpenJDK {target_java} is working fine.")
else:
    print(f"⚠ OpenJDK {target_java} not detected. Minecraft {server_version} may not run properly.")

#===============#7.5: Install/Verify Node.js ========================

print("\n🔧 Installing Node.js (if missing)...")

node_check = subprocess.run(["which", "node"], stdout=subprocess.PIPE, text=True)
if node_check.stdout.strip() == "":
    print("⏳ Node.js not found. Installing Node.js...")
    os.system("curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - &> /dev/null")
    os.system("sudo apt-get install -y nodejs &> /dev/null")
else:
    print("✅ Node.js already installed.")

node_version = subprocess.run(["node", "--version"], stdout=subprocess.PIPE, text=True)
npm_version = subprocess.run(["npm", "--version"], stdout=subprocess.PIPE, text=True)
print("🟢 Node.js version:", node_version.stdout.strip())
print("🟠 NPM version:", npm_version.stdout.strip())

#=====================================================================

#============================= Denger Zone ============================

jar_list = {
    'paper' : 'server.jar',
    'fabric': 'fabric-server-launch.jar',
    'generic': 'server.jar',
    'forge': 'forge.jar'
}
jar_name = jar_list.get(colabconfig["server_type"])
if jar_name is None:
    print(f"⚠ Unknown server_type '{colabconfig['server_type']}' — defaulting to server.jar.")
    jar_name = "server.jar"


if colabconfig["server_type"] == "paper":
    server_flags = "-XX:+UseG1GC -XX:+ParallelRefProcEnabled -XX:MaxGCPauseMillis=200 " \
                   "-XX:+UnlockExperimentalVMOptions -XX:+DisableExplicitGC -XX:+AlwaysPreTouch " \
                   "-XX:G1NewSizePercent=30 -XX:G1MaxNewSizePercent=40 -XX:G1HeapRegionSize=8M " \
                   "-XX:G1ReservePercent=20 -XX:G1HeapWastePercent=5 -XX:G1MixedGCCountTarget=4 " \
                   "-XX:InitiatingHeapOccupancyPercent=15 -XX:G1MixedGCLiveThresholdPercent=90 " \
                   "-XX:G1RSetUpdatingPauseTimePercent=5 -XX:SurvivorRatio=32 -XX:+PerfDisableSharedMem " \
                   "-XX:MaxTenuringThreshold=1 -Dusing.aikars.flags=https://mcflags.emc.gs " \
                   "-Daikars.new.flags=true"
else:
    server_flags = ""

#=======================================================================

# ========== #10: Dynamic RAM Allocation ==========

meminfo = subprocess.run(["grep", "MemTotal", "/proc/meminfo"], stdout=subprocess.PIPE, text=True)
mem_match = re.search(r'\d+', meminfo.stdout)
mem_kb = int(mem_match.group()) if mem_match else 8 * 1024 * 1024  # fallback: assume 8GB if detection fails
mem_gb = mem_kb // 1024 // 1024
xmx = max(1, int(mem_gb * 0.85))  # never allocate 0GB
xms = 2 if xmx > 4 else 1
xms = min(xms, xmx)  # Xms can never exceed Xmx or Java refuses to start
memory_allocation = f"-Xms{xms}G -Xmx{xmx}G"
print(f"🚀 Auto RAM Allocation: {memory_allocation}")

# ================ #11: Tunnel selection ==============
# NOTE: moved before the server launch — os.system() below blocks until the
# server process exits, so this never ran while the server was actually up.

tunnel = colabconfig.get("tunnel_service", "none").lower()

if tunnel == "playit":
    print("🌐 Using Playit for tunneling...")

elif tunnel == "ngrok":
    print("🌐 Using Ngrok for tunneling...")

else:
    print("⚠️ No tunneling active or unknown service:", tunnel)

# ================== #12: Run Server ===============

os.system(f"java {memory_allocation} {server_flags} -jar {jar_name} nogui")
