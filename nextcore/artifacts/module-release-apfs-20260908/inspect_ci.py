"""Read exact published-head Actions status; keep every observation."""
import concurrent.futures
import datetime
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent


def inspect(short):
    p = json.loads((HERE / f"{short}-published.json").read_text())
    raw = subprocess.check_output(["gh", "api", f"repos/{p['repository']}/actions/runs?head_sha={p['head']}&per_page=10"], timeout=60)
    runs = json.loads(raw)["workflow_runs"]
    return {"module": short, "head": p["head"], "runs": [{k: r[k] for k in ["id", "head_sha", "status", "conclusion", "html_url"]} for r in runs],
        "all_success": bool(runs) and all(r["head_sha"] == p["head"] and r["status"] == "completed" and r["conclusion"] == "success" for r in runs)}


if __name__ == "__main__":
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        modules = list(pool.map(inspect, ["Core", "EFI", "Tool"]))
    now = datetime.datetime.now(datetime.timezone.utc)
    result = {"observed_utc": now.isoformat(), "modules": modules,
              "passed": all(x["all_success"] for x in modules)}
    (HERE / ("ci-" + now.strftime("%H%M%S") + ".json")).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    (HERE / "ci-latest.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
