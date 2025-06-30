// Progress Dropdown
const progressBtn = document.getElementById('progressBtn');
const progressMenu = document.getElementById('progressMenu');

progressBtn.addEventListener('click', (e) => {
  e.stopPropagation();
  progressMenu.classList.toggle('show');
});

document.body.addEventListener('click', () => {
  progressMenu.classList.remove('show');
});

// Auto-expand chat textarea
const chatInput = document.querySelector('.chat-input');
if (chatInput) {
  chatInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
  });
}

// Basic send button handler (for demo)
const sendBtn = document.querySelector('.send-btn');
if (sendBtn && chatInput) {
  sendBtn.addEventListener('click', () => {
    if (chatInput.value.trim()) {
      alert('Message sent: ' + chatInput.value.trim());
      chatInput.value = '';
      chatInput.style.height = '44px';
    }
  });
}
