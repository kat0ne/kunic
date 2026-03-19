#!/usr/bin/env python3

BANNER = r"""
  ██╗  ██╗ ██╗  ██╗███████╗
  ██║ ██╔╝ ██║  ██║██╔════╝
  █████╔╝  ███████║█████╗  
  ██╔═██╗  ╚════██║██╔══╝  
  ██║  ██╗      ██║███████╗
  ╚═╝  ╚═╝      ╚═╝╚══════╝
  kunic — by k4e
  parameter-aware url deduplicator
"""

import sys
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
    if len(sys.argv) < 2:
        print("Usage: python3 kunic.py <input.txt> [output.txt]", file=sys.stderr)
        sys.exit(1)

    input_file  = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    with open(input_file, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    total   = sum(1 for l in lines if l.strip() and not l.startswith("#"))
    results = dedup(lines)
    removed = total - len(results)

    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(results) + "\n")
        print(f"[✓] {total} URLs lues → {len(results)} gardées ({removed} supprimées)")
        print(f"[✓] Résultat écrit dans : {output_file}")
    else:
        for url in results:
            print(url)
        print(f"\n[✓] {total} URLs lues → {len(results)} gardées ({removed} supprimées)", file=sys.stderr)

if __name__ == "__main__":
    main()
