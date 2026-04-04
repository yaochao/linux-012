# `tools/`

[English README](./README.en.md)

这个目录保存运行阶段使用的宿主机辅助工具。目前最核心的是 QEMU 驱动脚本。

## 当前文件

- `qemu_driver.py`
  负责准备启动介质、启动 QEMU、抓取 VGA 文本、通过 monitor 注入按键，以及完成自动验证
- `__init__.py`
  让这个目录可以被 Python 作为模块导入
