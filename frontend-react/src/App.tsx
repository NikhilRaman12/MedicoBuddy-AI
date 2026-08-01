import React from "react";
import { Layout } from "./components/layout/Layout";
import { MessageList } from "./components/chat/MessageList";
import { Composer } from "./components/chat/Composer";
import { useStore } from "./state/useStore";
import { sendChatMessage } from "./api/chat";
import { MedicoBuddyResponse } from "./api/schemas";



export const App: React.FC = () => {
  const {
    threadId,
    messages,
    addMessage,
    selectedLanguage,
    userContext,
  } = useStore();

  const [isGenerating, setIsGenerating] = React.useState(false);
  const [stageMessage, setStageMessage] = React.useState(
    "Running GraphRAG retrieval & evidence validation..."
  );

  const abortControllerRef = React.useRef<AbortController | null>(null);

  const handleSend = async (queryText: string) => {
    if (!queryText.trim() || isGenerating) return;

    const userMessageId = crypto.randomUUID();
    const assistantMessageId = crypto.randomUUID();
    const reqId = crypto.randomUUID();
    const timestamp = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

    // 1. Append user message
    addMessage({
      id: userMessageId,
      role: "user",
      content: queryText,
      timestamp,
    });

    setIsGenerating(true);
    setStageMessage("Checking safety guidelines...");

    abortControllerRef.current = new AbortController();

    const payload = {
      message: queryText,
      audience_mode: "patient_education",
      preferred_language: selectedLanguage,
      thread_id: threadId,
      age_range: userContext.age_range,
      pregnancy_status: userContext.pregnancy_status,
      chronic_conditions: userContext.chronic_conditions,
      allergies: userContext.allergies,
      current_medicines: userContext.current_medicines,
      immunocompromised: userContext.immunocompromised,
      region: userContext.region,
      consent_given: true,
    };

    try {
      // Send chat request
      const responseData: MedicoBuddyResponse = await sendChatMessage(
        payload,
        abortControllerRef.current.signal
      );

      // Append assistant message with structured response data
      addMessage({
        id: assistantMessageId,
        role: "assistant",
        content: responseData.summary || "Evidence-based health education response",
        data: responseData,
        requestId: reqId,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      });
    } catch (err: any) {
      if (err.name !== "AbortError") {
        addMessage({
          id: assistantMessageId,
          role: "assistant",
          content: "Grounded answer is temporarily unavailable. Please retry after backend evidence service recovers.",
          requestId: reqId,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        });
      }
    } finally {
      setIsGenerating(false);
      abortControllerRef.current = null;
    }
  };

  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsGenerating(false);
    }
  };

  return (
    <Layout>
      <MessageList
        messages={messages}
        onSelectQuery={handleSend}
        isGenerating={isGenerating}
        currentStageMessage={stageMessage}
      />
      <Composer
        onSend={handleSend}
        onStop={handleStop}
        isGenerating={isGenerating}
      />
    </Layout>
  );
};

export default App;
