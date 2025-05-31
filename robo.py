#!/usr/bin/env python3
import subprocess
import sys
import os
import time
import argparse

banner = r"""
 ________   ___  ___   ________   ________   ___   ___   ________     
|\   ____\ |\  \|\  \ |\   __  \ |\   __  \ |\  \ |\  \ |\   __  \    
\ \  \___| \ \  \\\  \\ \  \|\  \\ \  \|\  \\ \  \\_\  \\ \  \|\  \   
 \ \  \     \ \   __  \\ \  \\\  \\ \   _  _\\ \______  \\ \  \\\  \  
  \ \  \____ \ \  \ \  \\ \  \\\  \\ \  \\  \|\|_____|\  \\ \  \\\  \ 
   \ \_______\\ \__\ \__\\ \_______\\ \__\\ _\       \ \__\\ \_______\
    \|_______| \|__|\|__| \|_______| \|__|\|__|       \|__| \|_______|

                             chor4o
                             by chor4o
"""

def run_cmd(cmd, capture_output=False):
    # Runs a shell command, returns output if requested
    try:
        if capture_output:
            result = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return result.stdout.strip()
        else:
            subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[!] Command failed: {cmd}")
        print(e)

def ensure_log_dir():
    if not os.path.exists("logs"):
        os.makedirs("logs")

def process_domain(domain):
    print(f"\n[+] Starting recon for: {domain}\n")
    domain_log_prefix = f"logs/{domain}"

    # Chaos to get URLs & subdomains
    print("[*] Running Chaos...")
    run_cmd(f"chaos -d {domain} -silent | anew {domain_log_prefix}_domains.txt")
    time.sleep(5)

    # Subfinder to get subdomains
    print("[*] Running Subfinder...")
    run_cmd(f"echo {domain} | subfinder -all -silent | anew {domain_log_prefix}_domains.txt")
    run_cmd(f"echo {domain} | subfinder -dL -silent | anew {domain_log_prefix}_domains.txt")
    time.sleep(5)

    # Gau for URLs
    print("[*] Running Gau...")
    run_cmd(f"gau {domain} | anew {domain_log_prefix}_urls.txt")
    time.sleep(5)

    # Katana crawl
    print("[*] Running Katana on URLs...")
    run_cmd(f"cat {domain_log_prefix}_urls.txt | katana -d 5 -silent | anew {domain_log_prefix}_crawled_urls.txt")
    time.sleep(5)

    # SlicePathsURL on katana results
    print("[*] Running SlicePathsURL...")
    run_cmd(f"cat {domain_log_prefix}_crawled_urls.txt | slicepathsurl | anew {domain_log_prefix}_slicepaths.txt")
    time.sleep(5)

    # Httpx to check alive domains
    print("[*] Running Httpx to check alive hosts...")
    run_cmd(f"cat {domain_log_prefix}_domains.txt | httpx -silent | anew {domain_log_prefix}_alive.txt")
    time.sleep(5)

    # Naabu port scanning
    print("[*] Running Naabu port scan...")
    run_cmd(f"cat {domain_log_prefix}_alive.txt | naabu -silent | anew {domain_log_prefix}_ports.txt")
    time.sleep(5)

    # Httpx + nuclei vulnerability scan
    print("[*] Running Nuclei vulnerability scan...")
    run_cmd(f"cat {domain_log_prefix}_ports.txt | httpx -silent | nuclei -severity low,medium,high,critical")
    time.sleep(5)

    # XSS candidates with gf and Dalfox
    print("[*] Searching for XSS candidates...")
    run_cmd(f"cat {domain_log_prefix}_crawled_urls.txt | gf xss | anew {domain_log_prefix}_xss_candidates.txt")
    time.sleep(5)
    print("[*] Running Dalfox XSS analysis...")
    run_cmd(f"cat {domain_log_prefix}_xss_candidates.txt | dalfox pipe --skip-bav --mining-dom --deep-domxss --output-all --report --ignore-return -b 'https://chor4o.xss.ht/' --follow-redirects --output {domain_log_prefix}_dalfox_report.txt")
    time.sleep(5)

    # Katana file crawling (js, jsp, json)
    print("[*] Running Katana file crawling...")
    run_cmd(f"cat {domain_log_prefix}_alive.txt | katana -d 5 -silent -em js,jsp,json | anew {domain_log_prefix}_file_crawling.txt")
    time.sleep(5)

    print(f"[+] Recon for {domain} completed. Logs saved in logs/{domain}_*.txt")

def main():
    parser = argparse.ArgumentParser(description="Chor4o Recon Robot for Bug Bounty")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-l", "--list", help="File containing list of domains, one per line")
    group.add_argument("-u", "--url", help="Single domain to process")
    args = parser.parse_args()

    print(banner)
    ensure_log_dir()

    if args.list:
        if not os.path.isfile(args.list):
            print(f"[!] List file '{args.list}' not found.")
            sys.exit(1)
        with open(args.list, "r") as f:
            domains = [line.strip() for line in f if line.strip()]
        for domain in domains:
            process_domain(domain)
    elif args.url:
        process_domain(args.url)

if __name__ == "__main__":
    main()
