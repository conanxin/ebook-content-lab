import { useEffect, useState } from "react";
import { LibraryBig } from "lucide-react";
import { ProjectCard } from "../components/ProjectCard";
import type { ProjectIndex, ProjectIndexItem } from "../types/project";
import { projectsIndexPath } from "../utils/paths";

async function fetchProjectIndex() {
  const url = projectsIndexPath();
  const response = await fetch(url);
  if (!response.ok) throw new Error(`${url} ${response.status}`);
  return response.json() as Promise<ProjectIndex>;
}

export function HomePage() {
  const [projects, setProjects] = useState<ProjectIndexItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    fetchProjectIndex()
      .then((data) => {
        if (!alive) return;
        setProjects(data.projects ?? []);
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
  }, []);

  return (
    <main className="portal-shell">
      <section className="home-hero">
        <div className="home-brand">
          <LibraryBig size={28} />
          <span>ebook-content-lab</span>
        </div>
        <h1>电子书内容实验室</h1>
        <p>从电子书识别、证据抽取到可视化创作的开源项目集</p>
      </section>

      <section className="project-section" aria-label="电子书子项目">
        <div className="section-title-row">
          <h2>子项目</h2>
          <span>{projects.length} 个项目</span>
        </div>
        {loading && <div className="state-box">正在加载项目列表...</div>}
        {error && <div className="state-box error">项目列表加载失败：{error}</div>}
        {!loading && !error && projects.length === 0 && <div className="state-box">暂无公开项目。</div>}
        <div className="project-grid">
          {projects.map((project) => (
            <ProjectCard key={project.slug} project={project} />
          ))}
        </div>
      </section>
    </main>
  );
}
