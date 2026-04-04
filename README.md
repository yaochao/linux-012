# Linux 0.12 on QEMU

[English README](./README.en.md)

这个仓库的目标很直接：在现代宿主机上，从源码和仓库内清单出发，构建出 Linux 0.12 运行所需的两张 QEMU 镜像，启动进入 shell，并成功执行 `ls`。

仓库当前不再保存第三方运行时镜像。实际运行所需的镜像都由 `rebuild/` 工作流在本地生成：

- `rebuild/out/images/bootimage-0.12-hd`
- `rebuild/out/images/hdc-0.12.img`

## 项目结果

这套工程最终要做到的事情是：

- 从 `vendor/src/linux-0.12.tar.gz` 解包 Linux 0.12 源码
- 应用仓库内补丁，使其能在现代工具链和 QEMU 上构建
- 编译内核启动镜像
- 编译仓库自带的最小用户态程序 `/bin/sh` 和 `/bin/ls`
- 按仓库清单生成 Minix v1 根文件系统
- 启动 QEMU
- 进入 `[/usr/root]#`
- 执行 `ls`

这不是“导入历史镜像再启动”的项目，而是“本地重建运行镜像再启动”的项目。

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

### 3. 一键验证

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

### 4. 交互启动

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

## 常用命令

显式构建镜像：

```sh
python3 rebuild/driver.py build
```

仅做源码构建后的自动验证：

```sh
python3 rebuild/driver.py verify
```

用源码构建出来的镜像交互启动：

```sh
python3 rebuild/driver.py run
```

生成的核心产物位于：

- `rebuild/out/images/bootimage-0.12-hd`
- `rebuild/out/images/hdc-0.12.img`
- `out/verify/screen.txt`
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
9. 启动 QEMU，抓取 VGA 文本，并自动向 guest 发送按键完成验证

这条链路当前只实现“最小可运行系统”，不尝试复刻一个完整的历史 Linux 0.12 发行版。

## 仓库结构

- `scripts/`
  不同宿主机的入口脚本
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

当前项目明确不做这些事情：

- 还原完整历史 Linux 0.12 发行版
- 引入完整历史用户态软件集合
- 保留或依赖第三方运行时镜像

## 来源

- `vendor/src/linux-0.12.tar.gz` 来自 kernel.org 的 Linux 0.12 历史源码归档
- 运行镜像不来自第三方下载，而是由仓库内源码、补丁和清单在本地构建生成
