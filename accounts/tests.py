from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from .models import Profile, Follow

class AccountsModelAndAuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='user1', password='Password123!', email='u1@example.com')
        self.user2 = User.objects.create_user(username='user2', password='Password123!', email='u2@example.com')

    def test_profile_auto_created_via_signal(self):
        self.assertTrue(hasattr(self.user1, 'profile'))
        self.assertEqual(self.user1.profile.bio, '')

    def test_follow_and_unfollow(self):
        Follow.objects.create(follower=self.user1, following=self.user2)
        self.assertEqual(self.user1.following_set.count(), 1)
        self.assertEqual(self.user2.followers_set.count(), 1)

    def test_prevent_duplicate_follow(self):
        Follow.objects.create(follower=self.user1, following=self.user2)
        with self.assertRaises(IntegrityError):
            Follow.objects.create(follower=self.user1, following=self.user2)

    def test_prevent_self_follow(self):
        with self.assertRaises(ValidationError):
            follow = Follow(follower=self.user1, following=self.user1)
            follow.save()

    def test_follow_toggle_view(self):
        self.client.login(username='user1', password='Password123!')
        url = reverse('toggle_follow', kwargs={'username': 'user2'})
        res = self.client.post(url)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()['following'])
        self.assertEqual(res.json()['followers_count'], 1)

        # Toggle unfollow
        res2 = self.client.post(url)
        self.assertFalse(res2.json()['following'])
        self.assertEqual(res2.json()['followers_count'], 0)