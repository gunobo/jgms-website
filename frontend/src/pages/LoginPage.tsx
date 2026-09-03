import { GoogleLogin } from "@react-oauth/google";
import { useEffect, useState } from "react";
import { Navigate, useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export function LoginPage() {
  const { me, loading, loginWithGoogle } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (error) setError(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (loading) return null;
  if (me) {
    if (me.role === "unregistered") return <Navigate to="/no-access" replace />;
    return <Navigate to="/" replace />;
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 bg-gray-50 px-4">
      <div className="flex flex-col items-center gap-2 text-center">
        <h1 className="text-2xl font-bold text-gray-900">창의적 소프트웨어 체험·활용반</h1>
        <p className="text-gray-500">학교 구글 계정으로 로그인해주세요</p>
      </div>

      <GoogleLogin
        onSuccess={async (credentialResponse) => {
          if (!credentialResponse.credential) return;
          try {
            const result = await loginWithGoogle(credentialResponse.credential);
            const callbackUrl = params.get("callbackUrl");
            if (result.role === "unregistered") {
              navigate("/no-access", { replace: true });
            } else {
              navigate(callbackUrl || "/", { replace: true });
            }
          } catch {
            setError("로그인에 실패했습니다. 다시 시도해주세요.");
          }
        }}
        onError={() => setError("구글 로그인에 실패했습니다.")}
        text="signin_with"
      />

      {error && <p className="text-sm text-red-600">{error}</p>}
    </div>
  );
}
