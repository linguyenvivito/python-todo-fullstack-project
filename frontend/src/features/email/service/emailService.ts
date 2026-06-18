import { getEmailTemplates, sendEmail } from "../api/emailApi";
import type {
  EmailField,
  EmailPayloadManual,
  EmailPayloadTemplate,
  EmailTemplate,
  TemplateData,
  WithAuthenticatedRequest,
} from "../../../types";

/**
 * Create an empty field map for template fields.
 */
export function emptyFieldMap(fields: EmailField[] = []): TemplateData {
  const entries = fields.map((field) => [field.name, ""]);
  return Object.fromEntries(entries) as TemplateData;
}

/**
 * Fetch all email templates.
 */
export async function fetchEmailTemplates(
  withAuthenticatedRequest: WithAuthenticatedRequest
): Promise<EmailTemplate[]> {
  const payload = await withAuthenticatedRequest((token) => getEmailTemplates(token));
  return payload?.items || [];
}

/**
 * Build an email payload for manual or template mode.
 */
export function buildEmailPayload(
  mode: "manual" | "template",
  toEmail: string,
  subject: string,
  body: string,
  selectedTemplate: string,
  templateData: TemplateData
): EmailPayloadManual | EmailPayloadTemplate {
  if (mode === "template") {
    return {
      to_email: toEmail,
      template_name: selectedTemplate,
      template_data: templateData,
    };
  }

  return {
    to_email: toEmail,
    subject,
    body,
  };
}

/**
 * Send an email with the given payload.
 */
export async function sendEmailPayload(
  withAuthenticatedRequest: WithAuthenticatedRequest,
  payload: EmailPayloadManual | EmailPayloadTemplate,
  accessToken?: string
): Promise<{ detail: string }> {
  return withAuthenticatedRequest((token) =>
    sendEmail(token || accessToken || "", payload)
  );
}
