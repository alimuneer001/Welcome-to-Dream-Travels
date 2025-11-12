# Welcome to Dream Travels

A Flask-based travel booking web application that allows users to browse destinations, book trips, and manage their travel bookings.

## Features

- 🗺️ Browse travel destinations with detailed information
- 🛒 Shopping cart functionality
- 📅 Book trips with travel dates
- 👤 User authentication (signup/login)
- 🔐 Admin panel for managing destinations and bookings
- 💳 Checkout and order management
- 📧 Contact page

## Installation

1. Clone the repository:
```bash
git clone https://github.com/alimuneer001/Welcome-to-Dream-Travels.git
cd Welcome-to-Dream-Travels
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
```bash
# Windows
venv\Scripts\Activate.ps1

# Linux/Mac
source venv/bin/activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Run the application:
```bash
python app.py
```

Or using Flask CLI:
```bash
flask run
```

## Default Admin Credentials

- Username: `admin`
- Password: `admin123`

## Technologies Used

- Flask 3.0.2
- SQLite (Database)
- Jinja2 (Templates)
- Bootstrap (Frontend)

## Project Structure

```
.
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── travel.db             # SQLite database (created automatically)
├── static/               # Static files (CSS, JS, images)
│   └── css/
│       └── style.css
└── templates/            # HTML templates
    ├── base.html
    ├── home.html
    ├── login.html
    ├── signup.html
    ├── admin.html
    └── ...
```

## License

This project is open source and available for educational purposes.

