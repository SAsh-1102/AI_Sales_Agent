const chatEl = document.getElementById('chat');
const inputEl = document.getElementById('input');
const sendBtn = document.getElementById('send');
const micBtn = document.getElementById('mic');
const leadBadge = document.getElementById('leadBadge');
const emoLabel = document.getElementById('emoLabel');
const debugEl = document.getElementById('debug');

// session id persists
let sessionId = localStorage.getItem('sessionId');
if (!sessionId) {
  sessionId = 'sess_' + Math.random().toString(36).slice(2,10);
  localStorage.setItem('sessionId', sessionId);
}

function addMessage(who, text) {
  const d = document.createElement('div');
  d.className = 'message ' + (who === 'user' ? 'user' : 'bot');
  d.textContent = text;
  chatEl.appendChild(d);
  chatEl.scrollTop = chatEl.scrollHeight;
}

function setLeadStage(stage) {
  leadBadge.textContent = 'Lead: ' + stage;
  leadBadge.className = 'badge ' +
    (stage === 'cold' ? 'stage-cold' : stage === 'warm' ? 'stage-warm' : stage === 'hot' ? 'stage-hot' : 'stage-closed');
}

function setEmotion(e) {
  emoLabel.textContent = 'Emotion: ' + e;
}

// Send message to backend
async function sendMessageToBackend(formData) {
  addMessage('bot', 'Sales Agent is processing...');
  try {
    const res = await fetch("/chat/", { method: 'POST', body: formData });
    const data = await res.json();

    // remove typing bubble
    const msgs = chatEl.querySelectorAll('.message.bot');
    if (msgs.length) {
      const last = msgs[msgs.length-1];
      if (last.textContent === 'Sales Agent is processing...') last.remove();
    }

    addMessage('bot', data.reply);
    setLeadStage(data.lead_stage);
    setEmotion(data.emotion);
    debugEl.textContent = JSON.stringify(data.memory, null, 2);

    if (data.audio) {
      const audio = new Audio("data:audio/mp3;base64," + data.audio);
      audio.play();
    }
  } catch (err) {
    console.error(err);
    addMessage('bot', 'Error contacting server.');
  }
}

// Text send
sendBtn.addEventListener('click', () => {
  const text = inputEl.value.trim();
  if (!text) return;
  addMessage('user', text);

  const formData = new FormData();
  formData.append('session_id', sessionId);
  formData.append('message', text);

  sendMessageToBackend(formData);
  inputEl.value = '';
});

inputEl.addEventListener('keypress', e => {
  if (e.key === 'Enter') sendBtn.click();
});

// Mic → record audio → send to backend
let mediaRecorder, audioChunks = [], recordTimeout;

micBtn.addEventListener('click', async () => {
  if (mediaRecorder && mediaRecorder.state === "recording") {
    mediaRecorder.stop();
    clearTimeout(recordTimeout);
    return;
  }

  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    alert("Microphone not supported. Use Chrome.");
    return;
  }

  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  mediaRecorder = new MediaRecorder(stream);
  audioChunks = [];

  mediaRecorder.ondataavailable = e => audioChunks.push(e.data);

  mediaRecorder.onstop = async () => {
    clearTimeout(recordTimeout);
    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
    const formData = new FormData();
    formData.append('session_id', sessionId);
    formData.append('audio_file', audioBlob, 'user_audio.wav');

    addMessage('user', '🎤 You spoke...');
    sendMessageToBackend(formData);
  };

  mediaRecorder.start();
  addMessage('user', '🎤 Recording...');

  recordTimeout = setTimeout(() => {
    if (mediaRecorder && mediaRecorder.state === "recording") mediaRecorder.stop();
  }, 5000);
});

// Welcome message
window.addEventListener('load', () => {
  addMessage('bot', "🤖 Welcome! I'm your AI sales assistant. You can type or speak your question.");
});
