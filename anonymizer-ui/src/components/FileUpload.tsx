import React, { useCallback, useRef, useState } from 'react';

interface FileUploadProps {
  onTextLoaded: (text: string) => void;
  isProcessing: boolean;
}

export const FileUpload: React.FC<FileUploadProps> = ({ onTextLoaded, isProcessing }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback((file: File) => {
    if (file.type !== 'text/plain' && !file.name.endsWith('.txt')) {
      alert('Please upload a .txt file');
      return;
    }

    setFileName(file.name);
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target?.result as string;
      onTextLoaded(text);
    };
    reader.readAsText(file);
  }, [onTextLoaded]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const file = e.dataTransfer.files[0];
    if (file) {
      handleFile(file);
    }
  }, [handleFile]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFile(file);
    }
  };

  return (
    <div
      className={`file-upload ${isDragging ? 'dragging' : ''} ${isProcessing ? 'processing' : ''}`}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onClick={handleClick}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept=".txt,text/plain"
        onChange={handleInputChange}
        style={{ display: 'none' }}
      />
      <div className="upload-content">
        {isProcessing ? (
          <>
            <div className="spinner"></div>
            <p>Processing...</p>
          </>
        ) : (
          <>
            <span className="upload-icon">
              {fileName ? '📄' : '📁'}
            </span>
            <p className="upload-text">
              {fileName ? fileName : 'Drop your .txt file here or click to browse'}
            </p>
            <span className="upload-hint">Supports .txt files</span>
          </>
        )}
      </div>
    </div>
  );
};
