import { useEffect } from "react";
import { useEmailComposer } from "../storage/useEmailComposer";

export default function EmailPage({
  authUser,
  accessToken,
  withAuthenticatedRequest,
}) {
  const {
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
  } = useEmailComposer(accessToken, withAuthenticatedRequest);

  useEffect(() => {
    if (mode === "template" && templates.length === 0) {
      loadTemplates();
    }
  }, [loadTemplates, mode, templates.length]);

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
      <header className="card border border-base-200 shadow-xl">
        <div className="card-body p-6 sm:p-8">
          <p className="font-mono text-xs font-semibold uppercase tracking-[0.18em] text-primary">
            Task Management API
          </p>
          <h1 className="mt-2 text-4xl font-bold tracking-tight text-base-content sm:text-5xl">Email Console</h1>
          <small className="mt-1 block font-mono text-xs text-base-content/60">v0.6</small>
          <p className="mt-3 max-w-3xl text-sm text-base-content/70 sm:text-base">
            Send manual or templated transactional emails through your configured SMTP provider.
          </p>

          <div className="mt-5">
            <span className="font-mono text-xs uppercase tracking-wide text-base-content/70">
              Signed in as {authUser}
            </span>
          </div>
        </div>
      </header>

      <section className="card mt-4 border border-base-200 shadow-xl">
        <div className="card-body p-4 sm:p-5">
          <form onSubmit={submitEmail} className="grid gap-4">
            <div className="grid gap-3 md:grid-cols-2">
              <label className="form-control gap-1">
                <span className="label-text font-mono text-xs uppercase tracking-wide text-base-content/70">Recipient</span>
                <input
                  type="email"
                  className="input input-bordered w-full"
                  placeholder="recipient@example.com"
                  value={toEmail}
                  onChange={(event) => setToEmail(event.target.value)}
                  required
                />
              </label>

              <label className="form-control gap-1">
                <span className="label-text font-mono text-xs uppercase tracking-wide text-base-content/70">Mode</span>
                <select
                  className="select select-bordered w-full"
                  value={mode}
                  onChange={(event) => setMode(event.target.value)}
                >
                  <option value="manual">Manual subject/body</option>
                  <option value="template">Use template</option>
                </select>
              </label>
            </div>

            {mode === "manual" && (
              <div className="grid gap-3">
                <label className="form-control gap-1">
                  <span className="label-text font-mono text-xs uppercase tracking-wide text-base-content/70">Subject</span>
                  <input
                    type="text"
                    className="input input-bordered w-full"
                    value={subject}
                    onChange={(event) => setSubject(event.target.value)}
                    maxLength={160}
                    required
                  />
                </label>

                <label className="form-control gap-1">
                  <span className="label-text font-mono text-xs uppercase tracking-wide text-base-content/70">Body</span>
                  <textarea
                    className="textarea textarea-bordered min-h-36 w-full"
                    value={body}
                    onChange={(event) => setBody(event.target.value)}
                    maxLength={4000}
                    required
                  />
                </label>
              </div>
            )}

            {mode === "template" && (
              <div className="grid gap-3">
                <div className="grid gap-3 md:grid-cols-2">
                  <label className="form-control gap-1">
                    <span className="label-text font-mono text-xs uppercase tracking-wide text-base-content/70">Template</span>
                    <select
                      className="select select-bordered w-full"
                      value={selectedTemplate}
                      onChange={(event) => selectTemplate(event.target.value)}
                      disabled={loadingTemplates}
                      required
                    >
                      {templates.map((template) => (
                        <option key={template.name} value={template.name}>
                          {template.display_name}
                        </option>
                      ))}
                    </select>
                  </label>

                  <div className="alert alert-info">
                    <span className="text-sm">{currentTemplate?.description || "Select template mode to load available templates."}</span>
                  </div>
                </div>

                <div className="grid gap-3 md:grid-cols-2">
                  {(currentTemplate?.fields || []).map((field) => (
                    <label key={field.name} className="form-control gap-1">
                      <span className="label-text font-mono text-xs uppercase tracking-wide text-base-content/70">
                        {field.label}
                      </span>
                      <input
                        type="text"
                        className="input input-bordered w-full"
                        placeholder={field.placeholder || ""}
                        value={templateData[field.name] || ""}
                        onChange={(event) => updateTemplateField(field.name, event.target.value)}
                        required={field.required}
                      />
                    </label>
                  ))}
                </div>
              </div>
            )}

            <div className="flex flex-wrap gap-2">
              <button type="submit" className="btn btn-primary btn-sm" disabled={submitting || loadingTemplates}>
                {submitting ? "Sending..." : "Send Email"}
              </button>
              {mode === "template" && (
                <button type="button" className="btn btn-outline btn-sm" onClick={loadTemplates} disabled={loadingTemplates}>
                  {loadingTemplates ? "Loading..." : "Reload Templates"}
                </button>
              )}
            </div>
          </form>
        </div>
      </section>

      {error && (
        <div className="alert alert-error mt-4">
          <span>{error}</span>
        </div>
      )}

      {successMessage && (
        <div className="alert alert-success mt-4">
          <span>{successMessage}</span>
        </div>
      )}
    </div>
  );
}
