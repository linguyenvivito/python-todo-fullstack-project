import { FormEvent, useCallback, useMemo, useState } from "react";
import {
  emptyFieldMap,
  fetchEmailTemplates,
  buildEmailPayload,
  sendEmailPayload,
} from "../service/emailService";
import type {
  EmailField,
  EmailTemplate,
  TemplateData,
  WithAuthenticatedRequest,
} from "../../../types";

export function useEmailComposer(accessToken: string, withAuthenticatedRequest: WithAuthenticatedRequest) {
  const [mode, setMode] = useState<"manual" | "template">("manual");
  const [toEmail, setToEmail] = useState("");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [templates, setTemplates] = useState<EmailTemplate[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState("");
  const [templateData, setTemplateData] = useState<TemplateData>({});
  const [loadingTemplates, setLoadingTemplates] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  const currentTemplate = useMemo(
    () => templates.find((template) => template.name === selectedTemplate) || null,
    [templates, selectedTemplate]
  );

  const loadTemplates = useCallback(async () => {
    setLoadingTemplates(true);
    setError("");
    try {
      const items = await fetchEmailTemplates(withAuthenticatedRequest);
      setTemplates(items);
      if (items.length > 0 && !selectedTemplate) {
        setSelectedTemplate(items[0].name);
        setTemplateData(emptyFieldMap(items[0].fields));
      }
    } catch (err) {
      setError(err.message || "Failed to load templates");
    } finally {
      setLoadingTemplates(false);
    }
  }, [accessToken, selectedTemplate, withAuthenticatedRequest]);

  function selectTemplate(name: string) {
    setSelectedTemplate(name);
    const next = templates.find((template) => template.name === name);
    setTemplateData(emptyFieldMap(next?.fields || []));
  }

  function updateTemplateField(fieldName: string, value: string) {
    setTemplateData((current) => ({
      ...current,
      [fieldName]: value,
    }));
  }

  async function submitEmail(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    setSuccessMessage("");

    const payload = buildEmailPayload(mode, toEmail, subject, body, selectedTemplate, templateData);

    try {
      const result = await sendEmailPayload(withAuthenticatedRequest, payload, accessToken);
      setSuccessMessage(result?.detail || "Email sent");
      setToEmail("");
      if (mode === "manual") {
        setSubject("");
        setBody("");
      } else {
        setTemplateData(emptyFieldMap(currentTemplate?.fields || []));
      }
    } catch (err) {
      setError(err.message || "Failed to send email");
    } finally {
      setSubmitting(false);
    }
  }

  return {
    mode,
    setMode,
    toEmail,
    setToEmail,
    subject,
    setSubject,
    body,
    setBody,
    templates,
    selectedTemplate,
    selectTemplate,
    templateData,
    updateTemplateField,
    loadingTemplates,
    submitting,
    error,
    successMessage,
    currentTemplate,
    loadTemplates,
    submitEmail,
  };
}
