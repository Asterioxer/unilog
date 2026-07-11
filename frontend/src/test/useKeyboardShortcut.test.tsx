import { renderHook, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { useKeyboardShortcut } from "../hooks/useKeyboardShortcut";

describe("useKeyboardShortcut custom hotkey hook", () => {
  it("triggers callback when the matching key combination is pressed", () => {
    const callbackMock = vi.fn();
    renderHook(() => useKeyboardShortcut({ key: "k", ctrlKey: true }, callbackMock));

    // Dispatch non-matching event
    fireEvent.keyDown(window, { key: "k", ctrlKey: false });
    expect(callbackMock).not.toHaveBeenCalled();

    // Dispatch matching event
    fireEvent.keyDown(window, { key: "k", ctrlKey: true });
    expect(callbackMock).toHaveBeenCalled();
  });

  it("handles basic keydown checks without modifier arguments", () => {
    const callbackMock = vi.fn();
    renderHook(() => useKeyboardShortcut({ key: "Escape" }, callbackMock));

    fireEvent.keyDown(window, { key: "Escape" });
    expect(callbackMock).toHaveBeenCalled();
  });
});
