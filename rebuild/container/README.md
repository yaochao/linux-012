# `rebuild/container/`

[English README](./README.en.md)

这个目录保存容器内执行的构建脚本。它们在由 `rebuild/Dockerfile` 创建的环境中运行，负责真正生成 Linux 0.12 运行镜像。

## 当前文件

- `build_images.sh`
  构建启动镜像、最小用户态、Minix 根文件系统和硬盘镜像
