import { useEffect, useState } from "react";
import { ApiError, api } from "../../api/client";
import type { Admin } from "../../api/types";
import { useAuth } from "../../auth/AuthContext";

export function AdminAdminsPage() {
  const { me } = useAuth();
  const [admins, setAdmins] = useState<Admin[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({ email: "", name: "" });

  const load = () => api.get<Admin[]>("/api/admin/admins").then(setAdmins).catch(() => {});
  useEffect(() => {
    load();
  }, []);

  const addAdmin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await api.post("/api/admin/admins", { email: form.email, name: form.name || undefined });
      setForm({ email: "", name: "" });
      load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "추가에 실패했습니다.");
    }
  };

  const remove = async (id: string) => {
    if (!confirm("이 관리자를 삭제할까요?")) return;
    try {
      await api.del(`/api/admin/admins/${id}`);
      load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "삭제에 실패했습니다.");
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold text-gray-900">관리자 관리</h1>
      {error && <p className="rounded bg-red-50 p-3 text-sm text-red-600">{error}</p>}

      <form onSubmit={addAdmin} className="flex flex-wrap gap-3 rounded-lg border border-gray-200 bg-white p-5">
        <input
          required
          type="email"
          placeholder="학교 구글 이메일"
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
          className="min-w-[220px] flex-1 rounded border border-gray-300 px-3 py-2 text-sm"
        />
        <input
          placeholder="이름 (선택)"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
          className="min-w-[160px] flex-1 rounded border border-gray-300 px-3 py-2 text-sm"
        />
        <button className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">
          관리자 추가
        </button>
      </form>

      <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-left text-gray-500">
            <tr>
              <th className="px-4 py-2">이름</th>
              <th className="px-4 py-2">이메일</th>
              <th className="px-4 py-2"></th>
            </tr>
          </thead>
          <tbody>
            {admins.map((a) => (
              <tr key={a.id} className="border-t border-gray-100">
                <td className="px-4 py-2">{a.name || "-"}</td>
                <td className="px-4 py-2">{a.email}</td>
                <td className="px-4 py-2 text-right">
                  {a.email !== me?.email && (
                    <button
                      onClick={() => remove(a.id)}
                      className="text-xs font-medium text-red-500 hover:text-red-700"
                    >
                      삭제
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
