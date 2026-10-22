import { Activity, CheckCircle2, Plus } from "lucide-react";
import { Link } from "react-router-dom";
import { EmptyState } from "@/components/EmptyState";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useHealth } from "@/lib/queries";

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-4 py-1.5">
      <span className="text-zinc-500 dark:text-zinc-400">{label}</span>
      <span className="tabular truncate text-right">{children}</span>
    </div>
  );
}

function SystemCard() {
  const { data, isPending, isError } = useHealth();
  return (
    <Card data-testid="system-card">
      <CardHeader>
        <CardTitle>System</CardTitle>
      </CardHeader>
      <CardContent>
        {isPending ? (
          <div className="space-y-2">
            {[0, 1, 2].map((i) => (
              <div key={i} className="h-5 animate-pulse rounded bg-zinc-100 dark:bg-zinc-800" />
            ))}
          </div>
        ) : isError || !data ? (
          <Badge tone="failed">Backend unreachable</Badge>
        ) : (
          <>
            <Row label="Backend">v{data.version}</Row>
            <Row label="Database">
              <Badge tone={data.db.ok ? "done" : "failed"}>
                {data.db.ok ? `ok · ${data.db.journal_mode}` : "error"}
              </Badge>
            </Row>
            <Row label="Ollama">
              <Badge tone={data.ollama.reachable ? "done" : "failed"}>
                {data.ollama.reachable ? `connected · v${data.ollama.version}` : "unreachable"}
              </Badge>
            </Row>
            <Row label="Ollama URL">
              <span className="font-mono text-[13px]">{data.ollama.url}</span>
            </Row>
          </>
        )}
      </CardContent>
    </Card>
  );
}

export function Overview() {
  return (
    <div className="space-y-6">
      <div className="flex justify-end">
        <Button asChild>
          <Link to="/experiments">
            <Plus /> New experiment
          </Link>
        </Button>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Active run</CardTitle>
          </CardHeader>
          <CardContent>
            <EmptyState icon={Activity} message="No run is in progress." />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Last completed run</CardTitle>
          </CardHeader>
          <CardContent>
            <EmptyState icon={CheckCircle2} message="No runs have completed yet." />
          </CardContent>
        </Card>
        <SystemCard />
      </div>
    </div>
  );
}
