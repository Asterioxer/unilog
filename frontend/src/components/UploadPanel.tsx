import React, { useState, useRef } from "react";
import { Upload, X, AlertCircle } from "lucide-react";

interface UploadPanelProps {
  onFileSelect: (file: File) => void;
  selectedFile: File | null;
  onClear: () => void;
  isUploading: boolean;
  uploadProgress: number;
  onCancel: () => void;
  error: string | null;
  setError: (error: string | null) => void;
}

const ACCEPTED_EXTENSIONS = [".log", ".txt", ".json", ".gz"];
const MAX_FILE_SIZE_MB = 10;

export default function UploadPanel({
  onFileSelect,
  selectedFile,
  onClear,
  isUploading,
  uploadProgress,
  onCancel,
  error,
  setError,
}: UploadPanelProps) {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateAndSelectFile = (file: File) => {
    setError(null);

    // Validate size (e.g. 10MB limit)
    const fileSizeMB = file.size / (1024 * 1024);
    if (fileSizeMB > MAX_FILE_SIZE_MB) {
      setError(`Payload Too Large: File size exceeds ${MAX_FILE_SIZE_MB}MB limit`);
      return;
    }

    // Validate extension
    const extension = file.name.substring(file.name.lastIndexOf(".")).toLowerCase();
    if (!ACCEPTED_EXTENSIONS.includes(extension)) {
      setError("Invalid file type: Please select a .log, .txt, .json, or .gz file");
      return;
    }

    onFileSelect(file);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndSelectFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndSelectFile(e.target.files[0]);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      fileInputRef.current?.click();
    }
  };

  return (
    <div className="space-y-4">
      {/* Drag & Drop Box */}
      <div
        role="button"
        tabIndex={0}
        aria-label="Upload log file"
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !isUploading && fileInputRef.current?.click()}
        onKeyDown={handleKeyPress}
        className={`border-2 border-dashed rounded-xl p-8 flex flex-col items-center justify-center text-center cursor-pointer transition-all relative ${
          isDragging 
            ? "border-primary bg-primary/5 scale-[1.01]" 
            : "border-border hover:border-primary/50"
        } ${isUploading ? "pointer-events-none opacity-80" : ""}`}
      >
        <input
          type="file"
          ref={fileInputRef}
          className="hidden"
          onChange={handleFileChange}
          accept={ACCEPTED_EXTENSIONS.join(",")}
          disabled={isUploading}
        />
        <Upload className={`h-10 w-10 mb-4 transition-colors ${isDragging ? "text-primary" : "text-muted-foreground"}`} />
        
        {selectedFile ? (
          <div className="space-y-1">
            <p className="font-semibold text-primary text-sm truncate max-w-xs">{selectedFile.name}</p>
            <p className="text-xs text-muted-foreground">{(selectedFile.size / 1024).toFixed(2)} KB</p>
          </div>
        ) : (
          <div>
            <p className="text-sm font-semibold">Drag & drop log payload file, or click to browse</p>
            <p className="text-xs text-muted-foreground mt-1">Supports {ACCEPTED_EXTENSIONS.join(", ")} up to {MAX_FILE_SIZE_MB}MB</p>
          </div>
        )}
      </div>

      {/* Upload Progress bar */}
      {isUploading && (
        <div className="border border-border bg-muted/30 rounded-xl p-4 space-y-2">
          <div className="flex items-center justify-between text-xs font-semibold">
            <span className="text-muted-foreground">Uploading File...</span>
            <span className="text-primary">{uploadProgress}%</span>
          </div>
          <div className="w-full bg-muted rounded-full h-2 overflow-hidden">
            <div 
              data-testid="upload-progress-bar"
              className="bg-primary h-2 transition-all duration-300 rounded-full"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
          <div className="flex justify-end">
            <button
              onClick={(e) => {
                e.stopPropagation();
                onCancel();
              }}
              className="text-xs font-semibold text-destructive bg-destructive/5 hover:bg-destructive/10 border border-destructive/10 rounded-md px-2.5 py-1 transition-colors flex items-center gap-1"
            >
              <X className="h-3 w-3" />
              Cancel Upload
            </button>
          </div>
        </div>
      )}

      {/* Inline validation errors */}
      {error && (
        <div className="flex items-start gap-2.5 border border-destructive/20 bg-destructive/5 text-destructive rounded-xl p-3.5 text-xs animate-shake">
          <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="font-semibold">Upload Error</p>
            <p className="text-muted-foreground mt-0.5">{error}</p>
          </div>
          {selectedFile && !isUploading && (
            <button 
              onClick={(e) => {
                e.stopPropagation();
                onClear();
              }}
              className="p-1 hover:bg-destructive/10 rounded-md transition-colors"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>
      )}
    </div>
  );
}
