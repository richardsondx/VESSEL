"""Render the archived diagnostic report without network requests or evaluation."""
from pathlib import Path
import json

folder = Path(__file__).resolve().parent
data = json.loads((folder / "report-data.json").read_text(encoding="utf-8"))
template = (folder / "template.html").read_text(encoding="utf-8")
embedded = json.dumps(data).replace("<", "\\u003c")
(folder / "index.html").write_text(template.replace("__DATA__", embedded), encoding="utf-8")
print(folder / "index.html")
