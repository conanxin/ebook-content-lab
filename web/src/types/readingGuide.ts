export interface StructuralEvidenceRef {
  ref_id?: string;
  evidence_mode?: string;
  note?: string;
  section_id?: string;
  letter_id?: string;
  chunk_ids?: string[];
}

export interface ReadingGuideBook {
  title: string | null;
  author?: string | null;
  language?: string | null;
  publisher?: string | null;
  date?: string | null;
  source_type?: string | null;
}

export interface ReadingGuidePublicMeta {
  schema_version: string;
  status: string;
  generated_at?: string;
  visibility?: string;
  release_phase?: string;
  review_status?: string;
  preview_notice?: string;
  display_title?: string;
  subtitle?: string;
  book: ReadingGuideBook;
}

export interface BookOverviewData extends ReadingGuidePublicMeta {
  one_sentence_summary?: string;
  reading_purpose?: string;
  structure_overview?: {
    body_letter_count?: number;
    section_range?: {
      start?: string;
      end?: string;
    };
    place_count_from_titles?: number;
    theme_count_from_structural_tags?: number;
    source_mode?: string;
  };
  how_to_use?: string[];
  limitations?: string[];
  evidence_refs?: StructuralEvidenceRef[];
  source_enrichment?: Record<string, unknown>;
  place_source_stats?: {
    version?: string;
    a11_public_source_count?: number;
    public_source_count?: number;
    a12_public_source_count?: number;
    new_public_source_count?: number;
    needs_source_review_count?: number;
    total_place_count?: number;
    source_type_counts?: Record<string, number>;
  };
  route_index?: RouteIndexEntry[];
  then_now_summary?: string;
  place_then_now?: PlaceThenNow[];
}

export interface OriginalExcerpt {
  excerpt?: string;
  note?: string;
  mode?: string;
}

export interface PlaceThenNow {
  place?: string;
  place_name?: string;
  name?: string;
  letters?: string[];
  appears_in_letters?: string[];
  then_context?: string[];
  today_reading?: string;
  now_context?: string;
  source_status?: string;
  source_name?: string;
  source_url?: string | null;
  source_type?: string;
  source_review_note?: string;
  review_status?: string;
  change_note?: string;
  priority?: string;
  is_key_place?: boolean;
  updated_in?: string;
}

export interface RouteIndexEntry {
  chapter_id?: string;
  letter_id?: string;
  order?: number;
  title?: string;
  core_places?: string[];
  source_covered_places?: string[];
  pending_places?: string[];
  updated_in?: string;
}

export interface ChapterReadingCard {
  chapter_id: string;
  letter_id?: string;
  section_id?: string;
  order?: number;
  title?: string;
  summary?: string;
  letter_stamp?: string;
  route_label?: string;
  letter_summary?: string;
  route_note?: string;
  reading_focus?: string;
  theme_note?: string;
  review_notice?: string;
  source_enrichment_status?: string;
  source_informed_summary?: string;
  original_excerpt?: OriginalExcerpt[];
  original_scene_notes?: string[];
  route_then?: {
    places?: string[];
    route_label?: string;
    note?: string;
  };
  route_now?: PlaceThenNow[];
  place_source_summary?: {
    public_source_count?: number;
    needs_source_review_count?: number;
    updated_in?: string;
  };
  needs_source_review?: boolean;
  then_now_comparison?: string;
  reading_focus_expanded?: string;
  answer_hint_expanded?: string;
  places?: string[];
  themes?: string[];
  char_count?: number;
  paragraph_count?: number;
  chunk_count?: number;
  evidence_refs?: StructuralEvidenceRef[];
  review_status?: string;
}

export interface ChapterReadingCardsData extends ReadingGuidePublicMeta {
  chapters: ChapterReadingCard[];
}

export interface KeyConcept {
  concept_id: string;
  label?: string;
  description?: string;
  guide_note?: string;
  related_letters?: Array<{
    letter_id?: string;
    section_id?: string;
    title?: string;
  }>;
  evidence_refs?: StructuralEvidenceRef[];
  review_status?: string;
}

export interface KeyConceptsData extends ReadingGuidePublicMeta {
  concepts: KeyConcept[];
}

export interface QuoteIndexEntry {
  quote_id: string;
  letter_id?: string;
  section_id?: string;
  quote_mode?: string;
  quote?: string;
  note?: string;
  evidence_refs?: StructuralEvidenceRef[];
  review_status?: string;
}

export interface QuoteIndexData extends ReadingGuidePublicMeta {
  quote_mode?: string;
  reader_note?: string;
  quotes: QuoteIndexEntry[];
}

export interface ReadingQuestion {
  question_id: string;
  scope?: string;
  letter_id?: string;
  section_id?: string;
  question?: string;
  basis?: string;
  answer_hint?: string;
  reference_answer?: string;
  guide_answer?: string;
  answer_hint_expanded?: string;
  source_clues?: string[];
  place_clues?: string[];
  then_now_hint?: string;
  review_notice?: string;
  review_status?: string;
}

export interface ReadingQuestionsData extends ReadingGuidePublicMeta {
  questions: ReadingQuestion[];
}

export interface ReadingGuideDataBundle {
  bookOverview: BookOverviewData | null;
  chapterReadingCards: ChapterReadingCardsData | null;
  keyConcepts: KeyConceptsData | null;
  quoteIndex: QuoteIndexData | null;
  readingQuestions: ReadingQuestionsData | null;
}
