import { Users } from "lucide-react";
import { EmptyState } from "@/components/EmptyState";
import { Button } from "@/components/ui/button";

export function Personas() {
  return (
    <EmptyState
      icon={Users}
      message="Personas appear here once a run has generated them."
      action={
        <Button disabled title="Available in a later milestone">
          Select a run
        </Button>
      }
    />
  );
}
