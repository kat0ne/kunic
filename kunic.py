#!/usr/bin/env python3

BANNER = r"""
  ██╗  ██╗██╗   ██╗███╗   ██╗██╗ ██████╗
  ██║ ██╔╝██║   ██║████╗  ██║██║██╔════╝
  █████╔╝ ██║   ██║██╔██╗ ██║██║██║
  ██╔═██╗ ██║   ██║██║╚██╗██║██║██║
  ██║  ██╗╚██████╔╝██║ ╚████║██║╚██████╗
  ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝ ╚═════╝
  by k4e — parameter-aware url deduplicator
"""

import sys
import argparse
from urllib.parse import urlparse, parse_qs

def normalize_key(url: str) -> tuple:
    """
    Retourne une clé de normalisation : (scheme+host+path, frozenset des noms de params)
    Les valeurs sont ignorées → deux URLs avec mêmes clés mais valeurs différentes = même groupe
    """
    try:
        parsed = urlparse(url.strip())
        # Base = scheme://host/path (sans query ni fragment)
        base = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")
        # Clés de paramètres uniquement (pas les valeurs)
        param_keys = frozenset(parse_qs(parsed.query).keys())
        return (base, param_keys)
    except Exception:
        return (url.strip(), frozenset())

def dedup(lines: list[str]) -> list[str]:
    seen = {}       # clé → première URL gardée
    no_param = {}   # URLs sans paramètres → exact match

    for raw in lines:
        url = raw.strip()
        if not url or url.startswith("#"):
            continue

        parsed = urlparse(url)

        # Pas de paramètres → dédup exact
        if not parsed.query:
            if url not in no_param:
                no_param[url] = url
            continue

        key = normalize_key(url)
        if key not in seen:
            seen[key] = url   # garde la première

    return list(no_param.values()) + list(seen.values())

def main():
    print(BANNER, file=sys.stderr)

    parser = argparse.ArgumentParser(
        prog="kunic",
        description="Parameter-aware URL deduplicator for bug bounty hunters.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""examples:
  python3 kunic.py allurls.txt                        # stdout
  python3 kunic.py allurls.txt deduped.txt            # file output
  cat allurls.txt | gf xss | python3 kunic.py /dev/stdin
  cat allurls.txt | gf sqli | python3 kunic.py /dev/stdin sqli.txt
        """
    )
    parser.add_argument(
        "input",
        help="Input file containing URLs (use /dev/stdin for pipe)"
    )
    parser.add_argument(
        "output",
        nargs="?",
        default=None,
        help="Output file (optional — defaults to stdout)"
    )

    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    total   = sum(1 for l in lines if l.strip() and not l.startswith("#"))
    results = dedup(lines)
    removed = total - len(results)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write("\n".join(results) + "\n")
        print(f"[✓] {total} URLs read → {len(results)} kept ({removed} removed)", file=sys.stderr)
        print(f"[✓] Output written to : {args.output}", file=sys.stderr)
    else:
        for url in results:
            print(url)
        print(f"\n[✓] {total} URLs read → {len(results)} kept ({removed} removed)", file=sys.stderr)

if __name__ == "__main__":
    main()
