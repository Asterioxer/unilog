import { useRef } from "react";
import { Search } from "lucide-react";
import { useKeyboardShortcut } from "../../hooks/useKeyboardShortcut";

interface SearchBoxProps {
  value: string;
  onChange: (val: string) => void;
}

export default function SearchBox({ value, onChange }: SearchBoxProps) {
  const searchInputRef = useRef<HTMLInputElement>(null);

  useKeyboardShortcut({ key: "k", ctrlKey: true }, (e) => {
    e.preventDefault();
    searchInputRef.current?.focus();
  });

  return (
    <div className="relative min-w-[280px]">
      <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
      <input
        ref={searchInputRef}
        type="text"
        placeholder="Search matching entries (Ctrl+K)..."
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="pl-9 pr-4 py-2 w-full rounded-lg border border-border bg-background text-sm focus:ring-1 focus:ring-primary focus:outline-hidden"
      />
    </div>
  );
}
