import { useState } from "react";
import { Button } from "../ui/button";
import type { SynthesisOutlineSection } from "../../lib/api";

interface OutlineEditorProps {
  outline: SynthesisOutlineSection[];
  readOnly?: boolean;
  onSave: (outline: SynthesisOutlineSection[]) => void;
  onApprove: () => void;
}

export function OutlineEditor({ outline, readOnly, onSave, onApprove }: OutlineEditorProps) {
  const [sections, setSections] = useState<SynthesisOutlineSection[]>(outline);

  const updateSection = (index: number, field: keyof SynthesisOutlineSection, value: string) => {
    setSections((prev) => prev.map((s, i) => (i === index ? { ...s, [field]: value } : s)));
  };

  const moveSection = (index: number, direction: -1 | 1) => {
    const target = index + direction;
    if (target < 0 || target >= sections.length) return;
    setSections((prev) => {
      const next = [...prev];
      [next[index], next[target]] = [next[target], next[index]];
      return next;
    });
  };

  const removeSection = (index: number) => {
    setSections((prev) => prev.filter((_, i) => i !== index));
  };

  const addSection = () => {
    setSections((prev) => [...prev, { title: "", description: "" }]);
  };

  if (readOnly) {
    return (
      <div className="space-y-3">
        {sections.map((section, i) => (
          <div key={i} className="rounded border border-input bg-muted/40 p-3">
            <p className="font-medium text-sm">{section.title}</p>
            <p className="text-sm text-muted-foreground">{section.description}</p>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {sections.map((section, i) => (
        <div key={i} className="flex items-start gap-2">
          <div className="flex flex-col gap-1">
            <Button
              variant="ghost"
              size="sm"
              className="h-7 w-7 p-0"
              onClick={() => moveSection(i, -1)}
              disabled={i === 0}
            >
              &uarr;
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="h-7 w-7 p-0"
              onClick={() => moveSection(i, 1)}
              disabled={i === sections.length - 1}
            >
              &darr;
            </Button>
          </div>
          <div className="flex-1 space-y-1">
            <input
              type="text"
              className="w-full rounded border border-input bg-background px-3 py-1 text-sm"
              placeholder="Section title"
              value={section.title}
              onChange={(e) => updateSection(i, "title", e.target.value)}
            />
            <input
              type="text"
              className="w-full rounded border border-input bg-background px-3 py-1 text-sm"
              placeholder="Section description"
              value={section.description}
              onChange={(e) => updateSection(i, "description", e.target.value)}
            />
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="h-7 w-7 p-0 text-destructive"
            onClick={() => removeSection(i)}
          >
            &times;
          </Button>
        </div>
      ))}

      <Button variant="outline" size="sm" onClick={addSection}>
        + Add Section
      </Button>

      <div className="flex gap-2 pt-2">
        <Button variant="outline" onClick={() => onSave(sections)}>
          Save Changes
        </Button>
        <Button onClick={onApprove}>
          Approve &amp; Generate
        </Button>
      </div>
    </div>
  );
}
