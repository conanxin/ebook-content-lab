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
