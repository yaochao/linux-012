# `rebuild/rootfs/manifest/`

[English README](./README.en.md)

这个目录保存根文件系统清单。它描述应该创建哪些目录、哪些设备节点，以及哪些初始文件应该被复制进镜像。

## 当前文件

- `directories.txt`
  要创建的目录列表
- `devices.tsv`
  要创建的设备节点定义
- `etc/`
  写入 guest `/etc` 的文件
- `usr/`
  写入 guest `/usr` 的文件
