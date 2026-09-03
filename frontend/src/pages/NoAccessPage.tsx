import { useAuth } from "../auth/AuthContext";

export function NoAccessPage() {
  const { me, logout } = useAuth();

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-gray-50 px-4 text-center">
      <h1 className="text-xl font-bold text-gray-900">접근 권한이 없습니다</h1>
      <p className="max-w-sm text-gray-500">
        {me?.email} 계정은 동아리 명단에 등록되어 있지 않습니다. 담당 관리자에게 등록을
        요청해주세요.
      </p>
      <button
        onClick={logout}
        className="rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-700"
      >
        다른 계정으로 로그인
      </button>
    </div>
  );
}
