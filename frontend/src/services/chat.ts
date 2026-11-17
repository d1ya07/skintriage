import type { ChatMessage, ChatReply } from "@/types";
import { api } from "./api";

export const chatService = {
  async send(messages: ChatMessage[]): Promise<ChatReply> {
    const { data } = await api.post<ChatReply>("/chat", { messages });
    return data;
  },
};
