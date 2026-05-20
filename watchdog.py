import logging, os, select, signal, subprocess, sys, time
from dotenv import load_dotenv; load_dotenv()
from pathlib import Path

MAX_RESTARTS = int(os.getenv("WATCHDOG_MAX_RESTARTS","0"))
RESTART_DELAY = int(os.getenv("WATCHDOG_RESTART_DELAY","30"))
HANG_TIMEOUT = int(os.getenv("WATCHDOG_HANG_TIMEOUT","7200"))
QUEUE_FILE = os.getenv("REELS_QUEUE_FILE","examples/reels_queue_30_day_3_per_day_example.json")
PUBLIC_BASE_URL = os.getenv("REELS_PUBLIC_BASE_URL","").strip()
INTERVAL_HOURS = float(os.getenv("REELS_SCHEDULER_INTERVAL_HOURS","8"))
LOG_DIR = Path(os.getenv("LOG_PATH","logs/xeanvi_social_bot.log")).parent
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s | WATCHDOG | %(levelname)s | %(message)s",
    handlers=[logging.FileHandler(str(LOG_DIR/"watchdog.log")), logging.StreamHandler(sys.stdout)])
log = logging.getLogger("watchdog")

def disk_check():
    import shutil
    t,u,f = shutil.disk_usage("/")
    pct = u/t*100
    if pct > 90: log.error("DISK CRITICAL: %.1f%% used, %dGB free — clean outputs/ NOW", pct, f//1e9)
    elif pct > 80: log.warning("DISK WARNING: %.1f%% used, %dGB free", pct, f//1e9)
    else: log.info("disk: %.1f%% used, %dGB free", pct, f//1e9)

def build_cmd():
    if not PUBLIC_BASE_URL: log.error("REELS_PUBLIC_BASE_URL not set in .env"); sys.exit(1)
    if not Path(QUEUE_FILE).exists(): log.error("Queue file not found: %s", QUEUE_FILE); sys.exit(1)
    return [sys.executable,"-m","reels.scheduler","--queue",QUEUE_FILE,
            "--public-base-url",PUBLIC_BASE_URL,"--interval-hours",str(INTERVAL_HOURS)]

def run():
    cmd = build_cmd()
    restarts = 0
    current = None
    def shutdown(sig,frame):
        log.info("signal %s received — shutting down", sig)
        if current and current.poll() is None:
            current.terminate()
            try: current.wait(timeout=10)
            except: current.kill()
        sys.exit(0)
    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)
    log.info("watchdog starting | queue=%s | url=%s | interval=%sh", QUEUE_FILE, PUBLIC_BASE_URL, INTERVAL_HOURS)
    disk_check()
    while True:
        if MAX_RESTARTS and restarts >= MAX_RESTARTS:
            log.error("max restarts reached (%d)", MAX_RESTARTS); break
        t0 = time.time()
        log.info("starting scheduler (attempt #%d)", restarts+1)
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            current = proc
        except Exception as e:
            log.error("failed to start scheduler: %s", e); time.sleep(RESTART_DELAY); restarts+=1; continue
        last_out = time.time()
        while proc.poll() is None:
            try:
                ready,_,_ = select.select([proc.stdout],[],[],5.0)
                if ready:
                    line = proc.stdout.readline()
                    if line: log.info("[sched] %s", line.rstrip()); last_out=time.time()
            except: pass
            if time.time()-last_out > HANG_TIMEOUT:
                log.error("scheduler hung (%ds silence) — killing", HANG_TIMEOUT); proc.kill(); break
        if proc.stdout:
            for line in proc.stdout:
                if line.strip(): log.info("[sched] %s", line.rstrip())
        code = proc.wait(); elapsed = time.time()-t0; restarts+=1
        log.warning("scheduler exited: code=%d uptime=%.0fs restarts=%d", code, elapsed, restarts)
        disk_check()
        delay = RESTART_DELAY*3 if elapsed<60 else RESTART_DELAY
        log.info("restarting in %ds...", delay); time.sleep(delay)

if __name__=="__main__": run()
