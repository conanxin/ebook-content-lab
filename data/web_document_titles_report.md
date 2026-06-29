# Web Document Titles Report

Status: **pass**

## Summary

- Errors: 0
- Warnings: 0

## Errors

- None

## Warnings

- None

## Rules

- `<title>` in web/index.html should contain the site name.
- App.tsx must assign to document.title at least once.
- App.tsx should reference a home title and a not-found title literal.
- ProjectPage.tsx should still mention 'title' so future refactors don't drop the project title field.
- App.tsx must promote the route to not-found when fetchProjectMeta resolves null, so missing slugs do not leave document.title stuck on '正在加载项目'.
