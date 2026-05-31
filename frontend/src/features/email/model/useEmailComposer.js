import { useCallback, useMemo, useState } from "react";
import { getEmailTemplates, sendEmail } from "../api/emailApi";

function emptyFieldMap(fields = []) {
  const entries = fields.map((field) => [field.name, ""]);
  return Object.fromEntries(entries);
}

export function useEmailComposer(accessToken, withAuthenticatedRequest) {
  const [mode, setMode] = useState("manual");
  const [toEmail, setToEmail] = useState("");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState("");
  const [templateData, setTemplateData] = useState({});
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
      const payload = await withAuthenticatedRequest((token) => getEmailTemplates(token || accessToken));
      const items = payload?.items || [];
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

  function selectTemplate(name) {
    setSelectedTemplate(name);
    const next = templates.find((template) => template.name === name);
    setTemplateData(emptyFieldMap(next?.fields || []));
  }

  function updateTemplateField(fieldName, value) {
    setTemplateData((current) => ({
      ...current,
      [fieldName]: value,
    }));
  }

  async function submitEmail(event) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    setSuccessMessage("");

    const payload =
      mode === "template"
        ? {
            to_email: toEmail,
            template_name: selectedTemplate,
            template_data: templateData,
          }
        : {
            to_email: toEmail,
            subject,
            body,
          };

    try {
      const result = await withAuthenticatedRequest((token) => sendEmail(token || accessToken, payload));
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
