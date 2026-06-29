import { useEffect, useMemo, useState } from "react";
import {
  ArrowLeft,
  BookOpen,
  CircleHelp,
  FileText,
  Layers,
  Lightbulb,
  Quote,
} from "lucide-react";
import type { ProjectMetadata } from "../types/project";
import type {
  BookOverviewData,
  ChapterReadingCardsData,
  KeyConceptsData,
  QuoteIndexData,
  ReadingGuideDataBundle,
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

const PLACEHOLDER = "待第二本电子书导入后生成";

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
        description: "全书定位、阅读目的、结构概览和使用说明。",
      },
      {
        key: "chapterReadingCards",
        title: "章节导读",
        file: "chapter_reading_cards.json",
        status: moduleDataStatus(data, "chapterReadingCards"),
        count: countItems(data, "chapterReadingCards"),
        description: "按章节生成摘要、关键点、阅读提示和证据引用。",
      },
      {
        key: "keyConcepts",
        title: "核心概念",
        file: "key_concepts.json",
        status: moduleDataStatus(data, "keyConcepts"),
        count: countItems(data, "keyConcepts"),
        description: "整理术语、主题、人物或概念线索。",
      },
      {
        key: "quoteIndex",
        title: "引文索引",
        file: "quote_index.json",
        status: moduleDataStatus(data, "quoteIndex"),
        count: countItems(data, "quoteIndex"),
        description: "只保存短引文、页码和说明，不公开 OCR 全文。",
      },
      {
        key: "readingQuestions",
        title: "阅读问题",
        file: "reading_questions.json",
        status: moduleDataStatus(data, "readingQuestions"),
        count: countItems(data, "readingQuestions"),
        description: "生成理解、讨论、研究和反思问题。",
      },
    ],
    [data],
  );

  const overview = data.bookOverview;
  const bookTitle = project.book?.title || project.book_title || overview?.book?.title || "书名未定";

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
          当前项目为 reading-guide 草稿，尚未导入电子书。导入 PDF、完成 OCR 和证据抽取后，
          这里会展示全书导读、章节导读、核心概念、引文索引和阅读问题。
        </p>
        <dl>
          <div>
            <dt>书名</dt>
            <dd>{bookTitle}</dd>
          </div>
          <div>
            <dt>status</dt>
            <dd>{project.status}</dd>
          </div>
          <div>
            <dt>当前数据状态</dt>
            <dd>{loading ? "正在加载 draft 数据" : error ? "公开 draft 数据加载失败" : "draft 数据已就绪"}</dd>
          </div>
        </dl>
      </section>

      {error ? (
        <section className="state-box error">reading-guide 数据加载失败：{error}</section>
      ) : null}

      <section className="content-section reading-guide-notice">
        <h2>待导入电子书</h2>
        <p>
          该项目目前只包含通用数据骨架，没有 PDF、OCR 文本或书中内容。所有内容字段均保持草稿状态：
          {overview?.one_sentence_summary || PLACEHOLDER}。
        </p>
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
        <h2>后续生成流程</h2>
        <ol className="reading-guide-steps">
          <li>把第二本电子书放入项目 private/source 目录。</li>
          <li>运行 OCR，并把 OCR 全文保留在 private 目录。</li>
          <li>识别书名、作者、章节结构和内容类型。</li>
          <li>生成章节导读、核心概念、短引文索引和阅读问题。</li>
          <li>为每条判断补充页码、短摘和说明，再运行 reading-guide 校验。</li>
        </ol>
      </section>
    </main>
  );
}
