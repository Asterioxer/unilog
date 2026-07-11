import { render, screen, act, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import UploadPanel from "../components/UploadPanel";

describe("UploadPanel Component", () => {
  it("renders instructions and triggers file selection dialog click", () => {
    const onFileSelect = vi.fn();
    const onClear = vi.fn();
    const onCancel = vi.fn();
    const setError = vi.fn();

    render(
      <UploadPanel
        onFileSelect={onFileSelect}
        selectedFile={null}
        onClear={onClear}
        isUploading={false}
        uploadProgress={0}
        onCancel={onCancel}
        error={null}
        setError={setError}
      />
    );

    expect(screen.getByText(/Drag & drop log payload file/i)).toBeInTheDocument();
    
    const clickBox = screen.getByRole("button", { name: /Upload log file/i });
    expect(clickBox).toBeInTheDocument();
  });

  it("validates file size limit and flags Payload Too Large", async () => {
    const onFileSelect = vi.fn();
    const setError = vi.fn();

    render(
      <UploadPanel
        onFileSelect={onFileSelect}
        selectedFile={null}
        onClear={vi.fn()}
        isUploading={false}
        uploadProgress={0}
        onCancel={vi.fn()}
        error={null}
        setError={setError}
      />
    );

    // Create a mock large file: 15MB
    const largeFile = new File([new ArrayBuffer(15 * 1024 * 1024)], "large.log", { type: "text/plain" });

    const input = screen.getByLabelText(/Upload log file/i).querySelector("input[type='file']") as HTMLInputElement;
    expect(input).toBeInTheDocument();

    await act(async () => {
      fireEvent.change(input, { target: { files: [largeFile] } });
    });

    expect(setError).toHaveBeenCalledWith(expect.stringContaining("Payload Too Large"));
  });

  it("validates file extensions and rejects invalid suffixes", async () => {
    const onFileSelect = vi.fn();
    const setError = vi.fn();

    render(
      <UploadPanel
        onFileSelect={onFileSelect}
        selectedFile={null}
        onClear={vi.fn()}
        isUploading={false}
        uploadProgress={0}
        onCancel={vi.fn()}
        error={null}
        setError={setError}
      />
    );

    const invalidFile = new File(["foo"], "photo.png", { type: "image/png" });
    const input = screen.getByLabelText(/Upload log file/i).querySelector("input[type='file']") as HTMLInputElement;

    await act(async () => {
      fireEvent.change(input, { target: { files: [invalidFile] } });
    });

    expect(setError).toHaveBeenCalledWith(expect.stringContaining("Invalid file type"));
  });

  it("shows progress bar and supports cancellation trigger", async () => {
    const onCancel = vi.fn();
    const file = new File(["logs"], "unilog.log");

    render(
      <UploadPanel
        onFileSelect={vi.fn()}
        selectedFile={file}
        onClear={vi.fn()}
        isUploading={true}
        uploadProgress={45}
        onCancel={onCancel}
        error={null}
        setError={vi.fn()}
      />
    );

    expect(screen.getByText("45%")).toBeInTheDocument();
    
    const cancelBtn = screen.getByText(/Cancel Upload/i);
    await act(async () => {
      cancelBtn.click();
    });

    expect(onCancel).toHaveBeenCalled();
  });

  it("handles drag-and-drop actions", async () => {
    const onFileSelect = vi.fn();
    render(
      <UploadPanel
        onFileSelect={onFileSelect}
        selectedFile={null}
        onClear={vi.fn()}
        isUploading={false}
        uploadProgress={0}
        onCancel={vi.fn()}
        error={null}
        setError={vi.fn()}
      />
    );

    const dropZone = screen.getByRole("button", { name: /Upload log file/i });

    // Drag over
    await act(async () => {
      fireEvent.dragOver(dropZone);
    });
    expect(dropZone.className).toContain("bg-primary/5");

    // Drag leave
    await act(async () => {
      fireEvent.dragLeave(dropZone);
    });
    expect(dropZone.className).not.toContain("bg-primary/5");

    // Drop file
    const file = new File(["test log text"], "app.log");
    await act(async () => {
      fireEvent.drop(dropZone, {
        dataTransfer: {
          files: [file]
        }
      });
    });

    expect(onFileSelect).toHaveBeenCalledWith(file);
  });

  it("handles keyboard events and click triggers", async () => {
    const onFileSelect = vi.fn();
    render(
      <UploadPanel
        onFileSelect={onFileSelect}
        selectedFile={null}
        onClear={vi.fn()}
        isUploading={false}
        uploadProgress={0}
        onCancel={vi.fn()}
        error={null}
        setError={vi.fn()}
      />
    );

    const dropZone = screen.getByRole("button", { name: /Upload log file/i });

    // Click zone triggers file selection input click
    const input = dropZone.querySelector("input[type='file']") as HTMLInputElement;
    const inputClickSpy = vi.spyOn(input, "click").mockImplementation(() => {});

    await act(async () => {
      dropZone.click();
    });
    expect(inputClickSpy).toHaveBeenCalled();

    // Key down Enter triggers file selection input click
    await act(async () => {
      fireEvent.keyDown(dropZone, { key: "Enter" });
    });
    expect(inputClickSpy).toHaveBeenCalledTimes(2);
  });

  it("triggers onClear when the error card close icon is clicked", async () => {
    const onClear = vi.fn();
    const file = new File(["dummy"], "app.log");

    render(
      <UploadPanel
        onFileSelect={vi.fn()}
        selectedFile={file}
        onClear={onClear}
        isUploading={false}
        uploadProgress={0}
        onCancel={vi.fn()}
        error="Some dummy API error"
        setError={vi.fn()}
      />
    );

    // Find the close button inside the error card (it has SVG close path)
    const errorCard = screen.getByText("Upload Error").parentElement?.parentElement;
    expect(errorCard).toBeDefined();

    const closeBtn = errorCard?.querySelector("button") as HTMLButtonElement;
    expect(closeBtn).toBeDefined();

    await act(async () => {
      closeBtn.click();
    });

    expect(onClear).toHaveBeenCalled();
  });
});
