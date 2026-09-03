import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../../api/client";
import type { ResponseOut, SurveyDetail } from "../../api/types";
import { SheetLinkPanel } from "../../components/SheetLinkPanel";

export function AdminSurveyResponsesPage() {
  const { id } = useParams();
  const [survey, setSurvey] = useState<SurveyDetail | null>(null);
  const [responses, setResponses] = useState<ResponseOut[]>([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    if (!id) return;
    Promise.all([
      api.get<SurveyDetail>(`/api/admin/surveys/${id}`),
      api.get<ResponseOut[]>(`/api/admin/surveys/${id}/responses`),
    ])
      .then(([s, r]) => {
        setSurvey(s);
        setResponses(r);
      })
      .finally(() => setLoading(false));
  };
  useEffect(load, [id]);

  if (loading || !survey) return <p className="text-gray-400">불러오는 중...</p>;

  const answerFor = (r: ResponseOut, qId: string) => {
    const a = r.answers.find((a) => a.question_id === qId);
    if (!a) return "-";
    if (a.values && a.values.length > 0) return a.values.join(", ");
    return a.value || "-";
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-gray-900">{survey.title} - 응답</h1>
        <p className="text-sm text-gray-500">총 {responses.length}건 응답</p>
      </div>

      <SheetLinkPanel
        sheetId={survey.sheet_id}
        onLink={async (url) => {
          await api.post(`/api/admin/surveys/${id}/sheet`, { sheet_url_or_id: url });
          load();
        }}
        onUnlink={async () => {
          await api.del(`/api/admin/surveys/${id}/sheet`);
          load();
        }}
      />

      <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-left text-gray-500">
            <tr>
              <th className="whitespace-nowrap px-4 py-2">제출 시각</th>
              <th className="whitespace-nowrap px-4 py-2">이름</th>
              <th className="whitespace-nowrap px-4 py-2">학번</th>
              {survey.questions.map((q) => (
                <th key={q.id} className="whitespace-nowrap px-4 py-2">
                  {q.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {responses.length === 0 && (
              <tr>
                <td colSpan={survey.questions.length + 3} className="px-4 py-6 text-center text-gray-400">
                  아직 응답이 없습니다.
                </td>
              </tr>
            )}
            {responses.map((r) => (
              <tr key={r.id} className="border-t border-gray-100">
                <td className="whitespace-nowrap px-4 py-2 text-gray-500">
                  {new Date(r.submitted_at).toLocaleString("ko-KR")}
                </td>
                <td className="whitespace-nowrap px-4 py-2">{r.student_name}</td>
                <td className="whitespace-nowrap px-4 py-2">{r.student_number}</td>
                {survey.questions.map((q) => (
                  <td key={q.id} className="max-w-xs px-4 py-2">
                    {answerFor(r, q.id)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
