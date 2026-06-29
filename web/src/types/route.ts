export type CoordinateConfidence = "verified" | "approximate" | "missing" | string;
export type MovementType = "walked" | "vehicle" | "mixed" | "inferred" | "unclear" | string;
export type ContinuityStatus = "continuous" | "gap_before" | "gap_after" | "isolated" | "unclear" | string;
export type WalkabilityStatus =
  | "book_walkable"
  | "partially_walkable"
  | "not_walkable_as_written"
  | "needs_review"
  | string;
export type ModernFollowability =
  | "likely_followable"
  | "approximate_only"
  | "not_enough_information"
  | "needs_field_check"
  | string;

export interface PlacePoint {
  name: string;
  lat: number | null;
  lng: number | null;
  coordinate_source: string | null;
  coordinate_confidence: CoordinateConfidence;
}

export interface BookRef {
  page: number;
  quote: string;
  note: string;
}

export interface RouteSegment {
  id: string;
  order: number;
  chapter: string | null;
  title: string;
  start: PlacePoint;
  end: PlacePoint;
  via: PlacePoint[];
  distance_km_book: number | string | null;
  distance_km_computed: number | null;
  route_summary: string | null;
  walking_directions: string[];
  terrain: string | null;
  roads_or_paths: string | null;
  water_sources: string | null;
  resupply: string | null;
  lodging: string | null;
  risks_or_notes: string | null;
  book_refs: BookRef[];
  chapter_refs?: BookRef[];
  confidence: string;
  evidence_status?: string;
  evidence_notes?: string[];
  review_notes: string[];
  movement_type?: MovementType;
  continuity_status?: ContinuityStatus;
  walkability_status?: WalkabilityStatus;
  modern_followability?: ModernFollowability;
  gap_notes?: string[];
  do_not_connect_in_gpx?: boolean;
}

export interface WalkableBlock {
  block_id: string;
  segment_ids: string[];
  start_name: string;
  end_name: string;
  status: "continuous" | "partial" | "needs_review" | string;
  notes: string;
}
