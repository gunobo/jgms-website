import { NavLink } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export function TopNav({ links }: { links: { to: string; label: string }[] }) {
  const { me, logout } = useAuth();

  return (
    <header className="border-b border-gray-200 bg-white">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
        <div className="flex items-center gap-6">
          <span className="font-bold text-gray-900">창의적 소프트웨어 체험·활용반</span>
          <nav className="flex gap-4">
            {links.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                className={({ isActive }) =>
                  `text-sm font-medium ${
                    isActive ? "text-blue-600" : "text-gray-500 hover:text-gray-800"
                  }`
                }
              >
                {link.label}
              </NavLink>
            ))}
          </nav>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-500">{me?.name ?? me?.email}</span>
          <button onClick={logout} className="text-sm font-medium text-gray-500 hover:text-gray-800">
            로그아웃
          </button>
        </div>
      </div>
    </header>
  );
}
