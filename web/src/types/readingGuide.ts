export interface EvidenceRef {
  page: number | null;
  quote: string;
  note: string;
  source_file?: string | null;
}

export interface ReadingGuideBook {
  title: string | null;
  author?: string | null;
  language?: string | null;
}

export interface BookOverviewData {
  schema_version: string;
  status: string;
  book: ReadingGuideBook;
  one_sentence_summary?: string;
  reading_purpose?: string;
  structure_overview?: string;
  how_to_use?: string;
  limitations?: string[];
  evidence_refs?: EvidenceRef[];
}

export interface ChapterReadingCardsData {
  schema_version: string;
  status: string;
  book: ReadingGuideBook;
  chapters: unknown[];
}

export interface KeyConceptsData {
  schema_version: string;
  status: string;
  book: ReadingGuideBook;
  concepts: unknown[];
}

export interface QuoteIndexData {
  schema_version: string;
  status: string;
  book: ReadingGuideBook;
  quotes: unknown[];
}

export interface ReadingQuestionsData {
  schema_version: string;
  status: string;
  book: ReadingGuideBook;
  questions: unknown[];
}

export interface ReadingGuideDataBundle {
  bookOverview: BookOverviewData | null;
  chapterReadingCards: ChapterReadingCardsData | null;
  keyConcepts: KeyConceptsData | null;
  quoteIndex: QuoteIndexData | null;
  readingQuestions: ReadingQuestionsData | null;
}
