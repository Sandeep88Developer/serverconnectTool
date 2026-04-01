import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import paramiko
import threading
import base64


# ─── Git & Server command definitions ────────────────────────────────────────

def _get_git_auth_prefix(u, p):
    if u and p:
        auth_str = f"{u}:{p}"
        encoded  = base64.b64encode(auth_str.encode()).decode()
        return f'-c http.extraHeader="Authorization: Basic {encoded}"'
    elif p:
        return f'-c http.extraHeader="Authorization: Bearer {p}"'
    return ""


def _git_pull(f, b, u, p):
    auth = _get_git_auth_prefix(u, p)
    return f"cd {f} && git {auth} pull origin {b}"

def _git_push(f, b, u, p):
    auth = _get_git_auth_prefix(u, p)
    return f"cd {f} && git {auth} push origin {b}"

def _git_create_branch(f, b, u, p):
    return f"cd {f} && git checkout -b {b}"

def _git_checkout_branch(f, b, u, p):
    return f"cd {f} && git checkout {b}"

def _git_delete_branch(f, b, u, p):
    return f"cd {f} && git branch -d {b}"

def _git_merge_branch(f, b, u, p):
    return f"cd {f} && git merge {b}"


GIT_COMMANDS = {
    # 🔹 BASIC GIT
    "git pull origin <branch>"        : lambda f, b, u, p: _git_pull(f, b, u, p),
    "git push origin <branch>"        : lambda f, b, u, p: _git_push(f, b, u, p),
    "git status"                      : lambda f, b, u, p: f"cd {f} && git status",
    "git log --oneline -10"           : lambda f, b, u, p: f"cd {f} && git log --oneline -10",

    # 🔹 BRANCHING
    "git create branch <branch>"      : lambda f, b, u, p: _git_create_branch(f, b, u, p),
    "git checkout <branch>"           : lambda f, b, u, p: _git_checkout_branch(f, b, u, p),
    "git delete branch <branch>"      : lambda f, b, u, p: _git_delete_branch(f, b, u, p),
    "git merge <branch>"              : lambda f, b, u, p: _git_merge_branch(f, b, u, p),
    "git branch -a"                   : lambda f, b, u, p: f"cd {f} && git branch -a",

    # 🔹 SYNC / CLEAN
    "git fetch --all"                 : lambda f, b, u, p: f"cd {f} && git fetch --all",
    "git reset --hard origin/<branch>": lambda f, b, u, p: f"cd {f} && git reset --hard origin/{b}",
    "git clean -fd"                   : lambda f, b, u, p: f"cd {f} && git clean -fd",

    # 🔹 STASH
    "git stash"                       : lambda f, b, u, p: f"cd {f} && git stash",
    "git stash pop"                   : lambda f, b, u, p: f"cd {f} && git stash pop",

    # 🔹 DEBUG
    "git diff --stat"                 : lambda f, b, u, p: f"cd {f} && git diff --stat",
    "git remote -v"                   : lambda f, b, u, p: f"cd {f} && git remote -v",

    # 🔥 PM2 COMMANDS
    "pm2 restart all"                 : lambda f, b, u, p: "pm2 restart all",
    "pm2 status"                      : lambda f, b, u, p: "pm2 status",
    "pm2 list"                        : lambda f, b, u, p: "pm2 list",
    "pm2 stop all"                    : lambda f, b, u, p: "pm2 stop all",
    "pm2 logs (50 lines)"             : lambda f, b, u, p: "pm2 logs --lines 50 --no-colors",
    "pm2 flush (clear logs)"          : lambda f, b, u, p: "pm2 flush",

    # 🚀 NODE / NPM
    "npm install"                     : lambda f, b, u, p: f"cd {f} && npm install",
    "npm run build"                   : lambda f, b, u, p: f"cd {f} && npm run build",
    "node --version"                  : lambda f, b, u, p: "node -v",

    # 🐳 DOCKER (if applicable)
    "docker ps"                       : lambda f, b, u, p: "docker ps",
    "docker-compose up -d"            : lambda f, b, u, p: f"cd {f} && docker-compose up -d",
    "docker-compose restart"          : lambda f, b, u, p: f"cd {f} && docker-compose restart",

    # 🛠️ SERVER COMMANDS
    "check disk usage"                : lambda f, b, u, p: "df -h",
    "check memory"                    : lambda f, b, u, p: "free -m",
    "current directory"               : lambda f, b, u, p: f"cd {f} && pwd",
    "list files"                      : lambda f, b, u, p: f"cd {f} && ls -la",
}


# ─── Helpers ─────────────────────────────────────────────────────────────────

def get_ssh_client():
    host     = entry_host.get().strip()
    username = entry_user.get().strip()
    password = entry_pass.get().strip()

    if not host or not username:
        raise ValueError("Host and Username are required.")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, timeout=10)
    return client


def log(message: str):
    output.configure(state="normal")
    output.insert(tk.END, message + "\n")
    output.see(tk.END)
    output.configure(state="disabled")


def run_remote(client, command: str):
    _, stdout, stderr = client.exec_command(command)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    return out, err


# ─── Actions ─────────────────────────────────────────────────────────────────

def fetch_remote_folders():
    def task():
        log("─" * 50)
        log("🔍 Fetching subdirectories from /var/www/html/...")
        try:
            client = get_ssh_client()
            log("✔ Connected.")
            command = "find /var/www/html -maxdepth 1 -type d"
            out, err = run_remote(client, command)
            if out:
                lines = out.splitlines()
                folders = [line for line in lines if line != "/var/www/html"]
                root.after(0, lambda: folder_dropdown.configure(values=folders))
                if folders:
                    root.after(0, lambda: folder_dropdown.set(folders[0]))
                    log(f"✔ Found {len(folders)} folders.")
            if err: log(f"[stderr] {err}")
            client.close()
        except Exception as exc:
            log(f"✖ Error: {exc}")

    threading.Thread(target=task, daemon=True).start()


def deploy_code():
    folder   = entry_folder.get().strip()
    branch   = entry_branch.get().strip()
    git_user = entry_git_user.get().strip()
    git_pass = entry_git_pass.get().strip()

    if not folder or not branch:
        messagebox.showwarning("Missing Info", "Please select or type a Server Folder Path and Git Branch.")
        return

    def task():
        log("─" * 50)
        log("▶ Connecting to server…")
        try:
            client  = get_ssh_client()
            log("✔ Connected.")
            command = _git_pull(folder, branch, git_user, git_pass)
            log(f"▶ Running: git pull origin {branch}")
            out, err = run_remote(client, command)
            if out: log(out)
            if err: log(f"[stderr] {err}")
            log("✔ Deploy finished.")
            client.close()
        except Exception as exc:
            log(f"✖ Error: {exc}")

    threading.Thread(target=task, daemon=True).start()


def run_git_command():
    folder   = entry_folder.get().strip()
    branch   = entry_branch.get().strip()
    git_user = entry_git_user.get().strip()
    git_pass = entry_git_pass.get().strip()
    selected = git_cmd_var.get()

    if not selected:
        messagebox.showwarning("Missing Info", "Please select a command.")
        return

    cmd_builder = GIT_COMMANDS.get(selected)
    command = cmd_builder(folder, branch, git_user, git_pass)

    def task():
        log("─" * 50)
        log(f"▶ Command: {selected}")
        log("▶ Connecting to server…")
        try:
            client = get_ssh_client()
            log("✔ Connected.")
            log(f"▶ Running on server…")
            out, err = run_remote(client, command)
            if out: log(out)
            if err: log(f"[stderr] {err}")
            log("✔ Done.")
            client.close()
        except Exception as exc:
            log(f"✖ Error: {exc}")

    threading.Thread(target=task, daemon=True).start()


def test_git_connection():
    folder   = entry_folder.get().strip()
    git_user = entry_git_user.get().strip()
    git_pass = entry_git_pass.get().strip()

    if not folder:
        messagebox.showwarning("Missing Info", "Please select or type a Server Folder Path first.")
        return

    def task():
        log("─" * 50)
        log("▶ Testing Git Remote Connection…")
        try:
            client = get_ssh_client()
            log("✔ SSH Connected.")
            auth = _get_git_auth_prefix(git_user, git_pass)
            command = f"cd {folder} && git {auth} ls-remote --heads origin"
            out, err = run_remote(client, command)
            if "HEAD" in out or "refs/heads" in out:
                log("✔ Git Authentication Successful!")
            else:
                log("✖ Git Connection Failed.")
                if err: log(f"[stderr] {err}")
            client.close()
        except Exception as exc:
            log(f"✖ Error: {exc}")

    threading.Thread(target=task, daemon=True).start()


# ─── UI ──────────────────────────────────────────────────────────────────────

root = tk.Tk()
root.title("SSH Deployment & Server Tool")
root.geometry("850x700")  # Set a reasonable default size
root.resizable(True, True)  # ENABLE MAXIMIZE/MINIMIZE

BG        = "#1e1e2e"
PANEL     = "#2a2a3e"
ACCENT    = "#7c3aed"
ACCENT_HV = "#6d28d9"
TEXT      = "#e2e8f0"
MUTED     = "#94a3b8"
FONT_LBL  = ("Segoe UI", 10)
FONT_MONO = ("Consolas", 9)

# Column weight so everything fills horizontally
root.columnconfigure(0, weight=1)
root.configure(bg=BG)

style = ttk.Style()
style.theme_use("clam")
style.configure("TEntry", fieldbackground=PANEL, foreground=TEXT, insertcolor=TEXT, bordercolor="#3f3f5e", relief="flat", padding=6)
style.configure("TCombobox", fieldbackground=PANEL, foreground=TEXT, background=PANEL, selectbackground=ACCENT, selectforeground="white", bordercolor="#3f3f5e", arrowcolor=TEXT, relief="flat", padding=5)
style.map("TCombobox", fieldbackground=[("readonly", PANEL)], foreground=[("readonly", TEXT)])

# ── Header ───────────────────────────────────────────────────────────────────
header = tk.Frame(root, bg=ACCENT, pady=10)
header.grid(row=0, column=0, sticky="ew")
tk.Label(header, text="🚀  SSH Deployment Tool", font=("Segoe UI", 15, "bold"), bg=ACCENT, fg="white").pack()

# ── Form ─────────────────────────────────────────────────────────────────────
form = tk.Frame(root, bg=BG, padx=20, pady=10)
form.grid(row=1, column=0, sticky="ew")
form.columnconfigure((0, 1), weight=1)  # Make columns equal width

server_frame = tk.LabelFrame(form, text=" Server & SSH ", font=("Segoe UI", 9, "bold"), bg=BG, fg=ACCENT, padx=10, pady=10)
server_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

git_frame = tk.LabelFrame(form, text=" Git Credentials ", font=("Segoe UI", 9, "bold"), bg=BG, fg="#10b981", padx=10, pady=10)
git_frame.grid(row=0, column=1, sticky="nsew")

# Use pack for inner frames since we want vertical flow
tk.Label(server_frame, text="Host", font=FONT_LBL, bg=BG, fg=MUTED, anchor="w").pack(fill="x")
entry_host = ttk.Entry(server_frame); entry_host.pack(fill="x", pady=(0, 8))

tk.Label(server_frame, text="SSH Username", font=FONT_LBL, bg=BG, fg=MUTED, anchor="w").pack(fill="x")
entry_user = ttk.Entry(server_frame); entry_user.pack(fill="x", pady=(0, 8))

tk.Label(server_frame, text="SSH Password", font=FONT_LBL, bg=BG, fg=MUTED, anchor="w").pack(fill="x")
entry_pass = ttk.Entry(server_frame, show="●"); entry_pass.pack(fill="x", pady=(0, 8))

folder_lbl_row = tk.Frame(server_frame, bg=BG); folder_lbl_row.pack(fill="x")
tk.Label(folder_lbl_row, text="Server Folder Path", font=FONT_LBL, bg=BG, fg=MUTED, anchor="w").pack(side="left")
tk.Button(folder_lbl_row, text="🔍 Fetch", font=("Segoe UI", 7, "bold"), bg="#334155", fg="white", command=fetch_remote_folders, relief="flat", padx=4, cursor="hand2").pack(side="right")
entry_folder = tk.StringVar()
folder_dropdown = ttk.Combobox(server_frame, textvariable=entry_folder); folder_dropdown.pack(fill="x", pady=(0, 8)); folder_dropdown.set("/var/www/html")

tk.Label(git_frame, text="Git Branch", font=FONT_LBL, bg=BG, fg=MUTED, anchor="w").pack(fill="x")
entry_branch = ttk.Entry(git_frame); entry_branch.pack(fill="x", pady=(0, 8)); entry_branch.insert(0, "main")

tk.Label(git_frame, text="Git Username", font=FONT_LBL, bg=BG, fg=MUTED, anchor="w").pack(fill="x")
entry_git_user = ttk.Entry(git_frame); entry_git_user.pack(fill="x", pady=(0, 8))

tk.Label(git_frame, text="Git Password / Token", font=FONT_LBL, bg=BG, fg=MUTED, anchor="w").pack(fill="x")
entry_git_pass = ttk.Entry(git_frame, show="●"); entry_git_pass.pack(fill="x", pady=(0, 8))

# ── Command Selector ─────────────────────────────────────────────────────────
cmd_frame = tk.Frame(root, bg=BG, padx=20, pady=4)
cmd_frame.grid(row=2, column=0, sticky="ew")
cmd_frame.columnconfigure(1, weight=1)

tk.Label(cmd_frame, text="Command", font=FONT_LBL, bg=BG, fg=MUTED, anchor="w").grid(row=0, column=0, sticky="w")
git_cmd_var = tk.StringVar()
git_dropdown = ttk.Combobox(cmd_frame, textvariable=git_cmd_var, values=list(GIT_COMMANDS.keys()), state="readonly")
git_dropdown.set("git pull origin <branch>")
git_dropdown.grid(row=0, column=1, sticky="ew", padx=(10, 0))

# ── Buttons ───────────────────────────────────────────────────────────────────
btn_frame = tk.Frame(root, bg=BG, padx=20, pady=4)
btn_frame.grid(row=3, column=0, sticky="ew")
btn_frame.columnconfigure((0, 1, 2, 3), weight=1)

def make_button(parent, text, command, row, col, color=ACCENT):
    btn = tk.Button(parent, text=text, command=command, font=("Segoe UI", 9, "bold"), bg=color, fg="white", 
                    activebackground=ACCENT_HV, activeforeground="white", relief="flat", padx=12, pady=6, cursor="hand2", bd=0)
    btn.grid(row=row, column=col, padx=(0 if col == 0 else 8, 0), pady=6, sticky="ew")
    return btn

make_button(btn_frame, "🚀 Quick Deploy",   deploy_code,         0, 0, ACCENT)
make_button(btn_frame, "▶ Run Selected",     run_git_command,     0, 1, "#1d4ed8")
make_button(btn_frame, "🧪 Test Git",        test_git_connection, 0, 2, "#10b981")
make_button(btn_frame, "⚙ PM2 Restart",     lambda: threading.Thread(target=lambda: (log("─"*50), log("▶ Running PM2 Restart..."), [log(r) for r in run_remote(get_ssh_client(), "pm2 restart all")])).start(), 0, 3, "#0f766e")

# ── Output log ────────────────────────────────────────────────────────────────
log_frame = tk.Frame(root, bg=BG, padx=20, pady=10)
log_frame.grid(row=4, column=0, sticky="nsew")
log_frame.columnconfigure(0, weight=1)
log_frame.rowconfigure(1, weight=1)

tk.Label(log_frame, text="Output Log", font=("Segoe UI", 10, "bold"), bg=BG, fg=TEXT).grid(row=0, column=0, sticky="w", pady=(0, 4))
output = scrolledtext.ScrolledText(log_frame, bg=PANEL, fg=TEXT, font=FONT_MONO, insertbackground=TEXT, relief="flat", state="disabled", wrap="word", bd=0, highlightthickness=1, highlightbackground="#3f3f5e")
output.grid(row=1, column=0, sticky="nsew")

# ── Footer ────────────────────────────────────────────────────────────────────
footer_frame = tk.Frame(root, bg=BG, pady=6)
footer_frame.grid(row=5, column=0, sticky="ew")
tk.Label(footer_frame, text="© Copyright Sandeep Sharma", font=("Segoe UI", 8, "italic"), bg=BG, fg=MUTED).pack()

root.grid_rowconfigure(4, weight=1)
root.mainloop()
