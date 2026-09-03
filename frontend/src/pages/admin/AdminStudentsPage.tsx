import { useEffect, useState } from "react";
import { ApiError, api } from "../../api/client";
import type { Student } from "../../api/types";

export function AdminStudentsPage() {
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [form, setForm] = useState({ name: "", studentId: "", email: "", grade: "", className: "" });
  const [bulkText, setBulkText] = useState("");
  const [bulkResult, setBulkResult] = useState<{ created: number; skipped: string[] } | null>(null);

  const load = () => {
    setLoading(true);
    api
      .get<Student[]>("/api/admin/students")
      .then(setStudents)
      .catch((e) => setError(e instanceof ApiError ? e.message : "불러오기에 실패했습니다."))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const addStudent = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await api.post("/api/admin/students", {
        name: form.name,
        student_id: form.studentId,
        email: form.email,
        grade: form.grade || undefined,
        class_name: form.className || undefined,
      });
      setForm({ name: "", studentId: "", email: "", grade: "", className: "" });
      load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "추가에 실패했습니다.");
    }
  };

  const addBulk = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setBulkResult(null);
    try {
      const result = await api.post<{ created: number; skipped: string[] }>(
        "/api/admin/students/bulk",
        { text: bulkText }
      );
      setBulkResult(result);
      setBulkText("");
      load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "일괄 추가에 실패했습니다.");
    }
  };

  const remove = async (id: string) => {
    if (!confirm("이 학생을 명단에서 삭제할까요?")) return;
    try {
      await api.del(`/api/admin/students/${id}`);
      load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "삭제에 실패했습니다.");
    }
  };

  return (
    <div className="space-y-8">
      <h1 className="text-xl font-bold text-gray-900">학생 명단 관리</h1>
      {error && <p className="rounded bg-red-50 p-3 text-sm text-red-600">{error}</p>}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <form onSubmit={addStudent} className="space-y-3 rounded-lg border border-gray-200 bg-white p-5">
          <h2 className="font-semibold text-gray-900">학생 한 명 추가</h2>
          <input
            required
            placeholder="이름"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
          />
          <input
            required
            placeholder="학번"
            value={form.studentId}
            onChange={(e) => setForm({ ...form, studentId: e.target.value })}
            className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
          />
          <input
            required
            type="email"
            placeholder="학교 구글 이메일"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
          />
          <div className="flex gap-3">
            <input
              placeholder="학년 (선택)"
              value={form.grade}
              onChange={(e) => setForm({ ...form, grade: e.target.value })}
              className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
            />
            <input
              placeholder="반 (선택)"
              value={form.className}
              onChange={(e) => setForm({ ...form, className: e.target.value })}
              className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
            />
          </div>
          <button className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">
            추가
          </button>
        </form>

        <form onSubmit={addBulk} className="space-y-3 rounded-lg border border-gray-200 bg-white p-5">
          <h2 className="font-semibold text-gray-900">여러 명 한번에 추가</h2>
          <p className="text-xs text-gray-500">
            한 줄에 한 명씩, <code>이름,학번,이메일,학년,반</code> 형식 (학년/반은 생략 가능)
          </p>
          <textarea
            value={bulkText}
            onChange={(e) => setBulkText(e.target.value)}
            rows={6}
            placeholder={"김학생,10101,student1@jgms.hs.kr,1,1\n이학생,10102,student2@jgms.hs.kr"}
            className="w-full rounded border border-gray-300 px-3 py-2 font-mono text-xs"
          />
          <button className="rounded bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-700">
            일괄 추가
          </button>
          {bulkResult && (
            <p className="text-xs text-gray-500">
              {bulkResult.created}명 추가됨
              {bulkResult.skipped.length > 0 && `, ${bulkResult.skipped.length}건 건너뜀 (중복/형식 오류)`}
            </p>
          )}
        </form>
      </div>

      <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-left text-gray-500">
            <tr>
              <th className="px-4 py-2">이름</th>
              <th className="px-4 py-2">학번</th>
              <th className="px-4 py-2">이메일</th>
              <th className="px-4 py-2">학년/반</th>
              <th className="px-4 py-2"></th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr>
                <td colSpan={5} className="px-4 py-6 text-center text-gray-400">
                  불러오는 중...
                </td>
              </tr>
            )}
            {!loading && students.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-6 text-center text-gray-400">
                  등록된 학생이 없습니다.
                </td>
              </tr>
            )}
            {students.map((s) => (
              <tr key={s.id} className="border-t border-gray-100">
                <td className="px-4 py-2">{s.name}</td>
                <td className="px-4 py-2">{s.student_id}</td>
                <td className="px-4 py-2">{s.email}</td>
                <td className="px-4 py-2">
                  {[s.grade, s.class_name].filter(Boolean).join(" / ") || "-"}
                </td>
                <td className="px-4 py-2 text-right">
                  <button
                    onClick={() => remove(s.id)}
                    className="text-xs font-medium text-red-500 hover:text-red-700"
                  >
                    삭제
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
