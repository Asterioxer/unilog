import { useEffect } from "react";

type ShortcutConfig = {
  key: string;
  ctrlKey?: boolean;
  metaKey?: boolean;
  altKey?: boolean;
  shiftKey?: boolean;
};

export function useKeyboardShortcut(
  config: ShortcutConfig,
  callback: (e: KeyboardEvent) => void
) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const matchKey = e.key.toLowerCase() === config.key.toLowerCase();
      // Ensure that if we specified modifier as false/undefined, we check e.modifier is also not set
      const checkCtrl = config.ctrlKey === undefined || config.ctrlKey === e.ctrlKey;
      const checkMeta = config.metaKey === undefined || config.metaKey === e.metaKey;
      const checkAlt = config.altKey === undefined || config.altKey === e.altKey;
      const checkShift = config.shiftKey === undefined || config.shiftKey === e.shiftKey;

      if (matchKey && checkCtrl && checkMeta && checkAlt && checkShift) {
        callback(e);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [config, callback]);
}
