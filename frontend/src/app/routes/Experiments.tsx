import { FlaskConical } from "lucide-react";
import { EmptyState } from "@/components/EmptyState";
import { Button } from "@/components/ui/button";

export function Experiments() {
  return (
    <EmptyState
      icon={FlaskConical}
      message="No experiments yet. Create one to define a population, factors and a pipeline."
      action={
        <Button disabled title="Available in a later milestone">
          New experiment
        </Button>
      }
    />
  );
}
