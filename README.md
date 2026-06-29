# ebook-content-lab

从电子书识别、证据抽取到可视化创作的开源项目集。

当前状态：`v0.4.5` 多项目结构完成。

## 当前子项目

- `projects/dadou-shangdu/`：《从大都到上都》徒步路线图解
- project type: `route-map`
- Web 路由：`#/projects/dadou-shangdu`

这个子项目把《从大都到上都》整理成按书中线索组织的路线地图页面。页面展示路线段、书中路线证据、章节出处、复走状态、断点、GPX 连接规则和复核提示。它不是未经核验的户外导航资料。

## 在线部署

本仓库准备使用 GitHub Pages 发布 `web/dist`。

- 工作流：`.github/workflows/pages.yml`
- 发布说明：`docs/publishing.md`
- 默认部署路径：`https://<username>.github.io/<repo-name>/`
- Vite base path 由 `VITE_BASE` 控制，GitHub Actions 中默认使用 `/<repo-name>/`

## 本地运行

安装依赖：

```powershell
cd web
npm install
```

启动开发服务器：

```powershell
cd web
npm run dev -- --host 127.0.0.1
```

构建：

```powershell
cd web
npm run build
```

公开发布检查：

```powershell
python scripts\check_public_release.py
```

## 新增电子书项目

使用项目创建脚本：

```powershell
python scripts\create_project.py --slug another-book --title "《某书》时间线解读" --book-title "某书" --project-type timeline
```

支持的 `project_type` 包括：

- `route-map`
- `timeline`
- `character-map`
- `place-index`
- `reading-guide`
- `quote-atlas`
- `knowledge-map`
- `field-guide`

新增项目流程见：

- `docs/add-new-book-project.md`
- `docs/project-lifecycle.md`
- `docs/architecture.md`

## 数据公开策略

本仓库按“本地材料”和“公开数据”分层：

- `projects/<slug>/private/`：原始电子书、OCR PDF、OCR 全文等本地材料，不发布。
- `projects/<slug>/working/`：抽取、审计和整理过程中的工作文件，发布前需审查。
- `projects/<slug>/public/`：可公开的结构化数据和说明文件。
- `web/public/projects/<slug>/`：前端读取的公开项目数据。

不提交原始 PDF、OCR 全文、扫描页图片或包含大段原文的复核材料。公开数据只保留页面运行需要的结构化信息、短证据摘录、GeoJSON、GPX 和说明文档。

详细规则见 `docs/data-policy.md`。

## 许可证

- 代码：MIT License，见 `LICENSE`
- 原创说明文档、结构化数据和人工整理内容：CC BY 4.0，见 `LICENSE-CONTENT.md`
- `private/` 中的电子书源文件、OCR 全文和扫描页图片不属于公开发布内容，也不随本仓库授权。
