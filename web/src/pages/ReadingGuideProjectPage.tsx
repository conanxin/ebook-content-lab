import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  ArrowLeft,
  BookOpen,
  CircleHelp,
  FileText,
  Layers,
  Lightbulb,
  MapPinned,
  Quote,
  ShieldCheck,
} from "lucide-react";
import type { ProjectMetadata } from "../types/project";
import type {
  BookOverviewData,
  ChapterReadingCard,
  ChapterReadingCardsData,
  KeyConcept,
  KeyConceptsData,
  PlaceRouteIndexItem,
  PlaceThenNow,
  QuoteIndexData,
  ReadingGuideDataBundle,
  ReadingQuestion,
  ReadingQuestionsData,
  RouteIndexEntry,
  RouteTimelineNode,
  SourceClue,
  SourceExcerpt,
} from "../types/readingGuide";
import { projectDataPath } from "../utils/paths";

interface ReadingGuideProjectPageProps {
  project: ProjectMetadata;
  projectSlug: string;
}

interface ModuleStatus {
  key: keyof ReadingGuideDataBundle;
  title: string;
  file: string;
  status: string;
  count: number | null;
  description: string;
}

async function fetchJson<T>(slug: string, file: string): Promise<T> {
  const url = projectDataPath(slug, file);
  const response = await fetch(url);
  if (!response.ok) throw new Error(`${url} ${response.status}`);
  return response.json() as Promise<T>;
}

function countItems(data: ReadingGuideDataBundle, key: keyof ReadingGuideDataBundle): number | null {
  const value = data[key];
  if (!value) return null;
  if ("chapters" in value && Array.isArray(value.chapters)) return value.chapters.length;
  if ("concepts" in value && Array.isArray(value.concepts)) return value.concepts.length;
  if ("quotes" in value && Array.isArray(value.quotes)) return value.quotes.length;
  if ("questions" in value && Array.isArray(value.questions)) return value.questions.length;
  return null;
}

function moduleDataStatus(data: ReadingGuideDataBundle, key: keyof ReadingGuideDataBundle): string {
  return data[key]?.status || "missing";
}

function joinList(values?: string[], fallback = "待人工复核"): string {
  if (!values || values.length === 0) return fallback;
  return values.filter(Boolean).join("、") || fallback;
}

function displayText(value: string | null | undefined, fallback = "待人工复核"): string {
  const trimmed = value?.trim();
  return trimmed ? trimmed : fallback;
}

function excerptTypeLabel(type: string | undefined): string {
  const labels: Record<string, string> = {
    opening_scene: "开篇场景",
    route_movement: "路线移动",
    place_description: "地点描写",
    travel_observation: "旅途观察",
    reflection: "感受反思",
    closing_moment: "收束时刻",
    other: "阅读线索",
  };
  return labels[type || ""] || "原文选段";
}

function evidenceLabel(refs: Array<{ section_id?: string; letter_id?: string }> | undefined): string {
  if (!refs || refs.length === 0) return "结构证据待补充";
  return (
    refs
      .slice(0, 2)
      .map((ref) => [ref.section_id, ref.letter_id].filter(Boolean).join(" / "))
      .filter(Boolean)
      .join("；") || "结构证据待补充"
  );
}

function allPlaces(chapters: ChapterReadingCard[]): string[] {
  return Array.from(new Set(chapters.flatMap((chapter) => chapter.places || [])));
}

function placeName(place: PlaceThenNow | PlaceRouteIndexItem): string {
  const value = place as Record<string, unknown>;
  return String(value.place || value.place_name || value.name || "地点待复核");
}

function sourceStatusLabel(status?: string): string {
  return status === "public_source" ? "已补公开来源" : "待补来源";
}

function sourceStatusClass(status?: string): string {
  return status === "public_source" ? "source-status-public" : "source-status-pending";
}

function sourceTypeLabel(sourceType?: string): string {
  const labels: Record<string, string> = {
    official: "官方",
    unesco: "世界遗产",
    government: "政府",
    museum: "博物馆",
    encyclopedia: "百科",
    tourism: "文旅",
    other: "其他",
    unknown: "待复核",
  };
  return labels[sourceType || "unknown"] || sourceType || "待复核";
}

function coordinateStatusLabel(status?: string): string {
  if (status === "public_coordinate") return "已有坐标";
  if (status === "approximate_coordinate") return "近似坐标";
  return "待核坐标";
}

function coordinateStatusClass(status?: string): string {
  if (status === "public_coordinate") return "coordinate-public";
  if (status === "approximate_coordinate") return "coordinate-approximate";
  return "coordinate-pending";
}

function readingQuestionAnswer(question?: ReadingQuestion): string {
  return displayText(
    question?.close_reading_answer ||
      question?.answer_hint_expanded ||
      question?.answer_hint ||
      question?.reference_answer ||
      question?.guide_answer,
    "参考回答待人工复核。",
  );
}

function scrollToChapter(chapterId?: string): void {
  if (!chapterId) return;
  const node = document.getElementById(chapterId);
  node?.scrollIntoView({ behavior: "smooth", block: "start" });
}

function scrollToSection(sectionId: string): void {
  const node = document.getElementById(sectionId);
  node?.scrollIntoView({ behavior: "smooth", block: "start" });
}

export function ReadingGuideProjectPage({ project, projectSlug }: ReadingGuideProjectPageProps) {
  const [data, setData] = useState<ReadingGuideDataBundle>({
    bookOverview: null,
    chapterReadingCards: null,
    keyConcepts: null,
    quoteIndex: null,
    readingQuestions: null,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [placeFilter, setPlaceFilter] = useState("all");
  const [expandAllLetters, setExpandAllLetters] = useState(false);
  const [readingMode, setReadingMode] = useState<"quick" | "deep">("quick");

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setError(null);

    Promise.all([
      fetchJson<BookOverviewData>(projectSlug, "book_overview.json"),
      fetchJson<ChapterReadingCardsData>(projectSlug, "chapter_reading_cards.json"),
      fetchJson<KeyConceptsData>(projectSlug, "key_concepts.json"),
      fetchJson<QuoteIndexData>(projectSlug, "quote_index.json"),
      fetchJson<ReadingQuestionsData>(projectSlug, "reading_questions.json"),
    ])
      .then(([bookOverview, chapterReadingCards, keyConcepts, quoteIndex, readingQuestions]) => {
        if (!alive) return;
        setData({
          bookOverview,
          chapterReadingCards,
          keyConcepts,
          quoteIndex,
          readingQuestions,
        });
        setLoading(false);
      })
      .catch((err: Error) => {
        if (!alive) return;
        setError(err.message);
        setLoading(false);
      });

    return () => {
      alive = false;
    };
  }, [projectSlug]);

  const moduleStatuses = useMemo<ModuleStatus[]>(
    () => [
      {
        key: "bookOverview",
        title: "全书导读",
        file: "book_overview.json",
        status: moduleDataStatus(data, "bookOverview"),
        count: null,
        description: "书籍定位、路线总览、地点索引、页面结构和公开预览边界。",
      },
      {
        key: "chapterReadingCards",
        title: "25封书信",
        file: "chapter_reading_cards.json",
        status: moduleDataStatus(data, "chapterReadingCards"),
        count: countItems(data, "chapterReadingCards"),
        description: "每封信的路线、原文线索、精读步骤、景点对照和问题答案。",
      },
      {
        key: "keyConcepts",
        title: "核心概念",
        file: "key_concepts.json",
        status: moduleDataStatus(data, "keyConcepts"),
        count: countItems(data, "keyConcepts"),
        description: "由结构化主题聚合出的概念草稿，等待人工细读修订。",
      },
      {
        key: "quoteIndex",
        title: "原文线索",
        file: "quote_index.json",
        status: moduleDataStatus(data, "quoteIndex"),
        count: countItems(data, "quoteIndex"),
        description: "以短摘、线索和定位说明服务导读，不作为整章全文替代。",
      },
      {
        key: "readingQuestions",
        title: "阅读问题",
        file: "reading_questions.json",
        status: moduleDataStatus(data, "readingQuestions"),
        count: countItems(data, "readingQuestions"),
        description: "每个问题包含参考回答，并能回到对应书信。",
      },
    ],
    [data],
  );

  const overview = data.bookOverview;
  const chapters = data.chapterReadingCards?.chapters || [];
  const concepts = data.keyConcepts?.concepts || [];
  const quotes = data.quoteIndex?.quotes || [];
  const questions = data.readingQuestions?.questions || [];
  const questionsById = useMemo(() => new Map(questions.map((question) => [question.question_id, question])), [questions]);
  const places = allPlaces(chapters);
  const placeThenNow = overview?.place_then_now || [];
  const placeStats = overview?.place_source_stats;
  const publicSourceCount = placeStats?.public_source_count ?? placeThenNow.filter((place) => place.source_status === "public_source").length;
  const pendingSourceCount =
    placeStats?.needs_source_review_count ?? placeThenNow.filter((place) => place.source_status !== "public_source").length;
  const coordinateStats = overview?.coordinate_stats;
  const projectTitle = overview?.display_title || "《旅行人信札》阅读导览";
  const bookTitle = overview?.book?.title || project.book?.title || project.book_title || "《旅行人信札》";
  const subtitle = overview?.subtitle || project.subtitle || "25封旅行书信的路线、地点、场景与阅读线索";
  const schemaVersion = overview?.schema_version || data.chapterReadingCards?.schema_version || "reading-guide.v0.2";
  const publicStatus = overview?.status || project.status || "draft";
  const releasePhase = overview?.release_phase || "public-preview";
  const reviewStatus = typeof overview?.review_status === "string" ? overview.review_status : "manual-review-pending";

  const routeIndex: RouteIndexEntry[] =
    overview?.route_index ||
    chapters.map((chapter) => ({
      chapter_id: chapter.chapter_id,
      letter_id: chapter.letter_id,
      order: chapter.order,
      title: chapter.title,
      core_places: chapter.places || [],
      source_covered_places: (chapter.places || []).filter((name) =>
        placeThenNow.some((place) => placeName(place) === name && place.source_status === "public_source"),
      ),
      pending_places: (chapter.places || []).filter(
        (name) => !placeThenNow.some((place) => placeName(place) === name && place.source_status === "public_source"),
      ),
    }));
  const routeTimeline: RouteTimelineNode[] =
    overview?.route_timeline ||
    chapters.map((chapter) => ({
      letter_id: chapter.letter_id,
      letter_number: chapter.order,
      chapter_id: chapter.chapter_id,
      title: chapter.title,
      route_label: chapter.route_label || joinList(chapter.places),
      primary_places: chapter.places || [],
      then_context: chapter.route_then?.note || chapter.source_informed_summary,
      now_context: chapter.then_now_comparison,
      reading_mood: chapter.reading_focus_expanded || chapter.reading_focus,
      source_status_summary: chapter.place_source_summary,
      linked_question_ids: chapter.linked_questions || [],
    }));
  const placeRouteIndex: PlaceRouteIndexItem[] =
    overview?.place_route_index ||
    placeThenNow.map((place) => ({
      place_name: placeName(place),
      letters: place.appears_in_letters || place.letters || [],
      source_status: place.source_status,
      source_type: place.source_type,
      source_name: place.source_name,
      source_url: place.source_url,
      today_reading: place.now_context || place.today_reading,
      source_review_note: place.source_review_note,
      coordinates: place.coordinates,
      coordinate_status: place.coordinate_status,
      coordinate_review_note: place.coordinate_review_note,
    }));
  const filteredPlaceRouteIndex = placeRouteIndex.filter((place) => {
    if (placeFilter === "public-source") return place.source_status === "public_source";
    if (placeFilter === "pending-source") return place.source_status !== "public_source";
    if (placeFilter === "coordinate-ready") return ["public_coordinate", "approximate_coordinate"].includes(place.coordinate_status || "");
    if (placeFilter === "coordinate-pending") return place.coordinate_status === "needs_coordinate_review";
    return true;
  });
  const travelMapNodes =
    overview?.travel_map?.nodes ||
    filteredPlaceRouteIndex.map((place, index) => ({
      order: index + 1,
      place_name: place.place_name,
      letters: place.letters,
      coordinates: place.coordinates,
      coordinate_status: place.coordinate_status,
      source_status: place.source_status,
      source_name: place.source_name,
      coordinate_review_note: place.coordinate_review_note,
    }));
  const visibleTravelMapNodes = travelMapNodes.filter((node) =>
    filteredPlaceRouteIndex.some((place) => place.place_name === node.place_name),
  );

  return (
    <main className="portal-shell reading-guide-page letter-flow-page">
      <a className="back-link" href="#/">
        <ArrowLeft size={16} />
        返回首页
      </a>

      <section className="reading-guide-hero letter-flow-hero">
        <div className="reading-guide-kicker">
          <BookOpen size={18} />
          旅行书信阅读导览
        </div>
        <h1>{projectTitle}</h1>
        <p className="reading-guide-subtitle">{subtitle}</p>
        <p className="hero-reading-note">
          这页按 25 封书信顺序阅读：每封信集中呈现路线、核心地点、原文摘录与阅读线索、原文精读、昔日旅程与今日景点，以及对应阅读问题的参考回答。
        </p>

        <div className="reading-guide-status-strip" aria-label="public preview status">
          <span className="preview-badge is-draft">Draft</span>
          <span className="preview-badge is-preview">Public Preview</span>
          <span className="preview-badge is-pending">Manual review pending</span>
        </div>

        <div className="letter-flow-facts">
          <div>
            <span>书名</span>
            <strong>{bookTitle}</strong>
          </div>
          <div>
            <span>作者</span>
            <strong>{overview?.book?.author || project.book?.author || "陈嘉映"}</strong>
          </div>
          <div>
            <span>文体 / 题材</span>
            <strong>旅行书信 / 个人阅读导览</strong>
          </div>
          <div>
            <span>书信数量</span>
            <strong>{chapters.length || 25} 封</strong>
          </div>
          <div>
            <span>地点线索</span>
            <strong>{placeRouteIndex.length || places.length} 个</strong>
          </div>
          <div>
            <span>当前状态</span>
            <strong>公开预览，人工复核中</strong>
          </div>
        </div>
      </section>

      {error ? <section className="state-box error">reading-guide 数据加载失败：{error}</section> : null}

      <section className="content-section reading-guide-warning compact-warning">
        <AlertTriangle size={20} />
        <div>
          <h2>公开预览说明</h2>
          <p>
            当前版本用于个人阅读导览。页面补充短摘、场景线索、地点说明和参考回答，但仍不是 reviewed / final 版本；95 条人工复核任务尚未填写结果。
          </p>
        </div>
      </section>

      <nav className="reading-guide-nav sticky-reading-nav" aria-label="阅读导览导航">
        <div className="section-anchor-list">
          {[
            ["overview", "概览"],
            ["letters", "25封书信"],
            ["route-timeline", "路线时间线"],
            ["place-index", "地点索引"],
            ["questions", "阅读问题"],
          ].map(([sectionId, label]) => (
            <button className="reading-mode-toggle" key={sectionId} type="button" onClick={() => scrollToSection(sectionId)}>
              {label}
            </button>
          ))}
          <button className="mobile-section-toggle" type="button" onClick={() => setExpandAllLetters((value) => !value)}>
            {expandAllLetters ? "收起全部书信" : "展开全部书信"}
          </button>
        </div>
      </nav>

      <section className="content-section reading-guide-overview letter-flow-overview" id="overview">
        <h2>概览</h2>
        <p>{displayText(overview?.one_sentence_summary, "公开导读草稿已生成，概览仍待人工复核。")}</p>
        <div className="reading-flow-panel">
          <h3>25封书信连续阅读</h3>
          <p>
            本轮重设计把页面主线收束为 letter-001 到 letter-025。路线时间线、地点索引和阅读问题都作为辅助模块，先服务每封信本身，再服务全局查找。
          </p>
          <div className="filter-chip-row">
            <span>先看一封信写了什么</span>
            <span>再看原文线索和场景</span>
            <span>最后看地点今昔对照与参考回答</span>
          </div>
        </div>
        <div className="letter-flow-summary-strip">
          <div>
            <strong>{overview?.letter_reading_flow_summary?.letter_units ?? chapters.length}</strong>
            <span>书信阅读单元</span>
          </div>
          <div>
            <strong>{overview?.letter_reading_flow_summary?.source_clue_ready ?? chapters.length}</strong>
            <span>原文线索覆盖</span>
          </div>
          <div>
            <strong>{overview?.letter_reading_flow_summary?.embedded_places_ready ?? chapters.length}</strong>
            <span>景点嵌入覆盖</span>
          </div>
          <div>
            <strong>{overview?.letter_reading_flow_summary?.question_answer_ready ?? chapters.length}</strong>
            <span>问题答案覆盖</span>
          </div>
        </div>
      </section>

      <section className="content-section letter-reading-flow" id="letters">
        <header className="letter-flow-section-header">
          <div>
            <p className="section-eyebrow">main reading flow</p>
            <h2>25封书信连续阅读</h2>
          </div>
          <p>建议先用快速浏览走完整条路线，再对感兴趣的信切换到精读模式。快速浏览只显示核心原文选段和答案摘要，精读模式展开更多原文片段和完整说明。</p>
        </header>

        <div className="immersive-mode-bar" aria-label="阅读模式切换">
          <div className="reading-mode-quick reading-mode-deep">
            {[
              ["quick", "快速浏览"],
              ["deep", "精读模式"],
            ].map(([mode, label]) => (
              <button
                className={`mode-chip ${readingMode === mode ? "mode-chip-active" : ""}`}
                key={mode}
                type="button"
                onClick={() => setReadingMode(mode as "quick" | "deep")}
              >
                {label}
              </button>
            ))}
          </div>
          <span>{readingMode === "quick" ? "默认只显示核心 1-2 条原文选段。" : "精读模式会展开更多原文片段、场景、今昔对照和完整答案。"}</span>
        </div>

        <div className="letter-envelope-list compact-card-stack">
          {chapters.map((chapter: ChapterReadingCard) => {
            const unit = chapter.letter_reading_unit;
            const sourceExcerpts: SourceExcerpt[] =
              chapter.source_excerpts ||
              unit?.source_excerpts ||
              (unit?.source_clues || chapter.original_excerpt || []).map((item: SourceClue, index) => ({
                anchor_id: `${chapter.letter_id || chapter.chapter_id}-source-anchor-${index + 1}`,
                text: item.excerpt,
                note: item.note,
                reading_use: item.use,
                mode: item.mode,
              }));
            const coreSourceExcerpts = chapter.core_source_excerpts || unit?.core_source_excerpts || sourceExcerpts.slice(0, 2);
            const extraSourceExcerpts = chapter.extra_source_excerpts || unit?.extra_source_excerpts || sourceExcerpts.slice(2);
            const visibleSourceExcerpts = coreSourceExcerpts;
            const linkedQuestionId = unit?.question_answer?.question_id || chapter.linked_questions?.[0];
            const linkedQuestion = linkedQuestionId ? questionsById.get(linkedQuestionId) : undefined;
            const questionText = unit?.question_answer?.question || linkedQuestion?.question || "本封信的阅读问题待人工复核。";
            const quickAnswer = linkedQuestion?.quick_answer || chapter.reading_modes?.quick_summary || unit?.question_answer?.reference_answer || readingQuestionAnswer(linkedQuestion);
            const deepAnswer = linkedQuestion?.deep_answer || unit?.question_answer?.reference_answer || readingQuestionAnswer(linkedQuestion);
            const answerText = readingMode === "deep" ? deepAnswer : quickAnswer;
            const embeddedPlaces = unit?.embedded_places || [];
            const previousChapter = chapters.find((item) => item.letter_id === chapter.navigation?.previous_letter_id);
            const nextChapter = chapters.find((item) => item.letter_id === chapter.navigation?.next_letter_id);
            const deepOpen = readingMode === "deep" || expandAllLetters;

            return (
              <article className="letter-reading-unit letter-envelope-card" id={chapter.chapter_id} key={chapter.chapter_id}>
                <div className="letter-flap" aria-hidden="true" />
                <header className="letter-unit-header">
                  <div className="letter-number">{unit?.letter_number ?? chapter.order ?? "?"}</div>
                  <div>
                    <p className="letter-meta-line">
                      <span className="letter-stamp">{unit?.date_or_stamp || chapter.letter_stamp || "日期待复核"}</span>
                      <span>{chapter.section_id}</span>
                      <span>{chapter.letter_id}</span>
                    </p>
                    <h3>{displayText(unit?.route_title || chapter.title, "章节标题待复核")}</h3>
                    <p className="letter-one-line">{displayText(unit?.one_sentence_guide || chapter.source_informed_summary, "本封信导读摘要待复核。")}</p>
                  </div>
                </header>

                <div className="letter-theme-row">
                  {(unit?.themes || chapter.themes || []).map((theme) => (
                    <span key={`${chapter.chapter_id}-${theme}`}>{theme}</span>
                  ))}
                </div>

                <section className="source-anchor real-source-excerpts letter-source-block letter-body">
                  <h4>原文选段</h4>
                  <p className="source-anchor-intro">
                    {readingMode === "quick"
                      ? "快速浏览：先读核心 1-2 条真实原文，再继续路线和答案摘要。"
                      : "精读模式：显示本封信全部原文片段，再看场景、路线和今昔对照。"}
                  </p>
                  <div className="source-clue-list core-source-excerpts">
                    {visibleSourceExcerpts.slice(0, 4).map((item, index) => (
                      <article className="source-excerpt-card real-source-excerpt-card source-clue-card letter-original-excerpt" key={`${chapter.chapter_id}-source-${index}`}>
                        <span className="source-excerpt-type">{excerptTypeLabel(item.excerpt_type)}</span>
                        <p className="source-excerpt-text real-source-excerpt-text">{displayText(item.text, "原文选段待复核。")}</p>
                        <details className="source-excerpt-note">
                          <summary>选段说明</summary>
                          <small className="real-source-excerpt-note">{displayText(item.note, "这条原文选段用于辅助阅读。")}</small>
                          <span>{displayText(item.reading_use, "用于看风景、交通、城市感受或空间转换。")}</span>
                        </details>
                      </article>
                    ))}
                  </div>
                  {extraSourceExcerpts.length > 0 ? (
                    <details className="extra-source-excerpts more-source-excerpts collapsible-reading-panel" open={readingMode === "deep"}>
                      <summary>更多原文片段（{extraSourceExcerpts.length}）</summary>
                      <div className="source-clue-list">
                        {extraSourceExcerpts.map((item, index) => (
                          <article className="source-excerpt-card real-source-excerpt-card source-clue-card letter-original-excerpt" key={`${chapter.chapter_id}-extra-source-${index}`}>
                            <span className="source-excerpt-type">{excerptTypeLabel(item.excerpt_type)}</span>
                            <p className="source-excerpt-text real-source-excerpt-text">{displayText(item.text, "原文选段待复核。")}</p>
                            <details className="source-excerpt-note">
                              <summary>选段说明</summary>
                              <small className="real-source-excerpt-note">{displayText(item.note, "这条原文选段用于辅助阅读。")}</small>
                              <span>{displayText(item.reading_use, "用于看风景、交通、城市感受或空间转换。")}</span>
                            </details>
                          </article>
                        ))}
                      </div>
                    </details>
                  ) : null}
                </section>

                <section className="scene-explanation-panel close-reading-panel letter-close-reading">
                  <h4>场景说明</h4>
                  <div className="close-reading-grid">
                    <div className="close-reading-excerpt">
                      <strong>这封信写了什么</strong>
                      <p>{displayText(unit?.close_reading_flow?.what_it_says || chapter.source_informed_summary, "本封信内容摘要待复核。")}</p>
                    </div>
                    <div className="close-reading-explanation">
                      <strong>为什么值得注意</strong>
                      <p>{displayText(unit?.close_reading_flow?.why_it_matters || chapter.close_reading?.why_it_matters, "精读说明待人工复核。")}</p>
                    </div>
                  </div>
                  <div className="letter-scene-notes">
                    <strong>场景线索</strong>
                    <ul>
                      {(unit?.secondary_details?.scene_notes || chapter.original_scene_notes || ["场景线索待人工复核。"]).slice(0, 5).map((note) => (
                        <li key={`${chapter.chapter_id}-scene-top-${note}`}>{note}</li>
                      ))}
                    </ul>
                  </div>
                </section>

                <section className="route-structure-panel">
                  <h4>路线结构</h4>
                  <div className="letter-info-strip">
                    <div className="letter-route">
                      <MapPinned size={15} />
                      <span>{unit?.basic_info?.route || chapter.route_label || joinList(chapter.places)}</span>
                    </div>
                    <div>
                      <span>核心地点</span>
                      <strong>{joinList(unit?.basic_info?.core_places || chapter.places)}</strong>
                    </div>
                    <div>
                      <span>阅读长度</span>
                      <strong>{unit?.basic_info?.reading_length_hint || `${chapter.chunk_count ?? "待复核"} chunks`}</strong>
                    </div>
                    <div>
                      <span>这一封主要看什么</span>
                      <strong>{unit?.basic_info?.what_to_watch || chapter.reading_focus_expanded || chapter.reading_focus || "路线、场景和地点变化"}</strong>
                    </div>
                  </div>
                </section>

                <section className="then-now-panel letter-place-section">
                  <h4>今昔对照：本封涉及景点</h4>
                  <div className="embedded-place-list">
                    {embeddedPlaces.map((place) => (
                      <article className="embedded-place-card" key={`${chapter.chapter_id}-${place.place_name}`}>
                        <header>
                          <h5>{place.place_name}</h5>
                          <span className={`place-source-badge ${sourceStatusClass(place.source_status)}`}>{place.source_label}</span>
                        </header>
                        <p>
                          <strong>{place.role}</strong>：{displayText(place.then_perspective, "书信中的旅行语境待复核。")}
                        </p>
                        <p>{displayText(place.today_perspective, "今日景点信息待公开来源复核。")}</p>
                        <div className="reading-guide-tags">
                          <span className={`coordinate-badge ${coordinateStatusClass(place.coordinate_status)}`}>{place.coordinate_label}</span>
                          {place.source_url ? (
                            <a href={place.source_url} target="_blank" rel="noreferrer">
                              {place.source_name || "公开来源"}
                            </a>
                          ) : (
                            <span>{place.review_note || "待补充公开来源"}</span>
                          )}
                        </div>
                      </article>
                    ))}
                  </div>
                </section>

                <section className="question-answer-panel letter-answer">
                  <h4>阅读问题</h4>
                  <div className="close-reading-question">
                    <strong>{questionText}</strong>
                  </div>
                  <h4>参考答案</h4>
                  <div className="close-reading-answer">
                    <p>{answerText}</p>
                  </div>
                  <ol>
                    {(unit?.question_answer?.answer_steps || linkedQuestion?.answer_steps || []).slice(0, 4).map((step) => (
                      <li key={`${chapter.chapter_id}-answer-step-${step}`}>{step}</li>
                    ))}
                  </ol>
                  <small>{unit?.question_answer?.basis || "基于原书线索、地点说明、结构化导读与公开来源状态整理，待人工复核。"}</small>
                </section>

                <details className="secondary-reading-details collapsible-reading-panel" open={deepOpen}>
                  <summary>{readingMode === "deep" ? "精读内容已展开" : "展开精读"}</summary>
                  <div className="secondary-reading-grid">
                    <div className="letter-scene-notes">
                      <h4>原书场景线索</h4>
                      <ul>
                        {(unit?.secondary_details?.scene_notes || chapter.original_scene_notes || ["场景线索待人工复核。"]).map((note) => (
                          <li key={`${chapter.chapter_id}-scene-${note}`}>{note}</li>
                        ))}
                      </ul>
                    </div>
                    <div className="letter-then-now">
                      <h4>当年路线 / 今日对照</h4>
                      <p>{displayText(unit?.secondary_details?.then_route_note || chapter.route_then?.note, "当年路线说明待复核。")}</p>
                      <p>{displayText(unit?.secondary_details?.then_now_comparison || chapter.then_now_comparison, "昔日旅程与今日景点对照待补充。")}</p>
                    </div>
                    <div>
                      <h4>结构证据与复核</h4>
                      <p>{evidenceLabel(chapter.evidence_refs)}</p>
                      <p>{displayText(unit?.secondary_details?.review_notice || chapter.review_notice, "Public preview：本卡片仍待人工复核。")}</p>
                    </div>
                  </div>
                </details>

                <nav className="letter-navigation" aria-label={`${chapter.title || chapter.letter_id} 连续阅读导航`}>
                  <span>{chapter.navigation?.position_label || `第 ${chapter.order ?? "?"} 封`}</span>
                  <div className="letter-prev-next">
                    <button
                      className="letter-nav-button"
                      type="button"
                      disabled={!previousChapter}
                      onClick={() => scrollToChapter(previousChapter?.chapter_id)}
                    >
                      上一封
                    </button>
                    <button className="letter-nav-button" type="button" onClick={() => scrollToSection("letters")}>
                      回到 25 封信顶部
                    </button>
                    <button
                      className="letter-nav-button"
                      type="button"
                      disabled={!nextChapter}
                      onClick={() => scrollToChapter(nextChapter?.chapter_id)}
                    >
                      下一封
                    </button>
                  </div>
                </nav>
              </article>
            );
          })}
        </div>
      </section>

      <section className="content-section route-timeline-section" id="route-timeline">
        <h2>旅行路线时间线</h2>
        <p>{displayText(overview?.route_overview?.summary, "按 25 封旅行书信建立顺读时间线。")}</p>
        <div className="route-timeline">
          {routeTimeline.map((node) => (
            <article className="route-timeline-node" key={node.chapter_id || node.letter_id || node.title}>
              <div className="route-timeline-marker">{node.letter_number ?? "?"}</div>
              <div>
                <h3>{displayText(node.title, "书信标题待复核")}</h3>
                <p>{displayText(node.then_context, "当年旅程说明待复核。")}</p>
                <div className="route-timeline-places">
                  {(node.primary_places || []).map((place) => (
                    <span key={`${node.chapter_id}-${place}`}>{place}</span>
                  ))}
                </div>
                <button className="route-timeline-link" type="button" onClick={() => scrollToChapter(node.chapter_id)}>
                  回到本封信
                </button>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="content-section travel-map-section" id="place-index">
        <h2>地点路线索引 / 路线地图 / 纸面路线图</h2>
        <p>{overview?.travel_map?.description || "轻量纸面路线图使用公开或近似坐标辅助阅读，不作为导航轨迹。"}</p>
        <div className="place-overview-panel">
          <div>
            <strong>{placeStats?.total_place_count ?? placeRouteIndex.length}</strong>
            <span>地点总览</span>
          </div>
          <div>
            <strong>{publicSourceCount}</strong>
            <span>已补公开来源</span>
          </div>
          <div>
            <strong>{pendingSourceCount}</strong>
            <span>待补来源</span>
          </div>
          <div>
            <strong>{(coordinateStats?.public_coordinate_count ?? 0) + (coordinateStats?.approximate_coordinate_count ?? 0)}</strong>
            <span>已有或近似坐标</span>
          </div>
        </div>
        <div className="filter-chip-row">
          {[
            ["all", "全部地点"],
            ["public-source", "已有来源"],
            ["pending-source", "待补来源"],
            ["coordinate-ready", "已有坐标"],
            ["coordinate-pending", "待补坐标"],
          ].map(([value, label]) => (
            <button
              className={`reading-mode-toggle ${placeFilter === value ? "is-active" : ""}`}
              key={value}
              type="button"
              onClick={() => setPlaceFilter(value)}
            >
              {label}
            </button>
          ))}
        </div>
        <div className="travel-map-canvas" aria-label="纸面路线图节点">
          <div className="travel-map-path" aria-hidden="true" />
          {visibleTravelMapNodes.slice(0, 45).map((node) => (
            <button
              className={`travel-map-node ${coordinateStatusClass(node.coordinate_status)}`}
              key={`${node.order}-${node.place_name}`}
              type="button"
              onClick={() => scrollToSection("place-card-list")}
            >
              <span className="travel-map-label">
                {node.order}. {node.place_name}
              </span>
              <span className={`coordinate-badge ${coordinateStatusClass(node.coordinate_status)}`}>
                {coordinateStatusLabel(node.coordinate_status)}
              </span>
            </button>
          ))}
        </div>

        <div className="paper-map-section">
          <h3>地图式路线索引</h3>
          <div className="paper-map-route">
            {filteredPlaceRouteIndex.slice(0, 36).map((place, index) => (
              <article className="paper-map-node" key={`${place.place_name}-${index}`}>
                <span className={`place-source-badge ${sourceStatusClass(place.source_status)}`}>
                  {sourceStatusLabel(place.source_status)}
                </span>
                <span className={`coordinate-badge ${coordinateStatusClass(place.coordinate_status)}`}>
                  {coordinateStatusLabel(place.coordinate_status)}
                </span>
                <strong>{place.place_name}</strong>
                <small>第 {joinList((place.reading_order || []).map(String), "?")} 封</small>
              </article>
            ))}
          </div>
        </div>

        <div className="place-route-index" id="place-card-list">
          {filteredPlaceRouteIndex.map((place) => (
            <article className="place-route-index-item" key={place.place_name}>
              <h3>{place.place_name}</h3>
              <p>{displayText(place.today_reading, "今日读法待复核。")}</p>
              <div className="reading-guide-tags">
                <span className={`place-source-badge ${sourceStatusClass(place.source_status)}`}>
                  {sourceStatusLabel(place.source_status)}
                </span>
                <span className={`coordinate-badge ${coordinateStatusClass(place.coordinate_status)}`}>
                  {coordinateStatusLabel(place.coordinate_status)}
                </span>
                <span>{sourceTypeLabel(place.source_type)}</span>
                <span>关联：{joinList(place.letters, "待复核")}</span>
              </div>
              {place.source_url ? (
                <a href={place.source_url} target="_blank" rel="noreferrer">
                  {place.source_name || "公开来源"}
                </a>
              ) : (
                <span>{place.source_review_note || "待补充公开来源"}</span>
              )}
            </article>
          ))}
        </div>
      </section>

      <section className="content-section" id="then-now">
        <h2>昔日旅程与今日景点</h2>
        <p>{displayText(overview?.then_now_summary, "今日景点对照仍待补充公开来源。")}</p>
        <div className="route-index" aria-label="25封书信路线索引">
          {routeIndex.map((item) => (
            <button
              className="route-index-item"
              key={item.chapter_id || item.letter_id || item.title}
              type="button"
              onClick={() => scrollToChapter(item.chapter_id)}
            >
              <strong>第 {item.order ?? "?"} 封</strong>
              <span>{displayText(item.title, "书信标题待复核")}</span>
              <small>
                {joinList(item.source_covered_places, "暂无已补来源")} / {joinList(item.pending_places, "无待补来源")}
              </small>
            </button>
          ))}
        </div>
        <div className="place-comparison-grid">
          {placeThenNow.slice(0, 18).map((place) => (
            <article className="place-now-source place-comparison-card" key={placeName(place)}>
              <header>
                <h3>{placeName(place)}</h3>
                <span className={`place-source-badge ${sourceStatusClass(place.source_status)}`}>
                  {sourceStatusLabel(place.source_status)}
                </span>
              </header>
              <p>{displayText(place.now_context || place.today_reading, "今日景点信息待公开来源复核。")}</p>
              <p>{displayText(place.change_note, "当年旅行经验与今日景点状态的差异仍待补充。")}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="content-section quote-policy" id="quote-clues" data-quote-mode={data.quoteIndex?.quote_mode || "structural_no_quote"}>
        <header>
          <ShieldCheck size={22} />
          <div>
            <h2>原文摘录与阅读线索</h2>
            <p>
              当前页面把原文线索放回每封信内部：短摘用于定位场景，说明用于解释为什么值得读。这里保留全局索引，方便后续人工校订摘录、页码和地点说明。
            </p>
          </div>
        </header>
        <div className="reading-guide-stat-grid">
          <div>
            <strong>{quotes.length}</strong>
            <span>结构化线索槽位</span>
          </div>
          <div>
            <strong>{chapters.reduce((sum, chapter) => sum + (chapter.letter_reading_unit?.source_clues?.length || 0), 0)}</strong>
            <span>书信内原文线索</span>
          </div>
        </div>
      </section>

      <section className="content-section" id="questions">
        <h2>阅读问题总览</h2>
        <p>每个问题都显示参考回答，并可回到相关书信。问题不是标准答案，而是个人阅读导览的复核前提示。</p>
        <div className="question-list">
          {questions.map((question: ReadingQuestion) => (
            <article className="question-card" key={question.question_id}>
              <h3>{displayText(question.question, "阅读问题待复核")}</h3>
              <div className="question-answer">
                <strong>参考回答 / 导读提示</strong>
                <p>{readingMode === "deep" ? question.deep_answer || readingQuestionAnswer(question) : question.quick_answer || readingQuestionAnswer(question)}</p>
              </div>
              <div className="close-reading-steps">
                <strong>回答步骤</strong>
                <ol>
                  {(question.answer_steps || ["回到对应书信。", "看地点和场景。", "再组织回答。"]).map((step) => (
                    <li key={`${question.question_id}-${step}`}>{step}</li>
                  ))}
                </ol>
              </div>
              <div className="reading-guide-tags">
                {(question.linked_letters || []).slice(0, 4).map((letterId) => (
                  <button
                    className="route-timeline-link"
                    key={`${question.question_id}-${letterId}`}
                    type="button"
                    onClick={() => scrollToChapter(chapters.find((chapter) => chapter.letter_id === letterId)?.chapter_id)}
                  >
                    回到 {letterId}
                  </button>
                ))}
                {(question.place_clues || []).slice(0, 4).map((place) => (
                  <span key={`${question.question_id}-${place}`}>地点：{place}</span>
                ))}
              </div>
              <p>{displayText(question.route_context, "路线语境待人工复核。")}</p>
              <p>{displayText(question.place_context, "地点语境待人工复核。")}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="content-section">
        <h2>辅助数据模块</h2>
        <div className="reading-guide-module-grid compact-module-grid">
          {moduleStatuses.map((item) => (
            <article className="reading-guide-module" key={item.key}>
              <header>
                {item.key === "bookOverview" ? <FileText size={20} /> : null}
                {item.key === "chapterReadingCards" ? <Layers size={20} /> : null}
                {item.key === "keyConcepts" ? <Lightbulb size={20} /> : null}
                {item.key === "quoteIndex" ? <Quote size={20} /> : null}
                {item.key === "readingQuestions" ? <CircleHelp size={20} /> : null}
                <h3>{item.title}</h3>
              </header>
              <p>{item.description}</p>
              <dl>
                <div>
                  <dt>文件</dt>
                  <dd>{item.file}</dd>
                </div>
                <div>
                  <dt>状态</dt>
                  <dd>{loading ? "loading" : item.status}</dd>
                </div>
                <div>
                  <dt>条目数</dt>
                  <dd>{item.count === null ? "不适用" : item.count}</dd>
                </div>
              </dl>
            </article>
          ))}
        </div>
      </section>

      <section className="content-section">
        <h2>5个核心概念</h2>
        <div className="concept-grid">
          {concepts.map((concept: KeyConcept) => (
            <article className="concept-card" key={concept.concept_id}>
              <h3>{displayText(concept.label, "概念待复核")}</h3>
              <p>{displayText(concept.guide_note || concept.description, "概念说明待人工复核。")}</p>
              <p className="muted-line">
                关联书信：{concept.related_letters?.length ?? 0}；复核状态：{concept.review_status || "pending"}
              </p>
            </article>
          ))}
        </div>
      </section>

      <section className="content-section">
        <h2>公开数据下载</h2>
        <div className="download-row">
          <a href={projectDataPath(projectSlug, "book_overview.json")}>book_overview.json</a>
          <a href={projectDataPath(projectSlug, "chapter_reading_cards.json")}>chapter_reading_cards.json</a>
          <a href={projectDataPath(projectSlug, "key_concepts.json")}>key_concepts.json</a>
          <a href={projectDataPath(projectSlug, "quote_index.json")}>quote_index.json</a>
          <a href={projectDataPath(projectSlug, "reading_questions.json")}>reading_questions.json</a>
        </div>
      </section>

      <section className="content-section">
        <details className="version-details">
          <summary>版本信息</summary>
          <dl>
            <div>
              <dt>status</dt>
              <dd>{publicStatus}</dd>
            </div>
            <div>
              <dt>release phase</dt>
              <dd>{releasePhase}</dd>
            </div>
            <div>
              <dt>review status</dt>
              <dd>{reviewStatus}</dd>
            </div>
            <div>
              <dt>schema</dt>
              <dd>{schemaVersion}</dd>
            </div>
          </dl>
        </details>
      </section>

      <button className="back-to-top" type="button" onClick={() => scrollToSection("overview")}>
        回到顶部
      </button>
    </main>
  );
}
