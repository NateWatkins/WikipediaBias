import requests
import re

API = "https://en.wikipedia.org/w/api.php"

PAGES = [
    "Google",
    "Criticism of Google",
    "Algorithmic bias",
    "Digital divide",
]

def get_json(params):
    params.setdefault("format", "json")
    params.setdefault("formatversion", 2)
    return requests.get(API, params=params, timeout=20).json()

def get_info(title):
    data = get_json({ "action": "query", "prop": "info", "titles": title, "inprop": "url", "redirects": 1})
    page = data["query"]["pages"][0]
    return page.get("length", 0), page.get("touched", "")

def count_refs(title):

    data = get_json({ "action": "parse", "page": title, "prop": "wikitext", "redirects": 1})
    wikitext = data.get("parse", {}).get("wikitext", "") or ""
    return len(re.findall(r"<ref\b", wikitext, flags=re.IGNORECASE))

def main():
    print("    WikipediaBias (minimal)    ")
    print("Columns: LengthBytes | Refs | LastEdited (UTC)\n")

    for title in PAGES:
      length, last = get_info(title)
      refs = count_refs(title)
      print(f"{title}\n  {length:>11} | {refs:>4} | {last}\n")

if __name__ == "__main__":
    main()
