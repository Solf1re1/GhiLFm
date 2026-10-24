import urllib.request
import json
import subprocess
import os
import sys

# 1. Get auth token from git credential manager
p = subprocess.Popen(['git', 'credential', 'fill'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
out, _ = p.communicate('protocol=https\nhost=github.com\n')
creds = dict(line.split('=', 1) for line in out.strip().splitlines() if '=' in line)
token = creds.get('password')
if not token:
    raise RuntimeError('No token found')

# 2. Read release notes
with open('RELEASE_NOTES_v1.0.2.md', 'r', encoding='utf-8') as f:
    release_body = f.read()

# 3. Create Release on GitHub
payload = {
    'tag_name': 'v1.0.2',
    'target_commitish': 'main',
    'name': 'ApexClicker Pro v1.0.2 — Tab Navigation Fix & In-App Auto-Updater',
    'body': release_body,
    'draft': False,
    'prerelease': False
}

req = urllib.request.Request(
    'https://api.github.com/repos/Solf1re1/GhiLFm/releases',
    data=json.dumps(payload).encode('utf-8'),
    headers={
        'Authorization': f'token {token}',
        'User-Agent': 'ApexClicker-Release-Bot',
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json'
    },
    method='POST'
)

try:
    with urllib.request.urlopen(req) as resp:
        rel_data = json.loads(resp.read().decode())
        release_id = rel_data['id']
        upload_url_template = rel_data['upload_url']
        print(f"Release created successfully! ID: {release_id}")
        print(f"Release HTML URL: {rel_data.get('html_url')}")
except urllib.error.HTTPError as e:
    err_body = e.read().decode()
    print(f"HTTPError {e.code}: {err_body}")
    # If already exists, fetch it
    req_get = urllib.request.Request(
        'https://api.github.com/repos/Solf1re1/GhiLFm/releases/tags/v1.0.2',
        headers={
            'Authorization': f'token {token}',
            'User-Agent': 'ApexClicker-Release-Bot',
            'Accept': 'application/vnd.github.v3+json'
        }
    )
    with urllib.request.urlopen(req_get) as resp:
        rel_data = json.loads(resp.read().decode())
        release_id = rel_data['id']
        upload_url_template = rel_data['upload_url']
        print(f"Fetched existing release ID: {release_id}")

upload_url_base = upload_url_template.split('{')[0]

# 4. Upload Assets
assets_to_upload = [
    ('ApexClicker.exe', r'dist\ApexClicker.exe', 'application/vnd.microsoft.portable-executable'),
    ('ApexClicker-v1.0.2-Instant.zip', r'dist\ApexClicker-v1.0.2-Instant.zip', 'application/zip')
]

for name, filepath, content_type in assets_to_upload:
    size = os.path.getsize(filepath)
    print(f"Uploading {name} ({size / (1024*1024):.2f} MB)...")
    upload_url = f"{upload_url_base}?name={name}"
    with open(filepath, 'rb') as f:
        file_bytes = f.read()

    up_req = urllib.request.Request(
        upload_url,
        data=file_bytes,
        headers={
            'Authorization': f'token {token}',
            'User-Agent': 'ApexClicker-Release-Bot',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': content_type
        },
        method='POST'
    )
    try:
        with urllib.request.urlopen(up_req) as up_resp:
            up_data = json.loads(up_resp.read().decode())
            print(f"Uploaded {name} successfully! Asset ID: {up_data.get('id')}")
    except urllib.error.HTTPError as e:
        print(f"Error uploading {name}: {e.code} -> {e.read().decode()}")

print("DONE!")
