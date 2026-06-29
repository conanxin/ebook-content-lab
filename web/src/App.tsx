import { useEffect, useState } from "react";
import { HomePage } from "./pages/HomePage";
import { ProjectPage } from "./pages/ProjectPage";
import { getHashPath, getLegacyTabFromHash, legacyProjectTabUrl, type ProjectTab } from "./utils/hashRoute";
import { projectDataPath } from "./utils/paths";
import type { ProjectMetadata } from "./types/project";

const SITE_NAME = "ebook-content-lab";
const HOME_TITLE = `电子书内容实验室 · ${SITE_NAME}`;
const NOT_FOUND_TITLE = `未找到页面 · ${SITE_NAME}`;

type RouteState =
  | { name: "home" }
  | { name: "project"; slug: string }
  | { name: "legacy-tab"; tab: ProjectTab }
  | { name: "not-found"; path: string };

function parseHashRoute(): RouteState {
  const legacyTab = getLegacyTabFromHash();
  if (legacyTab) return { name: "legacy-tab", tab: legacyTab };

  const path = getHashPath();
  if (path === "/") return { name: "home" };

  const projectMatch = path.match(/^\/projects\/([a-z0-9-]+)(?:\?.*)?$/);
  if (projectMatch) return { name: "project", slug: projectMatch[1] };

  return { name: "not-found", path };
}

async function fetchProjectMeta(slug: string): Promise<ProjectMetadata | null> {
  try {
    const url = projectDataPath(slug, "project.json");
    const response = await fetch(url);
    if (!response.ok) return null;
    return (await response.json()) as ProjectMetadata;
  } catch {
    return null;
  }
}

export function App() {
  const [route, setRoute] = useState<RouteState>(() => parseHashRoute());
  const [projectMeta, setProjectMeta] = useState<{ slug: string; meta: ProjectMetadata } | null>(null);

  useEffect(() => {
    const handleHashChange = () => setRoute(parseHashRoute());
    window.addEventListener("hashchange", handleHashChange);
    return () => window.removeEventListener("hashchange", handleHashChange);
  }, []);

  useEffect(() => {
    if (route.name === "legacy-tab") {
      window.location.replace(legacyProjectTabUrl(route.tab));
    }
  }, [route]);

  // Reset project meta on every route change so titles never stick to a previous project.
  useEffect(() => {
    setProjectMeta(null);
  }, [route]);

  // Fetch project meta only when we're on the project route.
  useEffect(() => {
    if (route.name !== "project") return;
    let alive = true;
    fetchProjectMeta(route.slug).then((meta) => {
      if (!alive) return;
      if (meta) setProjectMeta({ slug: route.slug, meta });
    });
    return () => {
      alive = false;
    };
  }, [route]);

  // Centralised document.title — the single source of truth for browser tab titles.
  useEffect(() => {
    if (route.name === "home") {
      document.title = HOME_TITLE;
      return;
    }
    if (route.name === "project") {
      if (projectMeta && projectMeta.slug === route.slug) {
        document.title = `${projectMeta.meta.title} · ${SITE_NAME}`;
      } else {
        document.title = `正在加载项目 · ${SITE_NAME}`;
      }
      return;
    }
    if (route.name === "not-found") {
      document.title = NOT_FOUND_TITLE;
    }
  }, [route, projectMeta]);

  if (route.name === "home") return <HomePage />;
  if (route.name === "project") return <ProjectPage slug={route.slug} />;
  if (route.name === "legacy-tab") {
    return (
      <main className="portal-shell">
        <div className="state-box">
          正在跳转到子项目页面：<code>{legacyProjectTabUrl(route.tab)}</code>
        </div>
        <a className="back-link" href={legacyProjectTabUrl(route.tab)}>
          打开对应栏目
        </a>
      </main>
    );
  }

  return (
    <main className="portal-shell">
      <div className="state-box error">
        未找到页面：<code>{route.path}</code>
      </div>
      <a className="back-link" href="#/">
        返回首页
      </a>
    </main>
  );
}
