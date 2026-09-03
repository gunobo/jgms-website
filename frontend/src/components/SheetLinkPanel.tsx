import { useEffect, useState } from "react";
import { ApiError, api } from "../api/client";

interface Props {
  sheetId: string | null;
  onLink: (sheetUrlOrId: string) => Promise<void>;
  onUnlink: () => Promise<void>;
  extraAction?: { label: string; onClick: () => Promise<void> };
}

export function SheetLinkPanel({ sheetId, onLink, onUnlink, extraAction }: Props) {
  const [config, setConfig] = useState<{ sheets_configured: boolean; service_account_email: string | null }>();
  const [url, setUrl] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<{ sheets_configured: boolean; service_account_email: string | null }>("/api/admin/config")
      .then(setConfig)
      .catch(() => {});
  }, []);

  if (!config) return null;

  if (!config.sheets_configured) {
    return (
      <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-4 text-sm text-yellow-800">
        서버에 Google Sheets 서비스 계정이 설정되어 있지 않아 시트 연동을 사용할 수 없습니다.
      </div>
    );
  }

  return (
    <div className="space-y-3 rounded-lg border border-gray-200 bg-white p-5">
      <h2 className="font-semibold text-gray-900">Google 스프레드시트 연동</h2>
      {sheetId ? (
        <div className="space-y-2 text-sm">
          <p className="text-gray-600">
            연결된 시트 ID: <code className="rounded bg-gray-100 px-1.5 py-0.5">{sheetId}</code>
          </p>
          <div className="flex gap-2">
            {extraAction && (
              <button
                onClick={async () => {
                  setBusy(true);
                  await extraAction.onClick().catch((e) => setError(e instanceof ApiError ? e.message : "실패했습니다."));
                  setBusy(false);
                }}
                disabled={busy}
                className="rounded border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50"
              >
                {extraAction.label}
              </button>
            )}
            <button
              onClick={async () => {
                setBusy(true);
                await onUnlink().catch(() => {});
                setBusy(false);
              }}
              disabled={busy}
              className="rounded border border-red-200 px-3 py-1.5 text-xs font-medium text-red-500 hover:bg-red-50"
            >
              연결 해제
            </button>
          </div>
        </div>
      ) : (
        <>
          <p className="text-xs text-gray-500">
            아래 서비스 계정 이메일을 대상 스프레드시트에 <b>편집자</b>로 공유한 뒤 연결해주세요. 다른
            설문/과제와 같은 시트를 공유해도 탭이 자동으로 분리되니, 과제별로 별도 시트를 쓰고 싶다면
            각각 다른 스프레드시트 URL을 붙여넣으면 됩니다.
          </p>
          <p className="rounded bg-gray-50 px-2 py-1.5 font-mono text-xs text-gray-700">
            {config.service_account_email}
          </p>
          <div className="flex flex-wrap gap-2">
            <input
              placeholder="스프레드시트 URL 또는 ID"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="min-w-[240px] flex-1 rounded border border-gray-300 px-3 py-2 text-sm"
            />
            <button
              onClick={async () => {
                setBusy(true);
                setError(null);
                try {
                  await onLink(url);
                  setUrl("");
                } catch (e) {
                  setError(e instanceof ApiError ? e.message : "연결에 실패했습니다.");
                } finally {
                  setBusy(false);
                }
              }}
              disabled={busy || !url.trim()}
              className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              연결
            </button>
          </div>
        </>
      )}
      {error && <p className="text-xs text-red-600">{error}</p>}
    </div>
  );
}
