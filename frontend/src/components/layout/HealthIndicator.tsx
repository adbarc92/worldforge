import { useHealth } from "@/hooks/useHealth";

export function HealthIndicator() {
  const { data, isError } = useHealth();

  const color = isError
    ? "bg-red-500"
    : data?.status === "healthy"
      ? "bg-green-500"
      : "bg-yellow-500";

  const label = isError
    ? "Disconnected"
    : data?.status === "healthy"
      ? "All services up"
      : "Degraded";

  return (
    <div className="flex items-center gap-2 px-3 py-1 text-xs text-muted-foreground">
      <div className={`h-2 w-2 rounded-full ${color}`} />
      {label}
    </div>
  );
}
