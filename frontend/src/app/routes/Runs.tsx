import { PlayCircle } from "lucide-react";
import { EmptyState } from "@/components/EmptyState";
import { Button } from "@/components/ui/button";

export function Runs() {
  return (
    <EmptyState
      icon={PlayCircle}
      message="No runs yet. Start a run from an experiment."
      action={
        <Button disabled title="Available in a later milestone">
          Go to experiments
        </Button>
      }
    />
  );
}
