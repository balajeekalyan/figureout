import React, { useState, useEffect, useRef } from "react";
import { sendMessage } from "../api";
import "./Chat.css";

const SUGGESTED_QUESTIONS = [
  "How do I reset my password?",
  "What payment methods do you accept?",
  "How do I track my order?",
  "What is your refund policy?",
  "How do I cancel my subscription?",
  "I received the wrong item. What should I do?",
];

export default function Chat() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      answer: "Hi! I'm your support assistant. I can help you with account management, billing, and order questions. What can I help you with today?",
      relatedTopics: [],
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async (query) => {
    const text = query || input.trim();
    if (!text || loading) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", answer: text }]);
    setLoading(true);

    try {
      const data = await sendMessage(text);
      const payload = data.response || data;
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          answer: payload.answer || "I'm sorry, I couldn't find an answer to that. Please contact our support team.",
          relatedTopics: payload.related_topics || [],
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          answer: "Something went wrong. Please try again.",
          relatedTopics: [],
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-messages">
        {messages.map((msg, i) => (
          <div key={i} className={`chat-message chat-message--${msg.role}`}>
            {msg.role === "assistant" && (
              <div className="chat-avatar">S</div>
            )}
            <div className="chat-bubble-wrapper">
              <div className={`chat-bubble chat-bubble--${msg.role}`}>
                {msg.answer}
              </div>
              {msg.role === "assistant" && msg.relatedTopics && msg.relatedTopics.length > 0 && (
                <div className="chat-related-topics">
                  {msg.relatedTopics.map((topic, j) => (
                    <button
                      key={j}
                      className="chat-topic-chip"
                      onClick={() => handleSend(topic)}
                    >
                      {topic}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="chat-message chat-message--assistant">
            <div className="chat-avatar">S</div>
            <div className="chat-bubble chat-bubble--assistant chat-bubble--typing">
              <span className="typing-dot" />
              <span className="typing-dot" />
              <span className="typing-dot" />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {messages.length === 1 && (
        <div className="chat-suggestions">
          <p className="chat-suggestions-label">Suggested questions</p>
          <div className="chat-suggestions-grid">
            {SUGGESTED_QUESTIONS.map((q, i) => (
              <button key={i} className="chat-suggestion-btn" onClick={() => handleSend(q)}>
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="chat-input-row">
        <textarea
          className="chat-input"
          rows={1}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type your question..."
          disabled={loading}
        />
        <button
          className="chat-send-btn"
          onClick={() => handleSend()}
          disabled={loading || !input.trim()}
        >
          Send
        </button>
      </div>
    </div>
  );
}
