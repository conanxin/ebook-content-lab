import { useEffect, useState } from "react";
import { HomePage } from "./pages/HomePage";
import { ProjectPage } from "./pages/ProjectPage";
import { getHashPath, getLegacyTabFromHash, legacyProjectTabUrl, type ProjectTab } from "./utils/hashRoute";

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

export function App() {
  const [route, setRoute] = useState<RouteState>(() => parseHashRoute());

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
