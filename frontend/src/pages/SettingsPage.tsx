import { useState } from "react";
import { useSettings, useUpdateSettings } from "@/hooks/useSettings";
import { useHealth } from "@/hooks/useHealth";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";

export function SettingsPage() {
  const { data: settings, isLoading } = useSettings();
  const { data: health } = useHealth();
  const update = useUpdateSettings();

  // Track local overrides; null means use server value
  const [overrides, setOverrides] = useState<Record<string, string>>({});
  const [showKeys, setShowKeys] = useState(false);

  const form = {
    anthropic_api_key: overrides.anthropic_api_key ?? settings?.anthropic_api_key ?? "",
    openai_api_key: overrides.openai_api_key ?? settings?.openai_api_key ?? "",
    anthropic_model: overrides.anthropic_model ?? settings?.anthropic_model ?? "",
    openai_embedding_model: overrides.openai_embedding_model ?? settings?.openai_embedding_model ?? "",
  };

  const setForm = (updates: Partial<typeof form>) => {
    setOverrides((prev) => ({ ...prev, ...updates }));
  };

  const handleSave = () => {
    update.mutate(form, {
      onSuccess: (result) => {
        setOverrides({});
        const status = result.health.status;
        if (status === "healthy") {
          toast.success("Settings saved — all services connected");
        } else {
          toast.warning("Settings saved — some services unavailable");
        }
      },
      onError: (err) => toast.error(err.message),
    });
  };

  if (isLoading) return <div className="p-6">Loading settings...</div>;

  return (
    <div className="p-6 max-w-2xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Settings</h1>

      <Card>
        <CardHeader>
          <CardTitle>Service Status</CardTitle>
        </CardHeader>
        <CardContent className="flex gap-4">
          <div className="flex items-center gap-2">
            <Badge variant={health?.services.generator ? "default" : "destructive"}>
              {health?.services.generator ? "Connected" : "Disconnected"}
            </Badge>
            <span className="text-sm">Generator (Anthropic)</span>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={health?.services.embedder ? "default" : "destructive"}>
              {health?.services.embedder ? "Connected" : "Disconnected"}
            </Badge>
            <span className="text-sm">Embedder (OpenAI)</span>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>API Keys</CardTitle>
            <Button variant="ghost" size="sm" onClick={() => setShowKeys(!showKeys)}>
              {showKeys ? "Hide" : "Show"}
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="anthropic_key">Anthropic API Key</Label>
            <Input
              id="anthropic_key"
              type={showKeys ? "text" : "password"}
              value={form.anthropic_api_key}
              onChange={(e) =>
                setForm({ anthropic_api_key: e.target.value })
              }
              placeholder="sk-ant-api03-..."
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="openai_key">OpenAI API Key</Label>
            <Input
              id="openai_key"
              type={showKeys ? "text" : "password"}
              value={form.openai_api_key}
              onChange={(e) =>
                setForm({ openai_api_key: e.target.value })
              }
              placeholder="sk-proj-..."
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Models</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="anthropic_model">Anthropic Model</Label>
            <Input
              id="anthropic_model"
              value={form.anthropic_model}
              onChange={(e) =>
                setForm({ anthropic_model: e.target.value })
              }
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="embedding_model">OpenAI Embedding Model</Label>
            <Input
              id="embedding_model"
              value={form.openai_embedding_model}
              onChange={(e) =>
                setForm({ openai_embedding_model: e.target.value })
              }
            />
          </div>
        </CardContent>
      </Card>

      <Button onClick={handleSave} disabled={update.isPending} className="w-full">
        {update.isPending ? "Saving..." : "Save Settings"}
      </Button>
    </div>
  );
}
