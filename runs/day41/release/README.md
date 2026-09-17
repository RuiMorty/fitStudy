# Day41 发布记录

已发布： https://fitstudy.cn/go/41/

- 发布编号：`20260917T073444Z-day41`
- 远端备份：`/home/zhaoqr/fitness/.fitstudy-deploy-backups/20260917T073444Z-day41`
- 精确七文件清单：`release-manifest.json`；发布数据包：`day41-site.tar.gz`；增量应用脚本：`apply-release.py`。
- 本地浏览器验证：`browser-report.json`；线上验证：`live-files-report.json`、`live-browser-report.json`。
- 11张用户验收PNG与 `accepted-slide-hashes.json` 完全一致，ZIP CRC与内图哈希通过，文案含实际可访问短链。
- `day41-upload.zip` 仅为云控制台备用上传包，包含上述数据包及脚本，本次未使用。
- 回滚必须仅恢复本次七个路径：备份目录保存旧文件，`previously-absent.json` 记录原本不存在的文件。不要用全站 rollback-site.sh 处理本次增量备份。

连接方式与钥匙串条目见项目根目录 `DEPLOYMENT.md`、`.deploy-local.json`。
