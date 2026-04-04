# 变更日志

[English CHANGELOG](./CHANGELOG.en.md)

## v1.0.2

发布日期：2026-04-04

这是 `v1.0.1` 之后的维护发布，重点是把“长期稳定可用”这部分工程化补齐。

### 本次修复

- 新增构建可复现性检查：连续两次源码构建会比较 `bootimage-0.12-hd`、`hdc-0.12.img`、`hdc-0.12.img.xz` 的摘要
- 新增 release 回读验证：发布资产上传到 GitHub Release 后，会重新下载并再次启动验证
- 新增顶层 `Makefile`，统一 `build`、`run`、`verify`、`check-images`、`repro-check`、`release-readback` 等常用入口
- 新增 `LICENSE`、`THIRD_PARTY.md`、`THIRD_PARTY.en.md`，明确仓库自有代码与第三方源码输入、生成镜像之间的许可边界
- GitHub Actions CI 现在除了 Ubuntu / macOS / Windows 三平台校验外，还会自动执行可复现性 job
- README、脚本目录说明、工作流说明和 `images/manifest.json` 已与当前发布流程对齐

## v1.0.1

发布日期：2026-04-04

这是 `v1.0.0` 之后的维护发布，重点是把仓库快照、GitHub Release 资产和仓库首页展示收口到一致状态。

### 本次修复

- 运行时镜像的构建结果现在是可复现的：固定了根文件系统时间戳和 MBR disk identifier，连续两次构建会得到相同的系统镜像快照
- GitHub Release 资产发布已经自动化，推送 `v*` tag 或手动触发发布工作流时，会从源码重建镜像、执行启动验证并上传 release 资产
- `fetch-release-images` 重新拉回的资产现在会和仓库内 `images/manifest.json` 严格一致
- GitHub 仓库首页不再错误显示 `.github` 目录说明，而是显示根目录 `README.md`

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
