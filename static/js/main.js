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
  // Like/Unlike Toggle via AJAX
  document.querySelectorAll('.btn-like').forEach(button => {
    button.addEventListener('click', async (e) => {
      e.preventDefault();
      const postId = button.dataset.postId;
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
          countSpan.textContent = data.like_count;
          if (data.liked) {
            button.classList.add('liked');
          } else {
            button.classList.remove('liked');
          }
        }
      } catch (err) {
        console.error('Like error:', err);
      }
    });
  });

  // Follow/Unfollow Toggle
  const followBtn = document.querySelector('.btn-follow');
  if (followBtn) {
    followBtn.addEventListener('click', async (e) => {
      e.preventDefault();
      const username = followBtn.dataset.username;
      try {
        const res = await fetch(`/accounts/profile/${username}/follow/`, {
          method: 'POST',
          headers: {
            'X-CSRFToken': csrftoken,
            'X-Requested-With': 'XMLHttpRequest',
          },
        });
        if (res.ok) {
          const data = await res.json();
          followBtn.textContent = data.following ? 'Unfollow' : 'Follow';
          followBtn.className = data.following ? 'btn btn-outline btn-follow' : 'btn btn-primary btn-follow';
          const followersCounter = document.querySelector('#followers-counter');
          if (followersCounter) {
            followersCounter.textContent = data.followers_count;
          }
        }
      } catch (err) {
        console.error('Follow error:', err);
      }
    });
  }
});