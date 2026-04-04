# `rebuild/rootfs/`

[English README](./README.en.md)

这个目录保存根文件系统的装配输入。它决定磁盘布局、目录结构、设备节点来源以及要放入 guest 的初始文件。

## 主要内容

- `layout.sfdisk`
  硬盘分区布局
- `manifest/`
  根文件系统目录、设备节点和初始文件清单
- `overlay/`
  预留的附加覆盖目录，目前为空
