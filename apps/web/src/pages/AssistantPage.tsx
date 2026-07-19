import {
  Bot,
  LoaderCircle,
  Send,
  Sparkles,
  UserRound,
} from "lucide-react";
import {
  useState,
  type FormEvent,
} from "react";
import ReactMarkdown from "react-markdown";

import {
  askKnowledge,
  type KnowledgeSource,
} from "../api/chat";
import {
  getApiErrorMessage,
} from "../api/errors";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  retrievalMode?: string;
  sources?: KnowledgeSource[];
}

const suggestedQuestions = [
  "Summarize the main topics in my documents.",
  "What experience and projects are described?",
  "Which technologies appear most often?",
];

export default function AssistantPage() {
  const [question, setQuestion] =
    useState("");
  const [messages, setMessages] =
    useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] =
    useState(false);
  const [error, setError] =
    useState("");

  async function submitQuestion(
    value: string,
  ) {
    const cleanedQuestion = value.trim();

    if (!cleanedQuestion || isLoading) {
      return;
    }

    setError("");
    setQuestion("");
    setMessages((current) => [
      ...current,
      {
        id: crypto.randomUUID(),
        role: "user",
        content: cleanedQuestion,
      },
    ]);
    setIsLoading(true);

    try {
      const response =
        await askKnowledge(cleanedQuestion);

      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content:
            response.answer_markdown,
          retrievalMode:
            response.retrieval_mode,
          sources: response.sources,
        },
      ]);
    } catch (requestError) {
      setError(
        getApiErrorMessage(requestError),
      );
    } finally {
      setIsLoading(false);
    }
  }

  function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();
    void submitQuestion(question);
  }

  return (
    <section className="page-container assistant-page">
      <header className="page-header">
        <div>
          <p className="eyebrow">
            Grounded intelligence
          </p>

          <h1>Knowledge Assistant</h1>

          <p>
            Ask questions across your compiled
            Wiki and original document chunks.
          </p>
        </div>
      </header>

      <div className="chat-panel">
        <div className="chat-messages">
          {messages.length === 0 ? (
            <div className="assistant-welcome">
              <div className="assistant-avatar">
                <Sparkles size={28} />
              </div>

              <h2>
                Ask your knowledge base
              </h2>

              <p>
                Answers are generated from your
                documents and include traceable
                sources.
              </p>

              <div className="suggestion-grid">
                {suggestedQuestions.map(
                  (suggestion) => (
                    <button
                      type="button"
                      key={suggestion}
                      onClick={() =>
                        void submitQuestion(
                          suggestion,
                        )
                      }
                    >
                      {suggestion}
                    </button>
                  ),
                )}
              </div>
            </div>
          ) : (
            messages.map((message) => (
              <article
                key={message.id}
                className={`chat-message ${message.role}`}
              >
                <div className="message-avatar">
                  {message.role === "user" ? (
                    <UserRound size={18} />
                  ) : (
                    <Bot size={18} />
                  )}
                </div>

                <div className="message-content">
                  <ReactMarkdown>
                    {message.content}
                  </ReactMarkdown>

                  {message.retrievalMode && (
                    <span className="retrieval-mode">
                      {message.retrievalMode}
                    </span>
                  )}

                  {message.sources &&
                    message.sources.length > 0 && (
                      <div className="source-list">
                        <h3>Sources</h3>

                        {message.sources.map(
                          (source) => (
                            <div
                              className="source-card"
                              key={`${message.id}-${source.source_id}`}
                            >
                              <strong>
                                {source.source_id}:{" "}
                                {source.title}
                              </strong>

                              <span>
                                {source.source_type}
                                {source.page_number
                                  ? ` · page ${source.page_number}`
                                  : ""}
                                {" · "}
                                score{" "}
                                {source.score.toFixed(
                                  3,
                                )}
                              </span>
                            </div>
                          ),
                        )}
                      </div>
                    )}
                </div>
              </article>
            ))
          )}

          {isLoading && (
            <div className="chat-message assistant">
              <div className="message-avatar">
                <Bot size={18} />
              </div>

              <div className="message-content typing-message">
                <LoaderCircle
                  className="spin"
                  size={19}
                />
                Searching your knowledge base...
              </div>
            </div>
          )}
        </div>

        {error && (
          <div className="error-message chat-error">
            {error}
          </div>
        )}

        <form
          className="chat-composer"
          onSubmit={handleSubmit}
        >
          <textarea
            value={question}
            onChange={(event) =>
              setQuestion(event.target.value)
            }
            placeholder="Ask a question about your documents..."
            rows={2}
            disabled={isLoading}
            onKeyDown={(event) => {
              if (
                event.key === "Enter" &&
                !event.shiftKey
              ) {
                event.preventDefault();
                void submitQuestion(question);
              }
            }}
          />

          <button
            type="submit"
            className="primary-button icon-button"
            disabled={
              isLoading ||
              question.trim().length < 2
            }
            aria-label="Send question"
          >
            <Send size={19} />
          </button>
        </form>
      </div>
    </section>
  );
}
