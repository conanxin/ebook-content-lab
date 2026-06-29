# 项目结构约定

`ebook-content-lab` 使用一个仓库容纳多个电子书内容项目。

```text
projects/<slug>/
  project.json
  private/
    source/
    ocr/
  working/
  public/
  reports/
  review_pack/
```

## private

保存原始电子书、OCR PDF、OCR 原文和其他不适合公开发布的本地材料。

这些文件用于复核和再处理，不应复制到 `web/public`。

## working

保存抽取、审计和清理过程中的中间文件，例如 draft JSON、unsupported claims、citation mismatches。

## public

保存可公开发布的数据，例如结构化 JSON、GeoJSON、GPX、读者说明书。

## reports

保存 OCR 报告、证据审计报告、校验报告、最终验收报告。

## review_pack

保存人工复核入口、复核索引和 checklist。原书扫描页图片默认不发布到 `web/public`。

## data 兼容层

当前 `data/` 是历史兼容目录。新结构以 `projects/<slug>/` 为准。

