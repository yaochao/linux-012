# 第三方来源与许可说明

[English Version](./THIRD_PARTY.en.md)

这个仓库现在有两类内容：

- 仓库自行编写的脚本、补丁、最小用户态源码、测试和文档
- 为了重建 Linux 0.12 所需而保存的第三方源码输入

根目录 [LICENSE](./LICENSE) 只用于仓库自行编写的内容，不会覆盖第三方源码及其衍生义务。第三方内容继续遵循各自的上游许可条件。

## 已随仓库分发的第三方源码

### `vendor/src/linux-0.12.tar.gz`

- 类型：上游历史源码归档
- 用途：作为 `rebuild/` 流程的输入，生成 Linux 0.12 启动镜像和系统镜像
- 来源：kernel.org 历史版本归档中的 Linux 0.12 源码包
- 仓库内状态：归档文件保持原样，不在 `vendor/src/` 中直接改写
- 本地改动方式：所有兼容性和 QEMU 适配修改都以单独补丁形式保存在 `rebuild/patches/linux-0.12/`

## 生成产物的许可边界

- `images/bootimage-0.12-hd`
  包含由上游 Linux 0.12 源码构建出来的内核启动链路
- `images/hdc-0.12.img.xz`
  是由上游 Linux 0.12 源码、仓库自带最小用户态源码和根文件系统清单共同生成的运行镜像快照

这些镜像是构建产物，不应简单视为“只受根目录 MIT License 约束”的文件。重新分发或再利用时，需要同时考虑其中包含的上游 Linux 0.12 代码及其相应义务。

## 仓库自行编写的主要内容

通常由本仓库自行编写并受根目录 [LICENSE](./LICENSE) 约束的内容包括：

- `rebuild/driver.py`
- `rebuild/container/`
- `rebuild/tools/`
- `rebuild/rootfs/`
- `rebuild/userland/`
- `rebuild/patches/linux-0.12/`
- `tools/`
- `scripts/`
- `tests/`
- 仓库内文档与 GitHub Actions 工作流

## 未随仓库分发的外部依赖

下面这些组件是运行或构建依赖，但并不随仓库一起分发：

- QEMU
- Docker / Docker Desktop
- Python 3
- GitHub Actions 中使用的官方 action

这些组件各自有独立许可，使用时应分别遵循其上游项目要求。
