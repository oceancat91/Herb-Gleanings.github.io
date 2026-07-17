import sys, subprocess, time, urllib.request, re
from pathlib import Path

backend = Path(r"d:\HuaweiMoveData\Users\32002\Desktop\可视化期末\backend")

# kill old
out = subprocess.run(["netstat", "-ano"], capture_output=True, text=True).stdout
for line in out.split("\n"):
    if ":8000" not in line or "LISTENING" not in line:
        continue
    m = re.search(r"LISTENING\s+(\d+)", line)
    if m:
        subprocess.run(["taskkill", "/pid", m.group(1), "/f"], capture_output=True)
        print("killed", m.group(1))

time.sleep(1)

# start
p = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
    cwd=str(backend),
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

# wait
t0 = time.time()
ok = False
while time.time() - t0 < 15:
    try:
        urllib.request.urlopen("http://127.0.0.1:8000/api/stats", timeout=1)
        ok = True
        break
    except:
        time.sleep(0.5)

if ok:
    print("OK", round(time.time() - t0, 1), "s")
else:
    print("FAIL")
p.kill()
