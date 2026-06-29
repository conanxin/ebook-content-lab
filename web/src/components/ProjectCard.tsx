import { ArrowRight, BookOpen, CheckCircle2, FlaskConical } from "lucide-react";
import type { ProjectIndexItem, ProjectMetadata } from "../types/project";

interface ProjectCardProps {
  project: ProjectIndexItem | ProjectMetadata;
}

function qualityText(project: ProjectIndexItem | ProjectMetadata) {
  const quality = (project as ProjectMetadata).quality_summary;
  const routeStats = (project as ProjectMetadata).route_stats;
  const evidence = quality?.evidence_audit as { pass?: number; warning?: number; fail?: number } | undefined;
  const validation = quality?.validation as { errors?: number; warnings?: number } | undefined;

  if (evidence || validation) {
    const evidencePart = evidence
      ? `证据审计 pass ${evidence.pass ?? "unknown"} / warning ${evidence.warning ?? "unknown"} / fail ${evidence.fail ?? "unknown"}`
      : "证据审计 unknown";
    const validationPart = validation
      ? `校验 errors ${validation.errors ?? "unknown"} / warnings ${validation.warnings ?? "unknown"}`
      : "校验 unknown";
    return `${evidencePart}；${validationPart}`;
  }

  if (routeStats?.segments) {
    return `已记录 ${routeStats.segments} 个结构化段落，质量状态见项目报告。`;
  }

  return "证据审计尚未完成。";
}

function descriptionText(project: ProjectIndexItem | ProjectMetadata) {
  if ("description" in project && project.description) return project.description;
  return `基于《${project.book_title}》的 ${project.project_type} 子项目，当前状态：${project.status}。`;
}

export function ProjectCard({ project }: ProjectCardProps) {
  return (
    <article className="project-card">
      <div className="project-card-icon" aria-hidden="true">
        <BookOpen size={24} />
      </div>
      <div className="project-card-body">
        <div className="project-card-kicker">
          <FlaskConical size={14} />
          <span>{project.project_type}</span>
        </div>
        <h2>{project.title}</h2>
        <p className="project-book">书名：{project.book_title}</p>
        <p>{descriptionText(project)}</p>
        <div className="project-audit">
          <CheckCircle2 size={15} />
          <span>{qualityText(project)}</span>
        </div>
        <a className="project-link" href={`#/projects/${project.slug}`}>
          查看项目
          <ArrowRight size={16} />
        </a>
      </div>
    </article>
  );
}
