# Translations

`runixcloud.io` is the English edition and `runixcloud.com` the Chinese one.
They are one site: `tools/build_cn.py` renders the Chinese pages from the
English ones, replacing each translation unit with its entry in `zh-CN.json`.
`tools/i18n.py` lists the pages that have a Chinese edition.

## Updating both editions at once

1. Change the English page as usual (or its builder).
2. `python3 tools/build_cn.py --extract` writes `zh-CN.todo.json`: every string
   on a Chinese page that has no translation yet, grouped by page.
3. Add the translations to `zh-CN.json` (key = the English string exactly as
   it appears in the todo file, value = the Chinese).
4. `./deploy.sh` deploys both editions from the same commit. It stops if a
   Chinese page has an untranslated string; `CN_STALE_OK="<reason>"` ships
   those strings in English instead, for an urgent English-only fix.

A key that no page uses any more is harmless; `--extract` only lists what is
missing.

## Style for zh-CN

Read `DESIGN.md` section 8 for the typography. For the words:

- Keep names in English: Runix, Runix Lab, Runix Router, Runix Bench, Runix FS,
  Runix Models, Runix Data, Runix Pipeline, Runix Code, Runix Comic, AI Unix,
  Curvine, and every vendor, project, protocol and model id.
- Keep every HTML tag and attribute in a string exactly as it is (`<a href>`,
  `<b>`, `<span class>`, `<code>`, `<!--email_off-->`), translating only the
  text between them. Tags may move to fit Chinese word order.
- Keep numbers, units, code, URLs, e-mail addresses and command lines unchanged.
- Fixed terms: layer 层; Agents 智能体; Gateway 网关; Models 模型; Data 数据;
  Infrastructure 基础设施; available 已上线; early access 抢先体验;
  in development 开发中; waitlist open 开放候补名单; by engagement 按项目合作;
  set up by our team 由团队开通; deployed per customer 按客户部署;
  design partners 设计伙伴; open source 开源; New 新; Contact sales 联系销售;
  Request access 申请开通; Request early access 申请抢先体验; Docs 文档;
  Pricing 价格; Solutions 解决方案; Company 公司; Products 产品;
  gateway / relay 网关 / 中转; object storage 对象存储; bucket 存储桶;
  file system 文件系统; cache 缓存; benchmark 评测; endpoint 端点;
  provider 模型厂商; list price 官方标价; fine-tune 微调; open-weight 开放权重;
  key custody 密钥托管; per-key quota 按 Key 配额; Rebuild AI Unix 重构 AI Unix.
- Voice: literal and plain, like the English. No superlatives the English does
  not have, no marketing filler, no exclamation marks.
- Typography: full-width punctuation (，。：；？（）), a half-width space
  between Chinese and Latin letters or digits ("Runix FS 是一个文件系统"),
  no em dashes, no space around full-width punctuation.

## Where runixcloud.com is served

Decided 2026-11-27: from the Alibaba Cloud server in Hangzhou, under an ICP
filing. Until the filing is approved the domain serves nothing (Alibaba blocks
it, and a site that answers during review gets the filing rejected), so:

- `tools/deploy_cn.sh` keeps publishing the full edition to the preview,
  https://runix-cn.pages.dev (noindex), on every deploy.
- The English site carries no language link or hreflang to the domain
  (`i18n.ZH_LIVE = False`).

When the filing is approved:

1. Give the server an SSH key and an `~/.ssh/config` alias `runixcn`
   (or set `CN_HOST`).
2. Set `ICP_NUMBER` in `tools/i18n.py` to the approved number.
3. `tools/deploy_cn_aliyun.sh` renders the **mainland** profile (the pages in
   `i18n.MAINLAND_EXCLUDE`, which sell access to overseas model providers, are
   left out and their links go to the English site), puts the filing number in
   every footer linked to beian.miit.gov.cn, uploads it, installs the nginx
   server block it generates and reloads after `nginx -t`. Then issue the
   certificate (`certbot --nginx -d runixcloud.com -d www.runixcloud.com`).
4. Set `ZH_LIVE = True`, run `tools/flagship_nav.py` and
   `tools/build_cn.py --alternates`, and `./deploy.sh`: the English pages get
   the language link and hreflang, and from then on every deploy publishes all
   three (English, preview, mainland) from one commit.
