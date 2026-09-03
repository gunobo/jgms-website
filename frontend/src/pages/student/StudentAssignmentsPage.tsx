import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../api/client";
import type { AssignmentListItem } from "../../api/types";

export function StudentAssignmentsPage() {
  const [assignments, setAssignments] = useState<AssignmentListItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<AssignmentListItem[]>("/api/assignments")
      .then(setAssignments)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold text-gray-900">과제</h1>
      {loading && <p className="text-gray-400">불러오는 중...</p>}
      {!loading && assignments.length === 0 && (
        <p className="rounded-lg border border-dashed border-gray-300 p-8 text-center text-gray-400">
          현재 제출할 수 있는 과제가 없습니다.
        </p>
      )}
      <div className="space-y-3">
        {assignments.map((a) => (
          <Link
            key={a.id}
            to={`/assignments/${a.id}`}
            className="block rounded-lg border border-gray-200 bg-white p-4 hover:border-blue-300"
          >
            <div className="flex items-center justify-between gap-4">
              <div>
                <h2 className="font-semibold text-gray-900">{a.title}</h2>
                {a.description && <p className="mt-1 text-sm text-gray-500">{a.description}</p>}
                <p className="mt-2 text-xs text-gray-400">만점 {a.max_score}점</p>
              </div>
              <div className="shrink-0 text-right">
                {a.my_score !== null ? (
                  <span className="rounded bg-green-100 px-3 py-1.5 text-xs font-medium text-green-700">
                    {a.my_score} / {a.max_score}점
                  </span>
                ) : a.already_submitted ? (
                  <span className="rounded bg-gray-100 px-3 py-1.5 text-xs font-medium text-gray-500">
                    제출 완료 (채점 대기)
                  </span>
                ) : (
                  <span className="rounded bg-blue-600 px-3 py-1.5 text-xs font-medium text-white">제출하기</span>
                )}
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
