# File Tree Viewer (GUI)

A small Windows-friendly directory viewer with a tree UI and **native file/folder icons**.

## Setup

From this folder:

### Option 1: PowerShell (if execution policy allows)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

**If you get "running scripts is disabled" error**, use one of these fixes:

**Quick fix (current session only):**

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
.\.venv\Scripts\Activate.ps1
```

**Or use activate.bat instead (works in both PowerShell and CMD):**

```powershell
python -m venv .venv
.\.venv\Scripts\activate.bat
pip install -r requirements.txt
python app.py
```

### Option 2: Run without activating (simplest)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

### Option 3: Use Command Prompt (CMD)

```cmd
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
python app.py
```

## Features (v1)

- Folder/file tree view
- Native icons for folders + file types
- Choose any folder
- Quick search (expands matches)
- Copy selected path
- Open selected item in Explorer
- Optional file pattern filter (e.g. `*.py;*.md`)

## Next ideas

- Size calculation with caching
- Right-click: copy name, copy relative path, delete/rename
- Git-ignore / ignore patterns
- Tabs + history (back/forward)
- Preview panel (text/images)

