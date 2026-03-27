import { useRef, useState } from "react";

type UploadBoxProps = {
  file: File | null;
  onFileSelect: (file: File | null) => void;
};

export default function UploadBox({ file, onFileSelect }: UploadBoxProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleFiles = (files: FileList | null) => {
    if (!files || files.length === 0) {
      return;
    }

    const nextFile = files[0];
    if (nextFile.type.startsWith("video/")) {
      onFileSelect(nextFile);
    }
  };

  return (
    <div
      className={[
        "relative rounded-2xl border border-dashed p-6 transition duration-200",
        isDragging ? "border-neon bg-neon/10 shadow-neon" : "border-neon/30 bg-slate-950/70",
      ].join(" ")}
      onDragOver={(event) => {
        event.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={(event) => {
        event.preventDefault();
        setIsDragging(false);
        handleFiles(event.dataTransfer.files);
      }}
    >
      <input
        ref={inputRef}
        type="file"
        className="hidden"
        accept="video/mp4,video/x-matroska,video/quicktime,video/*"
        onChange={(event) => handleFiles(event.target.files)}
      />

      <div className="flex flex-col gap-5 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="font-display text-sm uppercase tracking-[0.22em] text-white">
            {file ? file.name : "Drag and drop file here"}
          </div>
          <div className="mt-2 text-sm text-muted">
            Limit 200MB per file · MP4, MKV, MOV, MPEG4
          </div>
        </div>

        <button
          type="button"
          className="subtle-button min-w-[160px]"
          onClick={() => inputRef.current?.click()}
        >
          Browse Files
        </button>
      </div>

      {file ? (
        <div className="mt-4 flex items-center justify-between rounded-xl border border-cyan/25 bg-cyan/5 px-4 py-3 text-sm text-cyan">
          <span>{(file.size / (1024 * 1024)).toFixed(2)} MB loaded</span>
          <button
            type="button"
            className="font-display text-xs uppercase tracking-[0.18em] text-white"
            onClick={() => onFileSelect(null)}
          >
            Clear
          </button>
        </div>
      ) : null}
    </div>
  );
}
