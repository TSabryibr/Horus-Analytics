"""
METASTOCK SCANNER (THE ALL-SEEER)
=================================
Automates the discovery of MetaStock data folders and symbol extraction.
Generates market metadata JSON files for use with Heimdall.

Author: LOKI for Horus Analytics
"""

import os
import json
import argparse
from colorama import Fore, Style, init
from core.adapters.MetaStockReader import  MetaStockReader

init(autoreset=True)

DEFAULT_DATA_ROOT = r"C:\MetaStock Data"

def scan_folder(folder_path):
    """Scan a single folder for MetaStock data and return symbol metadata."""
    try:
        reader = MetaStockReader(folder_path)
        symbols = reader.symbols
        
        # Prepare metadata structure
        metadata = {
            "indices": {
                "MAIN": list(symbols.keys()),
                "EGX30": list(symbols.keys()) # Generic fallback
            },
            "sectors": {s: "Unknown" for s in symbols.keys()},
            "names": {s: info['name'] for s, info in symbols.items()}
        }
        return metadata
    except Exception as e:
        print(Fore.RED + f"   [!] Failed to scan {folder_path}: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Scan MetaStock data folders.")
    parser.add_argument("--root", default=DEFAULT_DATA_ROOT, help="Root directory containing MetaStock folders.")
    args = parser.parse_args()

    if not os.path.exists(args.root):
        print(Fore.RED + f"Root directory {args.root} does not exist.")
        return

    print(Fore.CYAN + f"🔎 SCANNING DATA ROOT: {args.root}\n")
    
    discovered_markets = []

    for item in os.listdir(args.root):
        full_path = os.path.join(args.root, item)
        if os.path.isdir(full_path):
            # Check for MetaStock indices
            if os.path.exists(os.path.join(full_path, "MASTER")) or os.path.exists(os.path.join(full_path, "XMASTER")):
                print(Fore.YELLOW + f"📦 Found Market: {item}")
                metadata = scan_folder(full_path)
                
                if metadata:
                    # Create a clean filename
                    sanitized_name = item.lower().replace(" ", "_").replace("-", "_")
                    filename = f"metadata_{sanitized_name}.json"
                    
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, indent=2)
                    
                    print(Fore.GREEN + f"   ✅ Created {filename} ({len(metadata['names'])} symbols)")
                    
                    discovered_markets.append({
                        "CODE": sanitized_name.upper()[:10],
                        "NAME": item,
                        "PATH": full_path,
                        "METADATA": filename
                    })

    # Summary and Heimdall Snippet
    if discovered_markets:
        print(Fore.MAGENTA + "\n" + "="*50)
        print(Fore.WHITE + Style.BRIGHT + "HEIMDALL CONFIGURATION SNIPPET:")
        print(Fore.MAGENTA + "="*50)
        for m in discovered_markets:
            print(f"    \"{m['CODE']}\": {{")
            print(f"        \"NAME\": \"{m['NAME']}\",")
            print(f"        \"CURRENCY\": \"EGP\", # Default to EGP, update manually if needed")
            print(f"        \"DATA_SOURCE\": \"LOCAL_METASTOCK\",")
            print(f"        \"HISTORY_PATH\": r\"{m['PATH']}\",")
            print(f"        \"METADATA_FILE\": \"{m['METADATA']}\",")
            print(f"        \"INDEX\": \"MAIN\"")
            print(f"    }},")
        print(Fore.MAGENTA + "="*50)

if __name__ == "__main__":
    main()
