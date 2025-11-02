from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sqlite3
import uuid
import google.generativeai as genai

app = Flask(__name__)
CORS(app)

# Configure Google AI
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY", "AIzaSyCE7Rcv1DI8kVPzs2momYdLtRv_9vO5ybU"))

# Initialize database - Render uses /tmp for writable storage
def init_db():
    conn = sqlite3.connect('/tmp/chat_sessions.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS chat_sessions
        (session_id TEXT PRIMARY KEY,
         file_content TEXT,
         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS chat_messages
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         session_id TEXT,
         role TEXT,
         content TEXT,
         timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
         FOREIGN KEY (session_id) REFERENCES chat_sessions (session_id))
    ''')
    conn.commit()
    conn.close()

init_db()

def get_chat_history(session_id):
    conn = sqlite3.connect('/tmp/chat_sessions.db')
    c = conn.cursor()
    c.execute('SELECT role, content FROM chat_messages WHERE session_id = ? ORDER BY timestamp', (session_id,))
    messages = c.fetchall()
    conn.close()
    return messages

def save_message(session_id, role, content):
    conn = sqlite3.connect('/tmp/chat_sessions.db')
    c = conn.cursor()
    c.execute('INSERT INTO chat_messages (session_id, role, content) VALUES (?, ?, ?)', 
              (session_id, role, content))
    conn.commit()
    conn.close()

def create_session(session_id, file_content):
    conn = sqlite3.connect('/tmp/chat_sessions.db')
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO chat_sessions (session_id, file_content) VALUES (?, ?)', 
              (session_id, file_content))
    conn.commit()
    conn.close()

@app.route('/')
def home():
    return jsonify({
        "status": "Backend is running!", 
        "message": "Datathon AI Backend",
        "environment": "Render"
    })

@app.route('/analyze', methods=['POST'])
def analyze_document():
    try:
        data = request.json
        text = data.get('text', '')
        filename = data.get('filename', 'unknown file')
        
        # Create a new session
        session_id = str(uuid.uuid4())
        create_session(session_id, text)
        
        # Generate initial summary using Gemini
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = f"""
        Please analyze this document and provide a comprehensive, useful summary. 
        Focus on the actual content, main topics, and key insights.
        
        Document: {filename}
        
        Content to analyze:
        {text[:6000]}
        
        Please provide a clear, actionable summary.
        """
        
        response = model.generate_content(prompt)
        
        # Save the AI's initial summary
        save_message(session_id, 'assistant', f"Document Summary: {response.text}")
        
        return jsonify({
            'success': True,
            'analysis': response.text,
            'session_id': session_id,
            'filename': filename
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/chat', methods=['POST'])
def chat_with_ai():
    try:
        data = request.json
        session_id = data.get('session_id')
        message = data.get('message')
        
        if not session_id or not message:
            return jsonify({'success': False, 'error': 'Missing session_id or message'})
        
        # Get file content
        conn = sqlite3.connect('/tmp/chat_sessions.db')
        c = conn.cursor()
        c.execute('SELECT file_content FROM chat_sessions WHERE session_id = ?', (session_id,))
        result = c.fetchone()
        
        if not result:
            return jsonify({'success': False, 'error': 'Session not found'})
        
        file_content = result[0]
        
        # Get chat history
        chat_history = get_chat_history(session_id)
        
        # Save user message
        save_message(session_id, 'user', message)
        
        # Prepare context
        context = f"Document Content:\n{file_content[:4000]}\n\n"
        
        # Add recent chat history
        if chat_history:
            context += "Previous conversation:\n"
            for role, content in chat_history[-4:]:
                context += f"{role}: {content}\n"
        
        # Generate AI response
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = f"""
        {context}
        
        User's question: {message}
        
        Please provide a helpful response based on the document content and conversation history.
        """
        
        response = model.generate_content(prompt)
        
        # Save AI response
        save_message(session_id, 'assistant', response.text)
        
        return jsonify({
            'success': True,
            'response': response.text,
            'session_id': session_id
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
