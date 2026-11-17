import { Info, MessageCircle, Send, X } from "lucide-react";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { useNavigate } from "react-router";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { getErrorMessage } from "@/lib/errors";
import { cn } from "@/lib/utils";
import { chatService } from "@/services/chat";
import type { ChatAction, ChatMessage } from "@/types";

interface UiMessage extends ChatMessage {
  actions?: ChatAction[];
  refused?: boolean;
  isGreeting?: boolean;
}

const GREETING: UiMessage = {
  role: "assistant",
  content:
    "Hi! I'm the SkinTriage help assistant. Ask me how to use the platform: skin scans, urgency levels, booking or your account.",
  isGreeting: true,
};

const SUGGESTIONS = [
  "How does the skin scan work?",
  "What do the urgency levels mean?",
  "How do I book an appointment?",
  "How do I cancel a booking?",
];

export function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<UiMessage[]>([GREETING]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, open]);

  async function send(text: string) {
    const content = text.trim();
    if (!content || sending) return;
    const next: UiMessage[] = [...messages, { role: "user", content }];
    setMessages(next);
    setInput("");
    setSending(true);
    try {
      const history = next
        .filter((m) => !m.isGreeting)
        .map(({ role, content }) => ({ role, content }))
        .slice(-10);
      const reply = await chatService.send(history);
      setMessages((m) => [
        ...m,
        { role: "assistant", content: reply.reply, actions: reply.actions, refused: reply.refused },
      ]);
    } catch (e) {
      setMessages((m) => [
        ...m,
        { role: "assistant", content: getErrorMessage(e, "Sorry, I couldn't reply just now. Please try again.") },
      ]);
    } finally {
      setSending(false);
    }
  }

  function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    void send(input);
  }

  return (
    <>
      {open && (
        <div className="fixed bottom-20 right-4 z-50 flex h-[540px] max-h-[calc(100vh-7rem)] w-[min(380px,calc(100vw-2rem))] flex-col overflow-hidden rounded-xl border bg-background shadow-2xl">
          <div className="flex items-center justify-between border-b px-4 py-3">
            <div>
              <p className="font-semibold">SkinTriage Help</p>
              <p className="text-xs text-muted-foreground">Questions about using the platform</p>
            </div>
            <Button variant="ghost" size="icon" onClick={() => setOpen(false)} aria-label="Close chat">
              <X className="size-4" />
            </Button>
          </div>

          <div className="flex items-start gap-2 border-b bg-amber-50 px-4 py-2 text-xs text-amber-900 dark:bg-amber-950 dark:text-amber-200">
            <Info className="mt-0.5 size-3.5 shrink-0" />
            <span>General help only, not medical advice. For health concerns, use Skin Scan or see a doctor.</span>
          </div>

          <div className="flex-1 space-y-3 overflow-y-auto p-4">
            {messages.map((m, i) => (
              <div key={i} className={cn("flex flex-col", m.role === "user" ? "items-end" : "items-start")}>
                <div
                  className={cn(
                    "max-w-[85%] whitespace-pre-wrap rounded-lg px-3 py-2 text-sm",
                    m.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted",
                    m.refused && "border border-amber-300 bg-amber-50 text-amber-950 dark:bg-amber-950 dark:text-amber-100",
                  )}
                >
                  {m.content}
                </div>
                {m.actions && m.actions.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-2">
                    {m.actions.map((a) => (
                      <Button
                        key={a.to}
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          setOpen(false);
                          navigate(a.to);
                        }}
                      >
                        {a.label}
                      </Button>
                    ))}
                  </div>
                )}
              </div>
            ))}

            {messages.length === 1 && (
              <div className="flex flex-wrap gap-2 pt-2">
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => void send(s)}
                    className="rounded-full border px-3 py-1 text-xs hover:bg-muted"
                  >
                    {s}
                  </button>
                ))}
              </div>
            )}

            {sending && <div className="text-sm text-muted-foreground">Typing...</div>}
            <div ref={endRef} />
          </div>

          <form onSubmit={onSubmit} className="flex gap-2 border-t p-3">
            <Input
              placeholder="Ask about using SkinTriage..."
              value={input}
              maxLength={1000}
              onChange={(e) => setInput(e.target.value)}
            />
            <Button type="submit" size="icon" disabled={sending || !input.trim()} aria-label="Send">
              <Send className="size-4" />
            </Button>
          </form>
        </div>
      )}

      <Button
        size="icon"
        className="fixed bottom-4 right-4 z-50 size-14 rounded-full shadow-lg"
        onClick={() => setOpen((o) => !o)}
        aria-label={open ? "Close help chat" : "Open help chat"}
      >
        {open ? <X className="size-6" /> : <MessageCircle className="size-6" />}
      </Button>
    </>
  );
}
