import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ApiError, api } from "../../api/client";
import type { AssignmentDetail, RubricCriterionInput } from "../../api/types";

let tempIdCounter = 0;
function tempId() {
  tempIdCounter += 1;
  return `temp-${tempIdCounter}`;
}

function blankCriterion(order: number): RubricCriterionInput {
  return {
    id: tempId(),
    title: "",
    order,
    items: [{ id: tempId(), label: "", points: 5, order: 0 }],
  };
}

export function AdminAssignmentBuilderPage() {
  const { id } = useParams();
  const isEdit = Boolean(id);
  const navigate = useNavigate();

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [criteria, setCriteria] = useState<RubricCriterionInput[]>([blankCriterion(0)]);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(isEdit);

  useEffect(() => {
    if (!id) return;
    api
      .get<AssignmentDetail>(`/api/admin/assignments/${id}`)
      .then((a) => {
        setTitle(a.title);
        setDescription(a.description ?? "");
        setCriteria(a.criteria.length > 0 ? a.criteria : [blankCriterion(0)]);
      })
      .catch(() => setError("과제를 불러오지 못했습니다."))
      .finally(() => setLoading(false));
  }, [id]);

  const updateCriterion = (idx: number, patch: Partial<RubricCriterionInput>) => {
    setCriteria((cs) => cs.map((c, i) => (i === idx ? { ...c, ...patch } : c)));
  };

  const removeCriterion = (idx: number) => setCriteria((cs) => cs.filter((_, i) => i !== idx));

  const addCriterion = () => setCriteria((cs) => [...cs, blankCriterion(cs.length)]);

  const addItem = (cIdx: number) => {
    setCriteria((cs) =>
      cs.map((c, i) =>
        i === cIdx
          ? { ...c, items: [...c.items, { id: tempId(), label: "", points: 5, order: c.items.length }] }
          : c
      )
    );
  };

  const updateItem = (cIdx: number, iIdx: number, patch: Partial<{ label: string; points: number }>) => {
    setCriteria((cs) =>
      cs.map((c, i) =>
        i === cIdx
          ? { ...c, items: c.items.map((item, j) => (j === iIdx ? { ...item, ...patch } : item)) }
          : c
      )
    );
  };

  const removeItem = (cIdx: number, iIdx: number) => {
    setCriteria((cs) =>
      cs.map((c, i) => (i === cIdx ? { ...c, items: c.items.filter((_, j) => j !== iIdx) } : c))
    );
  };

  const maxScore = criteria.reduce((sum, c) => sum + c.items.reduce((s, item) => s + (item.points || 0), 0), 0);

  const save = async () => {
    setError(null);
    if (!title.trim()) {
      setError("제목을 입력해주세요.");
      return;
    }
    for (const c of criteria) {
      if (!c.title.trim()) {
        setError("모든 평가 항목에 이름을 입력해주세요.");
        return;
      }
      if (c.items.length === 0 || c.items.some((i) => !i.label.trim())) {
        setError(`"${c.title}" 항목의 모든 조건에 내용을 입력해주세요.`);
        return;
      }
    }

    const payload = {
      title,
      description: description || null,
      criteria: criteria.map((c, ci) => ({
        id: c.id?.startsWith("temp-") ? undefined : c.id,
        title: c.title,
        description: c.description || null,
        order: ci,
        items: c.items.map((item, ii) => ({
          id: item.id?.startsWith("temp-") ? undefined : item.id,
          label: item.label,
          points: Number(item.points) || 0,
          order: ii,
        })),
      })),
    };

    setSaving(true);
    try {
      if (isEdit) {
        await api.put(`/api/admin/assignments/${id}`, payload);
      } else {
        await api.post("/api/admin/assignments", payload);
      }
      navigate("/admin/assignments");
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "저장에 실패했습니다.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <p className="text-gray-400">불러오는 중...</p>;

  return (
    <div className="space-y-6 pb-20">
      <h1 className="text-xl font-bold text-gray-900">{isEdit ? "과제 편집" : "새 과제 만들기"}</h1>
      {error && <p className="rounded bg-red-50 p-3 text-sm text-red-600">{error}</p>}

      <div className="space-y-3 rounded-lg border border-gray-200 bg-white p-5">
        <input
          placeholder="과제 제목"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="w-full border-b border-gray-300 pb-2 text-lg font-semibold focus:border-blue-500 focus:outline-none"
        />
        <textarea
          placeholder="과제 설명 / 요구사항 (선택)"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
          className="w-full text-sm text-gray-600 focus:outline-none"
        />
      </div>

      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-gray-700">평가기준표 (루브릭)</h2>
        <span className="text-sm text-gray-500">만점 {maxScore}점</span>
      </div>

      <div className="space-y-4">
        {criteria.map((c, cIdx) => (
          <div key={c.id} className="space-y-3 rounded-lg border border-gray-200 bg-white p-5">
            <div className="flex items-start gap-3">
              <input
                placeholder={`평가 항목 ${cIdx + 1} (예: 코드 품질)`}
                value={c.title}
                onChange={(e) => updateCriterion(cIdx, { title: e.target.value })}
                className="flex-1 border-b border-gray-300 pb-1 font-medium focus:border-blue-500 focus:outline-none"
              />
              {criteria.length > 1 && (
                <button
                  onClick={() => removeCriterion(cIdx)}
                  className="text-xs text-red-400 hover:text-red-600"
                >
                  항목 삭제
                </button>
              )}
            </div>
            <textarea
              placeholder="이 항목에 대한 설명 (선택)"
              value={c.description ?? ""}
              onChange={(e) => updateCriterion(cIdx, { description: e.target.value })}
              rows={1}
              className="w-full text-sm text-gray-500 focus:outline-none"
            />

            <div className="space-y-2 pl-1">
              <p className="text-xs font-medium text-gray-400">체크 조건</p>
              {c.items.map((item, iIdx) => (
                <div key={item.id} className="flex items-center gap-2">
                  <input
                    value={item.label}
                    onChange={(e) => updateItem(cIdx, iIdx, { label: e.target.value })}
                    placeholder="조건 설명 (예: 변수명이 명확하게 작성됨)"
                    className="flex-1 rounded border border-gray-300 px-2 py-1.5 text-sm"
                  />
                  <input
                    type="number"
                    value={item.points}
                    onChange={(e) => updateItem(cIdx, iIdx, { points: Number(e.target.value) })}
                    className="w-20 rounded border border-gray-300 px-2 py-1.5 text-sm"
                  />
                  <span className="text-xs text-gray-400">점</span>
                  {c.items.length > 1 && (
                    <button
                      onClick={() => removeItem(cIdx, iIdx)}
                      className="text-xs text-gray-400 hover:text-red-500"
                    >
                      삭제
                    </button>
                  )}
                </div>
              ))}
              <button
                onClick={() => addItem(cIdx)}
                className="text-xs font-medium text-blue-600 hover:text-blue-800"
              >
                + 조건 추가
              </button>
            </div>
          </div>
        ))}

        <button
          onClick={addCriterion}
          className="w-full rounded-lg border border-dashed border-gray-300 py-3 text-sm font-medium text-gray-500 hover:border-blue-300 hover:text-blue-600"
        >
          + 평가 항목 추가
        </button>
      </div>

      <div className="fixed inset-x-0 bottom-0 border-t border-gray-200 bg-white p-4">
        <div className="mx-auto flex max-w-5xl justify-end gap-3">
          <button
            onClick={() => navigate("/admin/assignments")}
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
