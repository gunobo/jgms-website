import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ApiError, api } from "../../api/client";
import type { SurveyDetail } from "../../api/types";

type AnswerState = Record<string, { value?: string; values?: string[] }>;

export function StudentSurveyTakePage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [survey, setSurvey] = useState<SurveyDetail | null>(null);
  const [answers, setAnswers] = useState<AnswerState>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (!id) return;
    api
      .get<SurveyDetail>(`/api/surveys/${id}`)
      .then(setSurvey)
      .catch(() => setError("설문을 불러오지 못했습니다."))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <p className="text-gray-400">불러오는 중...</p>;
  if (error && !survey) return <p className="text-red-600">{error}</p>;
  if (!survey) return null;

  if (done) {
    return (
      <div className="space-y-4 rounded-lg border border-gray-200 bg-white p-8 text-center">
        <h1 className="text-lg font-bold text-gray-900">응답이 제출되었습니다</h1>
        <p className="text-sm text-gray-500">참여해주셔서 감사합니다.</p>
        <button
          onClick={() => navigate("/surveys")}
          className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          설문 목록으로
        </button>
      </div>
    );
  }

  const setValue = (qId: string, value: string) => setAnswers((a) => ({ ...a, [qId]: { value } }));
  const toggleValue = (qId: string, option: string) => {
    setAnswers((a) => {
      const current = a[qId]?.values ?? [];
      const next = current.includes(option) ? current.filter((v) => v !== option) : [...current, option];
      return { ...a, [qId]: { values: next } };
    });
  };

  const submit = async () => {
    setError(null);
    for (const q of survey.questions) {
      if (!q.required) continue;
      const a = answers[q.id];
      const hasValue = a && ((a.value && a.value.trim()) || (a.values && a.values.length > 0));
      if (!hasValue) {
        setError(`"${q.label}" 항목은 필수 입력입니다.`);
        return;
      }
    }

    setSubmitting(true);
    try {
      await api.post(`/api/surveys/${id}/responses`, {
        answers: Object.entries(answers).map(([question_id, a]) => ({
          question_id,
          value: a.value ?? null,
          values: a.values ?? null,
        })),
      });
      setDone(true);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "제출에 실패했습니다.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-gray-200 bg-white p-5">
        <h1 className="text-lg font-bold text-gray-900">{survey.title}</h1>
        {survey.description && <p className="mt-2 text-sm text-gray-500">{survey.description}</p>}
      </div>

      {error && <p className="rounded bg-red-50 p-3 text-sm text-red-600">{error}</p>}

      <div className="space-y-4">
        {survey.questions.map((q) => (
          <div key={q.id} className="rounded-lg border border-gray-200 bg-white p-5">
            <p className="font-medium text-gray-900">
              {q.label}
              {q.required && <span className="ml-1 text-red-500">*</span>}
            </p>
            {q.description && <p className="mt-1 text-sm text-gray-500">{q.description}</p>}

            <div className="mt-3">
              {q.type === "SHORT_TEXT" && (
                <input
                  value={answers[q.id]?.value ?? ""}
                  onChange={(e) => setValue(q.id, e.target.value)}
                  className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
                />
              )}
              {q.type === "PARAGRAPH" && (
                <textarea
                  value={answers[q.id]?.value ?? ""}
                  onChange={(e) => setValue(q.id, e.target.value)}
                  rows={4}
                  className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
                />
              )}
              {q.type === "SINGLE_CHOICE" && (
                <div className="space-y-2">
                  {q.choices?.map((c) => (
                    <label key={c} className="flex items-center gap-2 text-sm">
                      <input
                        type="radio"
                        name={q.id}
                        checked={answers[q.id]?.value === c}
                        onChange={() => setValue(q.id, c)}
                      />
                      {c}
                    </label>
                  ))}
                </div>
              )}
              {q.type === "MULTIPLE_CHOICE" && (
                <div className="space-y-2">
                  {q.choices?.map((c) => (
                    <label key={c} className="flex items-center gap-2 text-sm">
                      <input
                        type="checkbox"
                        checked={(answers[q.id]?.values ?? []).includes(c)}
                        onChange={() => toggleValue(q.id, c)}
                      />
                      {c}
                    </label>
                  ))}
                </div>
              )}
              {q.type === "DROPDOWN" && (
                <select
                  value={answers[q.id]?.value ?? ""}
                  onChange={(e) => setValue(q.id, e.target.value)}
                  className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
                >
                  <option value="">선택해주세요</option>
                  {q.choices?.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              )}
              {q.type === "LINEAR_SCALE" && q.linear_scale && (
                <div className="flex items-center gap-3">
                  {q.linear_scale.min_label && (
                    <span className="text-xs text-gray-400">{q.linear_scale.min_label}</span>
                  )}
                  {Array.from(
                    { length: q.linear_scale.max - q.linear_scale.min + 1 },
                    (_, i) => q.linear_scale!.min + i
                  ).map((n) => (
                    <label key={n} className="flex flex-col items-center gap-1 text-xs text-gray-500">
                      <input
                        type="radio"
                        name={q.id}
                        checked={answers[q.id]?.value === String(n)}
                        onChange={() => setValue(q.id, String(n))}
                      />
                      {n}
                    </label>
                  ))}
                  {q.linear_scale.max_label && (
                    <span className="text-xs text-gray-400">{q.linear_scale.max_label}</span>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      <button
        onClick={submit}
        disabled={submitting}
        className="w-full rounded bg-blue-600 py-3 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
      >
        {submitting ? "제출 중..." : "제출하기"}
      </button>
    </div>
  );
}
