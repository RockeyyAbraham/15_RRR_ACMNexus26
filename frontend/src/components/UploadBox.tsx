import { useCallback, useRef, useState } from "react";

type UploadBoxProps = {
  file: File | null;
  onFileSelect: (file: File | null) => void;
};

export default function UploadBox({ file, onFileSelect }: UploadBoxProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleFiles = useCallback((files: FileList | null) => {
    if (!files || files.length === 0) {
      return;
    }

    const nextFile = files[0];
    if (nextFile.type.startsWith("video/")) {
      onFileSelect(nextFile);
    }
  }, [onFileSelect]);

  const handleDragOver = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);
    handleFiles(event.dataTransfer.files);
  }, [handleFiles]);

  return (
    <div
      className={[
        "relative rounded-3xl border border-dashed p-8 transition-all duration-300 backdrop-blur-md",
        isDragging ? "border-neon bg-neon/10 shadow-[0_0_30px_rgba(212,255,0,0.1)]" : "border-white/10 bg-slate-950/40 hover:border-white/20",
      ].join(" ")}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <input
        ref={inputRef}
        type="file"
        className="hidden"
        accept="video/mp4,video/x-matroska,video/quicktime,video/*"
        onChange={(event) => handleFiles(event.target.files)}
      />

      <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
        <div className="flex-1">
          <div className="font-display text-sm font-bold uppercase tracking-[0.15em] text-white">
            {file ? file.name : "Drag & Drop Reference Video"}
          </div>
          <div className="mt-2 text-xs font-medium uppercase tracking-widest text-muted/60">
            Limit 200MB · MP4, MKV, MOV, MPEG4
          </div>
        </div>

        <button
          type="button"
          className="cyber-button w-full md:w-auto mt-2 md:mt-0"
          onClick={() => inputRef.current?.click()}
        >
          Select Asset
        </button>
      </div>

      {file ? (
        <div className="mt-6 flex items-center justify-between rounded-2xl border border-cyan/20 bg-cyan/5 px-5 py-4 text-xs font-bold uppercase tracking-widest text-cyan">
          <div className="flex items-center gap-3">
            <span className="h-2 w-2 rounded-full bg-cyan shadow-[0_0_8px_rgba(0,234,255,0.6)]" />
            {(file.size / (1024 * 1024)).toFixed(2)} MB Loaded
          </div>
          <button
            type="button"
            className="font-display text-[10px] uppercase font-bold tracking-[0.2em] text-white/40 hover:text-white transition-colors"
            onClick={() => onFileSelect(null)}
          >
            Clear
          </button>
        </div>
      ) : null}
    </div>
  );
}
