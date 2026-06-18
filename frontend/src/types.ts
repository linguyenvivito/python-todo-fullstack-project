export type ApiRequestOptions = Omit<RequestInit, "headers"> & {
  headers?: Record<string, string>;
};

export type AuthSessionPayload = {
  user: {
    username: string;
  };
  access_token: string;
  refresh_token: string;
};

export type StoredSession = {
  username: string;
  accessToken: string;
  refreshToken: string;
};

export type AuthRequestOperation<T = unknown> = (accessToken: string) => Promise<T>;

export type WithAuthenticatedRequest = <T>(operation: AuthRequestOperation<T>) => Promise<T>;

export type TaskStatus = "todo" | "in_progress" | "done" | "archived";

export type Task = {
  id: number;
  title: string;
  description: string | null;
  status: TaskStatus;
  created_at?: string;
};

export type TaskCreatePayload = {
  title: string;
  description: string | null;
};

export type TaskUpdatePayload = Partial<{
  title: string;
  description: string | null;
  status: TaskStatus;
}>;

export type Role = {
  id: number;
  name: string;
};

export type EmailField = {
  name: string;
  label: string;
  placeholder?: string;
  required?: boolean;
};

export type EmailTemplate = {
  name: string;
  display_name: string;
  description?: string;
  fields: EmailField[];
};

export type TemplateData = Record<string, string>;

export type EmailPayloadManual = {
  to_email: string;
  subject: string;
  body: string;
};

export type EmailPayloadTemplate = {
  to_email: string;
  template_name: string;
  template_data: TemplateData;
};

export type AuditLogQuery = {
  action: string | null;
  success: boolean | null;
  occurred_from: number | null;
  occurred_to: number | null;
  limit: number;
  offset: number;
};

export type AuditLogEntry = {
  id: number;
  occurred_at: number;
  action: string;
  success: boolean;
  actor_user_id: string | null;
  status_code?: string;
  path?: string;
  details?: unknown;
};
