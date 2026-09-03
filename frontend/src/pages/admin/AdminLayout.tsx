import { Outlet } from "react-router-dom";
import { TopNav } from "../../components/TopNav";

const links = [
  { to: "/admin", label: "대시보드" },
  { to: "/admin/students", label: "학생 명단" },
  { to: "/admin/admins", label: "관리자" },
  { to: "/admin/surveys", label: "설문조사" },
  { to: "/admin/assignments", label: "과제" },
];

export function AdminLayout() {
  return (
    <div className="min-h-screen bg-gray-50">
      <TopNav links={links} />
      <main className="mx-auto max-w-5xl px-4 py-8">
        <Outlet />
      </main>
    </div>
  );
}
