#!/usr/bin/env bash
# Publish the Chinese edition to the Alibaba Cloud server in Hangzhou that
# serves runixcloud.com (decided 2026-11-27: mainland hosting with an ICP filing).
#
# Refuses to run without the filing number: until the filing is approved the
# domain must not serve a site (Alibaba blocks it, and a site that answers
# during review gets the filing rejected). The number goes into every footer,
# linked to beian.miit.gov.cn, as the filing requires.
#
# Usage: tools/deploy_cn_aliyun.sh   (the number comes from tools/i18n.py ICP_NUMBER,
#        or ICP_NUMBER=... in the environment)
#   CN_HOST   ssh destination of the server (default: runixcn, an ~/.ssh/config alias)
#
# Renders the "mainland" profile (i18n.MAINLAND_EXCLUDE left out), uploads it
# to /var/www/runixcloud.com, installs the nginx server block it generates,
# and reloads only after `nginx -t` passes.
set -euo pipefail
cd "$(dirname "$0")/.." || exit 1

ICP_NUMBER="${ICP_NUMBER:-$(python3 -c 'import sys; sys.path.insert(0, "tools"); from i18n import ICP_NUMBER; print(ICP_NUMBER)')}"
[ -n "$ICP_NUMBER" ] || { echo "no ICP filing number (tools/i18n.py ICP_NUMBER): runixcloud.com must not serve a site before the filing is approved" >&2; exit 1; }
export ICP_NUMBER
HOST="${CN_HOST:-runixcn}"
OUT="$(mktemp -d)"
trap 'rm -rf "$OUT"' EXIT

echo "==> Render the mainland edition"
python3 tools/build_cn.py --out "$OUT" --profile mainland --nginx

echo "==> Upload to $HOST"
rsync -az --delete --exclude 'nginx-runixcloud.com.conf' "$OUT/" "$HOST:/tmp/runixcloud.com.new/"
scp -q "$OUT/nginx-runixcloud.com.conf" "$HOST:/tmp/nginx-runixcloud.com.conf"

echo "==> Install, test and reload nginx"
ssh "$HOST" 'set -e
  sudo mkdir -p /var/www/runixcloud.com
  sudo rsync -a --delete /tmp/runixcloud.com.new/ /var/www/runixcloud.com/
  # keep the certificate lines certbot added to the live block
  if [ -f /etc/nginx/sites-available/runixcloud.com ] && grep -q "managed by Certbot" /etc/nginx/sites-available/runixcloud.com; then
    echo "    certbot-managed block kept; compare /tmp/nginx-runixcloud.com.conf by hand if the redirects changed"
  else
    sudo cp /tmp/nginx-runixcloud.com.conf /etc/nginx/sites-available/runixcloud.com
    sudo ln -sf /etc/nginx/sites-available/runixcloud.com /etc/nginx/sites-enabled/runixcloud.com
  fi
  sudo nginx -t
  sudo systemctl reload nginx'

echo "==> Verify"
fail=0
for path in / /bench /fs /about; do
  lang=$(curl -s --max-time 20 "https://runixcloud.com$path" | grep -o '<html lang="[^"]*"' | head -1)
  printf '    %-8s %s\n' "$path" "${lang:-no answer}"
  [ "$lang" = '<html lang="zh-CN"' ] || fail=1
done
icp=$(curl -s --max-time 20 "https://runixcloud.com/" | grep -c "beian.miit.gov.cn")
printf '    ICP number in footer: %s\n' "$icp"
[ "$icp" -ge 1 ] || fail=1
[ "$fail" -eq 0 ] && echo "==> runixcloud.com OK" || { echo "==> runixcloud.com verification FAILED"; exit 1; }
