import type { BookRef } from "./route";

export interface BookOverview {
  one_sentence_summary: string;
  route_structure: string[];
  how_to_use_this_page: string[];
  movement_gpx_notes: string[];
  limitations: string[];
  source_policy?: string;
}

export interface SegmentReadingCard {
  segment_id: string;
  reading_title: string;
  book_scene_summary: string;
  route_narrative: string;
  landmarks_in_book: string[];
  walking_experience: string;
  what_to_notice: string[];
  route_practicality: string;
  evidence_refs: BookRef[];
  confidence: {
    route_confidence?: string;
    evidence_status?: string;
    coordinate_confidence?: string;
    modern_followability?: string;
  };
  review_notes: string[];
}

export interface PlaceIndexItem {
  name: string;
  appears_in_segments: string[];
  pages: number[];
  role: string;
  book_context: string;
  coordinate_confidence: string;
  review_status: string;
  refs: BookRef[];
}

export interface BookTheme {
  theme: string;
  summary: string;
  related_segments: string[];
  related_places: string[];
  refs: BookRef[];
}
