// CSRF Token Helper
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

const csrftoken = getCookie('csrftoken');

document.addEventListener('DOMContentLoaded', () => {
  
  // Like/Unlike Toggle via AJAX with instant visual feedback
  document.querySelectorAll('.btn-like').forEach(button => {
    button.addEventListener('click', async (e) => {
      e.preventDefault();
      const postId = button.dataset.postId;
      if (!postId) return;

      try {
        const res = await fetch(`/post/${postId}/like/`, {
          method: 'POST',
          headers: {
            'X-CSRFToken': csrftoken,
            'X-Requested-With': 'XMLHttpRequest',
          },
        });
        if (res.ok) {
          const data = await res.json();
          const countSpan = button.querySelector('.like-count');
          if (countSpan) countSpan.textContent = data.like_count;

          const icon = button.querySelector('.material-symbols-outlined');
          if (data.liked) {
            button.classList.add('liked', 'text-rose-600');
            button.classList.remove('text-slate-500');
            if (icon) icon.classList.add('fill');
          } else {
            button.classList.remove('liked', 'text-rose-600');
            button.classList.add('text-slate-500');
            if (icon) icon.classList.remove('fill');
          }
        }
      } catch (err) {
        console.error('Like error:', err);
      }
    });
  });

  // Follow/Unfollow Toggle across all follow buttons
  document.querySelectorAll('.btn-follow').forEach(followBtn => {
    followBtn.addEventListener('click', async (e) => {
      e.preventDefault();
      const username = followBtn.dataset.username;
      if (!username) return;

      try {
        const res = await fetch(`/accounts/follow/${username}/`, {
          method: 'POST',
          headers: {
            'X-CSRFToken': csrftoken,
            'X-Requested-With': 'XMLHttpRequest',
          },
        });
        if (res.ok) {
          const data = await res.json();
          followBtn.textContent = data.following ? 'Unfollow' : 'Follow';
          if (data.following) {
            followBtn.classList.remove('btn-primary');
            followBtn.classList.add('btn-outline');
          } else {
            followBtn.classList.remove('btn-outline');
            followBtn.classList.add('btn-primary');
          }

          const followersCounter = document.querySelector('#followers-counter');
          if (followersCounter) {
            followersCounter.textContent = data.followers_count;
          }
        }
      } catch (err) {
        console.error('Follow error:', err);
      }
    });
  });

});
