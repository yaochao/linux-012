# `images/`

[English README](./README.en.md)

这个目录保存受版本控制的运行镜像快照。它们不是第三方下载镜像，而是本仓库通过 `rebuild/` 流程自行构建出来并同步到这里的结果。为了减小仓库体积，系统硬盘镜像以压缩快照形式保存。

## 当前文件

- `bootimage-0.12-hd`
  Linux 0.12 启动镜像
- `hdc-0.12.img.xz`
  Linux 0.12 最小系统硬盘镜像的压缩快照
- `manifest.json`
  仓库快照的 SHA-256、大小和发布下载地址清单

## 使用方式

- `scripts/run.*` 会直接使用这里的快照，并把系统镜像自动解包到 `out/repo-images/`
- `scripts/run-window.*` 会直接使用这里的快照，并把系统镜像自动解包到 `out/repo-images/` 后弹出可见窗口
- `scripts/build-and-run.*` 和 `scripts/build-and-run-window.*` 会先重编，再刷新这里的镜像快照
- `scripts/check-images.*` 会校验这里的快照是否与 `manifest.json` 一致
- `scripts/fetch-release-images.*` 会按 `manifest.json` 从 GitHub Release 恢复这里的快照
