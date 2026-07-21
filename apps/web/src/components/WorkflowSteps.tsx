import {
  BookOpen,
  FileCheck2,
  MessageSquareText,
  Upload,
} from "lucide-react";

const steps = [
  {
    icon: Upload,
    label: "Upload",
    description: "Add a PDF, DOCX or TXT file.",
  },
  {
    icon: FileCheck2,
    label: "Process",
    description: "Extract and index the content.",
  },
  {
    icon: BookOpen,
    label: "Build Wiki",
    description: "Create connected knowledge pages.",
  },
  {
    icon: MessageSquareText,
    label: "Ask",
    description: "Get grounded answers with sources.",
  },
];

export default function WorkflowSteps() {
  return (
    <section className="workflow-card" aria-label="Getting started">
      <div className="workflow-heading">
        <p className="eyebrow">Getting started</p>
        <h2>Build your knowledge workspace in four steps</h2>
      </div>

      <div className="workflow-steps">
        {steps.map((step, index) => {
          const Icon = step.icon;

          return (
            <article key={step.label} className="workflow-step">
              <span className="workflow-number">{index + 1}</span>
              <span className="workflow-icon">
                <Icon size={18} />
              </span>
              <div>
                <strong>{step.label}</strong>
                <p>{step.description}</p>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
