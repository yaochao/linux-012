# `rebuild/patches/linux-0.12/`

[English README](./README.en.md)

这个目录保存 Linux 0.12 的补丁序列，用来让上游源码适配现代工具链、当前构建流程以及 QEMU 运行环境。

## 当前补丁

- `0001-modernize-toolchain.patch`
  处理现代工具链兼容性
- `0002-qemu-root-device.patch`
  调整 QEMU 启动所需的根设备行为
- `0003-modern-inline-semantics.patch`
  修正现代编译器对内联语义和 PIE/PIC 的差异
