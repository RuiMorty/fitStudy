# FitStudy 项目

- 发布前读取 `DEPLOYMENT.md` 和 `runs/daily-preview/review.json`，确认当前产物、验收及发布状态。
- 本机服务器连接资料在 `.deploy-local.json`；密码保存在 macOS 钥匙串，条目名称见配置。不要把密码打印、写入文件、日志、记忆或提交。
- `scripts/fitstudy-ssh.py` 从本机配置连接服务器，通过钥匙串完成密码认证。
- 每日课程沿用 `templates/study/v1/README.md` 与既有共用渲染器；图片规范见 `templates/study/v1/image-style.md`。不要因切换会话重新生成已验收内容。
