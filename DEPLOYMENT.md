# FitStudy 服务器发布

站点为 https://fitstudy.cn，服务器 `150.158.127.73:22`，账号 `zhaoqr`，目录 `/home/zhaoqr/fitness/site`。本机配置保存在已忽略的 `.deploy-local.json`。

用户于 2026-09-17 提供密码并要求跨会话保留，已保存至这台 Mac 的钥匙串：service 为 `fitstudy-ssh-150.158.127.73`，account 为 `zhaoqr`。项目不存密码。旧记录中的 `ubuntu` 和 `/Users/zhaoqr/.ssh/id_rsa` 不适用于当前连接。

用包装脚本连接，密码由 SSH 的 askpass 管道读取，不在终端打印：

```bash
python3 scripts/fitstudy-ssh.py ssh 'id; test -d /home/zhaoqr/fitness/site'
python3 scripts/fitstudy-ssh.py scp runs/day41/release/day41-site.tar.gz fitstudy:/tmp/day41-site.tar.gz
```

包装脚本要求服务器密钥已在本机 `known_hosts` 中；不自动接受未知或变更的主机密钥。不要直接执行 askpass 脚本或在终端显示钥匙串密码。

## Day47 已发布并通过公网验证

2026-09-27 用户明确授权“部署吧”，七文件增量安装完成，发布编号 `20260927T094205Z-day47`，备份位于 `/home/zhaoqr/fitness/.fitstudy-deploy-backups/20260927T094205Z-day47`。2026-09-28 已完成此前被审批系统错误阻断的公网验证：七个文件 HTTP 200 且 SHA-256 与发布包一致；短链 https://fitstudy.cn/go/47/ 正确跳转，390px/1440px 目录封面与课程弹窗、正文折叠、翻转卡、练习题和图片放大均通过。

当前记录为 `runs/day47/release/status.json`、`live-files-report.json`、`live-browser-report.json` 与 `final-verification.json`。验证阻塞记录已解决；本地 caption、lesson JSON 与 ZIP 已同步真实短链，并保留 SAQ 中文解释。此次收尾没有重新部署或生图。

`runs/day47/release/server-before` 是本次发布的真实旧版基线。项目根目录 `app.js`、`library/index.html` 存在历史差异，本次没有覆盖这些本地文件。原8张卡片及两份正式进度保持不变。

## Day42 历史状态

用户已验收 revision-05，并明确要求“OK了，部署吧”。2026-09-18 已完成七文件增量发布，短链为 https://fitstudy.cn/go/42/ 。课程目录最新项为 Day42；公网文件哈希、短链跳转、390px/1440px 目录封面与课程弹窗、正文图片和交互均已验证。当前状态以 `runs/day42/release/status.json` 与 `runs/daily-preview/review.json` 为准。

- 发布编号：`20260918T120927Z-day42`；增量标记：`site/.deploy-day42-current`。
- 备份目录：`/home/zhaoqr/fitness/.fitstudy-deploy-backups/20260918T120927Z-day42`，位于网站根目录外。
- 发布清单及脚本：`runs/day42/release/release-manifest.json`、`apply-release.py`；数据包为同目录 `day42-site.tar.gz`。
- 验证报告：`runs/day42/release/live-files-report.json`、`live-browser-report.json`、`final-verification.json`。
- 已验收正文、封面、详情图和11张小红书PNG原样保留；本地小红书文案和ZIP已加入真实短链。历史课程和两份本地进度未改，未向小红书平台上传。
- 回滚只处理本次七个路径，依据该备份目录的旧文件和 `previously-absent.json`；不要使用全站回滚脚本。

## Day41 历史发布

用户已验收 revision-02，并明确授权生成短链及部署服务器。短链为 `https://fitstudy.cn/go/41/`；2026-09-17 已上线，七个公网文件哈希、短链跳转、移动/桌面课程目录和正文交互已通过验证；以 `runs/day41/release/status.json` 为准。发布前再次读取该文件和 `runs/daily-preview/review.json`。

发布范围包括本课 HTML、详情 PNG、封面 PNG/WebP、短链、`app.js` 和 `library/index.html`。共用 logo 已与线上比对一致。保留历史内容、预览文件及进度；小红书文案和 ZIP 已加入短链，但不上传小红书平台。

发布应先校验远端旧版索引哈希并备份，再先安装图片、正文、短链，最后更新索引。不要直接运行全站替换脚本发布本次七个文件；它会打包当前目录下其他草稿。网络可达后，使用 release 目录中的清单和发布说明继续。

2026-09-17 排查：SSH 和独立 TCP 连接均在端口 22 超时，尚未进入密码认证；HTTPS 443 正常，Day41 短链返回 404。本机 NyaTerm 到同地址也曾显示 `SYN_SENT`。系统代理关闭、无 SSH ProxyCommand，路由为 en0。尚未确定是网络链路、服务器防火墙还是其他原因；不应归因于密码错误，也不应因此重新索要密码。

## 本次发布结果与网络恢复

- 发布编号：`20260917T073444Z-day41`。增量标记为服务器 `site/.deploy-day41-current`，未覆盖全站 `.deploy-current`。
- 备份：`/home/zhaoqr/fitness/.fitstudy-deploy-backups/20260917T073444Z-day41`，位于网站根目录外，目录权限 700、所有者 zhaoqr。旧的 `site/.deploy-backups` 属于 root，本次不改变它的权限。
- 实际执行：上传 `day41-site.tar.gz` 后，通过 SSH 把 `runs/day41/release/apply-release.py` 送入 `python3 - SITE_DIR ARCHIVE` 执行。脚本逐文件验证旧版与新版哈希，先安装图片、课程、短链，最后安装索引；写入失败自动恢复本次文件。
- 验证报告：`runs/day41/release/live-files-report.json` 与 `live-browser-report.json`。
- 用户切换网络后，SSH 密码认证成功。本机网关由 `172.22.164.1` 变为 `172.22.134.1`，系统代理均未启用；恢复与网络路径变化一致，尚未确认具体丢包设备。服务器 sshd 正常，云防火墙允许 TCP 22，UFW 未启用。腾讯云网页终端使用 TAT 免密连接，不经过公网 SSH。
- 腾讯云备用控制台：轻量服务器 `lhins-2v880f2i`，上海 `ap-shanghai`；OrcaTerm 的 TAT 可使用现有 zhaoqr 账号登录。本次实际发布使用恢复后的 SSH，没有通过网页上传。
