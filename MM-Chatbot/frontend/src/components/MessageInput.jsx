import React, { useState, useRef, useEffect } from 'react';
import { uploadDocument } from '../services/api';

export default function MessageInput({
  onSendMessage,
  onSendImage,
  onGenerateImage,
  disabled,
  placeholder,
  attachedDoc,
  onAttachDoc,
  onDetachDoc
}) {
  const [text, setText] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [selectedImage, setSelectedImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [isGenMode, setIsGenMode] = useState(false);
  const [isUploadingDoc, setIsUploadingDoc] = useState(false);

  const recognitionRef = useRef(null);
  const timerRef = useRef(null);
  const fileInputRef = useRef(null);
  const docInputRef = useRef(null);

  // Handle image selection
  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (!file.type.startsWith('image/')) {
        alert('Please select an image file (PNG, JPG, WEBP).');
        return;
      }
      setSelectedImage(file);
      setImagePreview(URL.createObjectURL(file));
      setIsGenMode(false);
    }
  };

  const clearImage = () => {
    setSelectedImage(null);
    setImagePreview(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  // Direct Document Upload from chat input
  const handleDocChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const ext = file.name.split('.').pop().toLowerCase();
    if (!['pdf', 'txt', 'docx'].includes(ext)) {
      alert('Supported document formats: PDF, TXT, DOCX.');
      return;
    }

    setIsUploadingDoc(true);
    try {
      const docRecord = await uploadDocument(file);
      if (onAttachDoc) {
        onAttachDoc(docRecord);
      }
    } catch (err) {
      alert(`Document upload error: ${err.message}`);
    } finally {
      setIsUploadingDoc(false);
      if (docInputRef.current) docInputRef.current.value = '';
    }
  };

  // Browser Web Speech Recognition (Real-time Speech-to-Text)
  const startListening = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Voice input requires Web Speech API. Please use Google Chrome, Microsoft Edge, or Brave.");
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      recognition.onstart = () => {
        setIsRecording(true);
        setRecordingSeconds(0);
        timerRef.current = setInterval(() => {
          setRecordingSeconds((prev) => prev + 1);
        }, 1000);
      };

      recognition.onresult = (event) => {
        let transcript = '';
        for (let i = 0; i < event.results.length; i++) {
          transcript += event.results[i][0].transcript;
        }
        if (transcript) {
          setText(transcript);
        }
      };

      recognition.onerror = (event) => {
        console.warn("Speech recognition notice:", event.error);
        if (event.error === 'not-allowed') {
          alert("Microphone access was denied. Please allow microphone permissions in your browser.");
        }
        stopListening();
      };

      recognition.onend = () => {
        setIsRecording(false);
        if (timerRef.current) clearInterval(timerRef.current);
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch (err) {
      alert(`Could not start microphone: ${err.message}`);
      setIsRecording(false);
    }
  };

  const stopListening = () => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (e) {}
    }
    setIsRecording(false);
    if (timerRef.current) clearInterval(timerRef.current);
  };

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (recognitionRef.current) {
        try { recognitionRef.current.stop(); } catch (e) {}
      }
    };
  }, []);

  const handleSend = () => {
    if (selectedImage) {
      onSendImage(selectedImage, text);
      clearImage();
      setText('');
      return;
    }

    if (!text.trim()) return;

    // Check if image generation is requested
    const lower = text.trim().toLowerCase();
    const isImagePrompt = isGenMode || lower.startsWith("generate image") || lower.startsWith("draw ") || lower.startsWith("/image") || lower.includes("image banao");

    if (isImagePrompt && onGenerateImage) {
      let prompt = text.trim();
      if (lower.startsWith("generate image")) prompt = prompt.replace(/^generate image\s*(of|:)?\s*/i, "");
      else if (lower.startsWith("draw ")) prompt = prompt.replace(/^draw\s*(a|an|the)?\s*/i, "");
      else if (lower.startsWith("/image")) prompt = prompt.replace(/^\/image\s*/i, "");
      else if (lower.includes("image banao")) prompt = prompt.replace(/image banao/i, "").trim();
      onGenerateImage(prompt);
      setText('');
      setIsGenMode(false);
      return;
    }

    onSendMessage(text, attachedDoc?.id);
    setText('');
  };

  return (
    <div className="input-area">
      {/* Attached Document Chip */}
      {attachedDoc && (
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '0.5rem',
          marginBottom: '0.4rem',
          background: '#e0f2fe',
          border: '1px solid #7dd3fc',
          padding: '0.25rem 0.6rem',
          borderRadius: '16px',
          fontSize: '0.8rem',
          color: '#0369a1'
        }}>
          <span>📄 <strong>{attachedDoc.filename}</strong> (Indexed for RAG)</span>
          <button
            onClick={onDetachDoc}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#0284c7', fontWeight: 'bold' }}
            title="Detach document from chat"
          >
            ✕
          </button>
        </div>
      )}

      {/* Image Preview Thumbnail */}
      {imagePreview && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          marginBottom: '0.5rem',
          background: '#f1f5f9',
          padding: '0.4rem 0.8rem',
          borderRadius: '8px',
          width: 'fit-content'
        }}>
          <img
            src={imagePreview}
            alt="Preview"
            style={{ width: '40px', height: '40px', objectFit: 'cover', borderRadius: '4px' }}
          />
          <span style={{ fontSize: '0.8rem', color: '#475569' }}>{selectedImage?.name}</span>
          <button
            onClick={clearImage}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#dc2626', fontWeight: 'bold' }}
            title="Remove image"
          >
            ✕
          </button>
        </div>
      )}

      {isGenMode && (
        <div style={{
          fontSize: '0.75rem',
          color: '#9333ea',
          background: '#f3e8ff',
          padding: '0.2rem 0.6rem',
          borderRadius: '4px',
          marginBottom: '0.4rem',
          width: 'fit-content'
        }}>
          🎨 Image Generation Mode: Describe what to generate
        </div>
      )}

      <div className="input-box-wrapper">
        {/* Hidden image input */}
        <input
          type="file"
          accept="image/*"
          ref={fileInputRef}
          style={{ display: 'none' }}
          onChange={handleImageChange}
        />

        {/* Hidden document input */}
        <input
          type="file"
          accept=".pdf,.txt,.docx"
          ref={docInputRef}
          style={{ display: 'none' }}
          onChange={handleDocChange}
        />

        {/* Attachment button for Images */}
        <button
          className="icon-btn"
          onClick={() => fileInputRef.current?.click()}
          title="Attach Image for Visual QA / OCR"
          disabled={disabled || isRecording}
        >
          📷
        </button>

        {/* Document Upload Button (Replaces non-working speaker) */}
        <button
          className={`icon-btn ${attachedDoc ? 'active' : ''}`}
          onClick={() => docInputRef.current?.click()}
          title="Attach Document (PDF, TXT, DOCX) for QA"
          disabled={disabled || isRecording || isUploadingDoc}
          style={{ color: attachedDoc ? '#0284c7' : '#94a3b8' }}
        >
          {isUploadingDoc ? '⏳' : '📄'}
        </button>

        {/* Image Generation Toggle Button */}
        <button
          className={`icon-btn ${isGenMode ? 'active' : ''}`}
          onClick={() => setIsGenMode(!isGenMode)}
          title="Toggle Free Image Generation"
          style={{ color: isGenMode ? '#9333ea' : '#94a3b8' }}
          disabled={disabled || isRecording}
        >
          🎨
        </button>

        {/* Real-time Microphone Button (Web Speech STT) */}
        <button
          className={`icon-btn ${isRecording ? 'recording' : ''}`}
          onClick={isRecording ? stopListening : startListening}
          title={isRecording ? "Click to stop recording" : "Voice Input (Speech-to-Text)"}
          disabled={disabled}
        >
          {isRecording ? `⏹ ${recordingSeconds}s` : '🎙️'}
        </button>

        {/* Text Area */}
        <textarea
          className="chat-input"
          placeholder={
            isRecording
              ? "Listening to your voice (speak now)..."
              : isGenMode
              ? "Describe an image to generate..."
              : attachedDoc
              ? `Ask anything about ${attachedDoc.filename}...`
              : (placeholder || "Type a question, ask about an image/document, or speak...")
          }
          rows={1}
          value={text}
          disabled={disabled}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
        />

        {/* Send Button */}
        <button
          className="btn-send"
          onClick={handleSend}
          disabled={disabled || (!text.trim() && !selectedImage) || isRecording}
          title="Send"
        >
          ➤
        </button>
      </div>
    </div>
  );
}
