import { useEffect, useState } from "react";
import { ArrowLeft, FileQuestion } from "lucide-react";
import type { ProjectMetadata } from "../types/project";
import { RouteMapProjectPage } from "./RouteMapProjectPage";

interface ProjectPageProps {
  slug: string;
}

async function fetchProject(slug: string) {
  const response = await fetch(`/projects/${slug}/project.json`);
  if (!response.ok) throw new Error(`/projects/${slug}/project.json ${response.status}`);
  return response.json() as Promise<ProjectMetadata>;
}

export function ProjectPage({ slug }: ProjectPageProps) {
  const [project, setProject] = useState<ProjectMetadata | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setError(null);
    fetchProject(slug)
      .then((data) => {
        if (!alive) return;
        setProject(data);
        setLoading(false);
      })
      .catch((err: Error) => {
        if (!alive) return;
        setError(err.message);
        setLoading(false);
      });
    return () => {
      alive = false;
    };
  }, [slug]);

  if (loading) {
    return (
      <main className="portal-shell">
        <div className="state-box">正在加载项目...</div>
      </main>
    );
  }

  if (error || !project) {
    return (
      <main className="portal-shell">
        <a className="back-link" href="#/">
          <ArrowLeft size={16} />
          返回首页
        </a>
        <div className="state-box error">项目加载失败：{error || "unknown"}</div>
      </main>
    );
  }

  if (project.project_type === "route-map") {
    return <RouteMapProjectPage project={project} dataBase={`/projects/${slug}`} />;
  }

  return (
    <main className="portal-shell">
      <a className="back-link" href="#/">
        <ArrowLeft size={16} />
        返回首页
      </a>
      <section className="unsupported-project">
        <FileQuestion size={36} />
        <h1>{project.title}</h1>
        <p>该项目类型页面尚未实现。</p>
        <dl>
          <div>
            <dt>书名</dt>
            <dd>{project.book_title}</dd>
          </div>
          <div>
            <dt>project_type</dt>
            <dd>{project.project_type}</dd>
          </div>
          <div>
            <dt>status</dt>
            <dd>{project.status}</dd>
          </div>
        </dl>
      </section>
    </main>
  );
}
