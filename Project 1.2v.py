import os
import re
import json
from google.colab import drive

# Step 1: Mount Google Drive
drive.mount('/content/drive')

# __Step 3: Change Directory__
os.chdir("/content/drive/My Drive/minecraft-server")
!ls

# Step 4: Install neofetch to show system info
!sudo apt install neofetch -y &> /dev/null
!neofetch

# Step 5: Load or create colabconfig
if os.path.isfile("colabconfig.json"):
  with open("colabconfig.json") as f:
    try:
        colabconfig = json.load(f)
    except json.JSONDecodeError:
        colabconfig = {}  # If file is broken

# Set default keys if missing
if "server_type" not in colabconfig:
    colabconfig["server_type"] = "generic"
if "server_version" not in colabconfig:
    colabconfig["server_version"] = "1.20.6"

# Save back updated config
with open("colabconfig.json", "w") as f:
    json.dump(colabconfig, f)

# Step 6: Install Java (with proper version parsing)
server_version = colabconfig["server_version"]
version_tuple = tuple(map(int, server_version.split(".")))

if colabconfig["server_type"] == "forge" and version_tuple < (1, 17):
    !sudo apt-get install openjdk-15-jre-headless -y &> /dev/null && echo "OpenJDK 15 installed."
else:
    !sudo apt-get install openjdk-21-jre-headless -y &> /dev/null && echo "OpenJDK 21 installed."

# Step 7: Java version check
import subprocess
java_version_output = subprocess.run(["java", "-version"], stderr=subprocess.PIPE, text=True)
print(java_version_output.stderr)

if "21" in java_version_output.stderr:
    print("✅ OpenJDK 21 is working fine.")
else:
    print("⚠ Java 21 not detected. Minecraft 1.17+ may not run properly.")

#===============#7.5: Install/Verify Node.js ========================

print("\n🔧 Installing Node.js (if missing)...")

node_check = subprocess.run(["which", "node"], stdout=subprocess.PIPE, text=True)
if node_check.stdout.strip() == "":
    print("⏳ Node.js not found. Installing Node.js...")
    !curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - &> /dev/null
    !sudo apt-get install -y nodejs &> /dev/null
else:
    print("✅ Node.js already installed.")

node_version = subprocess.run(["node", "--version"], stdout=subprocess.PIPE, text=True)
npm_version = subprocess.run(["npm", "--version"], stdout=subprocess.PIPE, text=True)
print("🟢 Node.js version:", node_version.stdout.strip())
print("🟠 NPM version:", npm_version.stdout.strip())

#=====================================================================

#============================= Denger Zone ============================

jar_list = {
    'paper': 'server.jar',
    'fabric': 'fabric-server-launch.jar',
    'generic': 'server.jar',
    'forge': 'forge.jar'
}
jar_name = jar_list[colabconfig["server_type"]]


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
mem_kb = int(re.search(r'\d+', meminfo.stdout).group())
mem_gb = mem_kb // 1024 // 1024
xmx = int(mem_gb * 0.85)
xms = 2 if xmx > 4 else 1
memory_allocation = f"-Xms{xms}G -Xmx{xmx}G"
print(f"🚀 Auto RAM Allocation: {memory_allocation}")

# ================== #12: Run Server ===============

!java {memory_allocation} {server_flags} -jar {jar_name} nogui

# ================ #11: Tunnel selection ==============

tunnel = colabconfig.get("tunnel_service", "none").lower()

if tunnel == "playit":
    print("🌐 Using Playit for tunneling...")

elif tunnel == "ngrok":
    print("🌐 Using Ngrok for tunneling...")

else:
    print("⚠️ No tunneling active or unknown service:", tunnel)
