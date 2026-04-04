# `images/`

[English README](./README.en.md)

这个目录保存受版本控制的运行镜像快照。它们不是第三方下载镜像，而是本仓库通过 `rebuild/` 流程自行构建出来并同步到这里的结果。

## 当前文件

- `bootimage-0.12-hd`
  Linux 0.12 启动镜像
- `hdc-0.12.img`
  Linux 0.12 最小系统硬盘镜像

## 使用方式

- `scripts/run.*` 直接使用这里的镜像启动
- `scripts/run-window.*` 直接使用这里的镜像并弹出可见窗口
- `scripts/build-and-run.*` 和 `scripts/build-and-run-window.*` 会先重编，再刷新这里的镜像
