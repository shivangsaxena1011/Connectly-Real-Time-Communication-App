# Connectly — Real-Time Communication & Social Media Web Platform

![Django](https://img.shields.io/badge/Django-5.0%2B-092E20?style=for-the-badge&logo=django&logoColor=white)
![Django Channels](https://img.shields.io/badge/Django_Channels-4.0%2B-25D366?style=for-the-badge&logo=websocket&logoColor=white)
![Daphne](https://img.shields.io/badge/ASGI-Daphne-4A154B?style=for-the-badge&logo=fastapi&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)

**Connectly** is a production-grade, full-stack social communication platform uniting traditional social media feeds with real-time direct messaging, live presence detection, dynamic typing indicators, and hybrid binary file & media attachments powered by **Django Channels**, **Daphne**, and **WebSockets**.

Designed with modern aesthetic principles using **Tailwind CSS**, **Plus Jakarta Sans**, and **Material Symbols**, Connectly delivers a lightweight, lightning-fast, and responsive user experience.

---

## 📑 Architecture & Technical Blueprints

Connectly is architected according to strict modern web specifications. Complete visual infographics and technical blueprints are preserved in the [`docs/`](docs/) directory:

| Document / Blueprint | Description | Link |
| :--- | :--- | :--- |
| **Technical Blueprint** | Real-Time Chat App End-to-End WebSocket & ASGI Architecture | [View Technical Blueprint](docs/Real-Time%20Chat%20App%20Technical%20Blueprint.png) |
| **Implementation Roadmap** | Step-by-step engineering roadmap and deployment phases | [View Roadmap](docs/Connectly%20Implementation%20Roadmap.png) |
| **Backend Schema Infographic** | Relational data models, foreign keys, constraints & indexing | [View Schema](docs/Connectly%20Backend%20Schema%20Infographic%20(1).png) |
| **Application Flow Infographic** | User lifecycle, authentication, event dispatch, and state handling | [View Application Flow](docs/Connectly%20Application%20Flow%20Infographic.png) |
| **UI/UX Design Brief** | Design tokens, color system, component typography & layouts | [View Design Brief](docs/Connectly%20UI_UX%20Design%20Brief%20(1).png) |
| **Product Requirements (PRD)** | Complete functional requirements, acceptance criteria & metrics | [View PRD](docs/Connectly%20Product%20Requirements%20Infographic.png) |

---

## 🌟 Key Features

### 1. 👥 Accounts & Social Graph (`accounts/`)
- **Secure Authentication**: User registration, session login, password encryption, and secure logout.
- **Custom Profiles**: User avatars (with automated Pillow validation), bios, location, and member timestamps.
- **Signal Automation**: Django `post_save` signals automatically create and maintain profile records on User creation.
- **Follow / Unfollow Engine**: Asynchronous follow/unfollow toggle with database-level uniqueness constraints and self-follow prevention.

### 2. 📰 Dynamic Feed & Discussions (`feed/`)
- **Rich Post Creation**: Text posts and image attachments with client-side previews and file size constraints (< 8MB).
- **Asynchronous Interactions**: Instant Like/Unlike toggle and comment publishing powered by vanilla JS and AJAX CSRF handling without page reloads.
- **Explore & Discovery**: Live search and trend exploration across users, handles, and discussion threads.
- **Author Permissions**: Guarded edit and delete permissions enforcing author ownership.

### 3. 💬 Real-Time WebSockets & Direct Messaging (`chat/`)
- **Bidirectional WebSockets**: Low-latency communication via `AsyncWebsocketConsumer` and ASGI URL routing (`/ws/chat/<room_id>/`).
- **Presence & Status Indicators**: Live online/offline status broadcast when participants connect or disconnect.
- **Interactive Typing Indicators**: Real-time debounce typing feedback displaying when the other party is drafting a response.
- **Read Receipts & Unread Badges**: Real-time unread message counters updated dynamically across conversations.

### 4. 📎 Optimized Hybrid Attachment Handling
Transferring multi-megabyte binary payloads directly over WebSockets causes head-of-line blocking and channel layer memory saturation. Connectly implements an **Optimized Hybrid Transfer Pattern**:
1. **Client Staging**: Drag-and-drop or file selection triggers instantaneous local thumbnail previews and size inspection (< 15MB limit).
2. **HTTP POST Multipart Upload**: Files are transmitted asynchronously via AJAX to `/chat/<room_id>/upload/`.
3. **Storage & Validation**: Safe file classification (image thumbnails vs. downloadable documents with badges) and database persistence.
4. **Channels Broadcast**: The server triggers a lightweight WebSocket event to the room's Channel Layer, instantly rendering formatted message bubbles and download links on both endpoints.

---

## 🏗️ Directory Layout

```text
Connectly/
├── manage.py
├── requirements.txt
├── .gitignore
├── README.md
├── docs/                                 # Architectural infographics & blueprints
│   ├── Connectly Implementation Roadmap.png
│   ├── Connectly Backend Schema Infographic (1).png
│   ├── Connectly UI_UX Design Brief (1).png
│   ├── Connectly Application Flow Infographic.png
│   ├── Connectly Product Requirements Infographic.png
│   └── Real-Time Chat App Technical Blueprint.png
├── connectly/                            # Project configuration root
│   ├── __init__.py
│   ├── asgi.py                           # ProtocolTypeRouter (HTTP + WebSockets)
│   ├── settings.py                       # Channel layer, Daphne, and app settings
│   ├── urls.py                           # Root URL routing
│   └── wsgi.py
├── accounts/                             # Authentication, Profiles & Social Graph
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py                         # Profile & Follow models
│   ├── signals.py                        # Automated profile generation signal
│   ├── tests.py                          # Auth & Follow test cases
│   ├── urls.py
│   └── views.py
├── feed/                                 # Post Feed, Likes, Comments & Explore
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py                         # Post, Comment, and Like models
│   ├── tests.py                          # Feed & interaction test cases
│   ├── urls.py
│   ├── views.py
│   └── management/commands/seed_data.py  # Automated demo data seeder
├── chat/                                 # Real-Time Channels & Direct Messaging
│   ├── admin.py
│   ├── apps.py
│   ├── consumers.py                      # AsyncWebsocketConsumer for messaging & presence
│   ├── models.py                         # Conversation & Message with attachments
│   ├── routing.py                        # WebSocket URL patterns
│   ├── tests.py                          # Channels WebSocket & upload test suite
│   ├── urls.py
│   └── views.py
├── static/
│   ├── css/
│   │   ├── style.css                     # Global design tokens and social cards
│   │   └── chat.css                      # Chat room, attachments, and composer styles
│   └── js/
│       ├── main.js                       # AJAX likes, comments, and follow scripts
│       └── chat.js                       # WebSocket client, file staging & drop zone
└── templates/
    ├── base.html                         # Master layout with responsive navbar
    ├── accounts/
    │   ├── login.html
    │   ├── register.html
    │   ├── profile.html
    │   └── edit_profile.html
    ├── feed/
    │   ├── home.html
    │   ├── explore.html
    │   ├── post_detail.html
    │   └── post_edit.html
    └── chat/
        ├── chat_list.html
        └── chat_room.html
```

---

## 🚀 Quickstart Guide

### 1. Clone the Repository & Enter Workspace
```bash
git clone https://github.com/shivangsaxena1011/Connectly-Real-Time-Communication-App.git
cd Connectly-Real-Time-Communication-App
```

### 2. Set Up Virtual Environment & Dependencies
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# macOS / Linux:
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

### 3. Run Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Seed Demo Content & Test Users
Connectly includes a built-in seeder command that generates demo accounts (`shivang`, `ananya`, `rohan`, `priya`), mock posts, comments, likes, and follow links:
```bash
python manage.py seed_data
```
> **Default credentials for all seeded demo users:**
> - **Username:** `shivang` (or `ananya`, `rohan`, `priya`)
> - **Password:** `DemoPassword123!`

### 5. Start the Real-Time Server
Because Connectly utilizes **Daphne** as its ASGI server, starting `manage.py runserver` automatically boots Daphne with full WebSocket support:
```bash
python manage.py runserver
```
Visit `http://127.0.0.1:8000/` in your browser.

---

## 🧪 Automated Testing Suite

Connectly includes a comprehensive test suite covering authentication, social graph operations, post access control, WebSocket communication, participant authorization, and file upload restrictions.

Run all tests:
```bash
python manage.py test
```

Expected output:
```text
Creating test database for alias 'default'...
................
----------------------------------------------------------------------
Ran 16 tests in ~25s

OK
Destroying test database for alias 'default'...
```

---

## ⚙️ Production Deployment Notes

1. **Redis Channel Layer**:
   In production, swap the development in-memory channel layer for Redis in `connectly/settings.py`:
   ```python
   CHANNEL_LAYERS = {
       'default': {
           'BACKEND': 'channels_redis.core.RedisChannelLayer',
           'CONFIG': {
               "hosts": [("127.0.0.1", 6379)],
           },
       },
   }
   ```
2. **Reverse Proxy Configuration**:
   When using **Nginx** in front of **Daphne**, ensure WebSocket upgrade headers are forwarded:
   ```nginx
   location /ws/ {
       proxy_pass http://127.0.0.1:8000;
       proxy_http_version 1.1;
       proxy_set_header Upgrade $http_upgrade;
       proxy_set_header Connection "upgrade";
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
   }
   ```

---

## 📜 License
Distributed under the MIT License. See `LICENSE` for more information.
