export type ProjectTab = "overview" | "map" | "reading-detail" | "place-index" | "field-guide";

const defaultProjectSlug = "dadou-shangdu";

export const validProjectTabs: ProjectTab[] = ["overview", "map", "reading-detail", "place-index", "field-guide"];

const legacyTabMap: Record<string, ProjectTab> = {
  overview: "overview",
  "map-route": "map",
  "reading-detail": "reading-detail",
  "place-index": "place-index",
  "field-guide": "field-guide",
};

export function getHashPath(): string {
  const hash = window.location.hash || "#/";
  return hash.replace(/^#/, "") || "/";
}

export function getRouteQuery(): URLSearchParams {
  const path = getHashPath();
  const queryStart = path.indexOf("?");
  return new URLSearchParams(queryStart >= 0 ? path.slice(queryStart + 1) : "");
}

export function isProjectTab(value: string | null): value is ProjectTab {
  return Boolean(value && validProjectTabs.includes(value as ProjectTab));
}

export function getActiveTab(defaultTab: ProjectTab = "overview"): ProjectTab {
  const tab = getRouteQuery().get("tab");
  return isProjectTab(tab) ? tab : defaultTab;
}

export function projectTabUrl(slug: string, tab: ProjectTab): string {
  return `#/projects/${slug}?tab=${tab}`;
}

export function setProjectTab(slug: string, tab: ProjectTab): void {
  window.location.hash = `/projects/${slug}?tab=${tab}`;
}

export function getLegacyTabFromHash(): ProjectTab | null {
  const key = getHashPath().replace(/^\/+/, "");
  return legacyTabMap[key] ?? null;
}

export function legacyProjectTabUrl(tab: ProjectTab, slug = defaultProjectSlug): string {
  return projectTabUrl(slug, tab);
}
