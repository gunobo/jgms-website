export type Role = "admin" | "student" | "unregistered";

export interface Me {
  email: string;
  role: Role;
  name: string | null;
  user_id: string | null;
}

export interface Student {
  id: string;
  name: string;
  student_id: string;
  email: string;
  grade: string | null;
  class_name: string | null;
  created_at: string;
}

export interface Admin {
  id: string;
  email: string;
  name: string | null;
  created_at: string;
}

export type QuestionType =
  | "SHORT_TEXT"
  | "PARAGRAPH"
  | "SINGLE_CHOICE"
  | "MULTIPLE_CHOICE"
  | "DROPDOWN"
  | "LINEAR_SCALE";

export interface LinearScaleOptions {
  min: number;
  max: number;
  min_label?: string | null;
  max_label?: string | null;
}

export interface QuestionInput {
  id?: string;
  type: QuestionType;
  label: string;
  description?: string | null;
  required: boolean;
  choices?: string[] | null;
  linear_scale?: LinearScaleOptions | null;
  order: number;
}

export interface Question extends QuestionInput {
  id: string;
}

export interface SurveyListItem {
  id: string;
  title: string;
  description: string | null;
  is_published: boolean;
  allow_multiple_responses: boolean;
  created_at: string;
  response_count: number;
  already_submitted: boolean;
}

export interface SurveyDetail {
  id: string;
  title: string;
  description: string | null;
  is_published: boolean;
  allow_multiple_responses: boolean;
  sheet_id: string | null;
  sheet_tab: string | null;
  created_at: string;
  questions: Question[];
  already_submitted: boolean;
}

export interface AnswerOut {
  question_id: string;
  value: string | null;
  values: string[] | null;
}

export interface ResponseOut {
  id: string;
  submitted_at: string;
  student_name: string;
  student_number: string;
  synced_to_sheet: boolean;
  answers: AnswerOut[];
}

// --- Assignments / Rubric grading ---

export interface RubricItemInput {
  id?: string;
  label: string;
  points: number;
  order: number;
}

export interface RubricItem extends RubricItemInput {
  id: string;
}

export interface RubricCriterionInput {
  id?: string;
  title: string;
  description?: string | null;
  order: number;
  items: RubricItemInput[];
}

export interface RubricCriterion extends RubricCriterionInput {
  id: string;
  items: RubricItem[];
}

export interface AssignmentListItem {
  id: string;
  title: string;
  description: string | null;
  is_published: boolean;
  created_at: string;
  max_score: number;
  submission_count: number;
  already_submitted: boolean;
  my_score: number | null;
}

export interface AssignmentDetail {
  id: string;
  title: string;
  description: string | null;
  is_published: boolean;
  sheet_id: string | null;
  rubric_sheet_tab: string | null;
  scores_sheet_tab: string | null;
  created_at: string;
  criteria: RubricCriterion[];
  max_score: number;
}

export interface SubmissionOut {
  id: string;
  link_url: string | null;
  text_content: string | null;
  file_name: string | null;
  submitted_at: string;
  updated_at: string;
}

export interface GradeOut {
  id: string;
  checked_item_ids: string[];
  total_score: number;
  max_score: number;
  comment: string | null;
  graded_at: string;
  graded_by_name: string | null;
}

export interface SubmissionWithGradeOut {
  submission: SubmissionOut;
  student_name: string;
  student_number: string;
  grade: GradeOut | null;
}

export interface MySubmissionOut {
  submission: SubmissionOut | null;
  grade: GradeOut | null;
}
