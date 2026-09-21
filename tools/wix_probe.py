"""Ask the Wix account what we still do not know, read only.

    python tools/wix_probe.py

Uses the OAuth token the Wix CLI wrote to ~/.wix/auth/account.json. The token is
never printed. Nothing here writes to the account or to the live site: every call
is a query. What we are after is the site id, and above all where the domain is
registered and when the subscription renews.
"""
import json
import os
import sys
import urllib.error
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
AUTH = os.path.expanduser("~/.wix/auth/account.json")

CALLS = [
    ("POST", "https://www.wixapis.com/site-list/v2/sites/query", {"query": {}}),
    ("GET", "https://www.wixapis.com/site-list/v2/sites", None),
    ("GET", "https://www.wixapis.com/premium/v1/subscriptions", None),
    ("GET", "https://www.wixapis.com/domains/v1/domains", None),
]


def token() -> str:
    with open(AUTH, encoding="utf-8") as fh:
        return json.load(fh)["accessToken"]


def call(method, url, body, tok):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": tok,
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:400]
    except Exception as e:                                    # noqa: BLE001
        return 0, str(e)[:200]


def main():
    tok = token()
    for method, url, body in CALLS:
        status, text = call(method, url, body, tok)
        name = url.split("wixapis.com")[-1]
        print(f"{status:>4}  {method:4s} {name}")
        if 200 <= status < 300:
            try:
                print("      " + json.dumps(json.loads(text), ensure_ascii=False)[:900])
            except ValueError:
                print("      " + text[:400])
        else:
            print("      " + text.replace("\n", " ")[:220])


if __name__ == "__main__":
    main()
