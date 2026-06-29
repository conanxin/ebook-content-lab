import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import L from "leaflet";
import { AlertTriangle, Download, FileJson, MapPinned, Route, Search } from "lucide-react";
import type { ProjectMetadata } from "../types/project";
import type { BookOverview, BookTheme, PlaceIndexItem, SegmentReadingCard } from "../types/contentDepth";
import type { BookRef, CoordinateConfidence, PlacePoint, RouteSegment, WalkableBlock } from "../types/route";
import { getActiveTab, projectTabUrl, setProjectTab, type ProjectTab } from "../utils/hashRoute";
import { projectDataPath } from "../utils/paths";

const projectTabs: Array<{ key: ProjectTab; label: string }> = [
  { key: "overview", label: "总览" },
  { key: "map", label: "地图路线" },
  { key: "reading-detail", label: "路线细读" },
  { key: "place-index", label: "书中地名" },
  { key: "field-guide", label: "复走说明" },
];

type FilterKey =
  | "all"
  | "walked"
  | "mixed"
  | "vehicle"
  | "gaps"
  | "do_not_connect"
  | "approximate"
  | "needs_field_check"
  | "unspecified"
  | "needs_review";

const filterLabels: Record<FilterKey, string> = {
  all: "全部",
  walked: "书中明确徒步",
  mixed: "混合 / 补走",
  vehicle: "乘车 / 非徒步",
  gaps: "有断点",
  do_not_connect: "不应连接 GPX",
  approximate: "坐标 approximate",
  needs_field_check: "needs_field_check",
  unspecified: "书中未明示字段",
  needs_review: "需要人工复核",
};

const routeColors = ["#2f6f7e", "#9a6a19", "#7b4f9f", "#3d7b45", "#b24a3a"];

const markerIcon = L.divIcon({
  className: "route-marker",
  html: "<span></span>",
  iconSize: [16, 16],
  iconAnchor: [8, 8],
});

const gapIcon = L.divIcon({
  className: "gap-marker",
  html: "<span>!</span>",
  iconSize: [24, 24],
  iconAnchor: [12, 12],
});

function pointHasCoord(point: PlacePoint): point is PlacePoint & { lat: number; lng: number } {
  return typeof point.lat === "number" && typeof point.lng === "number";
}

function segmentPoints(segment: RouteSegment) {
  return [segment.start, ...segment.via, segment.end];
}

function segmentCoordinateState(segment: RouteSegment): CoordinateConfidence {
  const states = segmentPoints(segment).map((point) => point.coordinate_confidence || "missing");
  if (states.includes("missing")) return "missing";
  if (states.includes("approximate")) return "approximate";
  return "verified";
}

function hasUnspecified(value: unknown): boolean {
  if (value === null || value === undefined || value === "") return true;
  if (Array.isArray(value)) return value.length === 0 || value.some(hasUnspecified);
  return String(value).includes("书中未明示");
}

function segmentHasUnspecified(segment: RouteSegment) {
  return [
    segment.route_summary,
    segment.walking_directions,
    segment.terrain,
    segment.roads_or_paths,
    segment.water_sources,
    segment.resupply,
    segment.lodging,
    segment.risks_or_notes,
    segment.distance_km_book,
  ].some(hasUnspecified);
}

function segmentNeedsReview(segment: RouteSegment) {
  return (
    segment.confidence === "needs_review" ||
    segment.evidence_status !== "pass" ||
    (segment.evidence_notes?.length ?? 0) > 0 ||
    segment.review_notes.length > 0 ||
    (segment.gap_notes?.length ?? 0) > 0 ||
    segment.modern_followability === "needs_field_check"
  );
}

function matchesFilter(segment: RouteSegment, filter: FilterKey) {
  if (filter === "all") return true;
  if (filter === "walked") return segment.movement_type === "walked";
  if (filter === "mixed") return segment.movement_type === "mixed";
  if (filter === "vehicle") return segment.movement_type === "vehicle" || segment.movement_type === "unclear";
  if (filter === "gaps") return ["gap_before", "gap_after", "isolated"].includes(String(segment.continuity_status));
  if (filter === "do_not_connect") return Boolean(segment.do_not_connect_in_gpx);
  if (filter === "approximate") return segmentCoordinateState(segment) === "approximate";
  if (filter === "needs_field_check") return segment.modern_followability === "needs_field_check";
  if (filter === "unspecified") return segmentHasUnspecified(segment);
  if (filter === "needs_review") return segmentNeedsReview(segment);
  return true;
}

function valueText(value: unknown): string {
  if (value === null || value === undefined || value === "") return "书中未明示";
  if (Array.isArray(value)) {
    if (value.length === 0) return "书中未明示";
    return value.map(valueText).join("；");
  }
  return String(value);
}

function confidenceLabel(value: string | undefined) {
  if (value === "verified") return "较明确";
  if (value === "approximate") return "大致确认";
  if (value === "missing") return "缺坐标";
  if (value === "needs_review") return "需要复核";
  return value || "书中未明示";
}

function movementLabel(value: string | undefined) {
  if (value === "walked") return "书中明确徒步";
  if (value === "vehicle") return "乘车 / 非徒步";
  if (value === "mixed") return "混合 / 补走";
  if (value === "inferred") return "推断徒步";
  if (value === "unclear") return "不明";
  return valueText(value);
}

function continuityLabel(value: string | undefined) {
  if (value === "continuous") return "连续";
  if (value === "gap_before") return "前段有断点";
  if (value === "gap_after") return "后段有断点";
  if (value === "isolated") return "孤立段";
  if (value === "unclear") return "连续性不明";
  return valueText(value);
}

function walkabilityLabel(value: string | undefined) {
  if (value === "book_walkable") return "可按书中徒步描述理解";
  if (value === "partially_walkable") return "部分可按书中描述走";
  if (value === "not_walkable_as_written") return "不可完整照走";
  if (value === "needs_review") return "需复核";
  return valueText(value);
}

function followabilityLabel(value: string | undefined) {
  if (value === "likely_followable") return "较可跟随";
  if (value === "approximate_only") return "只能大致参考";
  if (value === "not_enough_information") return "信息不足";
  if (value === "needs_field_check") return "需要现代路况核验";
  return valueText(value);
}

function statusClass(value: unknown) {
  if (
    value === true ||
    value === "mixed" ||
    value === "vehicle" ||
    value === "unclear" ||
    value === "gap_before" ||
    value === "gap_after" ||
    value === "isolated" ||
    value === "needs_field_check" ||
    value === "needs_review" ||
    value === "warning"
  ) {
    return "is-warning";
  }
  if (value === "walked" || value === "continuous" || value === "book_walkable" || value === "pass") {
    return "is-good";
  }
  return "";
}

async function fetchJson<T>(url: string): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`${url} ${response.status}`);
  return response.json() as Promise<T>;
}

function useRouteData(projectSlug: string) {
  const [segments, setSegments] = useState<RouteSegment[]>([]);
  const [routeGeoJson, setRouteGeoJson] = useState<GeoJSON.FeatureCollection | null>(null);
  const [placesGeoJson, setPlacesGeoJson] = useState<GeoJSON.FeatureCollection | null>(null);
  const [blocks, setBlocks] = useState<WalkableBlock[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    Promise.all([
      fetchJson<RouteSegment[]>(projectDataPath(projectSlug, "route_segments.json")),
      fetchJson<GeoJSON.FeatureCollection>(projectDataPath(projectSlug, "route.geojson")),
      fetchJson<GeoJSON.FeatureCollection>(projectDataPath(projectSlug, "route_places.geojson")),
      fetchJson<WalkableBlock[]>(projectDataPath(projectSlug, "route_walkable_blocks.json")),
    ])
      .then(([segmentData, routeData, placeData, blockData]) => {
        if (!alive) return;
        setSegments(segmentData);
        setRouteGeoJson(routeData);
        setPlacesGeoJson(placeData);
        setBlocks(blockData);
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

  return { segments, routeGeoJson, placesGeoJson, blocks, error, loading };
}

function useContentDepth(projectSlug: string) {
  const [overview, setOverview] = useState<BookOverview | null>(null);
  const [readingCards, setReadingCards] = useState<SegmentReadingCard[]>([]);
  const [placeIndex, setPlaceIndex] = useState<PlaceIndexItem[]>([]);
  const [themes, setThemes] = useState<BookTheme[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    Promise.all([
      fetchJson<BookOverview>(projectDataPath(projectSlug, "book_overview.json")),
      fetchJson<SegmentReadingCard[]>(projectDataPath(projectSlug, "segment_reading_cards.json")),
      fetchJson<PlaceIndexItem[]>(projectDataPath(projectSlug, "place_index.json")),
      fetchJson<BookTheme[]>(projectDataPath(projectSlug, "book_themes.json")),
    ])
      .then(([overviewData, cardData, placeData, themeData]) => {
        if (!alive) return;
        setOverview(overviewData);
        setReadingCards(cardData);
        setPlaceIndex(placeData);
        setThemes(themeData);
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

  return { overview, readingCards, placeIndex, themes, error, loading };
}

function buildBlockMap(blocks: WalkableBlock[]) {
  const map = new Map<string, WalkableBlock>();
  blocks.forEach((block) => {
    block.segment_ids.forEach((id) => map.set(id, block));
  });
  return map;
}

function segmentLatLngBounds(segment: RouteSegment) {
  const bounds = L.latLngBounds([]);
  segmentPoints(segment).forEach((point) => {
    if (pointHasCoord(point)) bounds.extend([point.lat, point.lng]);
  });
  return bounds;
}

interface MapPanelProps {
  segments: RouteSegment[];
  routeGeoJson: GeoJSON.FeatureCollection | null;
  placesGeoJson: GeoJSON.FeatureCollection | null;
  selectedId: string | null;
  onSelect: (segmentId: string) => void;
}

function MapPanel({ segments, routeGeoJson, placesGeoJson, selectedId, onSelect }: MapPanelProps) {
  const mapRef = useRef<L.Map | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const layerRef = useRef<L.LayerGroup | null>(null);
  const segmentBoundsRef = useRef<Map<string, L.LatLngBounds>>(new Map());

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const map = L.map(containerRef.current, {
      zoomControl: false,
      scrollWheelZoom: true,
    }).setView([41.0, 116.0], 7);
    L.control.zoom({ position: "bottomright" }).addTo(map);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      maxZoom: 18,
    }).addTo(map);
    mapRef.current = map;
    layerRef.current = L.layerGroup().addTo(map);
    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    const layer = layerRef.current;
    if (!map || !layer) return;
    layer.clearLayers();
    segmentBoundsRef.current.clear();
    const allBounds = L.latLngBounds([]);

    segments.forEach((segment) => {
      const bounds = segmentLatLngBounds(segment);
      if (bounds.isValid()) {
        segmentBoundsRef.current.set(segment.id, bounds);
        allBounds.extend(bounds);
      }
    });

    if (routeGeoJson) {
      L.geoJSON(routeGeoJson, {
        filter: (feature) => Boolean(feature.geometry),
        style: (feature) => {
          const order = Number(feature?.properties?.order || 1);
          return {
            color: routeColors[(order - 1) % routeColors.length],
            weight: feature?.properties?.segment_id === selectedId ? 6 : 4,
            opacity: feature?.properties?.segment_id === selectedId ? 0.95 : 0.68,
          };
        },
        onEachFeature: (feature, featureLayer) => {
          const props = feature.properties || {};
          const segmentId = String(props.segment_id || "");
          const bounds = (featureLayer as L.Polyline).getBounds?.();
          if (bounds?.isValid()) {
            segmentBoundsRef.current.set(segmentId, bounds);
            allBounds.extend(bounds);
          }
          featureLayer.on("click", () => {
            onSelect(segmentId);
            document.getElementById(segmentId)?.scrollIntoView({ behavior: "smooth", block: "start" });
          });
          const warnings = [
            props.do_not_connect_in_gpx ? "不应连接 GPX" : "",
            props.missing_geometry ? "缺少连续几何线" : "",
            props.route_gap ? "存在断点" : "",
          ]
            .filter(Boolean)
            .join("；");
          featureLayer.bindPopup(
            `<strong>${props.title || ""}</strong><br/>${props.start_name || ""} -> ${props.end_name || ""}<br/>页码：${
              Array.isArray(props.pages) ? props.pages.join(", ") : ""
            }<br/>${warnings ? `<b>${warnings}</b><br/>` : ""}证据：${props.confidence || ""}`,
          );
        },
      }).addTo(layer);
    }

    if (placesGeoJson) {
      L.geoJSON(placesGeoJson, {
        pointToLayer: (_feature, latlng) => L.marker(latlng, { icon: markerIcon }),
        onEachFeature: (feature, featureLayer) => {
          const props = feature.properties || {};
          featureLayer.bindPopup(
            `<strong>${props.name || ""}</strong><br/>${props.role || ""}<br/>${props.coordinate_confidence || ""}<br/>${
              props.coordinate_source || ""
            }`,
          );
        },
      }).addTo(layer);
    }

    segments
      .filter((segment) => segment.do_not_connect_in_gpx || ["gap_before", "gap_after", "isolated"].includes(String(segment.continuity_status)))
      .forEach((segment) => {
        const anchor = segmentPoints(segment).find(pointHasCoord);
        if (!anchor || !pointHasCoord(anchor)) return;
        const marker = L.marker([anchor.lat, anchor.lng], { icon: gapIcon });
        marker.on("click", () => {
          onSelect(segment.id);
          document.getElementById(segment.id)?.scrollIntoView({ behavior: "smooth", block: "start" });
        });
        marker.bindPopup(
          `<strong>${segment.title}</strong><br/>断点/复走提示<br/>${
            segment.do_not_connect_in_gpx
              ? "该段不应连接 GPX；只导出 waypoint；GeoJSON missing_geometry=true。"
              : "该段与前后段存在断点提示。"
          }`
        );
        marker.addTo(layer);
      });

    if (allBounds.isValid()) {
      map.fitBounds(allBounds.pad(0.12), { animate: false });
    }
  }, [routeGeoJson, placesGeoJson, segments, selectedId, onSelect]);

  useEffect(() => {
    if (!selectedId || !mapRef.current) return;
    const bounds = segmentBoundsRef.current.get(selectedId);
    if (bounds?.isValid()) {
      mapRef.current.fitBounds(bounds.pad(0.28), { maxZoom: 12 });
    }
  }, [selectedId]);

  const gapCount = segments.filter((segment) => segment.do_not_connect_in_gpx).length;
  const fieldCheckCount = segments.filter((segment) => segment.modern_followability === "needs_field_check").length;

  return (
    <section className="map-panel" aria-label="路线地图">
      <div className="map-toolbar">
        <div>
          <strong>路线地图</strong>
          <span>{segments.length} 段，{gapCount} 段不连接 GPX</span>
        </div>
        {fieldCheckCount > 0 && (
          <span className="map-warning">
            <AlertTriangle size={15} />
            {fieldCheckCount} 段需现代路况核验
          </span>
        )}
      </div>
      <div ref={containerRef} className="map-canvas" />
    </section>
  );
}

function Legend() {
  const items = [
    ["good", "书中明确徒步"],
    ["warn", "混合 / 补走"],
    ["danger", "乘车 / 非徒步"],
    ["good", "连续"],
    ["warn", "有断点"],
    ["danger", "不应连接 GPX"],
    ["warn", "坐标大致"],
    ["danger", "需要现代路况核验"],
    ["good", "证据已通过"],
    ["warn", "需人工复核"],
  ];
  return (
    <section className="legend-panel" aria-label="图例">
      <strong>图例</strong>
      <div>
        {items.map(([tone, label]) => (
          <span key={label} className={`legend-item ${tone}`}>
            <i />
            {label}
          </span>
        ))}
      </div>
    </section>
  );
}

interface RewalkSummaryProps {
  segments: RouteSegment[];
  blocks: WalkableBlock[];
}

function idList(items: RouteSegment[]) {
  return items.length > 0 ? items.map((segment) => `${segment.id} ${segment.title}`).join("；") : "无";
}

function RewalkSummary({ segments, blocks }: RewalkSummaryProps) {
  const walked = segments.filter((segment) => segment.movement_type === "walked");
  const mixed = segments.filter((segment) => ["mixed", "vehicle", "unclear"].includes(String(segment.movement_type)));
  const doNotConnect = segments.filter((segment) => segment.do_not_connect_in_gpx);
  const waypointOnly = doNotConnect;
  const approximate = segments.filter(
    (segment) => segmentCoordinateState(segment) === "approximate" || segment.modern_followability === "approximate_only",
  );
  const needsCheck = segments.filter(
    (segment) => segment.modern_followability === "needs_field_check" || segmentNeedsReview(segment),
  );
  return (
    <section className="rewalk-panel">
      <div className="panel-heading">
        <h2>复走提示</h2>
        <p>按书中线索整理的徒步路线图解，不是未经核验的户外导航路线。</p>
      </div>
      <div className="rewalk-grid">
        <SummaryItem label="书中明确徒步" value={idList(walked)} />
        <SummaryItem label="mixed / vehicle / unclear" value={idList(mixed)} />
        <SummaryItem label="不能直接作为连续 GPX" value={idList(doNotConnect)} />
        <SummaryItem label="只导出 waypoint" value={idList(waypointOnly)} />
        <SummaryItem label="文本解读或大致参考" value={idList(approximate)} />
        <SummaryItem label="需核对原书或现代路况" value={idList(needsCheck)} />
        <SummaryItem label="连续徒步块" value={`${blocks.length} 个：${blocks.map((block) => block.segment_ids.join("+")).join("；")}`} />
      </div>
    </section>
  );
}

function SummaryItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="summary-item">
      <span>{label}</span>
      <p>{value}</p>
    </div>
  );
}

interface SegmentCardProps {
  segment: RouteSegment;
  block: WalkableBlock | undefined;
  readingCard: SegmentReadingCard | undefined;
  readingHref: string;
  selected: boolean;
  onSelect: (segmentId: string) => void;
}

function FieldRow({ label, value }: { label: string; value: unknown }) {
  const text = valueText(value);
  return (
    <div className={`field-row ${text.includes("书中未明示") ? "is-warning" : ""}`}>
      <span>{label}</span>
      <p>{text}</p>
    </div>
  );
}

function StatusRow({ label, value, formatter }: { label: string; value: unknown; formatter?: (value: string | undefined) => string }) {
  const raw = value === null || value === undefined ? undefined : String(value);
  const text = formatter ? formatter(raw) : valueText(value);
  return (
    <div className={`status-row ${statusClass(value)}`}>
      <span>{label}</span>
      <strong>{text}</strong>
    </div>
  );
}

function RefList({ title, refs, kind }: { title: string; refs: BookRef[] | undefined; kind: "book" | "chapter" }) {
  const items = refs ?? [];
  return (
    <section className={`refs-section ${kind === "chapter" ? "chapter-refs" : "book-refs"}`}>
      <strong>{title}</strong>
      {kind === "chapter" && <p className="section-note">这些引用只作为章节或段落出处，不作为路线事实证据。</p>}
      {items.length === 0 && <p className="empty-value">书中未明示</p>}
      {items.map((ref) => (
        <blockquote key={`${title}-${ref.page}-${ref.quote}`}>
          <p>第 {ref.page} 页：{ref.quote}</p>
          <footer>{ref.note}</footer>
        </blockquote>
      ))}
    </section>
  );
}

function SegmentCard({ segment, block, readingCard, readingHref, selected, onSelect }: SegmentCardProps) {
  const coordState = segmentCoordinateState(segment);
  const pages = segment.book_refs.map((ref) => ref.page);
  const inTrack = Boolean(block) && !segment.do_not_connect_in_gpx;
  const waypointOnly = Boolean(segment.do_not_connect_in_gpx);
  return (
    <article
      id={segment.id}
      className={`segment-card ${selected ? "is-selected" : ""}`}
      onClick={() => onSelect(segment.id)}
    >
      <header className="segment-header">
        <span className="segment-order">{String(segment.order).padStart(2, "0")}</span>
        <div>
          <h2>{segment.title}</h2>
          <p>
            {segment.start.name} <span>→</span> {segment.end.name}
          </p>
        </div>
      </header>

      <div className="badges">
        <span className={statusClass(segment.evidence_status === "warning" ? "warning" : "pass")}>
          证据 {segment.evidence_status || "pass"}
        </span>
        <span className={statusClass(segment.movement_type)}>{movementLabel(segment.movement_type)}</span>
        <span className={statusClass(segment.continuity_status)}>{continuityLabel(segment.continuity_status)}</span>
        <span className={coordState === "approximate" ? "is-warning" : ""}>{confidenceLabel(coordState)}</span>
        {segment.do_not_connect_in_gpx && <span className="is-warning">GPX 不强连</span>}
        {pages.length > 0 && <span>证据页 {Array.from(new Set(pages)).join(", ")}</span>}
      </div>

      <p className="summary">{valueText(segment.route_summary)}</p>

      {readingCard && (
        <section className="reading-preview">
          <strong>书中细读</strong>
          <p>{readingCard.book_scene_summary}</p>
          <a href={readingHref} onClick={(event) => event.stopPropagation()}>
            查看路线细读
          </a>
        </section>
      )}

      <div className="status-grid">
        <StatusRow label="movement_type" value={segment.movement_type} formatter={movementLabel} />
        <StatusRow label="continuity_status" value={segment.continuity_status} formatter={continuityLabel} />
        <StatusRow label="walkability_status" value={segment.walkability_status} formatter={walkabilityLabel} />
        <StatusRow label="modern_followability" value={segment.modern_followability} formatter={followabilityLabel} />
        <StatusRow label="do_not_connect_in_gpx" value={segment.do_not_connect_in_gpx ? "true" : "false"} />
        <StatusRow label="route_walkable_block" value={block ? `${block.block_id} (${block.status})` : "书中未明示"} />
        <StatusRow label="作为 GPX track" value={inTrack ? "yes" : "no"} />
        <StatusRow label="只导出 waypoint" value={waypointOnly ? "yes" : "no"} />
      </div>

      <div className="field-grid">
        <FieldRow label="途经地" value={segment.via.map((point) => point.name)} />
        <FieldRow label="步行方向" value={segment.walking_directions} />
        <FieldRow label="地形" value={segment.terrain} />
        <FieldRow label="道路/路径" value={segment.roads_or_paths} />
        <FieldRow label="水源/河流" value={segment.water_sources} />
        <FieldRow label="补给" value={segment.resupply} />
        <FieldRow label="住宿" value={segment.lodging} />
        <FieldRow label="风险/备注" value={segment.risks_or_notes} />
        <FieldRow label="书中里程" value={segment.distance_km_book} />
        <FieldRow label="坐标折线距离" value={segment.distance_km_computed ? `${segment.distance_km_computed} km` : null} />
      </div>

      <section className="review-notes">
        <strong>断点 / GPX 连接规则</strong>
        <ul>
          {(segment.gap_notes?.length ? segment.gap_notes : ["书中未明示"]).map((note) => (
            <li key={note}>{note}</li>
          ))}
        </ul>
      </section>

      <RefList title="书中路线证据" refs={segment.book_refs} kind="book" />
      <RefList title="章节出处" refs={segment.chapter_refs} kind="chapter" />

      <section className="review-notes evidence-notes">
        <strong>证据状态 / 人工复核</strong>
        <div className="field-grid compact">
          <FieldRow label="confidence" value={segment.confidence} />
          <FieldRow label="evidence_status" value={segment.evidence_status} />
          <FieldRow label="evidence_notes" value={segment.evidence_notes} />
          <FieldRow label="review_notes" value={segment.review_notes} />
        </div>
      </section>
    </article>
  );
}

function OverviewTab({
  overview,
  themes,
  loading,
  error,
}: {
  overview: BookOverview | null;
  themes: BookTheme[];
  loading: boolean;
  error: string | null;
}) {
  if (loading) return <div className="state-box">正在加载书中细读数据...</div>;
  if (error) return <div className="state-box error">细读数据加载失败：{error}</div>;
  if (!overview) return <div className="state-box">书中细读数据暂不可用。</div>;
  return (
    <section className="content-tab-panel">
      <div className="depth-hero">
        <h2>总览</h2>
        <p>{overview.one_sentence_summary}</p>
        {overview.source_policy && <p className="content-note">{overview.source_policy}</p>}
      </div>
      <div className="depth-grid">
        <InfoList title="全书路线结构" items={overview.route_structure} />
        <InfoList title="如何使用这个页面" items={overview.how_to_use_this_page} />
        <InfoList title="徒步 / 混合 / 断点 / GPX" items={overview.movement_gpx_notes} />
        <InfoList title="页面限制" items={overview.limitations} />
      </div>
      <section className="content-section">
        <h2>主题线索</h2>
        <div className="theme-grid">
          {themes.map((theme) => (
            <article className="theme-card" key={theme.theme}>
              <h3>{theme.theme}</h3>
              <p>{theme.summary}</p>
              <FieldRow label="相关段落" value={theme.related_segments} />
              <FieldRow label="相关地名" value={theme.related_places} />
              <RefList title="主题证据" refs={theme.refs} kind="book" />
            </article>
          ))}
        </div>
      </section>
    </section>
  );
}

function InfoList({ title, items }: { title: string; items: string[] }) {
  return (
    <section className="info-list">
      <h3>{title}</h3>
      <ul>
        {(items?.length ? items : ["书中未明示"]).map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
  );
}

function ReadingCardsTab({ cards }: { cards: SegmentReadingCard[] }) {
  return (
    <section id="reading-detail" className="content-tab-panel">
      <div className="panel-heading">
        <h2>路线细读</h2>
        <p>新增细读内容依据 OCR 文本和书中证据整理，仍需人工复核标记处请以原书为准。</p>
      </div>
      <div className="reading-card-list">
        {cards.map((card) => (
          <article className="reading-card" key={card.segment_id}>
            <header>
              <span>{card.segment_id}</span>
              <h3>{card.reading_title}</h3>
            </header>
            <FieldRow label="书中这一段" value={card.book_scene_summary} />
            <FieldRow label="路线叙事" value={card.route_narrative} />
            <FieldRow label="沿途地名" value={card.landmarks_in_book} />
            <FieldRow label="行走体验" value={card.walking_experience} />
            <FieldRow label="读者应注意的细节" value={card.what_to_notice} />
            <FieldRow label="今日复走提示" value={card.route_practicality} />
            <div className="status-grid">
              <StatusRow label="evidence_status" value={card.confidence.evidence_status} />
              <StatusRow label="coordinate_confidence" value={card.confidence.coordinate_confidence} />
              <StatusRow label="modern_followability" value={card.confidence.modern_followability} />
              <StatusRow label="route_confidence" value={card.confidence.route_confidence} />
            </div>
            <RefList title="证据出处" refs={card.evidence_refs} kind="book" />
            <section className="review-notes">
              <strong>复核事项</strong>
              <ul>
                {card.review_notes.map((note) => (
                  <li key={note}>{note}</li>
                ))}
              </ul>
            </section>
          </article>
        ))}
      </div>
    </section>
  );
}

type PlaceFilter = "all" | "needs_review" | "needs_field_check" | "approximate" | "missing";

function PlacesTab({ places }: { places: PlaceIndexItem[] }) {
  const [filter, setFilter] = useState<PlaceFilter>("all");
  const filtered = places.filter((place) => {
    if (filter === "all") return true;
    if (filter === "needs_review") return place.review_status === "needs_review";
    if (filter === "needs_field_check") return place.review_status === "needs_field_check";
    if (filter === "approximate") return place.coordinate_confidence === "approximate";
    if (filter === "missing") return place.coordinate_confidence === "missing";
    return true;
  });
  return (
    <section className="content-tab-panel">
      <div className="panel-heading">
        <h2>书中地名</h2>
        <p>这里集中展示书中重要地名、关联段落、证据页和复核状态。历史地名和 OCR 不稳定处不作为已核定现代地点处理。</p>
      </div>
      <div className="filter-tabs place-filter" role="tablist" aria-label="地名筛选">
        {[
          ["all", "全部"],
          ["needs_review", "需人工复核"],
          ["needs_field_check", "需路况核验"],
          ["approximate", "坐标大致"],
          ["missing", "缺坐标"],
        ].map(([key, label]) => (
          <button key={key} className={filter === key ? "active" : ""} onClick={() => setFilter(key as PlaceFilter)} type="button">
            {label}
          </button>
        ))}
      </div>
      <div className="place-grid">
        {filtered.map((place) => (
          <article className="place-card" key={place.name}>
            <header>
              <h3>{place.name}</h3>
              <span className={statusClass(place.review_status)}>{place.review_status}</span>
            </header>
            <FieldRow label="角色" value={place.role} />
            <FieldRow label="关联段落" value={place.appears_in_segments} />
            <FieldRow label="页码" value={place.pages.map(String)} />
            <FieldRow label="书中上下文" value={place.book_context} />
            <div className="status-grid compact-status">
              <StatusRow label="coordinate_confidence" value={place.coordinate_confidence} />
              <StatusRow label="review_status" value={place.review_status} />
            </div>
            <RefList title="地名证据" refs={place.refs} kind="book" />
          </article>
        ))}
      </div>
    </section>
  );
}

function RewalkTab({ segments, blocks, projectSlug }: { segments: RouteSegment[]; blocks: WalkableBlock[]; projectSlug: string }) {
  return (
    <section className="content-tab-panel">
      <RewalkSummary segments={segments} blocks={blocks} />
      <section className="content-section">
        <h2>连续徒步块</h2>
        <div className="block-grid">
          {blocks.map((block) => (
            <article className="summary-item" key={block.block_id}>
              <span>{block.block_id}</span>
              <p>
                {block.start_name} → {block.end_name}
              </p>
              <p>{block.segment_ids.join(" + ")}</p>
              <p>{block.status}：{block.notes}</p>
            </article>
          ))}
        </div>
      </section>
      <section className="content-section">
        <h2>下载与使用说明</h2>
        <p className="content-note">GPX 分成多个连续 track；断点、补走、乘车或不应连接的段落只作为 waypoint 或文字解读使用。不要把 waypoint 之间自动连线当成书中徒步轨迹。</p>
        <div className="downloads">
          <DownloadLink href={projectDataPath(projectSlug, "route_segments.json")} label="路线 JSON" icon={<FileJson size={16} />} />
          <DownloadLink href={projectDataPath(projectSlug, "route.geojson")} label="GeoJSON" icon={<Route size={16} />} />
          <DownloadLink href={projectDataPath(projectSlug, "route.gpx")} label="GPX" icon={<Download size={16} />} />
          <DownloadLink href={projectDataPath(projectSlug, "field_guide.md")} label="复走说明" icon={<FileJson size={16} />} />
        </div>
      </section>
    </section>
  );
}

function DownloadLink({ href, label, icon }: { href: string; label: string; icon: ReactNode }) {
  return (
    <a className="download-link" href={href} download>
      {icon}
      {label}
    </a>
  );
}

interface RouteMapProjectPageProps {
  project: ProjectMetadata;
  projectSlug: string;
}

export function RouteMapProjectPage({ project, projectSlug }: RouteMapProjectPageProps) {
  const { segments, routeGeoJson, placesGeoJson, blocks, error, loading } = useRouteData(projectSlug);
  const contentDepth = useContentDepth(projectSlug);
  const [activeTab, setActiveTabState] = useState<ProjectTab>(() => getActiveTab("overview"));
  const [filter, setFilter] = useState<FilterKey>("all");
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const blockMap = useMemo(() => buildBlockMap(blocks), [blocks]);
  const readingCardMap = useMemo(() => {
    const map = new Map<string, SegmentReadingCard>();
    contentDepth.readingCards.forEach((card) => map.set(card.segment_id, card));
    return map;
  }, [contentDepth.readingCards]);

  const filteredSegments = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return segments.filter((segment) => {
      const filterMatch = matchesFilter(segment, filter);
      if (!normalizedQuery) return filterMatch;
      const text = [
        segment.title,
        segment.start.name,
        segment.end.name,
        ...segment.via.map((point) => point.name),
        valueText(segment.route_summary),
        valueText(segment.gap_notes),
      ].join(" ").toLowerCase();
      return filterMatch && text.includes(normalizedQuery);
    });
  }, [segments, filter, query]);

  const selectedSegment = segments.find((segment) => segment.id === selectedId) || null;
  const stats = useMemo(() => {
    const walked = segments.filter((segment) => segment.movement_type === "walked").length;
    const mixed = segments.filter((segment) => segment.movement_type === "mixed").length;
    const doNotConnect = segments.filter((segment) => segment.do_not_connect_in_gpx).length;
    const fieldCheck = segments.filter((segment) => segment.modern_followability === "needs_field_check").length;
    return { walked, mixed, doNotConnect, fieldCheck };
  }, [segments]);

  useEffect(() => {
    if (!selectedId && filteredSegments[0]) {
      setSelectedId(filteredSegments[0].id);
    }
  }, [filteredSegments, selectedId]);

  useEffect(() => {
    const handleHashChange = () => setActiveTabState(getActiveTab("overview"));
    window.addEventListener("hashchange", handleHashChange);
    handleHashChange();
    return () => window.removeEventListener("hashchange", handleHashChange);
  }, []);

  return (
    <main className="app-shell">
      <section className="intro">
        <a className="back-link" href="#/">
          返回项目首页
        </a>
        <div className="brand-line">
          <MapPinned size={22} />
          <span>按书中线索整理的徒步路线图解</span>
        </div>
        <div className="intro-main">
          <div>
            <h1>{project.title}</h1>
            <p>
              《从大都到上都》路线图解依据书中描述整理。页面中的坐标为现代地图辅助定位；存在历史地名不确定、乘车/补走、路线断点或需人工核对的地方，均以复核标记显示。本页面不是未经核验的户外导航路线。
            </p>
          </div>
          <div className="stats-panel" aria-label="路线统计">
            <span><strong>{segments.length}</strong>路线段</span>
            <span><strong>{stats.walked}</strong>明确徒步</span>
            <span><strong>{stats.mixed}</strong>混合/补走</span>
            <span><strong>{stats.doNotConnect}</strong>不连 GPX</span>
          </div>
        </div>
      </section>

      <nav className="project-tabs" aria-label="项目内容分区">
        {projectTabs.map((tab) => (
          <button key={tab.key} className={activeTab === tab.key ? "active" : ""} onClick={() => setProjectTab(projectSlug, tab.key)} type="button">
            {tab.label}
          </button>
        ))}
      </nav>

      {activeTab === "overview" && (
        <OverviewTab
          overview={contentDepth.overview}
          themes={contentDepth.themes}
          loading={contentDepth.loading}
          error={contentDepth.error}
        />
      )}

      {activeTab === "map" && (
      <section className="workspace">
        <MapPanel
          segments={segments}
          routeGeoJson={routeGeoJson}
          placesGeoJson={placesGeoJson}
          selectedId={selectedId}
          onSelect={setSelectedId}
        />

        <section className="route-panel">
          <Legend />
          <RewalkSummary segments={segments} blocks={blocks} />

          <div className="controls">
            <div className="search-box">
              <Search size={17} />
              <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索地名、段落、断点说明" />
            </div>
            <div className="filter-tabs" role="tablist" aria-label="路线筛选">
              {(Object.keys(filterLabels) as FilterKey[]).map((key) => (
                <button
                  key={key}
                  className={filter === key ? "active" : ""}
                  onClick={() => setFilter(key)}
                  type="button"
                >
                  {filterLabels[key]}
                </button>
              ))}
            </div>
            <div className="downloads">
              <DownloadLink href={projectDataPath(projectSlug, "route_segments.json")} label="路线 JSON" icon={<FileJson size={16} />} />
              <DownloadLink href={projectDataPath(projectSlug, "route.geojson")} label="GeoJSON" icon={<Route size={16} />} />
              <DownloadLink href={projectDataPath(projectSlug, "route.gpx")} label="GPX" icon={<Download size={16} />} />
              <DownloadLink href={projectDataPath(projectSlug, "field_guide.md")} label="复走说明" icon={<FileJson size={16} />} />
            </div>
          </div>

          {loading && <div className="state-box">正在加载路线数据...</div>}
          {error && <div className="state-box error">数据未就绪：{error}</div>}
          {!loading && !error && filteredSegments.length === 0 && <div className="state-box">没有符合筛选条件的路线段。</div>}

          <div className="segment-list">
            {filteredSegments.map((segment) => (
              <SegmentCard
                key={segment.id}
                segment={segment}
                block={blockMap.get(segment.id)}
                readingCard={readingCardMap.get(segment.id)}
                readingHref={projectTabUrl(projectSlug, "reading-detail")}
                selected={selectedSegment?.id === segment.id}
                onSelect={setSelectedId}
              />
            ))}
          </div>
        </section>
      </section>
      )}

      {activeTab === "reading-detail" &&
        (contentDepth.loading ? (
          <div className="content-tab-panel"><div className="state-box">正在加载路线细读...</div></div>
        ) : contentDepth.error ? (
          <div className="content-tab-panel"><div className="state-box error">路线细读加载失败：{contentDepth.error}</div></div>
        ) : (
          <ReadingCardsTab cards={contentDepth.readingCards} />
        ))}

      {activeTab === "place-index" &&
        (contentDepth.loading ? (
          <div className="content-tab-panel"><div className="state-box">正在加载书中地名...</div></div>
        ) : contentDepth.error ? (
          <div className="content-tab-panel"><div className="state-box error">书中地名加载失败：{contentDepth.error}</div></div>
        ) : (
          <PlacesTab places={contentDepth.placeIndex} />
        ))}

      {activeTab === "field-guide" && <RewalkTab segments={segments} blocks={blocks} projectSlug={projectSlug} />}
    </main>
  );
}
