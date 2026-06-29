export function withBasePath(path: string): string {
  const base = import.meta.env.BASE_URL || "/";
  const cleanBase = base.endsWith("/") ? base : `${base}/`;
  const cleanPath = path.replace(/^\/+/, "");
  return `${cleanBase}${cleanPath}`;
}

export function projectDataPath(slug: string, file: string): string {
  return withBasePath(`projects/${slug}/${file}`);
}

export function projectsIndexPath(): string {
  return withBasePath("projects/index.json");
}
