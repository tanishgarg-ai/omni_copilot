import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";

import { AppSidebar } from "@/components/AppSidebar";
import { ChatArea } from "@/components/ChatArea";
import { clearToken, getToken } from "@/lib/api";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Omni Copilot — Dashboard" },
      { name: "description", content: "Chat with your hybrid AI assistant and local knowledge base." },
    ],
  }),
  component: Dashboard,
});

function Dashboard() {
  const navigate = useNavigate();
  const [ready, setReady] = useState(false);
  const [username, setUsername] = useState("user");

  useEffect(() => {
    const token = getToken();
    if (!token) {
      navigate({ to: "/auth" });
      return;
    }
    // Best-effort: extract username from JWT payload (no verification — display only)
    try {
      const payload = JSON.parse(atob(token.split(".")[1]));
      if (typeof payload?.sub === "string") setUsername(payload.sub);
    } catch {
      // ignore
    }
    setReady(true);
  }, [navigate]);

  const handleLogout = () => {
    clearToken();
    navigate({ to: "/auth" });
  };

  if (!ready) {
    return <div className="min-h-screen bg-background" />;
  }

  return (
    <div className="flex h-screen w-full overflow-hidden bg-background">
      <AppSidebar onLogout={handleLogout} />
      <main className="flex-1 overflow-hidden">
        <ChatArea username={username} />
      </main>
    </div>
  );
}
