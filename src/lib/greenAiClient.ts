/**
 * Client service to communicate with GREEN_AI Multi-Agent Backend
 */

export interface GreenAiChatOptions {
  message: string;
  role: "student_parent" | "teacher_staff" | "visitor_applicant" | "alumni_ex_employee" | string;
  sessionId?: string;
  userId?: string;
  featureTag?: string;
  provider?: string;
  uiContext?: Record<string, any>;
}

export interface GreenAiChatResult {
  success: boolean;
  answer: string;
  followupSuggestions: string[];
  selectedAgentName?: string;
  providerUsed?: string;
  sources?: Array<{ module: string; summary: string; record_id?: string }>;
  actions?: Array<{ action_type: string; status: string; message: string }>;
}

export async function sendGreenAiQuery(options: GreenAiChatOptions): Promise<GreenAiChatResult> {
  try {
    const res = await fetch("/api/ai/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message: options.message,
        role: options.role,
        session_id: options.sessionId || `session_${options.role}`,
        user_id: options.userId || "KioskUser",
        feature_tag: options.featureTag,
        provider: options.provider || "auto",
        ui_context: options.uiContext || {},
      }),
    });

    if (!res.ok) {
      throw new Error(`AI Chat server returned ${res.status}`);
    }

    const json = await res.json();
    return {
      success: true,
      answer: json.answer || "I could not retrieve an answer at this time.",
      followupSuggestions: json.followup_suggestions || [],
      selectedAgentName: json.selected_agent_name || json.data?.selected_agent_name,
      providerUsed: json.provider_used || json.data?.provider_used,
      sources: json.sources || json.data?.sources || [],
      actions: json.actions || json.data?.actions || [],
    };
  } catch (err: any) {
    console.error("[sendGreenAiQuery] Error calling /api/ai/chat:", err);
    return {
      success: false,
      answer: "GREEN_AI is currently operating in offline mode. Please verify your connection to the campus AI server.",
      followupSuggestions: ["Try asking again", "Check timetable", "Check attendance"],
    };
  }
}
