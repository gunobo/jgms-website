import { useState } from "react";
import { ApiError, api } from "../api/client";

type FieldKey = "ignore" | "name" | "student_id" | "email" | "grade" | "class_name";

const FIELD_LABELS: Record<FieldKey, string> = {
  ignore: "무시",
  name: "이름",
  student_id: "학번",
  email: "이메일",
  grade: "학년",
  class_name: "반",
};

interface Props {
  onImported: () => void;
}

export function SheetImportPanel({ onImported }: Props) {
  const [sheetUrl, setSheetUrl] = useState("");
  const [range, setRange] = useState("A2:E200");
  const [rows, setRows] = useState<string[][] | null>(null);
  const [mapping, setMapping] = useState<FieldKey[]>([]);
  const [emailPattern, setEmailPattern] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{ created: number; skipped: string[] } | null>(null);

  const columnCount = rows ? Math.max(0, ...rows.map((r) => r.length)) : 0;

  const preview = async () => {
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const res = await api.post<{ rows: string[][] }>("/api/admin/students/sheet-preview", {
        sheet_url_or_id: sheetUrl,
        range,
      });
      setRows(res.rows);
      const count = Math.max(0, ...res.rows.map((r) => r.length));
      setMapping(Array.from({ length: count }, () => "ignore" as FieldKey));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "미리보기를 불러오지 못했습니다.");
      setRows(null);
    } finally {
      setBusy(false);
    }
  };

  const hasEmailColumn = mapping.includes("email");

  const doImport = async () => {
    if (!rows) return;
    if (!mapping.includes("name") || !mapping.includes("student_id")) {
      setError("이름과 학번 열은 반드시 지정해주세요.");
      return;
    }
    if (!hasEmailColumn && !emailPattern.includes("{학번}")) {
      setError("이메일 열이 없으면 이메일 생성 규칙에 {학번}을 포함해주세요.");
      return;
    }

    const nameIdx = mapping.indexOf("name");
    const idIdx = mapping.indexOf("student_id");
    const emailIdx = mapping.indexOf("email");
    const gradeIdx = mapping.indexOf("grade");
    const classIdx = mapping.indexOf("class_name");

    const students = rows
      .filter((r) => (r[nameIdx] ?? "").trim() && (r[idIdx] ?? "").trim())
      .map((r) => {
        const studentId = (r[idIdx] ?? "").trim();
        const email = hasEmailColumn
          ? (r[emailIdx] ?? "").trim()
          : emailPattern.replace("{학번}", studentId);
        return {
          name: (r[nameIdx] ?? "").trim(),
          student_id: studentId,
          email,
          grade: gradeIdx >= 0 ? (r[gradeIdx] ?? "").trim() || undefined : undefined,
          class_name: classIdx >= 0 ? (r[classIdx] ?? "").trim() || undefined : undefined,
        };
      });

    setBusy(true);
    setError(null);
    try {
      const res = await api.post<{ created: number; skipped: string[] }>("/api/admin/students/import", {
        students,
      });
      setResult(res);
      onImported();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "가져오기에 실패했습니다.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-3 rounded-lg border border-gray-200 bg-white p-5">
      <h2 className="font-semibold text-gray-900">시트에서 가져오기</h2>
      <p className="text-xs text-gray-500">
        이미 다른 곳에 적어둔 명단이 있을 때, 그 스프레드시트에서 범위를 지정해 한 번에 가져옵니다.
        (서비스 계정과 공유되어 있어야 합니다)
      </p>

      <div className="flex flex-wrap gap-2">
        <input
          placeholder="스프레드시트 URL 또는 ID"
          value={sheetUrl}
          onChange={(e) => setSheetUrl(e.target.value)}
          className="min-w-[240px] flex-1 rounded border border-gray-300 px-3 py-2 text-sm"
        />
        <input
          placeholder="범위 (예: A2:E200)"
          value={range}
          onChange={(e) => setRange(e.target.value)}
          className="w-40 rounded border border-gray-300 px-3 py-2 text-sm"
        />
        <button
          onClick={preview}
          disabled={busy || !sheetUrl.trim() || !range.trim()}
          className="rounded border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
        >
          미리보기
        </button>
      </div>

      {error && <p className="text-xs text-red-600">{error}</p>}

      {rows && rows.length > 0 && (
        <div className="space-y-3">
          <div className="overflow-x-auto rounded border border-gray-200">
            <table className="w-full text-xs">
              <thead className="bg-gray-50">
                <tr>
                  {Array.from({ length: columnCount }, (_, i) => (
                    <th key={i} className="px-2 py-1">
                      <select
                        value={mapping[i] ?? "ignore"}
                        onChange={(e) =>
                          setMapping((m) => {
                            const next = [...m];
                            next[i] = e.target.value as FieldKey;
                            return next;
                          })
                        }
                        className="rounded border border-gray-300 px-1 py-0.5 text-xs"
                      >
                        {(Object.keys(FIELD_LABELS) as FieldKey[]).map((k) => (
                          <option key={k} value={k}>
                            {FIELD_LABELS[k]}
                          </option>
                        ))}
                      </select>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.slice(0, 8).map((r, ri) => (
                  <tr key={ri} className="border-t border-gray-100">
                    {Array.from({ length: columnCount }, (_, ci) => (
                      <td key={ci} className="px-2 py-1 text-gray-600">
                        {r[ci] ?? ""}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {rows.length > 8 && (
            <p className="text-xs text-gray-400">...외 {rows.length - 8}행 더</p>
          )}

          {!hasEmailColumn && (
            <div className="space-y-1">
              <label className="text-xs font-medium text-gray-600">
                이메일 열이 없어요 — 자동 생성 규칙 (예: 26{"{학번}"}@jeonggwan.ms.kr)
              </label>
              <input
                value={emailPattern}
                onChange={(e) => setEmailPattern(e.target.value)}
                placeholder="26{학번}@jeonggwan.ms.kr"
                className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
              />
            </div>
          )}

          <button
            onClick={doImport}
            disabled={busy}
            className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {busy ? "가져오는 중..." : "가져오기"}
          </button>
        </div>
      )}

      {result && (
        <p className="text-xs text-gray-500">
          {result.created}명 추가됨
          {result.skipped.length > 0 && `, ${result.skipped.length}건 건너뜀 (중복/형식 오류)`}
        </p>
      )}
    </div>
  );
}
