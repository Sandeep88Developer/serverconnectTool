# serverconnectTool
#  SSH Deployment & Server Tool

A simple and powerful Python desktop application built with **Tkinter** and **Paramiko** to manage remote server deployments and execute common Git, PM2, and system commands via SSH.

---

## ✨ Features

- **🚀 Quick Deploy**: One-click `git pull` with support for authenticated HTTPS (via Tokens/Base64).
- **📂 Remote Browser**: Fetch all subdirectories from `/var/www/html/` on your server to avoid typing paths.
- **📥 Command Library**: Built-in list of 30+ common commands (Git, PM2, Docker, NPM, System).
- **🧪 Health Checks**: Test your Git authentication and SSH connectivity before running commands.
- **📈 Scalable UI**: Fully resizable and maximizable window with an adaptive log viewer.
- **🔒 Security**: Passwords and Git Tokens are masked for privacy.

---

## 🛠 Prerequisites

Ensure you have **Python 3.10+** installed on your machine.

1. **Install dependencies**:
   ```bash
   pip install paramiko pyinstaller
   ```

---

## ▶️ How to Run

1. **Clone the project** (or copy `app.py`).
2. **Start the tool**:
   ```bash
   python app.py
   ```

### 💡 Using the Tool:
- **Server Settings**: Enter your SSH Host, Username, and Password.
- **Project Setup**: Click **🔍 Fetch Subfolders** to see all projects in `/var/www/html/` on your server.
- **Git Config**: Enter your Git Username and Token (PAT) for authenticated pulls/pushes.
- **Action**: Use **🚀 Quick Deploy** for a simple update, or select a specific command and click **▶ Run Selected**.

---

## 🏗️ Building the Standalone (.exe)

To convert this Python script into a single `.exe` file for Windows:

```bash
python -m PyInstaller --onefile --noconsole --clean app.py
```

- The final file will be located in the `dist/` folder.
- You can move this `app.exe` anywhere and run it **without** needing Python installed.

---

## ©️ License
© Copyright **Sandeep Sharma**. All rights reserved.

