"""Refit strengths with current data and regenerate the app with current odds."""
import subprocess, sys, os
d = os.path.dirname(os.path.abspath(__file__))
for script in ("build_data.py", "build_app.py"):
    print(f"running {script} ...")
    subprocess.run([sys.executable, script], cwd=d, check=True)
print("app rebuilt -> wc-betting-studio.html")
