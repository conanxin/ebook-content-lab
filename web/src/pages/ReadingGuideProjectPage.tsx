import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  ArrowLeft,
  BookOpen,
  CircleHelp,
  FileText,
  Layers,
  Lightbulb,
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
  QuoteIndexData,
  ReadingGuideDataBundle,
  ReadingQuestion,
  ReadingQuestionsData,
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
  return refs
    .slice(0, 2)
    .map((ref) => [ref.section_id, ref.letter_id].filter(Boolean).join(" / "))
    .filter(Boolean)
    .join("；") || "结构证据待补充";
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
        title: "章节导读",
        file: "chapter_reading_cards.json",
        status: moduleDataStatus(data, "chapterReadingCards"),
        count: countItems(data, "chapterReadingCards"),
        description: "按 25 封书信展示标题、结构摘要、地点、主题和复核状态。",
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
        title: "引文索引",
        file: "quote_index.json",
        status: moduleDataStatus(data, "quoteIndex"),
        count: countItems(data, "quoteIndex"),
        description: "当前只保留结构引用，不发布原文引文或长摘录。",
      },
      {
        key: "readingQuestions",
        title: "阅读问题",
        file: "reading_questions.json",
        status: moduleDataStatus(data, "readingQuestions"),
        count: countItems(data, "readingQuestions"),
        description: "基于标题、地点和主题生成的轻量阅读提示。",
      },
    ],
    [data],
  );

  const overview = data.bookOverview;
  const chapters = data.chapterReadingCards?.chapters || [];
  const concepts = data.keyConcepts?.concepts || [];
  const quotes = data.quoteIndex?.quotes || [];
  const questions = data.readingQuestions?.questions || [];
  const bookTitle = project.book?.title || project.book_title || overview?.book?.title || "待定书名";
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

      <section className="reading-guide-hero">
        <div className="reading-guide-kicker">
          <BookOpen size={18} />
          reading-guide
        </div>
        <h1>{project.title}</h1>
        <p>
          这是第二个电子书子项目的公开预览版。页面展示的是结构化导读草案：章节卡、概念、问题和结构化引文槽位已经公开，
          但人工复核尚未完成，因此不能视为最终导读或审定内容。
        </p>

        <div className="reading-guide-status-strip" aria-label="public preview status">
          <span className="preview-badge is-draft">Draft</span>
          <span className="preview-badge is-preview">Public Preview</span>
          <span className="preview-badge is-pending">Manual review pending</span>
        </div>

        <dl>
          <div>
            <dt>书名</dt>
            <dd>{bookTitle}</dd>
          </div>
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
          <div>
            <dt>数据状态</dt>
            <dd>{loading ? "加载中" : error ? "加载失败" : "公开预览数据已加载"}</dd>
          </div>
        </dl>
      </section>

      {error ? <section className="state-box error">reading-guide 数据加载失败：{error}</section> : null}

      <section className="content-section reading-guide-warning">
        <AlertTriangle size={20} />
        <div>
          <h2>公开预览说明</h2>
          <p>
            本页面只发布结构化摘要、主题标签和复核任务所需的公开数据，不发布电子书正文、长段摘录或本地来源路径。
            当前 95 条人工复核任务尚未完成，页面内容需要后续人工确认。
          </p>
        </div>
      </section>

      <section className="content-section reading-guide-overview">
        <h2>书籍概览</h2>
        <p>{displayText(overview?.one_sentence_summary, "公开导读草案已生成，概览仍待人工复核。")}</p>
        <p>{displayText(overview?.reading_purpose, "阅读目的仍待人工复核。")}</p>
        <div className="reading-guide-stat-grid">
          <div>
            <strong>{overview?.structure_overview?.body_letter_count ?? chapters.length}</strong>
            <span>章节卡</span>
          </div>
          <div>
            <strong>{concepts.length}</strong>
            <span>核心概念</span>
          </div>
          <div>
            <strong>{questions.length}</strong>
            <span>阅读问题</span>
          </div>
          <div>
            <strong>{quotes.length}</strong>
            <span>结构化引文槽位</span>
          </div>
        </div>
        <div className="reading-guide-two-column">
          <div>
            <h3>如何使用</h3>
            <ul>
              {(overview?.how_to_use || ["先按章节顺序浏览导读卡，再查看概念和问题。"]).map((item) => (
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

      <section className="content-section">
        <h2>25 个章节导读卡</h2>
        <div className="chapter-card-list">
          {chapters.map((chapter: ChapterReadingCard) => (
            <article className="chapter-card" key={chapter.chapter_id}>
              <header>
                <span>{chapter.order ?? "?"}</span>
                <div>
                  <h3>{displayText(chapter.title, "章节标题待复核")}</h3>
                  <p>{chapter.section_id} / {chapter.letter_id}</p>
                </div>
              </header>
              <p>{displayText(chapter.summary, "结构摘要待复核。")}</p>
              <div className="reading-guide-tags">
                <span>地点：{joinList(chapter.places)}</span>
                <span>主题：{joinList(chapter.themes)}</span>
                <span>chunk：{chapter.chunk_count ?? "待复核"}</span>
                <span>复核：{chapter.review_status || "pending"}</span>
              </div>
              <small>结构证据：{evidenceLabel(chapter.evidence_refs)}</small>
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
              <p>{displayText(concept.description, "概念说明待人工复核。")}</p>
              <p className="muted-line">
                关联章节：{concept.related_letters?.length ?? 0}；复核状态：{concept.review_status || "pending"}
              </p>
            </article>
          ))}
        </div>
      </section>

      <section className="content-section quote-policy">
        <header>
          <ShieldCheck size={22} />
          <div>
            <h2>引文索引策略</h2>
            <p>
              当前 quote index 使用 <code>{data.quoteIndex?.quote_mode || "structural_no_quote"}</code>：
              只保留章节和书信级结构引用，不发布原文句子。后续如需加入短摘，必须经过人工复核。
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

      <section className="content-section">
        <h2>26 个阅读问题</h2>
        <div className="question-list">
          {questions.map((question: ReadingQuestion) => (
            <article className="question-card" key={question.question_id}>
              <h3>{displayText(question.question, "阅读问题待复核")}</h3>
              <p>{displayText(question.basis, "结构依据待复核。")}</p>
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
    </main>
  );
}
