import React from "react";

export const highlightMatch = (
  text: string,
  query: string
): React.ReactNode => {
  if (!query || !query.trim()) {
    return text;
  }

  // Escape regex characters safely
  const escapedQuery = query.replace(/[-\\^$*+?.()|[\]{}]/g, "\\$&");
  const parts = text.split(new RegExp(`(${escapedQuery})`, "gi"));

  return (
    <>
      {parts.map((part, index) =>
        part.toLowerCase() === query.toLowerCase() ? (
          <mark
            key={index}
            className="bg-primary/20 text-foreground font-semibold px-0.5 rounded-sm"
          >
            {part}
          </mark>
        ) : (
          part
        )
      )}
    </>
  );
};
