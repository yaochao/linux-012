# Linux 0.12 On QEMU

[English Version](./README.en.md)

这个仓库把 Linux 0.12 跑在 `qemu-system-i386` 上，并且把项目运行所需的文件都放在仓库内部。整个运行时围绕一个 Python 驱动组织，同时提供不同宿主机的薄包装脚本，当前支持：

- macOS arm64
- Ubuntu 22.04
- Windows 10

当前仓库采用的启动路径是：

- 一张历史 Linux 0.12 启动软盘镜像
- 一张作为 `hda` 挂载的 Linux 0.12 硬盘镜像
- 每次启动前把较短的 boot image 补齐成标准 1.44MB 软盘镜像

在 macOS 和 Ubuntu 22.04 上，`./scripts/run.sh` 会以终端 curses 界面启动，并最终进入 Linux 0.12 的 `[/]#` 提示符。
在 Windows 10 上，`scripts\run.cmd` 或 `.\scripts\run.ps1` 会打开默认的 QEMU 图形窗口，并驱动相同的启动流程。
自动验证入口会启动同一台虚拟机，执行 `ls`，如果验证失败则返回非零退出码。

## 宿主机要求

### macOS arm64

```sh
brew install qemu
```

### Ubuntu 22.04

```sh
sudo apt update
sudo apt install -y python3 qemu-system-x86
```

### Windows 10

- 安装 Python 3。
- 安装 Windows 版 QEMU。
- 确保 `qemu-system-i386.exe` 在 `PATH` 中，或者把 `LINUX012_QEMU_BIN` 设置为 QEMU 可执行文件的完整路径。

安装完成后，用对应平台的入口检查宿主机依赖：

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

验证命令会把最新运行结果保存在 `out/verify/`，包括：

- `screen.txt`：最终解码后的 VGA 文本屏幕
- `m.log`：QEMU monitor 交互日志
- `q.log`：QEMU 标准输出和错误输出

交互启动时对应的运行产物会保存在 `out/run/`。

## 从源码重建运行镜像

`rebuild/` 目录提供了当前仓库的源码重建工作流，需要 Docker。这个阶段的边界是：

- `bootimage-0.12-hd` 由打过补丁的 Linux 0.12 内核源码直接编译得到
- `hdc-0.12.img` 由仓库内提交的 canonical rootfs 基线和 overlay 本地重建得到

之所以这样拆分，是因为 `vendor/src/linux-0.12.tar.gz` 只包含内核源码，不包含完整的 `sh`、`ls` 和用户态系统。

常用命令：

```sh
python3 rebuild/driver.py build
python3 rebuild/driver.py verify
```

如果需要把默认运行时切换到这两张自主重建的镜像：

```sh
python3 rebuild/driver.py promote
```

如果需要重新从当前默认硬盘镜像采集 canonical rootfs 基线：

```sh
python3 rebuild/driver.py capture-rootfs
```

## 仓库结构

- `scripts/bootstrap-host.sh`、`scripts/run.sh`、`scripts/verify.sh`：macOS 和 Ubuntu 22.04 的 Unix 包装脚本
- `scripts/bootstrap-host.ps1`、`scripts/run.ps1`、`scripts/verify.ps1`：Windows 10 的 PowerShell 包装脚本
- `scripts/bootstrap-host.cmd`、`scripts/run.cmd`、`scripts/verify.cmd`：Windows 10 命令提示符入口，内部转调 PowerShell
- `tools/qemu_driver.py`：负责准备运行时镜像、发现 QEMU、启动 QEMU、抓取 VGA 文本和注入按键
- `rebuild/driver.py`：负责采集 canonical rootfs、重建镜像、验证重建结果，并在通过后把重建镜像推广到默认运行时
- `vendor/src/linux-0.12.tar.gz`：Linux 0.12 源码归档
- `vendor/images/bootimage-0.12-hd`：用于硬盘根文件系统启动的历史 Linux 0.12 boot image
- `vendor/images/hdc-0.12.img`：以 `hda` 挂载的 Linux 0.12 硬盘镜像

## 说明

- 仓库内的 boot image 本身不足 1.44MB。驱动会在启动前把它补齐到 `out/run/boot.img` 或 `out/verify/boot.img`。
- QEMU 总是以 `-snapshot` 方式启动，因此重复运行不会改写仓库内置的硬盘镜像。
- macOS 和 Ubuntu 22.04 在交互模式下使用本地 Unix socket 作为 QEMU monitor，并启用 `-display curses`。
- Windows 10 由于没有 Unix domain socket，改用本机 `localhost` TCP monitor；交互模式使用 QEMU 默认可见窗口。
- 这个 Linux 0.12 镜像在进入 shell 前会打印 `/root: ENOENT`。这是镜像本身的已知现象，不影响进入命令行。

## 资源来源

- `vendor/src/linux-0.12.tar.gz` 来自 kernel.org 的历史归档。
- `vendor/images/bootimage-0.12-hd` 来自 OldLinux 的 `linux-0.12-080324.zip`。
- `vendor/images/hdc-0.12.img` 来自 `chenzhengchen200821109/linux-0.12` 仓库中提供的 Linux 0.12 QEMU 硬盘镜像。
- `python3 rebuild/driver.py promote` 会在重建镜像通过验证后覆盖 `vendor/images/` 下的默认运行镜像。
