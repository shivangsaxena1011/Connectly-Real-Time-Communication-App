from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.db.utils import IntegrityError
from .models import Post, Comment, Like

class FeedAppTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.author = User.objects.create_user(username='author', password='Password123!')
        self.other_user = User.objects.create_user(username='other', password='Password123!')
        self.post = Post.objects.create(author=self.author, content='Hello Connectly!')

    def test_create_post(self):
        self.client.login(username='author', password='Password123!')
        res = self.client.post(reverse('home'), {'content': 'Second post test'})
        self.assertEqual(res.status_code, 302)
        self.assertEqual(Post.objects.count(), 2)

    def test_post_edit_authorization(self):
        self.client.login(username='other', password='Password123!')
        edit_url = reverse('post_edit', kwargs={'pk': self.post.pk})
        res = self.client.post(edit_url, {'content': 'Hacked post content'})
        self.assertEqual(res.status_code, 403)
        self.post.refresh_from_db()
        self.assertEqual(self.post.content, 'Hello Connectly!')

    def test_post_delete_authorization(self):
        self.client.login(username='other', password='Password123!')
        delete_url = reverse('post_delete', kwargs={'pk': self.post.pk})
        res = self.client.post(delete_url)
        self.assertEqual(res.status_code, 403)
        self.assertEqual(Post.objects.count(), 1)

    def test_like_toggle_and_duplicate_prevention(self):
        self.client.login(username='other', password='Password123!')
        like_url = reverse('toggle_like', kwargs={'pk': self.post.pk})
        res1 = self.client.post(like_url)
        self.assertEqual(res1.status_code, 200)
        self.assertTrue(res1.json()['liked'])
        self.assertEqual(self.post.likes.count(), 1)

        # Unliking
        res2 = self.client.post(like_url)
        self.assertFalse(res2.json()['liked'])
        self.assertEqual(self.post.likes.count(), 0)

    def test_comment_creation_and_ownership(self):
        self.client.login(username='other', password='Password123!')
        url = reverse('add_comment', kwargs={'pk': self.post.pk})
        res = self.client.post(url, {'content': 'Great post!'})
        self.assertEqual(res.status_code, 302)
        self.assertEqual(self.post.comments.count(), 1)

        comment = self.post.comments.first()
        self.assertEqual(comment.author, self.other_user)