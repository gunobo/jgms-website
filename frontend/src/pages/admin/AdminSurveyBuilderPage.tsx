import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ApiError, api } from "../../api/client";
import type { QuestionInput, QuestionType, SurveyDetail } from "../../api/types";

const QUESTION_TYPE_LABELS: Record<QuestionType, string> = {
  SHORT_TEXT: "단답형",
  PARAGRAPH: "장문형",
  SINGLE_CHOICE: "객관식 (단일 선택)",
  MULTIPLE_CHOICE: "체크박스 (다중 선택)",
  DROPDOWN: "드롭다운",
  LINEAR_SCALE: "선형 배율",
};

const CHOICE_TYPES: QuestionType[] = ["SINGLE_CHOICE", "MULTIPLE_CHOICE", "DROPDOWN"];

let tempIdCounter = 0;
function tempId() {
  tempIdCounter += 1;
  return `temp-${tempIdCounter}`;
}

function blankQuestion(order: number): QuestionInput {
  return { id: tempId(), type: "SHORT_TEXT", label: "", required: false, order };
}

export function AdminSurveyBuilderPage() {
  const { id } = useParams();
  const isEdit = Boolean(id);
  const navigate = useNavigate();

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [allowMultiple, setAllowMultiple] = useState(false);
  const [questions, setQuestions] = useState<QuestionInput[]>([blankQuestion(0)]);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(isEdit);

  useEffect(() => {
    if (!id) return;
    api
      .get<SurveyDetail>(`/api/admin/surveys/${id}`)
      .then((s) => {
        setTitle(s.title);
        setDescription(s.description ?? "");
        setAllowMultiple(s.allow_multiple_responses);
        setQuestions(s.questions.length > 0 ? s.questions : [blankQuestion(0)]);
      })
      .catch(() => setError("설문을 불러오지 못했습니다."))
      .finally(() => setLoading(false));
  }, [id]);

  const updateQuestion = (idx: number, patch: Partial<QuestionInput>) => {
    setQuestions((qs) => qs.map((q, i) => (i === idx ? { ...q, ...patch } : q)));
  };

  const removeQuestion = (idx: number) => {
    setQuestions((qs) => qs.filter((_, i) => i !== idx));
  };

  const moveQuestion = (idx: number, dir: -1 | 1) => {
    setQuestions((qs) => {
      const next = [...qs];
      const target = idx + dir;
      if (target < 0 || target >= next.length) return qs;
      [next[idx], next[target]] = [next[target], next[idx]];
      return next;
    });
  };

  const addQuestion = () => {
    setQuestions((qs) => [...qs, blankQuestion(qs.length)]);
  };

  const save = async () => {
    setError(null);
    if (!title.trim()) {
      setError("제목을 입력해주세요.");
      return;
    }
    if (questions.length === 0) {
      setError("질문을 1개 이상 추가해주세요.");
      return;
    }
    for (const q of questions) {
      if (!q.label.trim()) {
        setError("모든 질문에 내용을 입력해주세요.");
        return;
      }
      if (CHOICE_TYPES.includes(q.type) && (!q.choices || q.choices.filter((c) => c.trim()).length < 2)) {
        setError(`"${q.label}" 질문에는 선택지를 2개 이상 입력해주세요.`);
        return;
      }
      if (q.type === "LINEAR_SCALE" && (!q.linear_scale || q.linear_scale.max <= q.linear_scale.min)) {
        setError(`"${q.label}" 질문의 배율 범위를 확인해주세요.`);
        return;
      }
    }

    const payload = {
      title,
      description: description || null,
      allow_multiple_responses: allowMultiple,
      questions: questions.map((q, i) => ({
        id: q.id?.startsWith("temp-") ? undefined : q.id,
        type: q.type,
        label: q.label,
        description: q.description || null,
        required: q.required,
        choices: CHOICE_TYPES.includes(q.type) ? (q.choices ?? []).filter((c) => c.trim()) : undefined,
        linear_scale: q.type === "LINEAR_SCALE" ? q.linear_scale : undefined,
        order: i,
      })),
    };

    setSaving(true);
    try {
      if (isEdit) {
        await api.put(`/api/admin/surveys/${id}`, payload);
      } else {
        await api.post("/api/admin/surveys", payload);
      }
      navigate("/admin/surveys");
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "저장에 실패했습니다.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <p className="text-gray-400">불러오는 중...</p>;

  return (
    <div className="space-y-6 pb-20">
      <h1 className="text-xl font-bold text-gray-900">{isEdit ? "설문 편집" : "새 설문 만들기"}</h1>
      {error && <p className="rounded bg-red-50 p-3 text-sm text-red-600">{error}</p>}

      <div className="space-y-3 rounded-lg border border-gray-200 bg-white p-5">
        <input
          placeholder="설문 제목"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="w-full border-b border-gray-300 pb-2 text-lg font-semibold focus:border-blue-500 focus:outline-none"
        />
        <textarea
          placeholder="설문 설명 (선택)"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={2}
          className="w-full text-sm text-gray-600 focus:outline-none"
        />
        <label className="flex items-center gap-2 text-sm text-gray-600">
          <input
            type="checkbox"
            checked={allowMultiple}
            onChange={(e) => setAllowMultiple(e.target.checked)}
          />
          한 학생이 여러 번 응답할 수 있도록 허용
        </label>
      </div>

      <div className="space-y-4">
        {questions.map((q, idx) => (
          <div key={q.id} className="space-y-3 rounded-lg border border-gray-200 bg-white p-5">
            <div className="flex items-start gap-3">
              <input
                placeholder={`질문 ${idx + 1}`}
                value={q.label}
                onChange={(e) => updateQuestion(idx, { label: e.target.value })}
                className="flex-1 border-b border-gray-300 pb-1 font-medium focus:border-blue-500 focus:outline-none"
              />
              <select
                value={q.type}
                onChange={(e) => {
                  const type = e.target.value as QuestionType;
                  const patch: Partial<QuestionInput> = { type };
                  if (CHOICE_TYPES.includes(type) && !q.choices) patch.choices = ["", ""];
                  if (type === "LINEAR_SCALE" && !q.linear_scale) {
                    patch.linear_scale = { min: 1, max: 5, min_label: "", max_label: "" };
                  }
                  updateQuestion(idx, patch);
                }}
                className="rounded border border-gray-300 px-2 py-1 text-sm"
              >
                {Object.entries(QUESTION_TYPE_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </div>

            {CHOICE_TYPES.includes(q.type) && (
              <div className="space-y-2 pl-1">
                {(q.choices ?? ["", ""]).map((choice, ci) => (
                  <div key={ci} className="flex items-center gap-2">
                    <span className="text-xs text-gray-400">{ci + 1}.</span>
                    <input
                      value={choice}
                      onChange={(e) => {
                        const next = [...(q.choices ?? [])];
                        next[ci] = e.target.value;
                        updateQuestion(idx, { choices: next });
                      }}
                      placeholder="선택지"
                      className="flex-1 rounded border border-gray-300 px-2 py-1 text-sm"
                    />
                    {(q.choices?.length ?? 0) > 2 && (
                      <button
                        onClick={() => {
                          const next = (q.choices ?? []).filter((_, i) => i !== ci);
                          updateQuestion(idx, { choices: next });
                        }}
                        className="text-xs text-gray-400 hover:text-red-500"
                      >
                        삭제
                      </button>
                    )}
                  </div>
                ))}
                <button
                  onClick={() => updateQuestion(idx, { choices: [...(q.choices ?? []), ""] })}
                  className="text-xs font-medium text-blue-600 hover:text-blue-800"
                >
                  + 선택지 추가
                </button>
              </div>
            )}

            {q.type === "LINEAR_SCALE" && (
              <div className="flex flex-wrap items-center gap-3 pl-1 text-sm">
                <span>최소</span>
                <input
                  type="number"
                  value={q.linear_scale?.min ?? 1}
                  onChange={(e) =>
                    updateQuestion(idx, {
                      linear_scale: { ...q.linear_scale!, min: Number(e.target.value) },
                    })
                  }
                  className="w-16 rounded border border-gray-300 px-2 py-1"
                />
                <span>~ 최대</span>
                <input
                  type="number"
                  value={q.linear_scale?.max ?? 5}
                  onChange={(e) =>
                    updateQuestion(idx, {
                      linear_scale: { ...q.linear_scale!, max: Number(e.target.value) },
                    })
                  }
                  className="w-16 rounded border border-gray-300 px-2 py-1"
                />
                <input
                  placeholder="최소값 라벨 (선택)"
                  value={q.linear_scale?.min_label ?? ""}
                  onChange={(e) =>
                    updateQuestion(idx, {
                      linear_scale: { ...q.linear_scale!, min_label: e.target.value },
                    })
                  }
                  className="w-36 rounded border border-gray-300 px-2 py-1"
                />
                <input
                  placeholder="최대값 라벨 (선택)"
                  value={q.linear_scale?.max_label ?? ""}
                  onChange={(e) =>
                    updateQuestion(idx, {
                      linear_scale: { ...q.linear_scale!, max_label: e.target.value },
                    })
                  }
                  className="w-36 rounded border border-gray-300 px-2 py-1"
                />
              </div>
            )}

            <div className="flex items-center justify-between border-t border-gray-100 pt-3">
              <label className="flex items-center gap-2 text-xs text-gray-500">
                <input
                  type="checkbox"
                  checked={q.required}
                  onChange={(e) => updateQuestion(idx, { required: e.target.checked })}
                />
                필수 응답
              </label>
              <div className="flex gap-2 text-xs text-gray-400">
                <button onClick={() => moveQuestion(idx, -1)} disabled={idx === 0} className="disabled:opacity-30">
                  ↑
                </button>
                <button
                  onClick={() => moveQuestion(idx, 1)}
                  disabled={idx === questions.length - 1}
                  className="disabled:opacity-30"
                >
                  ↓
                </button>
                <button onClick={() => removeQuestion(idx)} className="text-red-400 hover:text-red-600">
                  질문 삭제
                </button>
              </div>
            </div>
          </div>
        ))}

        <button
          onClick={addQuestion}
          className="w-full rounded-lg border border-dashed border-gray-300 py-3 text-sm font-medium text-gray-500 hover:border-blue-300 hover:text-blue-600"
        >
          + 질문 추가
        </button>
      </div>

      <div className="fixed inset-x-0 bottom-0 border-t border-gray-200 bg-white p-4">
        <div className="mx-auto flex max-w-5xl justify-end gap-3">
          <button
            onClick={() => navigate("/admin/surveys")}
            className="rounded border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700"
          >
            취소
          </button>
          <button
            onClick={save}
            disabled={saving}
            className="rounded bg-blue-600 px-5 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {saving ? "저장 중..." : "저장"}
          </button>
        </div>
      </div>
    </div>
  );
}
