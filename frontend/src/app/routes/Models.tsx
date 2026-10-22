import { Bot } from "lucide-react";
import { EmptyState } from "@/components/EmptyState";
import { Button } from "@/components/ui/button";

export function Models() {
  return (
    <EmptyState
      icon={Bot}
      message="Installed Ollama models and their benchmarks will be listed here."
      action={
        <Button disabled title="Available in a later milestone">
          Pull a model
        </Button>
      }
    />
  );
}
