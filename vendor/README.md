# `vendor/`

[English README](./README.en.md)

`vendor/` 只保存第三方源码输入，不保存第三方运行时镜像。这个目录目前主要用来存放 Linux 0.12 的上游源码归档，供 `rebuild/` 构建流程使用。

这个目录里的第三方内容不受根目录 `LICENSE` 重新授权。具体边界见仓库根目录的 [THIRD_PARTY.md](../THIRD_PARTY.md)。

## 主要内容

- `src/`
  第三方源码归档所在目录

## 当前约束

- 允许第三方源码归档进入 `vendor/src/`
- 不允许第三方运行时镜像进入仓库
- 运行镜像必须由本仓库自己的源码、补丁和清单本地生成
