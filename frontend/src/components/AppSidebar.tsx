import { useState } from "react";
import { FolderSync, Loader2, LogOut, Sparkles, FolderOpen } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { ingest } from "@/lib/api";

export function AppSidebar({ onLogout }: { onLogout: () => void }) {
  const [path, setPath] = useState("");
  const [syncing, setSyncing] = useState(false);
  const [lastSynced, setLastSynced] = useState<string | null>(null);

  const handleSync = async () => {
    const trimmed = path.trim();
    if (!trimmed || syncing) return;
    setSyncing(true);
    try {
      const res = await ingest(trimmed);
      toast.success(res.status || "Directory synced");
      setLastSynced(trimmed);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Sync failed");
    } finally {
      setSyncing(false);
    }
  };

  return (
    <aside className="flex h-full w-[280px] shrink-0 flex-col border-r border-border/60 bg-sidebar">
      <div className="flex h-14 items-center gap-2 border-b border-border/60 px-5">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/15 ring-1 ring-primary/30">
          <Sparkles className="h-4 w-4 text-primary" />
        </div>
        <div>
          <h1 className="text-sm font-semibold tracking-tight text-sidebar-foreground">Omni Copilot</h1>
          <p className="text-[10px] uppercase tracking-wider text-muted-foreground">Hybrid AI</p>
        </div>
      </div>

      <div className="flex-1 space-y-6 overflow-y-auto p-5">
        <div>
          <div className="mb-3 flex items-center gap-2">
            <FolderOpen className="h-3.5 w-3.5 text-muted-foreground" />
            <h2 className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
              Local Knowledge Base
            </h2>
          </div>

          <div className="space-y-3 rounded-xl border border-border/60 bg-card/50 p-3">
            <div className="space-y-1.5">
              <Label htmlFor="dir-path" className="text-xs text-muted-foreground">
                Directory path
              </Label>
              <Input
                id="dir-path"
                value={path}
                onChange={(e) => setPath(e.target.value)}
                placeholder="/Users/name/docs"
                disabled={syncing}
                className="h-9 text-xs"
              />
            </div>
            <Button
              onClick={handleSync}
              disabled={syncing || !path.trim()}
              className="w-full"
              size="sm"
            >
              {syncing ? (
                <>
                  <Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" /> Syncing…
                </>
              ) : (
                <>
                  <FolderSync className="mr-2 h-3.5 w-3.5" /> Sync Directory
                </>
              )}
            </Button>
            {lastSynced && (
              <div className="border-t border-border/60 pt-2">
                <p className="text-[10px] uppercase tracking-wider text-muted-foreground">Last synced</p>
                <p className="mt-0.5 truncate font-mono text-[11px] text-foreground" title={lastSynced}>
                  {lastSynced}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      <Separator />
      <div className="p-4">
        <Button
          variant="ghost"
          onClick={onLogout}
          className="w-full justify-start text-muted-foreground hover:text-foreground"
        >
          <LogOut className="mr-2 h-4 w-4" /> Sign out
        </Button>
      </div>
    </aside>
  );
}
