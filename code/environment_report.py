import json, platform, sqlite3, sys
from pathlib import Path
out={
  "python": sys.version,
  "sqlite": sqlite3.sqlite_version,
  "platform": platform.platform(),
  "implementation": platform.python_implementation(),
}
dest=Path(__file__).resolve().parents[1]/"results"/"environment.json"
dest.write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
