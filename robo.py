import os
import sys
import time
import subprocess
from datetime import datetime

def run_cmd(cmd):
    print(f"[cmd] {cmd}")
    subprocess.run(cmd, shell=True)

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def banner():
    print(r"""
 ________   ___  ___   ________   ________   ___   ___   ________     
|\   ____\ |\  \|\  \ |\   __  \ |\   __  \ |\  \ |\  \ |\   __  \    
\ \  \___| \ \  \\\  \\ \  \|\  \\ \  \|\  \\ \  \\\_\  \\ \  \|\  \   
 \ \  \     \ \   __  \\ \  \\\  \\ \   _  _\\ \______  \\ \  \\\  \  
  \ \  \____ \ \  \ \  \\ \  \\\  \\ \  \\  \|\|_____|\  \\ \  \\\  \ 
   \ \_______\\ \__\ \__\\ \_______\\ \__\\ _\       \ \__\\ \_______\
    \|_______| \|__|\|__| \|_______| \|__|\|__|       \|__| \|_______|
                            by chor4o
                         version 1.0.2
    """)

if len(sys.argv) != 3 or sys.argv[1] not in ['-l', '-u']:
    print("Usage: python robo.py -l domains.txt   # for list of domains")
    print("       python robo.py -u domain.com     # for single domain")
    sys.exit(1)

banner()

if sys.argv[1] == '-l':
    with open(sys.argv[2]) as f:
        domains = [line.strip() for line in f if line.strip()]
else:
    domains = [sys.argv[2]]

time_tag = datetime.now().strftime("%Y%m%d_%H%M%S")
base_log_dir = f"logs/recon_{time_tag}"
ensure_dir(base_log_dir)

for domain in domains:
    print(f"\n[***] Starting recon on {domain}...")

    clean_domain = domain.replace("https://", "").replace("http://", "").replace("/", "")
    domain_dir = os.path.join(base_log_dir, clean_domain)
    ensure_dir(domain_dir)
    domain_log_prefix = os.path.join(domain_dir, clean_domain)

    # Chaos
    run_cmd(f"chaos -d {domain} -silent | anew {domain_log_prefix}_chaos.txt")

    # Subfinder
    run_cmd(f"subfinder -d {domain} -all -silent | anew {domain_log_prefix}_subfinder.txt")

    # Combine domains and run httpx
    run_cmd(f"cat {domain_log_prefix}_chaos.txt {domain_log_prefix}_subfinder.txt | anew {domain_log_prefix}_domains.txt")
    run_cmd(f"cat {domain_log_prefix}_domains.txt | httpx -silent | anew {domain_log_prefix}_httpx_200.txt")

    # Apenas continua se houver URLs ativas
    if not os.path.exists(f"{domain_log_prefix}_httpx_200.txt") or os.path.getsize(f"{domain_log_prefix}_httpx_200.txt") == 0:
        print(f"[!] Skipping {domain} — no active URLs found.")
        continue

    # Naabu
    run_cmd(f"cat {domain_log_prefix}_domains.txt | naabu -silent | anew {domain_log_prefix}_ports.txt")

    # Katana
    run_cmd(f"cat {domain_log_prefix}_httpx_200.txt | katana -d 5 -silent | anew {domain_log_prefix}_katana.txt")

    # Gau
    run_cmd(f"gau {domain} | anew {domain_log_prefix}_gau.txt")

    # SlicePathsURL
    run_cmd(f"cat {domain_log_prefix}_katana.txt {domain_log_prefix}_gau.txt | slicepathsurl | anew {domain_log_prefix}_sliced.txt")

    # Unir e filtrar URLs com parâmetros
    run_cmd(f"cat {domain_log_prefix}_katana.txt {domain_log_prefix}_gau.txt | anew {domain_log_prefix}_all_urls.txt")
    run_cmd(f"cat {domain_log_prefix}_all_urls.txt | grep '?' | anew {domain_log_prefix}_param_urls.txt")

    # gf xss
    run_cmd(f"cat {domain_log_prefix}_param_urls.txt | gf xss | anew {domain_log_prefix}_xss_candidates.txt")

    # qsreplace '<chorao>' + httpx
    run_cmd(f"cat {domain_log_prefix}_xss_candidates.txt | qsreplace '<chorao>' | httpx -silent -ms '<chorao>' | anew {domain_log_prefix}_possible_xss1.txt")

    # Open Redirect
    run_cmd(f"cat {domain_log_prefix}_param_urls.txt | qsreplace 'https://evil.com' | httpx -silent -ms 'Location: https://evil.com' | anew {domain_log_prefix}_openredirects.txt")

    # Dalfox (após combinar e limpar as URLs com parâmetro)
    if os.path.exists(f"{domain_log_prefix}_possible_xss1.txt") and os.path.getsize(f"{domain_log_prefix}_possible_xss1.txt") > 0:
        run_cmd(f"cat {domain_log_prefix}_possible_xss1.txt | dalfox pipe --skip-bav --mining-dom --deep-domxss --output-all --report --ignore-return --follow-redirects")
    else:
        print(f"[!] Skipping Dalfox for {domain} — no XSS candidates found.")

    # Crawling de JS/JSON/JSP
    run_cmd(f"cat {domain_log_prefix}_httpx_200.txt | katana -d 5 -silent -em js,jsp,json | anew {domain_log_prefix}_files.txt")

    # Nuclei (em cima das URLs ativas + naabu)
    run_cmd(f"cat {domain_log_prefix}_httpx_200.txt {domain_log_prefix}_ports.txt | anew {domain_log_prefix}_nuclei_targets.txt")
    if os.path.exists(f"{domain_log_prefix}_nuclei_targets.txt") and os.path.getsize(f"{domain_log_prefix}_nuclei_targets.txt") > 0:
        run_cmd(f"cat {domain_log_prefix}_nuclei_targets.txt | nuclei -severity low,medium,high,critical")
    else:
        print(f"[!] Skipping Nuclei for {domain} — no valid targets found.")

print("\n[*] Recon complete for all domains.")
