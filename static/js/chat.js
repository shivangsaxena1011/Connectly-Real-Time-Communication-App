document.addEventListener('DOMContentLoaded', () => {
  const roomId = window.ROOM_ID;
  const currentUser = window.CURRENT_USER;
  const uploadUrl = window.UPLOAD_URL;

  const messagesContainer = document.getElementById('chat-messages');
  const chatForm = document.getElementById('chat-form');
  const chatInput = document.getElementById('chat-input');
  const attachmentInput = document.getElementById('attachment-input');
  const previewBar = document.getElementById('attachment-preview-bar');
  const previewImage = document.getElementById('preview-image');
  const previewFileIcon = document.getElementById('preview-file-icon');
  const previewFilename = document.getElementById('preview-filename');
  const previewFilesize = document.getElementById('preview-filesize');
  const btnRemoveAttachment = document.getElementById('btn-remove-attachment');
  const typingNotice = document.getElementById('typing-indicator');
  const statusIndicator = document.getElementById('user-status-indicator');

  let stagedFile = null;
  let chatSocket = null;
  let typingTimer = null;

  function scrollToBottom() {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }
  scrollToBottom();

  function getCsrfToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
  }

  // --- Attachment Staging Preview Logic ---
  attachmentInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (file.size > 15 * 1024 * 1024) {
      alert('File size exceeds the 15MB limit.');
      attachmentInput.value = '';
      return;
    }

    stagedFile = file;
    previewFilename.textContent = file.name;
    previewFilesize.textContent = (file.size / 1024).toFixed(1) + ' KB';
    previewBar.classList.remove('hidden');

    if (file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = (re) => {
        previewImage.src = re.target.result;
        previewImage.classList.remove('hidden');
        previewFileIcon.classList.add('hidden');
      };
      reader.readAsDataURL(file);
    } else {
      previewImage.classList.add('hidden');
      previewFileIcon.classList.remove('hidden');
    }
  });

  btnRemoveAttachment.addEventListener('click', () => {
    stagedFile = null;
    attachmentInput.value = '';
    previewBar.classList.add('hidden');
    previewImage.src = '';
  });

  // --- Render Message Bubbles ---
  function renderIncomingMessage(data) {
    const isMe = data.sender === currentUser;
    const bubbleWrapper = document.createElement('div');
    bubbleWrapper.className = `message-bubble-wrapper ${isMe ? 'me' : 'them'}`;

    let attachmentHTML = '';
    if (data.attachment_url) {
      if (data.message_type === 'image' || data.attachment_url.match(/\.(jpg|jpeg|png|gif|webp)$/i)) {
        attachmentHTML = `
          <div class="chat-image-attachment">
<a href="${data.attachment_url}" rel="noopener" target="_blank">
<img alt="${data.attachment_name || 'image'}" class="chat-img-thumb" loading="lazy" src="${data.attachment_url}"/>
</a>
</div>
        `;
      } else {
        attachmentHTML = `
          <div class="chat-file-attachment">
<div class="file-icon-box">
<svg fill="none" height="24" stroke="currentColor" stroke-width="2" viewbox="0 0 24 24" width="24">
<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
<polyline points="14 2 14 8 20 8"></polyline>
</svg>
</div>
<div class="file-details">
<span class="file-name" title="${data.attachment_name}">${data.attachment_name}</span>
<span class="file-size">${data.attachment_size || ''}</span>
</div>
<a class="btn-download" download="" href="${data.attachment_url}" title="Download file">
<svg fill="none" height="18" stroke="currentColor" stroke-width="2" viewbox="0 0 24 24" width="18">
<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
<polyline points="7 10 12 15 17 10"></polyline>
<line x1="12" x2="12" y1="15" y2="3"></line>
</svg>
</a>
</div>
        `;
      }
    }

    let textContentHTML = data.content ? `<p class="message-text"></p>` : '';

    bubbleWrapper.innerHTML = `
      <div class="message-bubble">
        ${attachmentHTML}
        ${textContentHTML}
        <span class="message-meta">${data.timestamp || 'Just now'}</span>
</div>
    `;

    if (data.content) {
      bubbleWrapper.querySelector('.message-text').textContent = data.content;
    }

    messagesContainer.appendChild(bubbleWrapper);
    scrollToBottom();
  }

  // --- WebSocket Connection ---
  const wsScheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
  const socketUrl = `${wsScheme}://${window.location.host}/ws/chat/${roomId}/`;

  function connectWebSocket() {
    chatSocket = new WebSocket(socketUrl);

    chatSocket.onmessage = (e) => {
      const data = JSON.parse(e.data);

      if (data.type === 'chat_message') {
        renderIncomingMessage(data);
        if (data.sender !== currentUser) {
          chatSocket.send(JSON.stringify({ type: 'mark_read' }));
        }
      } else if (data.type === 'typing') {
        if (data.is_typing) {
          typingNotice.classList.remove('hidden');
        } else {
          typingNotice.classList.add('hidden');
        }
        scrollToBottom();
      } else if (data.type === 'user_status') {
        if (data.status === 'online') {
          statusIndicator.textContent = 'online';
          statusIndicator.className = 'status-indicator online';
        } else {
          statusIndicator.textContent = 'offline';
          statusIndicator.className = 'status-indicator offline';
        }
      }
    };

    chatSocket.onclose = () => {
      setTimeout(connectWebSocket, 2000);
    };
  }

  connectWebSocket();

  // --- Form Submission Handling ---
  chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const content = chatInput.value.trim();

    // If a file is staged, send via multipart upload endpoint
    if (stagedFile) {
      const formData = new FormData();
      formData.append('attachment', stagedFile);
      formData.append('content', content);

      try {
        const res = await fetch(uploadUrl, {
          method: 'POST',
          headers: {
            'X-CSRFToken': getCsrfToken(),
            'X-Requested-With': 'XMLHttpRequest'
          },
          body: formData
        });

        if (res.ok) {
          chatInput.value = '';
          stagedFile = null;
          attachmentInput.value = '';
          previewBar.classList.add('hidden');
        } else {
          const errData = await res.json();
          alert(errData.error || 'Upload failed.');
        }
      } catch (err) {
        console.error('File upload error:', err);
        alert('Network error while uploading file.');
      }
      return;
    }

    // Standard text message sent via WebSocket
    if (content && chatSocket && chatSocket.readyState === WebSocket.OPEN) {
      chatSocket.send(JSON.stringify({
        type: 'chat_message',
        content: content
      }));
      chatSocket.send(JSON.stringify({ type: 'typing', is_typing: false }));
      chatInput.value = '';
    }
  });

  // Typing indicator debounce
  chatInput.addEventListener('input', () => {
    if (chatSocket && chatSocket.readyState === WebSocket.OPEN) {
      chatSocket.send(JSON.stringify({ type: 'typing', is_typing: true }));
      clearTimeout(typingTimer);
      typingTimer = setTimeout(() => {
        chatSocket.send(JSON.stringify({ type: 'typing', is_typing: false }));
      }, 1500);
    }
  });
});