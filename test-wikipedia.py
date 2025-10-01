import argparse, csv, re, sys, time
import requests

API = "https://en.wikipedia.org/w/api.php"

# one session for all calls
S = requests.Session()
S.headers.update({"User-Agent": "WikipediaBiasMinimal/1.0"})

def get_json(params, retries=2, sleep=1.2):
    base = {"format": "json", "formatversion": 2, "origin": "*", "errorformat": "plaintext"}
    for i in range(retries + 1):
        r = S.get(API, params={**base, **params}, timeout=20)
        if "application/json" not in r.headers.get("Content-Type", ""):
            if i < retries:
                time.sleep(sleep)
                continue
            raise RuntimeError(f"Non-JSON (HTTP {r.status_code})")
        data = r.json()
        if "error" in data:
            msg = data["error"].get("info", "API error")
            if i < retries and any(k in msg.lower() for k in ("ratelimit", "timeout", "throttle")):
                time.sleep(sleep)
                continue
            raise RuntimeError(msg)
        return data
    raise RuntimeError("exhausted retries")

def fetch_length_lastedit(title):
    d = get_json({
        "action": "query",
        "prop": "revisions",
        "titles": title,
        "rvprop": "timestamp|size",
        "rvslots": "main",
        "redirects": 1
    })
    page = d["query"]["pages"][0]
    if "missing" in page:
        return 0, ""
    rev = page["revisions"][0]
    return rev.get("size", 0), rev.get("timestamp", "")

def fetch_refs(title):
    d = get_json({"action": "parse", "page": title, "prop": "wikitext", "redirects": 1})
    wikitext = d.get("parse", {}).get("wikitext", "") or ""
    return len(re.findall(r"<ref\b", wikitext, flags=re.IGNORECASE))

def load_titles(args):
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    if args.titles:
        return args.titles
    return ["Google", "Criticism of Google", "Algorithmic bias", "Digital divide"]

def print_table(rows):
    print("    WikipediaBias (minimal)    ")
    print("Columns: LengthBytes | # of Refs | LastEdited (UTC)\n")
    for r in rows:
        title, length, refs, last, err = r
        print(f"{title}\n  {length:>11} | {refs:>4} | {last}\n")

def write_csv(rows, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Title", "LengthBytes", "Refs", "LastEditedUTC", "Error"])
        w.writerows(rows)

def main():
    ap = argparse.ArgumentParser(description="Tiny Wikipedia stats: length, refs, last edit.")
    ap.add_argument("titles", nargs="*", help="Article titles")
    ap.add_argument("--file", "-f", help="File with titles (one per line)")
    ap.add_argument("--csv", help="Write results to CSV file")
    args = ap.parse_args()

    titles = load_titles(args)
    rows = []
    for t in titles:
        try:
            length, last = fetch_length_lastedit(t)
            refs = fetch_refs(t)
            rows.append([t, length, refs, last, ""])
        except Exception as e:
            rows.append([t, 0, 0, "", str(e)])

    print_table(rows)
    if args.csv:
        write_csv(rows, args.csv)
        print(f"Saved CSV → {args.csv}")

if __name__ == "__main__":
    main()
