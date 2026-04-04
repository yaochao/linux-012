# 变更日志

[English CHANGELOG](./CHANGELOG.en.md)

## v1.0.0

发布日期：2026-04-04

这是这个仓库的第一个正式发布版本。到这个版本为止，项目已经从“在当前机器上实验性跑通”收敛成“可提交、可验证、可重复启动”的状态。

### 主要能力

- 从 `vendor/src/linux-0.12.tar.gz` 和仓库内补丁、清单、最小用户态源码出发，构建 Linux 0.12 所需的启动镜像和系统镜像
- 在 QEMU 中启动进入 shell，并自动执行 `ls`
- 提供最小用户态 `/bin/sh` 和 `/bin/ls`
- shell 内建支持 `cd`、`pwd`、`echo`、`cat`、`uname`、`exit`
- 支持 macOS arm64、Ubuntu 22.04、Windows 10 作为宿主机
- 提供终端版和可见窗口版的一键启动脚本
- 提供从编译阶段开始的一键启动脚本
- 提供 `verify` 和 `verify-userland` 自动验证入口

### 工程化结果

- 仓库不依赖第三方运行时镜像
- 仓库内提交的是自编译运行快照，其中系统镜像以压缩形式保存为 `images/hdc-0.12.img.xz`
- 运行时会自动解包到 `out/repo-images/hdc-0.12.img`
- GitHub Actions 已在 `ubuntu-22.04` 上自动执行单元测试、源码构建和 QEMU 启动验证
- CI workflow 已升级到 Node 24 兼容的官方 action 版本

### 发布资产

- `images/bootimage-0.12-hd`
- `images/hdc-0.12.img.xz`

### 已知边界

- 当前目标是“最小可运行 Linux 0.12 系统”，不是完整历史发行版
- 真实宿主机验证主要已在当前 macOS 主机和 GitHub Ubuntu runner 上完成
- Windows 10 与 Ubuntu 22.04 的入口脚本和平台分支已经落地，但仍建议继续补真实主机回归
