# 📖 Sphere

> **Every memory deserves a page.**

Sphere is a scrapbook-inspired social media platform built with **Django**, designed to feel warm, nostalgic, and handcrafted instead of looking like a modern corporate social network. Every interaction is designed to resemble memories pasted into a scrapbook using paper, tape, handwritten notes, coffee stains, and polaroid photographs.

---

## ✨ Features

### 👤 User Accounts
- User registration & login
- Secure authentication
- Profile pictures
- Display names
- User profiles
- Logout support

---

### 📸 Stories
- Upload images
- Upload videos
- Story captions
- Story preview before upload
- Video trimming
- Optional music upload
- Upload progress
- Automatic story expiration (24 hours)

---

### 💬 Social Features
- Follow users
- Like stories
- View other user profiles
- Personalized feed
- Story viewer
- Memory style interactions

---

### 🎨 Scrapbook UI

Unlike traditional social media websites, Sphere uses a handcrafted scrapbook aesthetic featuring:

- 📄 Vintage paper cards
- 📎 Masking tape decorations
- ☕ Coffee stains
- ✏️ Handwritten typography
- 📷 Polaroid-style photos
- 🌿 Warm paper color palette
- 📚 Journal inspired layouts
- ✨ Soft shadows and layered paper effects

Every page feels like opening someone's personal memory book.

---

## 🛠 Built With

- Django
- Python
- HTML5
- CSS3
- JavaScript
- SQLite (Development)

---

## 📂 Project Structure

```
Sphere/
│
├── users/
├── stories/
├── templates/
├── static/
│   ├── css/
│   ├── js/
│   ├── images/
│
├── media/
├── manage.py
└── requirements.txt
```

---

## 🚀 Installation

Clone the repository

```bash
git clone https://github.com/StiLLAngry993/Sphere.git
```

Enter the project

```bash
cd Sphere
```

Create virtual environment

```bash
python -m venv venv
```

Activate it

Windows

```bash
venv\Scripts\activate
```

Linux / Mac

```bash
source venv/bin/activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

Run migrations

```bash
python manage.py migrate
```

Create admin account

```bash
python manage.py createsuperuser
```

Run the server

```bash
python manage.py runserver
```

Open

```
http://127.0.0.1:8000/
```

---

## 🔒 Security

Sphere follows Django's built-in security features including:

- CSRF Protection
- Password Hashing
- SQL Injection Protection (ORM)
- XSS Protection
- Secure Authentication
- Session Management

---

## 📸 Screenshots

Add screenshots here after deployment.

```
screenshots/
├── home.png
├── profile.png
├── upload-story.png
├── login.png
└── register.png
```

---

## 🌱 Future Plans

- Direct Messaging
- Comments
- Notifications
- Story Reactions
- Saved Memories
- Story Highlights
- Explore Page
- Search Users
- Dark Scrapbook Theme
- AI Generated Scrapbook Covers

---

## 🤝 Contributing

Contributions are welcome.

Feel free to fork the repository and submit a pull request.

---

## 📜 License

This project is licensed under the MIT License.

---

# ❤️ About

Sphere was created to bring back the feeling of preserving memories in a scrapbook rather than endlessly scrolling through another social media feed.

Instead of endless feeds and flashy interfaces, Sphere focuses on warmth, nostalgia, and meaningful moments.

Every upload becomes another page in your digital scrapbook.
