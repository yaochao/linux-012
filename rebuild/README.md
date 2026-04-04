# `rebuild/`

[English README](./README.en.md)

`rebuild/` 是本仓库的源码到镜像构建中心，负责把 Linux 0.12 内核源码、最小用户态源码、rootfs 清单和补丁组装成可被 QEMU 启动的运行镜像。

## 这个目录负责什么

- 构建 `rebuild/out/images/bootimage-0.12-hd`
- 构建 `rebuild/out/images/hdc-0.12.img`
- 通过 `driver.py` 调用 Docker 和 QEMU 完成构建、启动与验证
- 在需要时把构建出来的镜像同步到仓库根目录的 `images/`

## 主要内容

- `driver.py`
  宿主机侧入口，负责 `build`、`run`、`verify` 等命令
- `Dockerfile`
  构建 Linux 0.12 兼容工具链的容器定义
- `container/`
  容器内执行的镜像构建脚本
- `patches/`
  针对 Linux 0.12 源码的补丁
- `rootfs/`
  根文件系统布局、目录清单、设备节点和初始文件
- `tools/`
  构建过程中使用的辅助脚本
- `userland/`
  仓库自带的最小 Linux 0.12 用户态源码

## 常用命令

```sh
python3 rebuild/driver.py build
python3 rebuild/driver.py verify
python3 rebuild/driver.py run-repo-images
python3 rebuild/driver.py run-repo-images-window
```

## 边界

- 这里只管理源码构建和镜像装配流程
- 运行时输出在 `rebuild/out/`，属于生成产物
- 受版本控制的镜像快照在仓库根目录 `images/`
