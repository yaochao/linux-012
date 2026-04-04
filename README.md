# Linux 0.12 on QEMU

[English README](./README.en.md)
[变更日志](./CHANGELOG.md)

这个仓库的目标很直接：在现代宿主机上，从源码和仓库内清单出发，构建出 Linux 0.12 运行所需的两张 QEMU 镜像，启动进入 shell，并成功执行 `ls`。

仓库当前不再保存第三方运行时镜像。仓库里提交的是本项目自己编译出来的镜像快照：

- `images/bootimage-0.12-hd`
- `images/hdc-0.12.img.xz`
- `images/manifest.json`

同一套源码构建链还会在本地生成工作镜像：

- `rebuild/out/images/bootimage-0.12-hd`
- `rebuild/out/images/hdc-0.12.img`

## 项目结果

这套工程最终要做到的事情是：

- 从 `vendor/src/linux-0.12.tar.gz` 解包 Linux 0.12 源码
- 应用仓库内补丁，使其能在现代工具链和 QEMU 上构建
- 编译内核启动镜像
- 编译仓库自带的最小用户态程序 `/bin/sh` 和 `/bin/ls`
- 按仓库清单生成 Minix v1 根文件系统
- 生成仓库内置镜像 `images/bootimage-0.12-hd` 和 `images/hdc-0.12.img.xz`
- 启动 QEMU
- 进入 `[/usr/root]#`
- 执行 `ls`

这不是“导入历史镜像再启动”的项目，而是“本地重建运行镜像再启动”的项目。

当前正式发布版本：`v1.0.1`

仓库还带有自动发布资产的 GitHub Actions 工作流：推送 `v*` tag，或者手动触发 `.github/workflows/release.yml`，都会从源码重建镜像、执行一次真实启动验证，并把 `bootimage-0.12-hd`、`hdc-0.12.img.xz`、`manifest.json` 上传到对应的 GitHub Release。手动触发时还可以额外指定 `source_ref`，用于从当前 `main` 或其他 ref 重新发布某个已有 release 的资产。

## 支持的宿主机

- macOS arm64
- Ubuntu 22.04
- Windows 10

## 快速开始

### 1. 安装依赖

所有平台都需要：

- Python 3
- Docker
- QEMU

macOS arm64：

```sh
brew install qemu
```

Ubuntu 22.04：

```sh
sudo apt update
sudo apt install -y python3 qemu-system-x86 docker.io
```

Windows 10：

- 安装 Python 3
- 安装 Docker Desktop
- 安装 Windows 版 QEMU
- 确保 `qemu-system-i386.exe` 在 `PATH` 中，或者把 `LINUX012_QEMU_BIN` 设为完整路径

说明：

- Ubuntu 上需要当前用户能直接执行 `docker`
- 第一次构建会比较慢，因为需要准备 Docker 构建环境

### 2. 检查宿主机依赖

macOS / Ubuntu：

```sh
./scripts/bootstrap-host.sh
```

Windows PowerShell：

```powershell
.\scripts\bootstrap-host.ps1
```

Windows CMD：

```bat
scripts\bootstrap-host.cmd
```

### 3. 直接启动仓库内置镜像

如果你想先检查仓库快照是否完整，可以运行：

macOS / Ubuntu：

```sh
./scripts/check-images.sh
```

Windows PowerShell：

```powershell
.\scripts\check-images.ps1
```

Windows CMD：

```bat
scripts\check-images.cmd
```

如果你删掉了 `images/` 里的运行快照，想从当前发布版本重新拉回它们，可以运行：

macOS / Ubuntu：

```sh
./scripts/fetch-release-images.sh
```

Windows PowerShell：

```powershell
.\scripts\fetch-release-images.ps1
```

Windows CMD：

```bat
scripts\fetch-release-images.cmd
```

这条入口会根据 `images/manifest.json` 里的发布地址和 SHA-256 摘要下载并校验仓库快照。

如果你只是想立即启动 Linux 0.12，直接运行：

macOS / Ubuntu：

```sh
./scripts/run.sh
```

Windows PowerShell：

```powershell
.\scripts\run.ps1
```

Windows CMD：

```bat
scripts\run.cmd
```

这条入口直接使用仓库里的 `images/` 快照，不会先重编源码。系统硬盘镜像会先自动解包到 `out/repo-images/hdc-0.12.img`，然后再启动。macOS / Ubuntu 下它保留当前的终端交互方式；Windows 下本来就是图形窗口。

### 4. 弹出可见的 QEMU 窗口并手动操作

如果你要在这台机器上看到独立的 QEMU 窗口，并自己进去操作 Linux 0.12，运行：

macOS / Ubuntu：

```sh
./scripts/run-window.sh
```

Windows PowerShell：

```powershell
.\scripts\run-window.ps1
```

Windows CMD：

```bat
scripts\run-window.cmd
```

在这台 macOS 主机上，这条入口会显式使用 QEMU 的 `cocoa` 显示后端，弹出可见窗口。

### 5. 从编译阶段开始，再启动 QEMU

如果你要从源码编译开始跑完整流程，运行：

macOS / Ubuntu：

```sh
./scripts/build-and-run.sh
```

Windows PowerShell：

```powershell
.\scripts\build-and-run.ps1
```

Windows CMD：

```bat
scripts\build-and-run.cmd
```

这条入口会强制重新编译，完成后把新的镜像同步到 `images/`，其中硬盘镜像会以压缩快照形式写成 `images/hdc-0.12.img.xz`，然后启动 QEMU。

如果你既要“从编译开始”，又要最后看到可交互的 QEMU 窗口，运行：

macOS / Ubuntu：

```sh
./scripts/build-and-run-window.sh
```

Windows PowerShell：

```powershell
.\scripts\build-and-run-window.ps1
```

Windows CMD：

```bat
scripts\build-and-run-window.cmd
```

### 6. 一键验证

推荐直接运行验证入口。缺少运行镜像时，它会自动触发源码构建。

macOS / Ubuntu：

```sh
./scripts/verify.sh
```

Windows PowerShell：

```powershell
.\scripts\verify.ps1
```

Windows CMD：

```bat
scripts\verify.cmd
```

验证成功后，屏幕会停在类似下面的状态：

```text
[/usr/root]# ls
README
[/usr/root]#
```

如果你还想把当前最小 shell 内建命令也做一轮实机验证，可以运行：

macOS / Ubuntu：

```sh
./scripts/verify-userland.sh
```

Windows PowerShell：

```powershell
.\scripts\verify-userland.ps1
```

Windows CMD：

```bat
scripts\verify-userland.cmd
```

## 常用命令

直接启动仓库内置镜像：

```sh
python3 rebuild/driver.py run-repo-images
```

校验仓库镜像快照：

```sh
python3 rebuild/driver.py check-repo-images
```

从 GitHub Release 重新拉取仓库镜像快照：

```sh
python3 rebuild/driver.py fetch-release-images
```

直接弹出可见的 QEMU 窗口：

```sh
python3 rebuild/driver.py run-repo-images-window
```

强制从源码重编、同步 `images/`，再启动：

```sh
python3 rebuild/driver.py build-and-run-repo-images
```

强制从源码重编、同步 `images/`，再弹出可见窗口：

```sh
python3 rebuild/driver.py build-and-run-repo-images-window
```

## 持续集成

仓库现在包含 GitHub Actions 工作流 [ci.yml](/Users/infoxmed-01/ai/workspace/linux-012/.github/workflows/ci.yml)。它会在推送到 `main` 或对 `main` 发起 Pull Request 时执行两类任务：

- `ubuntu-22.04` 完整链路：
  `python3 -m unittest discover -s tests -v`
  `./scripts/bootstrap-host.sh`
  `python3 rebuild/driver.py build`
  `./scripts/verify.sh`
- `windows-2022` 宿主机 smoke：
  `py -3 -m unittest discover -s tests -v`
  `py -3 tools/qemu_driver.py bootstrap-host`
  基于仓库快照自动解包系统镜像
  `py -3 tools/qemu_driver.py verify --dry-run`
  `py -3 tools/qemu_driver.py run-window --dry-run`
- `macos-14` 宿主机 smoke：
  `brew install qemu`
  `python3 -m unittest discover -s tests -v`
  `python3 tools/qemu_driver.py bootstrap-host`
  基于仓库快照自动解包系统镜像
  `python3 tools/qemu_driver.py verify --dry-run`
  `python3 tools/qemu_driver.py run-window --dry-run`

失败时会上传 Ubuntu 的 `out/verify`、`rebuild/out/logs`，以及 Windows 和 macOS 的 `out/repo-images` 作为排查产物。

显式构建镜像：

```sh
python3 rebuild/driver.py build
```

仅做源码构建后的自动验证：

```sh
python3 rebuild/driver.py verify
```

验证 `pwd`、`echo`、`cat`、`uname` 和 `cd` 这些当前 shell 内建命令：

```sh
python3 rebuild/driver.py verify-userland
```

用源码构建出来的镜像交互启动：

```sh
python3 rebuild/driver.py run
```

生成的核心产物位于：

- `rebuild/out/images/bootimage-0.12-hd`
- `rebuild/out/images/hdc-0.12.img`
- `images/bootimage-0.12-hd`
- `images/hdc-0.12.img.xz`
- `images/manifest.json`
- `out/repo-images/hdc-0.12.img`
- `out/verify/screen.txt`
- `out/verify-userland/screen.txt`
- `out/run/boot.img`

## 这套构建链路做了什么

`rebuild/` 目录负责完整的源码到镜像流程：

1. 解包 `vendor/src/linux-0.12.tar.gz`
2. 应用 `rebuild/patches/linux-0.12/` 里的补丁
3. 编译 Linux 0.12 启动镜像
4. 编译 `rebuild/userland/` 里的最小用户态源码
5. 把生成的 ELF 打包成 Linux 0.12 可执行的 `ZMAGIC` a.out
6. 根据 `rebuild/rootfs/manifest/` 创建目录、设备节点和启动脚本
7. 生成 Linux 0.12 可挂载的 Minix v1 根文件系统
8. 组装成 `hdc-0.12.img`
9. 按需把新的启动镜像和压缩后的系统镜像同步到仓库的 `images/`
10. 启动 QEMU，抓取 VGA 文本，并自动向 guest 发送按键完成验证

这条链路当前只实现“最小可运行系统”，不尝试复刻一个完整的历史 Linux 0.12 发行版。

当前 shell 内建提供这些命令：

- `cd`
- `pwd`
- `echo`
- `cat`
- `uname`
- `exit`

独立用户态二进制当前提供：

- `/bin/sh`
- `/bin/ls`

## 仓库结构

- `scripts/`
  不同宿主机的入口脚本
- `images/`
  提交到仓库中的自编译运行镜像快照，其中系统镜像以压缩形式保存
- `images/manifest.json`
  仓库快照的 SHA-256、大小和发布下载地址清单
- `rebuild/driver.py`
  源码构建、运行和验证入口
- `rebuild/container/build_images.sh`
  容器内镜像构建脚本
- `rebuild/patches/linux-0.12/`
  Linux 0.12 适配 QEMU 和现代工具链的补丁
- `rebuild/userland/`
  最小 Linux 0.12 用户态源码
- `rebuild/rootfs/manifest/`
  根文件系统目录、设备节点和启动文件清单
- `rebuild/tools/aout_pack.py`
  把 ELF 打包成 Linux 0.12 `ZMAGIC` 可执行文件
- `tools/qemu_driver.py`
  QEMU 启动、VGA 抓取和自动按键注入
- `tests/`
  针对构建链路和运行入口的测试
- `vendor/src/linux-0.12.tar.gz`
  上游 Linux 0.12 源码归档

## 运行说明

- 启动镜像本身不足 1.44MB，驱动会在启动前补齐成标准软盘镜像
- `scripts/check-images.*` 会按 `images/manifest.json` 校验仓库快照
- `scripts/fetch-release-images.*` 会从 `images/manifest.json` 指向的 GitHub Release 重新拉取仓库快照
- `scripts/run.*` 默认直接使用仓库里的 `images/` 快照，并在 `out/repo-images/` 里自动解包系统镜像
- `scripts/run-window.*` 默认直接使用仓库里的 `images/` 快照，并在 `out/repo-images/` 里自动解包系统镜像后弹出可见的 QEMU 窗口
- `scripts/build-and-run.*` 会重编源码并刷新 `images/`
- `scripts/build-and-run-window.*` 会重编源码、刷新 `images/`，然后弹出可见的 QEMU 窗口
- QEMU 始终以 `-snapshot` 启动，所以重复运行不会改写 `rebuild/out/images/hdc-0.12.img`
- macOS 和 Ubuntu 22.04 的交互模式使用 `-display curses`
- Windows 10 的交互模式使用 QEMU 默认图形窗口
- macOS / Ubuntu 使用本地 Unix socket 作为 QEMU monitor
- Windows 10 使用本机 `localhost` TCP monitor

## 边界

当前项目明确做这些事情：

- 从源码构建运行镜像
- 启动到 shell
- 自动执行 `ls`
- 自动验证当前最小 shell 内建命令

当前项目明确不做这些事情：

- 还原完整历史 Linux 0.12 发行版
- 引入完整历史用户态软件集合
- 保留或依赖第三方运行时镜像

## 来源

- `vendor/src/linux-0.12.tar.gz` 来自 kernel.org 的 Linux 0.12 历史源码归档
- 运行镜像不来自第三方下载，而是由仓库内源码、补丁和清单在本地构建生成
