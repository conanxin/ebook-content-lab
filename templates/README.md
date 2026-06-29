# Templates

优先使用创建脚本生成新电子书内容项目：

```powershell
python scripts\create_project.py --slug another-book --title "《某书》时间线解读" --book-title "某书" --project-type timeline
```

脚本会复制 `project-template/`、写入 `project.json` 和 `README.md`，并更新 `web/public/projects/index.json`。

模板目录保留标准空目录，供脚本复制：

- `private/source/`
- `private/ocr/`
- `working/`
- `public/`
- `reports/`
- `review_pack/`

后续流程见 `docs/add-new-book-project.md` 和 `docs/project-lifecycle.md`。
