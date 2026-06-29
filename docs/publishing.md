# Publishing

This project is deployed with GitHub Pages and GitHub Actions.

## Current Deployment

- GitHub repository: [https://github.com/conanxin/ebook-content-lab](https://github.com/conanxin/ebook-content-lab)
- Online home page: [https://conanxin.github.io/ebook-content-lab/](https://conanxin.github.io/ebook-content-lab/)
- `dadou-shangdu` project page: [https://conanxin.github.io/ebook-content-lab/#/projects/dadou-shangdu](https://conanxin.github.io/ebook-content-lab/#/projects/dadou-shangdu)

GitHub Pages is configured to use GitHub Actions. The workflow builds `web/` and deploys `web/dist`.

## Verified Public Endpoints

The following 10 public endpoints have been verified as HTTP 200 after deployment:

- `/`
- `/#/projects/dadou-shangdu`
- `/projects/index.json`
- `/projects/dadou-shangdu/project.json`
- `/projects/dadou-shangdu/route_segments.json`
- `/projects/dadou-shangdu/route.geojson`
- `/projects/dadou-shangdu/route_places.geojson`
- `/projects/dadou-shangdu/route.gpx`
- `/projects/dadou-shangdu/route_walkable_blocks.json`
- `/projects/dadou-shangdu/field_guide.md`

Full hash route:

```text
https://conanxin.github.io/ebook-content-lab/#/projects/dadou-shangdu
```

## GitHub Actions Workflow

Workflow file:

```text
.github/workflows/pages.yml
```

It currently:

1. Runs on push to `main`.
2. Supports `workflow_dispatch` manual deployment.
3. Uses Node 20.
4. Installs dependencies under `web/`.
5. Runs `npm run build`.
6. Uploads `web/dist`.
7. Deploys to GitHub Pages.

## VITE_BASE

`web/vite.config.ts` uses:

```ts
base: process.env.VITE_BASE || "/"
```

For this repository, the GitHub Pages project path is:

```text
/ebook-content-lab/
```

The workflow sets:

```yaml
VITE_BASE: /${{ github.event.repository.name }}/
```

For this repo that resolves to:

```text
VITE_BASE=/ebook-content-lab/
```

If this project is later published as a root user site such as `conanxin.github.io`, change the workflow to:

```yaml
VITE_BASE: /
```

If using a custom domain at the domain root, also use `/`. If using a custom domain subpath, set `VITE_BASE` to that subpath.

## 404 and Cache Notes

If the page is temporarily 404 after a successful deployment, or if it shows old content, wait for GitHub Pages/CDN cache refresh and test again.

For endpoint verification, use a no-cache request, for example:

```powershell
curl.exe -H "Cache-Control: no-cache" https://conanxin.github.io/ebook-content-lab/projects/index.json
```

If static JS/CSS assets are 404, check:

- `VITE_BASE` matches the deployed base path.
- The workflow has rebuilt after changing `VITE_BASE`.
- The published URL includes `/ebook-content-lab/`.

## Hash Routes

The app uses hash routes:

```text
#/
#/projects/dadou-shangdu
```

The route after `#` is handled by the browser. GitHub Pages receives only the path before the hash, so refreshing the project page should not require a server-side nested route.

## Local Checks Before Deployment

Run:

```powershell
python scripts\check_public_release.py
cd web
npm run build
```
