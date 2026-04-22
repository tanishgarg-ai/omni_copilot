import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Loader2, Send, Sparkles } from "lucide-react";
import { toast } from "sonner";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { chat } from "@/lib/api";
import { cn } from "@/lib/utils";

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
};

const EXAMPLES = [
  "Summarize the documents I just synced.",
  "What's the difference between RAG and fine-tuning?",
  "Write a Python function to deduplicate a list.",
];

export function ChatArea({ username }: { username: string }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [pending, setPending] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const el = scrollRef.current?.querySelector("[data-radix-scroll-area-viewport]") as HTMLElement | null;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, pending]);

  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = `${Math.min(ta.scrollHeight, 200)}px`;
  }, [input]);

  const send = async () => {
    const text = input.trim();
    if (!text || pending) return;
    const userMsg: Message = { id: crypto.randomUUID(), role: "user", content: text };
    setMessages((m) => [...m, userMsg]);
    setInput("");
    setPending(true);
    try {
      const res = await chat(text);
      setMessages((m) => [...m, { id: crypto.randomUUID(), role: "assistant", content: res.response }]);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Request failed";
      toast.error(msg);
      setMessages((m) => [
        ...m,
        { id: crypto.randomUUID(), role: "assistant", content: `⚠️ ${msg}` },
      ]);
    } finally {
      setPending(false);
    }
  };

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  return (
    <div className="flex h-full flex-col">
      <header className="flex h-14 shrink-0 items-center justify-between border-b border-border/60 px-6">
        <div className="flex items-center gap-2">
          <div className="h-2 w-2 rounded-full bg-primary shadow-[0_0_10px_var(--color-primary)]" />
          <h2 className="text-sm font-medium text-foreground">Conversation</h2>
        </div>
        <span className="text-xs text-muted-foreground">Signed in as {username}</span>
      </header>

      <ScrollArea ref={scrollRef} className="flex-1">
        <div className="mx-auto w-full max-w-3xl px-6 py-8">
          {messages.length === 0 ? (
            <EmptyState onPick={(p) => setInput(p)} />
          ) : (
            <div className="space-y-6">
              {messages.map((m) => (
                <MessageBubble key={m.id} message={m} username={username} />
              ))}
              {pending && <ThinkingIndicator />}
            </div>
          )}
        </div>
      </ScrollArea>

      <div className="shrink-0 border-t border-border/60 bg-background/80 backdrop-blur">
        <div className="mx-auto w-full max-w-3xl px-6 py-4">
          <div className="flex items-end gap-2 rounded-2xl border border-border/80 bg-card p-2 shadow-lg shadow-black/20 focus-within:border-primary/50 focus-within:ring-2 focus-within:ring-primary/20">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={onKeyDown}
              placeholder="Ask Omni Copilot anything…"
              rows={1}
              disabled={pending}
              className="flex-1 resize-none bg-transparent px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none disabled:opacity-60"
            />
            <Button
              size="icon"
              onClick={send}
              disabled={pending || !input.trim()}
              className="h-9 w-9 shrink-0 rounded-xl"
            >
              {pending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            </Button>
          </div>
          <p className="mt-2 text-center text-[11px] text-muted-foreground">
            Press <kbd className="rounded bg-muted px-1.5 py-0.5 text-[10px]">Enter</kbd> to send,{" "}
            <kbd className="rounded bg-muted px-1.5 py-0.5 text-[10px]">Shift + Enter</kbd> for new line
          </p>
        </div>
      </div>
    </div>
  );
}

function EmptyState({ onPick }: { onPick: (prompt: string) => void }) {
  return (
    <div className="flex flex-col items-center text-center">
      <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 ring-1 ring-primary/20">
        <Sparkles className="h-7 w-7 text-primary" />
      </div>
      <h3 className="text-2xl font-semibold tracking-tight text-foreground">How can I help today?</h3>
      <p className="mt-2 max-w-md text-sm text-muted-foreground">
        Ask anything, or sync a local directory from the sidebar to chat over your own documents.
      </p>
      <div className="mt-8 grid w-full max-w-2xl grid-cols-1 gap-2 sm:grid-cols-3">
        {EXAMPLES.map((e) => (
          <button
            key={e}
            onClick={() => onPick(e)}
            className="rounded-xl border border-border/60 bg-card/60 p-3 text-left text-xs text-muted-foreground transition-colors hover:border-primary/50 hover:bg-card hover:text-foreground"
          >
            {e}
          </button>
        ))}
      </div>
    </div>
  );
}

function MessageBubble({ message, username }: { message: Message; username: string }) {
  const isUser = message.role === "user";
  return (
    <div className={cn("flex gap-3", isUser ? "flex-row-reverse" : "flex-row")}>
      <Avatar className="h-8 w-8 shrink-0">
        <AvatarFallback
          className={cn(
            "text-xs font-medium",
            isUser ? "bg-primary/20 text-primary" : "bg-accent text-accent-foreground",
          )}
        >
          {isUser ? username.charAt(0).toUpperCase() : <Sparkles className="h-4 w-4" />}
        </AvatarFallback>
      </Avatar>
      <div
        className={cn(
          "max-w-[80%] rounded-2xl px-4 py-3 text-sm",
          isUser
            ? "bg-primary/15 text-foreground ring-1 ring-primary/20"
            : "bg-card text-foreground ring-1 ring-border/60",
        )}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
        ) : (
          <div className="prose prose-sm prose-invert max-w-none prose-p:my-2 prose-pre:my-2 prose-pre:rounded-lg prose-pre:bg-background/60 prose-code:rounded prose-code:bg-muted prose-code:px-1 prose-code:py-0.5 prose-code:text-[0.85em] prose-code:before:content-none prose-code:after:content-none prose-headings:mb-2 prose-headings:mt-3 prose-ul:my-2 prose-ol:my-2 prose-li:my-0.5">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}

function ThinkingIndicator() {
  return (
    <div className="flex gap-3">
      <Avatar className="h-8 w-8 shrink-0">
        <AvatarFallback className="bg-accent text-accent-foreground">
          <Sparkles className="h-4 w-4" />
        </AvatarFallback>
      </Avatar>
      <div className="flex items-center gap-2 rounded-2xl bg-card px-4 py-3 text-sm text-muted-foreground ring-1 ring-border/60">
        <span>Omni Copilot is thinking</span>
        <span className="flex gap-1">
          <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground [animation-delay:-0.3s]" />
          <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground [animation-delay:-0.15s]" />
          <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground" />
        </span>
      </div>
    </div>
  );
}
