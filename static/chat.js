const chat = document.getElementById('chat');
const input = document.getElementById('user-input');
const form = document.getElementById('input-bar');

function addMessage(text, sender) {
  const msg = document.createElement('div');
  msg.className = `message ${sender}`;
  msg.innerHTML = text.replace(/\n/g, '<br>');
  chat.appendChild(msg);
  chat.scrollTop = chat.scrollHeight;
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const userText = input.value.trim();
  if (!userText) return;
  addMessage(userText, 'user');
  input.value = '';
  try {
    const res = await fetch('/webchat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({Body: userText, User: 'Web Guest', Visited: false})
    });
    const data = await res.json();
    addMessage(data.reply, 'bot');
  } catch (err) {
    addMessage('Oops, something glitched. Try again?', 'bot');
  }
});

window.onload = () => {
  addMessage('👋 Welcome to Canyon Concierge! Text your questions or requests below.', 'bot');
  const resetBtn = document.getElementById('reset-session');
  if (resetBtn) {
    resetBtn.addEventListener('click', async () => {
      try {
        const res = await fetch('/reset_session', {method: 'POST'});
        if (res.ok) window.location.reload();
      } catch (e) {
        alert('Could not reset session.');
      }
    });
  }
};
