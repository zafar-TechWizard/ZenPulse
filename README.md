<div align="center">
  <img src="MAIN_APP/static/images/new-logo.png" alt="ZenPulse Logo" width="200"/>

  # ZenPulse: Empowering Mental Wellness

  [![Flask](https://img.shields.io/badge/Flask-2.0.1-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
  [![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
  [![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
  [![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

  <strong>Nurture Your Mind, Empower Your Well-being</strong>

  [Features](#-key-features) • [Demo](#-live-demo) • [Getting Started](#-getting-started) • [Tech Stack](#%EF%B8%8F-tech-stack) • [Contributing](#-contributing) • [License](#-license)
</div>

---

## 🌟 Key Features

<table>
  <tr>
    <td width="50%">
      <h3>🤖 AI-powered Chatbot</h3>
      <p>24/7 emotional support and guidance from our virtual psychiatrist.</p>
    </td>
    <td width="50%">
      <h3>📊 Mood Tracking</h3>
      <p>Visualize your emotional journey with interactive charts and insights.</p>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>🎮 Interactive Games</h3>
      <p>Engage in stress-reducing and cognition-improving activities.</p>
    </td>
    <td width="50%">
      <h3>🐾 Virtual Pet Companion</h3>
      <p>Care for a digital pet to experience the joy of companionship.</p>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>🎵 Personalized Music</h3>
      <p>Access mood-boosting playlists tailored to your emotional state.</p>
    </td>
    <td width="50%">
      <h3>💡 Self-Care Suggestions</h3>
      <p>Receive personalized tips based on your mood and activities.</p>
    </td>
  </tr>
</table>

## 🚀 Live Demo

Experience ZenPulse in action: [ZenPulse Demo](https://your-demo-link-here.com)

<div align="center">
  <img src="path/to/demo.gif" alt="ZenPulse Demo" width="80%"/>
</div>

## 🛠 Getting Started

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/zenpulse.git
   cd zenpulse
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```
   GROQ_API_KEY=your_api_key_here
   SECRET_KEY=your_secret_key_here
   ```

5. **Initialize the database**
   ```bash
   flask db init
   flask db migrate
   flask db upgrade
   ```

6. **Run the application**
   ```bash
   flask run
   ```

7. Open your browser and navigate to `http://localhost:5000`

## 🛠️ Tech Stack

<table>
  <tr>
    <td align="center" width="96">
      <a href="https://flask.palletsprojects.com/">
        <img src="https://flask.palletsprojects.com/en/2.0.x/_images/flask-logo.png" width="48" height="48" alt="Flask" />
      </a>
      <br>Flask
    </td>
    <td align="center" width="96">
      <a href="https://www.python.org/">
        <img src="https://upload.wikimedia.org/wikipedia/commons/c/c3/Python-logo-notext.svg" width="48" height="48" alt="Python" />
      </a>
      <br>Python
    </td>
    <td align="center" width="96">
      <a href="https://www.sqlite.org/">
        <img src="https://www.sqlite.org/images/sqlite370_banner.gif" width="48" height="48" alt="SQLite" />
      </a>
      <br>SQLite
    </td>
    <td align="center" width="96">
      <a href="https://developer.mozilla.org/en-US/docs/Web/JavaScript">
        <img src="https://upload.wikimedia.org/wikipedia/commons/9/99/Unofficial_JavaScript_logo_2.svg" width="48" height="48" alt="JavaScript" />
      </a>
      <br>JavaScript
    </td>
    <td align="center" width="96">
      <a href="https://groq.com/">
        <img src="path/to/groq-logo.png" width="48" height="48" alt="GROQ API" />
      </a>
      <br>GROQ API
    </td>
  </tr>
</table>

## 📁 Project Structure

```
zenpulse/
│
├── MAIN_APP/
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   │
│   ├── templates/
│   │   ├── index.html
│   │   ├── dashboard.html
│   │   ├── chat.html
│   │   └── ...
│   │
│   ├── app.py
│   └── model.py
│
├── venv/
├── .gitignore
├── requirements.txt
└── README.md
```

## 🤝 Contributing

We welcome contributions to ZenPulse! Please check out our [Contributing Guidelines](CONTRIBUTING.md) for details on how to get started.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

## 🙏 Acknowledgments

- [Flask](https://flask.palletsprojects.com/) and its extensions
- [GROQ API](https://groq.com/) for powering our AI responses
- All the open-source libraries used in this project

---

<div align="center">
  <strong>Remember, your mental health matters. ZenPulse is here to support you every step of the way.</strong>
  <br><br>
  <a href="https://your-website.com">Website</a>
  •
  <a href="https://twitter.com/your-twitter">Twitter</a>
  •
  <a href="https://www.linkedin.com/company/your-linkedin">LinkedIn</a>
</div>