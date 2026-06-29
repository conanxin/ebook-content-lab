import { useEffect, useState } from "react";
import { HomePage } from "./pages/HomePage";
import { ProjectPage } from "./pages/ProjectPage";

type RouteState =
  | { name: "home" }
  | { name: "project"; slug: string }
  | { name: "not-found"; path: string };

function parseHashRoute(): RouteState {
  const hash = window.location.hash || "#/";
  const path = hash.replace(/^#/, "") || "/";
  if (path === "/") return { name: "home" };

  const projectMatch = path.match(/^\/projects\/([a-z0-9-]+)$/);
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

  if (route.name === "home") return <HomePage />;
  if (route.name === "project") return <ProjectPage slug={route.slug} />;

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
