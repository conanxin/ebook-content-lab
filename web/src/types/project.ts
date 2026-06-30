export type ProjectType =
  | "route-map"
  | "timeline"
  | "character-map"
  | "place-index"
  | "reading-guide"
  | "quote-atlas"
  | "knowledge-map"
  | "field-guide"
  | string;

export interface ProjectIndexItem {
  slug: string;
  title: string;
  book_title: string;
  project_type: ProjectType;
  status: string;
  public_path: string;
  project_json: string;
  subtitle?: string;
  release_phase?: string;
  review_status?: string | Record<string, unknown>;
}

export interface ProjectIndex {
  repository: string;
  projects: ProjectIndexItem[];
}

export interface ProjectMetadata extends ProjectIndexItem {
  source_type?: string;
  visibility?: {
    private_source_kept_in?: string;
    public_artifacts_kept_in?: string;
    web_public_path?: string;
  };
  public_files?: string[];
  quality_summary?: Record<string, unknown>;
  route_stats?: Record<string, unknown>;
  review_status?: string | Record<string, unknown>;
  book?: {
    title?: string | null;
    author?: string | null;
    publication_info?: string | null;
    publisher?: string | null;
    publication_date?: string | null;
    isbn?: string | null;
    source_type?: string | null;
    language?: string | null;
    is_scanned_likely?: boolean | "unknown" | null;
    total_pages?: number | null;
  };
  suggested_content_types?: string[];
  suggested_project_types?: string[];
  identity_status?: string;
  description?: string;
}
