import { useState } from "react";
import api from "../services/api";

function AgentChat() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  const askAgent = async () => {
    if (!question.trim()) {
      return;
    }

    const userQuestion = question;

    setMessages((previous) => [
      ...previous,
      {
        role: "user",
        text: userQuestion,
      },
    ]);

    setQuestion("");
    setLoading(true);

    try {
      const history = messages.map(
        (message) => ({
         role: message.role,
        text: message.text,
        })
       );

       const response = await api.post(
           "/agent/query",
       {
            question: userQuestion,
            history: history,
        }
        );

      setMessages((previous) => [
        ...previous,
        {
          role: "agent",
          text: response.data.answer,
        },
      ]);
    } catch (error) {
      console.error(error);

      setMessages((previous) => [
        ...previous,
        {
          role: "agent",
          text: "Unable to get an answer from the Insight Agent.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2 className="agent-title">
          FleetGuard Insight Agent
      </h2>

      <p>
        Ask questions about vehicle risk,
        failure probability and remaining useful life.        
      </p>

      <div
        style={{
          border: "1px solid #ccc",
          padding: "15px",
          minHeight: "300px",
          marginBottom: "15px",
        }}
      >
        {messages.length === 0 && (
          <p>
            Ask a question to get started.
          </p>
        )}

        {messages.map((message, index) => (
          <div
            key={index}
            style={{
              marginBottom: "15px",
            }}
          >
            <strong>
              {message.role === "user"
                ? "You"
                : "FleetGuard AI"}
              :
            </strong>

            <div>
              {message.text}
            </div>
          </div>
        ))}

        {loading && (
          <p>
            FleetGuard AI is analyzing...
          </p>
        )}
      </div>

      <input
        type="text"
        value={question}
        placeholder="Ask FleetGuard AI..."
        onChange={(e) =>
          setQuestion(e.target.value)
        }
        onKeyDown={(e) => {
          if (e.key === "Enter") {
            askAgent();
          }
        }}
        style={{
          width: "70%",
          padding: "8px",
        }}
      />

      {" "}

      <button
        onClick={askAgent}
        disabled={loading}
      >
        Ask
      </button>
    </div>
  );
}

export default AgentChat;