import { useState, useCallback } from 'react';
import { FileUpload } from './components/FileUpload';
import { TextPanel } from './components/TextPanel';
import { LegendPanel } from './components/LegendPanel';
import { anonymizeText } from './services/mockAnonymizer';
import type { AnonymizationResult } from './services/mockAnonymizer';
import './App.css';

function App() {
  const [isProcessing, setIsProcessing] = useState(false);
  const [result, setResult] = useState<AnonymizationResult | null>(null);

  const handleTextLoaded = useCallback(async (text: string) => {
    setIsProcessing(true);
    try {
      const anonymizationResult = await anonymizeText(text);
      setResult(anonymizationResult);
    } catch (error) {
      console.error('Error processing text:', error);
    } finally {
      setIsProcessing(false);
    }
  }, []);

  const handleClear = () => {
    setResult(null);
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <div className="logo">
            <span className="logo-icon">🎭</span>
            <h1>NoFace</h1>
          </div>
          <p className="tagline">AI-Powered Text Anonymization</p>
        </div>
        {result && (
          <button className="clear-btn" onClick={handleClear}>
            Clear
          </button>
        )}
      </header>

      <main className="app-main">
        {!result ? (
          <div className="upload-section">
            <FileUpload onTextLoaded={handleTextLoaded} isProcessing={isProcessing} />
            <LegendPanel />
          </div>
        ) : (
          <div className="panels-container">
            <TextPanel
              title="Original Text"
              text={result.originalText}
              icon="📝"
            />
            <TextPanel
              title="Anonymized"
              text={result.anonymizedText}
              highlightLabels={true}
              icon="🔒"
            />
            <TextPanel
              title="Replaced Values"
              text={result.replacedText}
              icon="🔄"
            />
          </div>
        )}
      </main>

      <footer className="app-footer">
        <p>Built for HackNation 2024</p>
      </footer>
    </div>
  );
}

export default App;
