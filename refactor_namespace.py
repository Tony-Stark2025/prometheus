import os
import glob

files = glob.glob("prometheus/**/*.py", recursive=True) + glob.glob("prometheus/*.py")
for filepath in files:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    updated = (
        content
        .replace("from app.", "from prometheus.")
        .replace("import app.", "import prometheus.")
        .replace("'app.", "'prometheus.")
        .replace('"app.', '"prometheus.')
        .replace("app.main:app", "prometheus.main:app")
    )
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(updated)

print(f"Refactored {len(files)} files to prometheus.* namespace.")
