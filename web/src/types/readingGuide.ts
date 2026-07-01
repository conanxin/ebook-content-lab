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
  route_overview?: {
    summary?: string;
    reading_method?: string;
    then_now_note?: string;
    updated_in?: string;
  };
  route_timeline?: RouteTimelineNode[];
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
  coordinate_stats?: {
    version?: string;
    total_place_count?: number;
    public_coordinate_count?: number;
    approximate_coordinate_count?: number;
    needs_coordinate_review_count?: number;
    coordinate_ready_count?: number;
    coordinate_source_type_counts?: Record<string, number>;
  };
  travel_map?: {
    version?: string;
    map_mode?: string;
    description?: string;
    nodes?: TravelMapNode[];
  };
  route_index?: RouteIndexEntry[];
  place_route_index?: PlaceRouteIndexItem[];
  close_reading_overview?: {
    method?: string;
    scope?: string;
    updated_in?: string;
  };
  page_redesign?: {
    version?: string;
    mode?: string;
    main_axis?: string;
    layout?: string;
    goal?: string;
  };
  letter_reading_flow_summary?: {
    letter_units?: number;
    source_clue_ready?: number;
    embedded_places_ready?: number;
    question_answer_ready?: number;
    updated_in?: string;
  };
  navigation_model?: {
    version?: string;
    anchors?: string[];
    note?: string;
  };
  then_now_summary?: string;
  place_then_now?: PlaceThenNow[];
}

export interface OriginalExcerpt {
  excerpt?: string;
  note?: string;
  mode?: string;
  clue_id?: string;
  use?: string;
}

export interface SourceClue {
  clue_id?: string;
  mode?: string;
  excerpt?: string;
  note?: string;
  use?: string;
}

export interface EmbeddedLetterPlace {
  place_name?: string;
  role?: string;
  then_perspective?: string;
  today_perspective?: string;
  source_status?: string;
  source_label?: string;
  source_name?: string | null;
  source_url?: string | null;
  coordinate_status?: string;
  coordinate_label?: string;
  review_note?: string;
}

export interface LetterReadingUnit {
  version?: string;
  letter_number?: number;
  letter_id?: string;
  section_id?: string;
  date_or_stamp?: string;
  route_title?: string;
  one_sentence_guide?: string;
  themes?: string[];
  basic_info?: {
    route?: string;
    core_places?: string[];
    chunk_count?: number;
    char_count?: number;
    reading_length_hint?: string;
    what_to_watch?: string;
  };
  source_clues?: SourceClue[];
  close_reading_flow?: {
    what_it_says?: string;
    why_it_matters?: string;
    reading_steps?: string[];
    changes_to_notice?: string;
  };
  embedded_places?: EmbeddedLetterPlace[];
  question_answer?: {
    question_id?: string | null;
    question?: string | null;
    reference_answer?: string | null;
    answer_steps?: string[];
    basis?: string;
  };
  secondary_details?: {
    scene_notes?: string[];
    then_route_note?: string;
    then_now_comparison?: string;
    evidence_refs?: StructuralEvidenceRef[];
    review_notice?: string;
  };
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
  coordinates?: {
    lat?: number;
    lng?: number;
  } | null;
  coordinate_status?: string;
  coordinate_source_name?: string | null;
  coordinate_source_url?: string | null;
  coordinate_source_type?: string;
  coordinate_review_note?: string;
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

export interface RouteTimelineNode {
  letter_id?: string;
  letter_number?: number;
  chapter_id?: string;
  title?: string;
  route_label?: string;
  primary_places?: string[];
  then_context?: string;
  now_context?: string;
  reading_mood?: string;
  source_status_summary?: {
    public_source_count?: number;
    needs_source_review_count?: number;
  };
  linked_question_ids?: string[];
  updated_in?: string;
}

export interface PlaceRouteIndexItem {
  place_name?: string;
  letters?: string[];
  letter_titles?: string[];
  reading_order?: number[];
  source_status?: string;
  source_type?: string;
  source_name?: string;
  source_url?: string | null;
  today_reading?: string;
  then_context?: string[];
  source_review_note?: string;
  coordinates?: {
    lat?: number;
    lng?: number;
  } | null;
  coordinate_status?: string;
  coordinate_source_name?: string | null;
  coordinate_source_url?: string | null;
  coordinate_source_type?: string;
  coordinate_review_note?: string;
  updated_in?: string;
}

export interface TravelMapNode {
  order?: number;
  place_name?: string;
  letters?: string[];
  coordinates?: {
    lat?: number;
    lng?: number;
  } | null;
  coordinate_status?: string;
  source_status?: string;
  source_name?: string;
  coordinate_review_note?: string;
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
  letter_reading_unit?: LetterReadingUnit;
  letter_reading_flow_ready?: boolean;
  embedded_place_count?: number;
  updated_in?: string;
  timeline_node?: RouteTimelineNode;
  close_reading?: {
    excerpt_focus?: string;
    why_it_matters?: string;
    scene_to_notice?: string[];
    place_to_notice?: string[];
    then_now_prompt?: string;
    question_bridge?: string;
    answer_bridge?: string;
    updated_in?: string;
  };
  reading_steps?: string[];
  linked_questions?: string[];
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
  linked_letters?: string[];
  route_context?: string;
  close_reading_answer?: string;
  answer_steps?: string[];
  place_context?: string;
  then_now_context?: string;
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
