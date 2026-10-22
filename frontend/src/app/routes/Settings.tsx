import { Settings as SettingsIcon } from "lucide-react";
import { EmptyState } from "@/components/EmptyState";
import { Button } from "@/components/ui/button";

export function Settings() {
  return (
    <EmptyState
      icon={SettingsIcon}
      message="Data directory, Ollama URL, concurrency and provider settings will live here."
      action={
        <Button disabled title="Available in a later milestone">
          Edit settings
        </Button>
      }
    />
  );
}
