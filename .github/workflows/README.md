# `.github/workflows/`

[English README](./README.en.md)

这个目录保存 GitHub Actions 工作流。当前既有持续集成工作流，也有 GitHub Release 资产发布工作流。

## 当前文件

- `ci.yml`
  持续集成工作流，覆盖单测、构建、`ls` 启动验证，以及双次构建可复现性检查
- `release.yml`
  发布资产工作流，按 tag 或手动触发，从源码重建镜像并上传到 GitHub Release；上传后还会把发布资产重新拉回并再次启动验证；手动触发时支持额外指定 `source_ref`
