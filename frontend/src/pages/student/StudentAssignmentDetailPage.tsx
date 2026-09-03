import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { ApiError, api } from "../../api/client";
import type { AssignmentDetail, MySubmissionOut } from "../../api/types";

export function StudentAssignmentDetailPage() {
  const { id } = useParams();
  const [assignment, setAssignment] = useState<AssignmentDetail | null>(null);
  const [mySubmission, setMySubmission] = useState<MySubmissionOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const [linkUrl, setLinkUrl] = useState("");
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);

  const load = () => {
    if (!id) return;
    Promise.all([
      api.get<AssignmentDetail>(`/api/assignments/${id}`),
      api.get<MySubmissionOut>(`/api/assignments/${id}/my-submission`),
    ])
      .then(([a, s]) => {
        setAssignment(a);
        setMySubmission(s);
        if (s.submission) {
          setLinkUrl(s.submission.link_url ?? "");
          setText(s.submission.text_content ?? "");
        }
      })
      .catch(() => setError("과제를 불러오지 못했습니다."))
      .finally(() => setLoading(false));
  };
  useEffect(load, [id]);

  if (loading) return <p className="text-gray-400">불러오는 중...</p>;
  if (!assignment) return <p className="text-red-600">{error}</p>;

  const isGraded = Boolean(mySubmission?.grade);

  const submit = async () => {
    setError(null);
    if (!linkUrl.trim() && !text.trim() && !file) {
      setError("링크, 텍스트, 파일 중 최소 하나는 입력해주세요.");
      return;
    }
    const formData = new FormData();
    if (linkUrl.trim()) formData.append("link_url", linkUrl.trim());
    if (text.trim()) formData.append("text_content", text.trim());
    if (file) formData.append("file", file);

    setSubmitting(true);
    try {
      await api.postForm(`/api/assignments/${id}/submissions`, formData);
      setFile(null);
      load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "제출에 실패했습니다.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-gray-200 bg-white p-5">
        <h1 className="text-lg font-bold text-gray-900">{assignment.title}</h1>
        {assignment.description && (
          <p className="mt-2 whitespace-pre-wrap text-sm text-gray-500">{assignment.description}</p>
        )}
      </div>

      <div className="space-y-3 rounded-lg border border-gray-200 bg-white p-5">
        <h2 className="font-semibold text-gray-900">평가기준표 (만점 {assignment.max_score}점)</h2>
        {assignment.criteria.map((c) => (
          <div key={c.id}>
            <p className="text-sm font-medium text-gray-800">{c.title}</p>
            {c.description && <p className="text-xs text-gray-500">{c.description}</p>}
            <ul className="mt-1 space-y-0.5 pl-4 text-sm text-gray-600">
              {c.items.map((i) => (
                <li key={i.id} className="list-disc">
                  {i.label} <span className="text-xs text-gray-400">({i.points}점)</span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      {isGraded && mySubmission?.grade && (
        <div className="space-y-1 rounded-lg border border-green-200 bg-green-50 p-5">
          <h2 className="font-semibold text-green-800">
            채점 결과: {mySubmission.grade.total_score} / {mySubmission.grade.max_score}점
          </h2>
          {mySubmission.grade.comment && (
            <p className="text-sm text-green-700">코멘트: {mySubmission.grade.comment}</p>
          )}
        </div>
      )}

      <div className="space-y-3 rounded-lg border border-gray-200 bg-white p-5">
        <h2 className="font-semibold text-gray-900">
          {mySubmission?.submission ? "제출물 수정" : "과제 제출"}
        </h2>
        {error && <p className="rounded bg-red-50 p-2 text-sm text-red-600">{error}</p>}
        <input
          placeholder="링크 (예: GitHub 저장소, 배포 URL)"
          value={linkUrl}
          onChange={(e) => setLinkUrl(e.target.value)}
          className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
        />
        <textarea
          placeholder="텍스트 답안 (선택)"
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={4}
          className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
        />
        <input
          type="file"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          className="w-full text-sm"
        />
        {mySubmission?.submission?.file_name && !file && (
          <p className="text-xs text-gray-400">현재 첨부: {mySubmission.submission.file_name}</p>
        )}
        <button
          onClick={submit}
          disabled={submitting}
          className="w-full rounded bg-blue-600 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {submitting ? "제출 중..." : mySubmission?.submission ? "다시 제출" : "제출하기"}
        </button>
      </div>
    </div>
  );
}
