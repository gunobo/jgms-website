import { Route, Routes } from "react-router-dom";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { HomePage } from "./pages/HomePage";
import { LoginPage } from "./pages/LoginPage";
import { NoAccessPage } from "./pages/NoAccessPage";

import { AdminLayout } from "./pages/admin/AdminLayout";
import { AdminDashboardPage } from "./pages/admin/AdminDashboardPage";
import { AdminStudentsPage } from "./pages/admin/AdminStudentsPage";
import { AdminAdminsPage } from "./pages/admin/AdminAdminsPage";
import { AdminSurveysPage } from "./pages/admin/AdminSurveysPage";
import { AdminSurveyBuilderPage } from "./pages/admin/AdminSurveyBuilderPage";
import { AdminSurveyResponsesPage } from "./pages/admin/AdminSurveyResponsesPage";
import { AdminAssignmentsPage } from "./pages/admin/AdminAssignmentsPage";
import { AdminAssignmentBuilderPage } from "./pages/admin/AdminAssignmentBuilderPage";
import { AdminAssignmentGradingPage } from "./pages/admin/AdminAssignmentGradingPage";

import { StudentLayout } from "./pages/student/StudentLayout";
import { StudentSurveysPage } from "./pages/student/StudentSurveysPage";
import { StudentSurveyTakePage } from "./pages/student/StudentSurveyTakePage";
import { StudentAssignmentsPage } from "./pages/student/StudentAssignmentsPage";
import { StudentAssignmentDetailPage } from "./pages/student/StudentAssignmentDetailPage";

function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/no-access" element={<NoAccessPage />} />

      <Route
        path="/admin"
        element={
          <ProtectedRoute role="admin">
            <AdminLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<AdminDashboardPage />} />
        <Route path="students" element={<AdminStudentsPage />} />
        <Route path="admins" element={<AdminAdminsPage />} />
        <Route path="surveys" element={<AdminSurveysPage />} />
        <Route path="surveys/new" element={<AdminSurveyBuilderPage />} />
        <Route path="surveys/:id/edit" element={<AdminSurveyBuilderPage />} />
        <Route path="surveys/:id/responses" element={<AdminSurveyResponsesPage />} />
        <Route path="assignments" element={<AdminAssignmentsPage />} />
        <Route path="assignments/new" element={<AdminAssignmentBuilderPage />} />
        <Route path="assignments/:id/edit" element={<AdminAssignmentBuilderPage />} />
        <Route path="assignments/:id/submissions" element={<AdminAssignmentGradingPage />} />
      </Route>

      <Route
        path="/"
        element={
          <ProtectedRoute role="student">
            <StudentLayout />
          </ProtectedRoute>
        }
      >
        <Route path="surveys" element={<StudentSurveysPage />} />
        <Route path="surveys/:id" element={<StudentSurveyTakePage />} />
        <Route path="assignments" element={<StudentAssignmentsPage />} />
        <Route path="assignments/:id" element={<StudentAssignmentDetailPage />} />
      </Route>
    </Routes>
  );
}

export default App;
