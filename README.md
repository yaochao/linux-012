# Linux 0.12 On QEMU

[English Version](./README.en.md)

这个仓库在本地从源码和仓库内清单生成 Linux 0.12 运行所需的两张 QEMU 镜像，然后启动 QEMU、进入 shell，并自动执行 `ls` 验证。

当前仓库不再保存第三方运行时镜像。默认运行时镜像全部由 `rebuild/` 工作流生成到 `rebuild/out/images/`：

- `bootimage-0.12-hd`：由打过补丁的 Linux 0.12 内核源码编译得到
- `hdc-0.12.img`：由仓库内最小用户态源码、rootfs 清单和 Minix v1 文件系统装配流程生成

当前支持的宿主机：

- macOS arm64
- Ubuntu 22.04
- Windows 10

验证通过后的目标状态是进入 Linux 0.12 的 `[/usr/root]#` 提示符，并成功执行 `ls`。

## 宿主机要求

所有平台都需要：

- Python 3
- Docker
- QEMU

### macOS arm64

```sh
brew install qemu
```

### Ubuntu 22.04

```sh
sudo apt update
sudo apt install -y python3 qemu-system-x86 docker.io
```

### Windows 10

- 安装 Python 3
- 安装 Docker Desktop
- 安装 Windows 版 QEMU
- 确保 `qemu-system-i386.exe` 在 `PATH` 中，或者把 `LINUX012_QEMU_BIN` 设为它的完整路径

先检查宿主机依赖：

```sh
./scripts/bootstrap-host.sh
```

```powershell
.\scripts\bootstrap-host.ps1
```

```bat
scripts\bootstrap-host.cmd
```

## 使用方式

### 先显式构建镜像

```sh
python3 rebuild/driver.py build
```

生成结果位于：

- `rebuild/out/images/bootimage-0.12-hd`
- `rebuild/out/images/hdc-0.12.img`

### macOS 和 Ubuntu 22.04

交互启动：

```sh
./scripts/run.sh
```

自动验证：

```sh
./scripts/verify.sh
```

### Windows 10 PowerShell

交互启动：

```powershell
.\scripts\run.ps1
```

自动验证：

```powershell
.\scripts\verify.ps1
```

### Windows 10 命令提示符

交互启动：

```bat
scripts\run.cmd
```

自动验证：

```bat
scripts\verify.cmd
```

`run` 和 `verify` 在缺少运行镜像时会自动触发 `python3 rebuild/driver.py build`。

验证命令会把最新结果写到 `out/verify/`：

- `screen.txt`：最终解码后的 VGA 文本屏幕
- `m.log`：QEMU monitor 交互日志
- `q.log`：QEMU 标准输出和错误输出

交互启动的运行产物会写到 `out/run/`。

## 这套源码构建做了什么

`rebuild/` 目录负责完整的源码到镜像流程：

- 解包 `vendor/src/linux-0.12.tar.gz`
- 应用仓库里的 Linux 0.12 补丁，使其能在现代工具链和 QEMU 上构建运行
- 编译 Linux 0.12 启动镜像
- 编译仓库自带的最小 Linux 0.12 兼容用户态程序：
  - `/bin/sh`
  - `/bin/ls`
- 按仓库内的 rootfs 清单创建目录树、设备节点和启动脚本
- 生成 Linux 0.12 可挂载的 Minix v1 根文件系统
- 组装成 `hdc-0.12.img`
- 启动 QEMU，进入 shell，并自动执行 `ls`

这一步并不尝试还原一个完整的历史 Linux 0.12 发行版；它只实现本项目当前需要的最小系统。

## 仓库结构

- `scripts/bootstrap-host.*`、`scripts/run.*`、`scripts/verify.*`：不同宿主机的入口脚本
- `rebuild/driver.py`：源码构建、运行和验证入口
- `rebuild/container/build_images.sh`：容器内镜像构建脚本
- `rebuild/patches/linux-0.12/`：Linux 0.12 适配 QEMU 和现代工具链的补丁
- `rebuild/userland/`：仓库自带的最小 Linux 0.12 用户态源码
- `rebuild/rootfs/manifest/`：目录、设备节点和启动文件清单
- `rebuild/tools/aout_pack.py`：把生成的 ELF 打包成 Linux 0.12 可执行的 `ZMAGIC` a.out
- `rebuild/out/images/`：本地生成的运行镜像
- `tools/qemu_driver.py`：QEMU 启动、VGA 抓取和按键注入
- `vendor/src/linux-0.12.tar.gz`：Linux 0.12 上游源码归档

## 说明

- 启动镜像本身不足 1.44MB，驱动会在启动前补齐成标准软盘镜像，写到 `out/run/boot.img` 或 `out/verify/boot.img`
- QEMU 始终以 `-snapshot` 方式启动，重复运行不会改写 `rebuild/out/images/hdc-0.12.img`
- macOS 和 Ubuntu 22.04 在交互模式下使用本地 Unix socket 作为 QEMU monitor，并启用 `-display curses`
- Windows 10 使用本机 `localhost` TCP monitor，交互模式使用 QEMU 默认图形窗口

## 资源来源

- `vendor/src/linux-0.12.tar.gz` 来自 kernel.org 的历史源码归档
- 运行镜像不再来自第三方下载；它们由仓库内源码、补丁和清单在本地构建生成
