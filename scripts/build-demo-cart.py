#!/usr/bin/env python3
"""Build every approved built-in cartridge from site/cartridges.json."""
from cartridges import main

if __name__ == '__main__':
    raise SystemExit(main(['build']))
