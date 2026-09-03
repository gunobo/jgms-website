import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../api/client";
import type { AssignmentListItem, Student, SurveyListItem } from "../../api/types";

export function AdminDashboardPage() {
  const [students, setStudents] = useState<Student[]>([]);
  const [surveys, setSurveys] = useState<SurveyListItem[]>([]);
  const [assignments, setAssignments] = useState<AssignmentListItem[]>([]);

  useEffect(() => {
    api.get<Student[]>("/api/admin/students").then(setStudents).catch(() => {});
    api.get<SurveyListItem[]>("/api/admin/surveys").then(setSurveys).catch(() => {});
    api.get<AssignmentListItem[]>("/api/admin/assignments").then(setAssignments).catch(() => {});
  }, []);

  const cards = [
    { label: "학생 수", value: students.length, to: "/admin/students" },
    {
      label: "공개된 설문",
      value: surveys.filter((s) => s.is_published).length,
      to: "/admin/surveys",
    },
    {
      label: "공개된 과제",
      value: assignments.filter((a) => a.is_published).length,
      to: "/admin/assignments",
    },
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold text-gray-900">대시보드</h1>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {cards.map((c) => (
          <Link
            key={c.label}
            to={c.to}
            className="rounded-lg border border-gray-200 bg-white p-5 hover:border-blue-300"
          >
            <p className="text-sm text-gray-500">{c.label}</p>
            <p className="mt-1 text-2xl font-bold text-gray-900">{c.value}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
