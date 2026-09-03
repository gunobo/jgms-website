import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { ApiError, api } from "../../api/client";
import type { AssignmentDetail, SubmissionWithGradeOut } from "../../api/types";
import { SheetLinkPanel } from "../../components/SheetLinkPanel";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8001";

function GradingPanel({
  assignment,
  item,
  onSaved,
}: {
  assignment: AssignmentDetail;
  item: SubmissionWithGradeOut;
  onSaved: () => void;
}) {
  const [checked, setChecked] = useState<Set<string>>(new Set(item.grade?.checked_item_ids ?? []));
  const [comment, setComment] = useState(item.grade?.comment ?? "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const total = assignment.criteria.reduce(
    (sum, c) => sum + c.items.reduce((s, i) => s + (checked.has(i.id) ? i.points : 0), 0),
    0
  );

  const toggle = (itemId: string) => {
    setChecked((prev) => {
      const next = new Set(prev);
      if (next.has(itemId)) next.delete(itemId);
      else next.add(itemId);
      return next;
    });
  };

  const save = async () => {
    setSaving(true);
    setError(null);
    try {
      await api.post(
        `/api/admin/assignments/${assignment.id}/submissions/${item.submission.id}/grade`,
        { checked_item_ids: Array.from(checked), comment: comment || null }
      );
      onSaved();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "채점 저장에 실패했습니다.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-4 border-t border-gray-100 bg-gray-50 p-4">
      <div className="space-y-1 text-sm">
        {item.submission.link_url && (
          <p>
            링크:{" "}
            <a
              href={item.submission.link_url}
              target="_blank"
              rel="noreferrer"
              className="text-blue-600 hover:underline"
            >
              {item.submission.link_url}
            </a>
          </p>
        )}
        {item.submission.text_content && (
          <p className="whitespace-pre-wrap text-gray-700">{item.submission.text_content}</p>
        )}
        {item.submission.file_name && (
          <p>
            첨부파일:{" "}
            <a
              href={`${API_URL}/api/admin/assignments/${assignment.id}/submissions/${item.submission.id}/file`}
              target="_blank"
              rel="noreferrer"
              className="text-blue-600 hover:underline"
            >
              {item.submission.file_name}
            </a>
          </p>
        )}
      </div>

      <div className="space-y-3">
        {assignment.criteria.map((c) => (
          <div key={c.id}>
            <p className="text-sm font-medium text-gray-800">{c.title}</p>
            <div className="mt-1 space-y-1 pl-2">
              {c.items.map((i) => (
                <label key={i.id} className="flex items-center gap-2 text-sm text-gray-600">
                  <input type="checkbox" checked={checked.has(i.id)} onChange={() => toggle(i.id)} />
                  {i.label}
                  <span className="text-xs text-gray-400">({i.points}점)</span>
                </label>
              ))}
            </div>
          </div>
        ))}
      </div>

      <textarea
        placeholder="코멘트 (선택)"
        value={comment}
        onChange={(e) => setComment(e.target.value)}
        rows={2}
        className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
      />

      {error && <p className="text-xs text-red-600">{error}</p>}

      <div className="flex items-center justify-between">
        <p className="text-sm font-semibold text-gray-900">
          총점 {total} / {assignment.max_score}
        </p>
        <button
          onClick={save}
          disabled={saving}
          className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {saving ? "저장 중..." : "채점 저장"}
        </button>
      </div>
    </div>
  );
}

export function AdminAssignmentGradingPage() {
  const { id } = useParams();
  const [assignment, setAssignment] = useState<AssignmentDetail | null>(null);
  const [submissions, setSubmissions] = useState<SubmissionWithGradeOut[]>([]);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = () => {
    if (!id) return;
    Promise.all([
      api.get<AssignmentDetail>(`/api/admin/assignments/${id}`),
      api.get<SubmissionWithGradeOut[]>(`/api/admin/assignments/${id}/submissions`),
    ])
      .then(([a, s]) => {
        setAssignment(a);
        setSubmissions(s);
      })
      .finally(() => setLoading(false));
  };
  useEffect(load, [id]);

  if (loading || !assignment) return <p className="text-gray-400">불러오는 중...</p>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-gray-900">{assignment.title} - 제출물 / 채점</h1>
        <p className="text-sm text-gray-500">
          총 {submissions.length}건 제출 · 만점 {assignment.max_score}점
        </p>
      </div>

      <SheetLinkPanel
        sheetId={assignment.sheet_id}
        onLink={async (url) => {
          await api.post(`/api/admin/assignments/${id}/sheet`, { sheet_url_or_id: url });
          load();
        }}
        onUnlink={async () => {
          await api.del(`/api/admin/assignments/${id}/sheet`);
          load();
        }}
      />

      <div className="space-y-3">
        {submissions.length === 0 && (
          <p className="rounded-lg border border-dashed border-gray-300 p-8 text-center text-gray-400">
            아직 제출물이 없습니다.
          </p>
        )}
        {submissions.map((s) => (
          <div key={s.submission.id} className="rounded-lg border border-gray-200 bg-white">
            <button
              onClick={() => setExpanded(expanded === s.submission.id ? null : s.submission.id)}
              className="flex w-full items-center justify-between p-4 text-left"
            >
              <div>
                <p className="font-medium text-gray-900">
                  {s.student_name} ({s.student_number})
                </p>
                <p className="text-xs text-gray-400">
                  {new Date(s.submission.submitted_at).toLocaleString("ko-KR")}
                </p>
              </div>
              <div className="flex items-center gap-3">
                {s.grade ? (
                  <span className="rounded bg-green-100 px-2 py-1 text-xs font-medium text-green-700">
                    {s.grade.total_score} / {assignment.max_score}점
                  </span>
                ) : (
                  <span className="rounded bg-gray-100 px-2 py-1 text-xs font-medium text-gray-500">
                    미채점
                  </span>
                )}
                <span className="text-gray-400">{expanded === s.submission.id ? "▲" : "▼"}</span>
              </div>
            </button>
            {expanded === s.submission.id && (
              <GradingPanel assignment={assignment} item={s} onSaved={load} />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
