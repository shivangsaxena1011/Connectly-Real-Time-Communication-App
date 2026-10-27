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
    if (messagesContainer) {
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
  }
  scrollToBottom();

  function escapeHTML(str) {
    if (!str) return '';
    return str.replace(/[&<>'"]/g, 
      tag => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        "'": '&#39;',
        '"': '&quot;'
      }[tag] || tag)
    );
  }

  function getCsrfToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
  }

  function stageFile(file) {
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
  }

  // --- Drag and Drop onto Message Stream / Composer ---
  ['dragenter', 'dragover'].forEach(evt => {
    document.addEventListener(evt, (e) => {
      e.preventDefault();
      document.querySelector('.chat-container')?.classList.add('dragover');
    });
  });

  ['dragleave', 'drop'].forEach(evt => {
    document.addEventListener(evt, (e) => {
      e.preventDefault();
      document.querySelector('.chat-container')?.classList.remove('dragover');
    });
  });

  document.addEventListener('drop', (e) => {
    e.preventDefault();
    if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      stageFile(e.dataTransfer.files[0]);
    }
  });

  // --- Attachment Staging Preview Logic ---
  attachmentInput.addEventListener('change', (e) => {
    stageFile(e.target.files[0]);
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
      const safeUrl = encodeURI(data.attachment_url);
      const safeName = escapeHTML(data.attachment_name || 'attachment');
      const safeSize = escapeHTML(data.attachment_size || '');

      if (data.message_type === 'image' || data.attachment_url.match(/\.(jpg|jpeg|png|gif|webp)$/i)) {
        attachmentHTML = `
          <div class="chat-image-attachment">
            <a href="${safeUrl}" target="_blank" rel="noopener">
              <img src="${safeUrl}" alt="${safeName}" class="chat-img-thumb" loading="lazy" />
            </a>
          </div>
        `;
      } else {
        attachmentHTML = `
          <div class="chat-file-attachment">
            <div class="file-icon-box">
              <svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
              </svg>
            </div>
            <div class="file-details">
              <span class="file-name" title="${safeName}">${safeName}</span>
              <span class="file-size">${safeSize}</span>
            </div>
            <a href="${safeUrl}" download class="btn-download" title="Download file">
              <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="7 10 12 15 17 10"></polyline>
                <line x1="12" y1="15" x2="12" y2="3"></line>
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
        <span class="message-meta">${escapeHTML(data.timestamp || 'Just now')}</span>
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
      try {
        const data = JSON.parse(e.data);

        if (data.type === 'chat_message') {
          renderIncomingMessage(data);
          if (data.sender !== currentUser && chatSocket.readyState === WebSocket.OPEN) {
            chatSocket.send(JSON.stringify({ type: 'mark_read' }));
          }
        } else if (data.type === 'typing') {
          if (typingNotice) {
            if (data.is_typing) {
              typingNotice.classList.remove('hidden');
            } else {
              typingNotice.classList.add('hidden');
            }
          }
          scrollToBottom();
        } else if (data.type === 'user_status') {
          if (statusIndicator) {
            if (data.status === 'online') {
              statusIndicator.textContent = 'online';
              statusIndicator.className = 'status-indicator online';
            } else {
              statusIndicator.textContent = 'offline';
              statusIndicator.className = 'status-indicator offline';
            }
          }
        }
      } catch (err) {
        console.error('Error handling WebSocket message:', err);
      }
    };

    chatSocket.onclose = (e) => {
      // Reconnect automatically if closed unexpectedly
      if (!e.wasClean) {
        setTimeout(connectWebSocket, 2000);
      }
    };

    chatSocket.onerror = (err) => {
      console.warn('WebSocket encountered an issue:', err);
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
        if (chatSocket && chatSocket.readyState === WebSocket.OPEN) {
          chatSocket.send(JSON.stringify({ type: 'typing', is_typing: false }));
        }
      }, 1500);
    }
  });
});
