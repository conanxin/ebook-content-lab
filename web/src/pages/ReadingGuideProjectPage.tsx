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
  return values.join("、");
}

function displayText(value: string | null | undefined, fallback = "待人工复核"): string {
  const trimmed = value?.trim();
  return trimmed ? trimmed : fallback;
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

function placeName(place: PlaceThenNow): string {
  return place.place || place.place_name || place.name || "地点待复核";
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
        description: "书籍定位、阅读目的、结构概览、使用方式和限制说明。",
      },
      {
        key: "chapterReadingCards",
        title: "书信导读",
        file: "chapter_reading_cards.json",
        status: moduleDataStatus(data, "chapterReadingCards"),
        count: countItems(data, "chapterReadingCards"),
        description: "25 封书信的信封卡片，展示地点、路线、主题和导读摘要。",
      },
      {
        key: "keyConcepts",
        title: "核心概念",
        file: "key_concepts.json",
        status: moduleDataStatus(data, "keyConcepts"),
        count: countItems(data, "keyConcepts"),
        description: "由结构化主题聚合出的概念草案，等待人工细读修订。",
      },
      {
        key: "quoteIndex",
        title: "引文状态",
        file: "quote_index.json",
        status: moduleDataStatus(data, "quoteIndex"),
        count: countItems(data, "quoteIndex"),
        description: "暂不公开原文摘录，只保留后续人工复核用的结构定位槽位。",
      },
      {
        key: "readingQuestions",
        title: "阅读问题",
        file: "reading_questions.json",
        status: moduleDataStatus(data, "readingQuestions"),
        count: countItems(data, "readingQuestions"),
        description: "每个问题附参考回答，基于标题、地点和结构化主题生成。",
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
      pending_places: (chapter.places || []).filter((name) =>
        !placeThenNow.some((place) => placeName(place) === name && place.source_status === "public_source"),
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
    }));
  const projectTitle = overview?.display_title || project.title || "《旅行人信札》阅读导览";
  const bookTitle = overview?.book?.title || project.book?.title || project.book_title || "《旅行人信札》";
  const subtitle = overview?.subtitle || project.subtitle || "25 封旅行书信的路线、地点与主题导读";
  const schemaVersion = overview?.schema_version || data.chapterReadingCards?.schema_version || "reading-guide.v0.2";
  const publicStatus = overview?.status || project.status || "draft";
  const releasePhase = overview?.release_phase || "public-preview";
  const reviewStatus = overview?.review_status || "manual-review-pending";

  return (
    <main className="portal-shell reading-guide-page">
      <a className="back-link" href="#/">
        <ArrowLeft size={16} />
        返回首页
      </a>

      <section className="reading-guide-hero letter-hero">
        <div className="reading-guide-kicker">
          <BookOpen size={18} />
          旅行书信阅读导览
        </div>
        <h1>{projectTitle}</h1>
        <p className="reading-guide-subtitle">{subtitle}</p>
        <p>
          这是一份公开预览版导读：先把《旅行人信札》的 25 封旅行书信整理成路线、地点、主题和问题线索，
          方便读者进入文本。内容仍在人工复核中，不是最终审定版。
        </p>

        <div className="reading-guide-status-strip" aria-label="public preview status">
          <span className="preview-badge is-draft">Draft</span>
          <span className="preview-badge is-preview">Public Preview</span>
          <span className="preview-badge is-pending">Manual review pending</span>
        </div>

        <div className="reading-guide-stat-grid hero-stat-grid">
          <div>
            <strong>{chapters.length || 25}</strong>
            <span>封旅行书信</span>
          </div>
          <div>
            <strong>{places.length || "待复核"}</strong>
            <span>个地点线索</span>
          </div>
          <div>
            <strong>{concepts.length || 5}</strong>
            <span>个主题概念</span>
          </div>
          <div>
            <strong>{questions.length || 26}</strong>
            <span>个阅读问题</span>
          </div>
        </div>

        <div className="reading-guide-route-summary">
          <MapPinned size={18} />
          <span>主要地点线索：{joinList(places.slice(0, 12), "待人工复核")}</span>
        </div>
      </section>

      {error ? <section className="state-box error">reading-guide 数据加载失败：{error}</section> : null}

      <section className="content-section reading-guide-warning">
        <AlertTriangle size={20} />
        <div>
          <h2>公开预览说明</h2>
          <p>
            本页面发布的是原创导读草案和结构化线索，不发布电子书正文、长段摘录或本地来源路径。
            当前 95 条人工复核任务尚未完成，所有导读摘要和参考回答都需要后续人工确认。
          </p>
        </div>
      </section>

      <nav className="reading-guide-nav" aria-label="阅读导览导航">
        <div className="section-anchor-list">
          {[
            ["overview", "概览"],
            ["route-timeline", "旅行路线时间线"],
            ["then-now", "昔日旅程与今日景点"],
            ["letters", "25 封信"],
            ["quote-clues", "原文摘录与阅读线索"],
            ["questions", "阅读问题"],
          ].map(([sectionId, label]) => (
            <button className="reading-mode-toggle" key={sectionId} type="button" onClick={() => scrollToSection(sectionId)}>
              {label}
            </button>
          ))}
        </div>
      </nav>

      <section className="content-section reading-guide-overview" id="overview">
        <h2>全书导读</h2>
        <p>{displayText(overview?.one_sentence_summary, "公开导读草案已生成，概览仍待人工复核。")}</p>
        <p>{displayText(overview?.reading_purpose, "阅读目的仍待人工复核。")}</p>
        <div className="reading-flow-panel">
          <h3>原文精读怎么走</h3>
          <p>
            {displayText(
              overview?.close_reading_overview?.method,
              "按“摘录或原文线索 → 场景 → 地点 → 昔日/今日对照 → 问题 → 回答”的顺序精读。",
            )}
          </p>
          <div className="filter-chip-row">
            <span>先顺读时间线</span>
            <span>再看地点路线索引</span>
            <span>最后展开信封做精读</span>
          </div>
        </div>
        <div className="reading-guide-two-column">
          <div>
            <h3>如何使用</h3>
            <ul>
              {(overview?.how_to_use || ["先按书信顺序浏览信封卡片，再查看概念和问题。"]).map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
          <div>
            <h3>限制说明</h3>
            <ul>
              {(overview?.limitations || ["当前版本仍是 draft，需人工复核。"]).map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
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
                <p>{displayText(node.now_context, "今日对照待复核。")}</p>
                <div className="route-timeline-places">
                  {(node.primary_places || []).map((place) => (
                    <span key={`${node.chapter_id}-${place}`}>{place}</span>
                  ))}
                </div>
                <button className="route-timeline-link" type="button" onClick={() => scrollToChapter(node.chapter_id)}>
                  跳到本封信
                </button>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="content-section paper-map-section">
        <h2>地图式路线索引</h2>
        <p>这是纸面地图式的地点路线索引：先按书信顺序看地点节点，再区分已补公开来源和待补来源。</p>
        <div className="paper-map-route">
          {placeRouteIndex.slice(0, 36).map((place, index) => (
            <article className="paper-map-node" key={`${place.place_name}-${index}`}>
              <span className={`place-source-badge ${sourceStatusClass(place.source_status)}`}>
                {sourceStatusLabel(place.source_status)}
              </span>
              <strong>{place.place_name}</strong>
              <small>第{joinList((place.reading_order || []).map(String), "?")}封</small>
            </article>
          ))}
        </div>
        <div className="place-route-index">
          {placeRouteIndex.map((place) => (
            <article className="place-route-index-item" key={place.place_name}>
              <h3>{place.place_name}</h3>
              <p>{displayText(place.today_reading, "今日读法待复核。")}</p>
              <div className="reading-guide-tags">
                <span>{sourceStatusLabel(place.source_status)}</span>
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
        <div className="place-overview-panel">
          <div>
            <strong>{placeStats?.total_place_count ?? placeThenNow.length}</strong>
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
            <strong>{routeIndex.length}</strong>
            <span>书信路线索引</span>
          </div>
        </div>

        <div className="route-index" aria-label="25 封书信路线索引">
          {routeIndex.map((item) => (
            <button
              className="route-index-item"
              key={item.chapter_id || item.letter_id || item.title}
              type="button"
              onClick={() => scrollToChapter(item.chapter_id)}
            >
              <strong>第{item.order ?? "?"}封</strong>
              <span>{displayText(item.title, "书信标题待复核")}</span>
              <small>
                {joinList(item.source_covered_places, "暂无已补来源")} / {joinList(item.pending_places, "无待补来源")}
              </small>
            </button>
          ))}
        </div>

        <div className="place-comparison-grid">
          {placeThenNow.map((place) => (
            <article className="place-now-source place-comparison-card" key={placeName(place)}>
              <header>
                <h3>{placeName(place)}</h3>
                <span className={`place-source-badge ${sourceStatusClass(place.source_status)}`}>
                  {sourceStatusLabel(place.source_status)}
                </span>
              </header>
              <p>{displayText(place.now_context || place.today_reading, "今日景点信息待公开来源复核。")}</p>
              <p>{displayText(place.change_note, "当年旅行经验与今日景点状态的差异仍待补充。")}</p>
              <dl>
                <div>
                  <dt>书信位置</dt>
                  <dd>{joinList(place.appears_in_letters || place.letters, "待复核")}</dd>
                </div>
                <div>
                  <dt>当年语境</dt>
                  <dd>{joinList(place.then_context, "书中语境待人工复核")}</dd>
                </div>
                <div>
                  <dt>来源类型</dt>
                  <dd>{sourceTypeLabel(place.source_type)}</dd>
                </div>
                <div>
                  <dt>今日来源</dt>
                  <dd>
                    {place.source_url ? (
                      <a href={place.source_url} target="_blank" rel="noreferrer">
                        {place.source_name || "公开来源"}
                      </a>
                    ) : (
                      place.source_name || "待补充公开来源"
                    )}
                  </dd>
                </div>
                <div>
                  <dt>复核状态</dt>
                  <dd>{displayText(place.source_review_note || place.review_status || place.source_status, "待补充公开来源")}</dd>
                </div>
              </dl>
            </article>
          ))}
        </div>
      </section>

      <section className="content-section">
        <h2>内容模块</h2>
        <div className="reading-guide-module-grid">
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

      <section className="content-section" id="letters">
        <h2>25 封旅行书信</h2>
        <div className="letter-envelope-list">
          {chapters.map((chapter: ChapterReadingCard) => (
            <article className="letter-envelope-card" id={chapter.chapter_id} key={chapter.chapter_id}>
              <div className="letter-flap" aria-hidden="true" />
              <header>
                <span className="letter-number">{chapter.order ?? "?"}</span>
                <div>
                  <p className="letter-stamp">{chapter.letter_stamp || "日期待复核"}</p>
                  <h3>{displayText(chapter.title, "章节标题待复核")}</h3>
                </div>
              </header>
              <div className="letter-route">
                <MapPinned size={15} />
                <span>{chapter.route_label || joinList(chapter.places)}</span>
              </div>
              <div className="letter-body">
                <p className="letter-source-summary">
                  {displayText(chapter.source_informed_summary || chapter.letter_summary || chapter.summary, "本封信导读摘要待复核。")}
                </p>
                <p>{displayText(chapter.route_note, "路线说明待复核。")}</p>
                <p>{displayText(chapter.reading_focus_expanded || chapter.reading_focus, "阅读重点待复核。")}</p>
              </div>
              <details className="letter-answer">
                <summary>展开阅读线索</summary>
                <div className="letter-original-clues">
                  <h4>原文摘录与阅读线索</h4>
                  {(chapter.original_excerpt || []).map((item, index) => (
                    <blockquote className="letter-original-excerpt" key={`${chapter.chapter_id}-excerpt-${index}`}>
                      <p>{displayText(item.excerpt, "原文线索待复核。")}</p>
                      <cite>{displayText(item.note, "这条线索用于辅助阅读，不替代原书。")}</cite>
                    </blockquote>
                  ))}
                </div>
                <div className="close-reading-panel">
                  <h4>原文精读</h4>
                  <div className="close-reading-excerpt">
                    <strong>摘录焦点</strong>
                    <p>{displayText(chapter.close_reading?.excerpt_focus, "摘录焦点待人工复核。")}</p>
                  </div>
                  <div className="close-reading-explanation">
                    <strong>为什么值得注意</strong>
                    <p>{displayText(chapter.close_reading?.why_it_matters, "精读说明待人工复核。")}</p>
                  </div>
                  <div className="close-reading-steps">
                    <strong>精读步骤</strong>
                    <ol>
                      {(chapter.reading_steps || ["先看路线。", "再读线索。", "最后回答问题。"]).map((step) => (
                        <li key={step}>{step}</li>
                      ))}
                    </ol>
                  </div>
                  <div className="close-reading-question">
                    <strong>关联问题</strong>
                    {(chapter.linked_questions || []).map((questionId) => {
                      const question = questionsById.get(questionId);
                      return (
                        <button className="route-timeline-link" key={questionId} type="button" onClick={() => scrollToSection("questions")}>
                          {question?.question || questionId}
                        </button>
                      );
                    })}
                  </div>
                  <div className="close-reading-answer">
                    <strong>参考回答</strong>
                    <p>{displayText(chapter.close_reading?.answer_bridge || chapter.answer_hint_expanded, "参考回答待人工复核。")}</p>
                  </div>
                </div>
                <div className="letter-scene-notes">
                  <h4>原书场景线索</h4>
                  <ul>
                    {(chapter.original_scene_notes || ["场景线索待人工复核。"]).map((note) => (
                      <li key={note}>{note}</li>
                    ))}
                  </ul>
                </div>
                <div className="letter-then-now">
                  <h4>当年路线 / 今日对照</h4>
                  <p>{displayText(chapter.route_then?.note, "当年路线说明待复核。")}</p>
                  <p>{displayText(chapter.then_now_comparison, "昔日旅程与今日景点对照待补充。")}</p>
                  <div className="reading-guide-tags">
                    {(chapter.route_now || []).map((place) => (
                      <span className={`place-source-badge ${sourceStatusClass(place.source_status)}`} key={`${chapter.chapter_id}-${placeName(place)}`}>
                        {placeName(place)}：{sourceStatusLabel(place.source_status)}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="letter-answer-expanded">
                  <h4>对应问题与参考回答</h4>
                  <p>{displayText(chapter.answer_hint_expanded, "参考回答待人工复核。")}</p>
                </div>
                <div className="reading-guide-tags">
                  <span>地点：{joinList(chapter.places)}</span>
                  <span>主题：{joinList(chapter.themes)}</span>
                  <span>chunk：{chapter.chunk_count ?? "待复核"}</span>
                  <span>复核：{chapter.review_status || "pending"}</span>
                </div>
                <small>结构证据：{evidenceLabel(chapter.evidence_refs)}</small>
                <p>{displayText(chapter.review_notice, "Public preview：本卡片仍待人工复核。")}</p>
              </details>
            </article>
          ))}
        </div>
      </section>

      <section className="content-section">
        <h2>5 个核心概念</h2>
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

      <section className="content-section quote-policy" id="quote-clues" data-quote-mode={data.quoteIndex?.quote_mode || "structural_no_quote"}>
        <header>
          <ShieldCheck size={22} />
          <div>
            <h2>原文摘录与阅读线索</h2>
            <p>
              {data.quoteIndex?.reader_note ||
                "当前页面作为个人阅读导览，补充来自原书的摘录、场景摘要、地点线索和阅读提示。页面仍处于公开预览与人工复核阶段。"}
            </p>
          </div>
        </header>
        <div className="reading-guide-stat-grid">
          <div>
            <strong>{quotes.length}</strong>
            <span>结构化槽位</span>
          </div>
          <div>
            <strong>0</strong>
            <span>公开原文引文</span>
          </div>
        </div>
      </section>

      <section className="content-section" id="questions">
        <h2>26 个阅读问题与参考回答</h2>
        <div className="question-list">
          {questions.map((question: ReadingQuestion) => (
            <article className="question-card" key={question.question_id}>
              <h3>{displayText(question.question, "阅读问题待复核")}</h3>
              <div className="question-answer">
                <strong>参考回答 / 导读提示</strong>
                <p>
                  {displayText(
                    question.close_reading_answer ||
                      question.answer_hint_expanded ||
                      question.answer_hint ||
                      question.reference_answer ||
                      question.guide_answer,
                    "参考回答待人工复核。",
                  )}
                </p>
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
                {(question.source_clues || []).slice(0, 2).map((clue, index) => (
                  <span key={`${question.question_id}-clue-${index}`}>线索：{clue}</span>
                ))}
              </div>
              <p>{displayText(question.route_context, "路线语境待人工复核。")}</p>
              <p>{displayText(question.place_context, "地点语境待人工复核。")}</p>
              <p>{displayText(question.then_now_hint, "今日对照待补充公开来源。")}</p>
              <p>{displayText(question.basis, "基于标题、地点线索与结构化主题生成，待人工复核。")}</p>
              <span>
                {question.scope || "scope pending"} {question.section_id ? ` / ${question.section_id}` : ""}
              </span>
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
    </main>
  );
}
