import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../api/client";
import type { SurveyListItem } from "../../api/types";

export function StudentSurveysPage() {
  const [surveys, setSurveys] = useState<SurveyListItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<SurveyListItem[]>("/api/surveys")
      .then(setSurveys)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold text-gray-900">설문조사</h1>
      {loading && <p className="text-gray-400">불러오는 중...</p>}
      {!loading && surveys.length === 0 && (
        <p className="rounded-lg border border-dashed border-gray-300 p-8 text-center text-gray-400">
          현재 참여할 수 있는 설문이 없습니다.
        </p>
      )}
      <div className="space-y-3">
        {surveys.map((s) => (
          <div key={s.id} className="rounded-lg border border-gray-200 bg-white p-4">
            <div className="flex items-center justify-between gap-4">
              <div>
                <h2 className="font-semibold text-gray-900">{s.title}</h2>
                {s.description && <p className="mt-1 text-sm text-gray-500">{s.description}</p>}
              </div>
              {s.already_submitted && !s.allow_multiple_responses ? (
                <span className="shrink-0 rounded bg-gray-100 px-3 py-1.5 text-xs font-medium text-gray-500">
                  제출 완료
                </span>
              ) : (
                <Link
                  to={`/surveys/${s.id}`}
                  className="shrink-0 rounded bg-blue-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
                >
                  {s.already_submitted ? "다시 응답하기" : "응답하기"}
                </Link>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
