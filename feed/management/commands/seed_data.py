from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from feed.models import Post, Comment, Like
from accounts.models import Follow
from chat.models import Conversation, Message

class Command(BaseCommand):
    help = 'Seeds initial demo users, posts, comments, likes, and follow relationships.'

    def handle(self, *args, **options):
        self.stdout.write("Purging prior demo seed records...")
        User.objects.filter(username__in=['shivang', 'ananya', 'rohan', 'priya']).delete()

        self.stdout.write("Creating demo users...")
        users = {}
        for username in ['shivang', 'ananya', 'rohan', 'priya']:
            u = User.objects.create_user(
                username=username,
                email=f"{username}@connectly.demo",
                password="DemoPassword123!",
                first_name=username.capitalize()
            )
            u.profile.bio = f"Hi! I am {username.capitalize()}, collaborating on Connectly!"
            u.profile.location = "San Francisco, CA"
            u.profile.save()
            users[username] = u

        self.stdout.write("Creating initial posts...")
        p1 = Post.objects.create(author=users['shivang'], content="Welcome to Connectly! Built with Django 5, Daphne ASGI, and pure Vanilla JS.")
        p2 = Post.objects.create(author=users['ananya'], content="Excited to share our technical specs, real-time WebSockets, and responsive UI design.")
        p3 = Post.objects.create(author=users['rohan'], content="Reviewing database relationships: User, Post, Comment, Like, Follow, and Conversations.")

        self.stdout.write("Adding likes, comments, and follow relationships...")
        Like.objects.create(user=users['ananya'], post=p1)
        Like.objects.create(user=users['rohan'], post=p1)
        Like.objects.create(user=users['priya'], post=p2)

        Comment.objects.create(author=users['priya'], post=p1, content="Awesome launch! UI feels super fast.")
        Comment.objects.create(author=users['shivang'], post=p2, content="Clean typography and responsive cards!")

        Follow.objects.create(follower=users['ananya'], following=users['shivang'])
        Follow.objects.create(follower=users['rohan'], following=users['shivang'])
        Follow.objects.create(follower=users['priya'], following=users['ananya'])

        self.stdout.write("Seeding sample real-time direct conversations...")
        conv, _ = Conversation.get_or_create_direct_chat(users['shivang'], users['ananya'])
        Message.objects.create(
            conversation=conv,
            sender=users['ananya'],
            content="Hey Shivang! Have you tested the real-time chat with attachment support?",
            is_read=True
        )
        Message.objects.create(
            conversation=conv,
            sender=users['shivang'],
            content="Yes! Images, documents, and presence indicators are all functioning seamlessly.",
            is_read=True
        )

        conv2, _ = Conversation.get_or_create_direct_chat(users['shivang'], users['rohan'])
        Message.objects.create(
            conversation=conv2,
            sender=users['rohan'],
            content="The automated test suite runs 16 tests asynchronously with full coverage.",
            is_read=False
        )

        self.stdout.write(self.style.SUCCESS("Demo database seeded successfully! Credentials for all demo users: DemoPassword123!"))
