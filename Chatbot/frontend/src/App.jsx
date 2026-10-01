import { useState } from 'react'
import './App.css'

function App() {
  const [messages, setMessages] = useState([
    { role: 'ai', content: 'Hello! I am your Multimodal AI Chatbot. How can I help you today?' }
  ])
  const [input, setInput] = useState('')

  const handleSend = async () => {
    if (!input.trim()) return
    const newMessages = [...messages, { role: 'user', content: input }]
    setMessages(newMessages)
    setInput('')
    // Call FastAPI backend
    try {
      const formData = new FormData();
      formData.append('message', input);
      
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setMessages([...newMessages, { role: 'ai', content: data.answer }]);
    } catch (error) {
      console.error('Error fetching chat response:', error);
      setMessages([...newMessages, { role: 'ai', content: `Error: ${error.message}` }]);
    }
  }

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>Multimodal AI</h1>
      </header>
      
      <main className="chat-area">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message-row ${msg.role}`}>
            <div className="message-bubble">
              <div className="message-sender">{msg.role === 'user' ? 'User' : 'AI'}</div>
              <div className="message-content">{msg.content}</div>
            </div>
          </div>
        ))}
      </main>
      
      <footer className="input-area">
        <div className="input-actions">
          <button className="icon-btn" title="Attach Document">📎</button>
          <button className="icon-btn" title="Upload Image">🖼️</button>
          <button className="icon-btn" title="Voice Input">🎤</button>
        </div>
        <div className="input-field-wrapper">
          <input 
            type="text" 
            className="text-input" 
            placeholder="Type your message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          />
        </div>
        <button className="send-btn" onClick={handleSend} title="Send Message">➤</button>
      </footer>
    </div>
  )
}

export default App
