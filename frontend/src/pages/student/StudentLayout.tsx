import { Outlet } from "react-router-dom";
import { TopNav } from "../../components/TopNav";

const links = [
  { to: "/surveys", label: "설문조사" },
  { to: "/assignments", label: "과제" },
];

export function StudentLayout() {
  return (
    <div className="min-h-screen bg-gray-50">
      <TopNav links={links} />
      <main className="mx-auto max-w-3xl px-4 py-8">
        <Outlet />
      </main>
    </div>
  );
}
