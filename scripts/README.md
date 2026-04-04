# `scripts/`

[English README](./README.en.md)

这个目录保存面向宿主机用户的一键入口脚本。不同平台各有一组脚本，但它们最终都委托给 `rebuild/driver.py`。

## 脚本分类

- `bootstrap-host.*`
  检查 Python、QEMU、Docker 等宿主依赖
- `run.*`
  直接使用仓库镜像快照启动，并自动解包系统镜像
- `run-window.*`
  直接使用仓库镜像快照、自动解包系统镜像，并弹出可见 QEMU 窗口
- `build-and-run.*`
  先编译再启动
- `build-and-run-window.*`
  先编译再启动，并弹出可见 QEMU 窗口
- `check-images.*`
  校验仓库镜像快照和清单
- `fetch-release-images.*`
  从 GitHub Release 恢复仓库镜像快照
- `verify.*`
  自动启动并验证 `ls`
- `verify-userland.*`
  自动验证最小 shell 内建命令
