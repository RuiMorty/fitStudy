# Day42 发布记录

已发布：https://fitstudy.cn/go/42/

- 用户验收版本：`revision-05`；发布授权：“OK了，部署吧”。
- 发布编号：`20260918T120927Z-day42`。
- 远端备份：`/home/zhaoqr/fitness/.fitstudy-deploy-backups/20260918T120927Z-day42`。
- 七文件清单：`release-manifest.json`；数据包：`day42-site.tar.gz`；应用脚本：`apply-release.py`。
- 线上索引与本地发布前版本相同；共用Logo相同，无需上传。安装顺序为图片、正文、短链、索引，并验证旧版和新版哈希。
- 本地入口验证：`local-browser-report.json`；公网验证：`live-files-report.json`、`live-browser-report.json`。
- 11张用户验收PNG与正文、详情图、封面哈希未变；ZIP CRC、包内图片哈希及真实短链通过。核对结果见 `final-verification.json`。
- 历史课程、两份本地进度及远端现有进度保持不变。小红书交付保留本地，未上传平台。
- 回滚仅恢复本次七个路径：备份目录保存旧文件，`previously-absent.json` 记录原本不存在的文件。不要对本次增量备份使用全站回滚脚本。

服务器连接方式见项目根目录 `DEPLOYMENT.md`。密码由钥匙串读取，不存入发布包。
