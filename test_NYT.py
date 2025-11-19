# nyt_bias_scores.py
import requests, os, sys
from textblob import TextBlob

S = requests.Session()
API = "https://api.nytimes.com/svc/search/v2/articlesearch.json"
subj = lambda t: float(TextBlob(t).sentiment.subjectivity) if t else 0.0


def load_names(path):
    return [x.strip() for x in open(path, encoding="utf-8") if x.strip()]


def get_score(q, key):
    r = S.get(API, params={"q": q, "page": 0, "api-key": key}, timeout=12).json()
    docs = r.get("response", {}).get("docs") or []
    if not docs:
        return q, None

    d = docs[0]
    h = (d.get("headline") or {}).get("main", "") or ""
    a = d.get("abstract") or ""
    l = d.get("lead_paragraph") or ""
    text = f"{h} {a} {l}".strip()
    return q, subj(text)


def main():
    if len(sys.argv) < 2:
        print("usage: python nyt_bias_scores.py config.txt")
        sys.exit(1)

    cfg = sys.argv[1]
    key = os.getenv("NYT_API_KEY")
    if not key:
        print("ERROR: set NYT_API_KEY env var")
        sys.exit(1)

    for q in load_names(cfg):
        name, score = get_score(q, key)
        if score is None:
            print(f"{name}: ERROR (no article)")
        else:
            print(f"{name}: {score:.3f}")


if __name__ == "__main__":
    main()
