# Publishing

本项目使用 GitHub Actions 将 `web/dist` 发布到 GitHub Pages。

## 1. 创建 GitHub 仓库

在 GitHub 创建仓库，例如：

```text
ebook-content-lab
```

普通项目站点的 URL 通常是：

```text
https://<username>.github.io/<repo-name>/
```

如果仓库名是 `<username>.github.io`，则通常作为根站点发布：

```text
https://<username>.github.io/
```

## 2. 推送代码

示例命令：

```powershell
git remote add origin https://github.com/<username>/<repo-name>.git
git branch -M main
git push -u origin main
```

不要提交 `projects/*/private/`、原始 PDF、OCR 全文、扫描页图片或本地复核扫描材料。

## 3. GitHub Pages 设置

在 GitHub 仓库中：

1. 打开 **Settings -> Pages**。
2. 在 **Build and deployment** 中选择 **GitHub Actions**。
3. 推送到 `main`，或在 **Actions** 页面手动运行 `Deploy site to GitHub Pages`。

工作流文件：

```text
.github/workflows/pages.yml
```

工作流会：

1. 使用 Node 20。
2. 在 `web/` 中安装依赖。
3. 运行 `npm run build`。
4. 上传 `web/dist`。
5. 部署到 GitHub Pages。

## 4. VITE_BASE

Vite 在子路径部署时需要正确的 `base`。

`web/vite.config.ts` 使用：

```ts
base: process.env.VITE_BASE || "/"
```

GitHub Actions 中默认设置：

```yaml
VITE_BASE: /${{ github.event.repository.name }}/
```

这适合普通项目站点，例如：

```text
https://<username>.github.io/ebook-content-lab/
```

如果发布到 `<username>.github.io` 根站点，手动改成：

```yaml
VITE_BASE: /
```

如果使用自定义域名，并且站点在域名根路径，也使用：

```yaml
VITE_BASE: /
```

如果自定义域名下仍使用子路径，则设置为对应子路径。

## 5. 常见 404 和静态资源问题

如果页面空白或 JS/CSS 资源 404，优先检查：

- GitHub Pages URL 是否包含仓库名子路径。
- `VITE_BASE` 是否与部署路径一致。
- `web/dist/index.html` 中的资源路径是否以正确的 base 开头。

如果项目页刷新后仍可打开，这是因为 Web 使用 hash route：

```text
#/
#/projects/dadou-shangdu
```

`#` 后的路由由浏览器处理，GitHub Pages 只接收 `#` 前的路径，因此刷新子项目页通常不会触发嵌套路由 404。

## 6. 本地构建检查

发布前运行：

```powershell
python scripts\check_public_release.py
cd web
npm run build
```
