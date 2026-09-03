import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../api/client";
import type { SurveyListItem } from "../../api/types";

export function AdminSurveysPage() {
  const [surveys, setSurveys] = useState<SurveyListItem[]>([]);
  const [loading, setLoading] = useState(true);

  const load = () =>
    api
      .get<SurveyListItem[]>("/api/admin/surveys")
      .then(setSurveys)
      .finally(() => setLoading(false));
  useEffect(() => {
    load();
  }, []);

  const togglePublish = async (s: SurveyListItem) => {
    await api.post(`/api/admin/surveys/${s.id}/publish`, undefined, { published: !s.is_published });
    load();
  };

  const remove = async (id: string) => {
    if (!confirm("이 설문을 삭제할까요? 응답 데이터도 함께 삭제됩니다.")) return;
    await api.del(`/api/admin/surveys/${id}`);
    load();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-900">설문조사</h1>
        <Link
          to="/admin/surveys/new"
          className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          + 새 설문 만들기
        </Link>
      </div>

      {loading && <p className="text-gray-400">불러오는 중...</p>}
      {!loading && surveys.length === 0 && (
        <p className="rounded-lg border border-dashed border-gray-300 p-8 text-center text-gray-400">
          아직 만든 설문이 없습니다.
        </p>
      )}

      <div className="space-y-3">
        {surveys.map((s) => (
          <div key={s.id} className="rounded-lg border border-gray-200 bg-white p-4">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="font-semibold text-gray-900">{s.title}</h2>
                  <span
                    className={`rounded px-2 py-0.5 text-xs font-medium ${
                      s.is_published ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"
                    }`}
                  >
                    {s.is_published ? "공개중" : "비공개"}
                  </span>
                </div>
                {s.description && <p className="mt-1 text-sm text-gray-500">{s.description}</p>}
                <p className="mt-2 text-xs text-gray-400">응답 {s.response_count}건</p>
              </div>
              <div className="flex shrink-0 flex-wrap gap-2 text-sm">
                <button
                  onClick={() => togglePublish(s)}
                  className="rounded border border-gray-300 px-3 py-1.5 font-medium text-gray-700 hover:bg-gray-50"
                >
                  {s.is_published ? "비공개로 전환" : "공개하기"}
                </button>
                <Link
                  to={`/admin/surveys/${s.id}/edit`}
                  className="rounded border border-gray-300 px-3 py-1.5 font-medium text-gray-700 hover:bg-gray-50"
                >
                  편집
                </Link>
                <Link
                  to={`/admin/surveys/${s.id}/responses`}
                  className="rounded border border-gray-300 px-3 py-1.5 font-medium text-gray-700 hover:bg-gray-50"
                >
                  응답 보기
                </Link>
                <button
                  onClick={() => remove(s.id)}
                  className="rounded border border-red-200 px-3 py-1.5 font-medium text-red-500 hover:bg-red-50"
                >
                  삭제
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
