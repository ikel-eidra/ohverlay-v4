# OHVERLAY (ZenFish) - Installation Guide

## Option A: Portable .exe (Recommended for office PC, NO admin needed)

### Step 1: Build the .exe (do this at home)

You need Python on ANY computer to build it once. Then copy the result to your office PC.

```
# On your home PC with Python installed:
git clone https://github.com/ohverlay/ohverlay.git
cd ohverlay

pip install pyinstaller PySide6 numpy loguru requests pynput anthropic
pyinstaller zenfish.spec --noconfirm --clean
```

Or just double-click `build_windows.bat`.

### Step 2: Copy to office PC

1. The build creates a folder: `dist/ZenFish/`
2. Copy the entire `ZenFish` folder to a USB drive
3. On your office PC, paste it anywhere you have access:
   - `C:\Users\YourName\Desktop\ZenFish\`
   - `C:\Users\YourName\Documents\ZenFish\`
   - Or even run it directly from the USB drive
4. Double-click `ZenFish.exe` - that's it!

No Python, no admin, no installation. Just run.

---

## Option B: Portable Python (if you want to modify the code at office)

If you can't install Python normally (no admin), use the **embeddable** version:

### Step 1: Download Portable Python

1. Go to https://www.python.org/downloads/windows/
2. Download **"Windows embeddable package (64-bit)"** (a .zip file, ~10MB)
3. Extract to: `C:\Users\YourName\PortablePython\`

### Step 2: Enable pip

1. Open `C:\Users\YourName\PortablePython\python311._pth` in Notepad
2. Uncomment (remove the #) from the line: `#import site` → `import site`
3. Save the file
4. Download https://bootstrap.pypa.io/get-pip.py (right-click → Save As)
5. Open Command Prompt (Win+R → cmd → Enter):
   ```
   C:\Users\YourName\PortablePython\python.exe get-pip.py
   ```

### Step 3: Install ZenFish

```cmd
set PATH=C:\Users\YourName\PortablePython;C:\Users\YourName\PortablePython\Scripts;%PATH%

cd C:\Users\YourName\Desktop
git clone https://github.com/ohverlay/ohverlay.git
cd ohverlay

pip install --user PySide6 numpy loguru requests pynput anthropic
```

### Step 4: Run

```cmd
C:\Users\YourName\PortablePython\python.exe main.py
```

### Step 5 (Optional): Create a shortcut

1. Right-click Desktop → New → Shortcut
2. Location: `C:\Users\YourName\PortablePython\python.exe C:\Users\YourName\Desktop\ohverlay\main.py`
3. Name it "ZenFish"
4. Double-click to launch!

---

## Option C: Normal install (if you have admin)

```
pip install PySide6 numpy loguru requests pynput anthropic
git clone https://github.com/ohverlay/ohverlay.git
cd ohverlay
python main.py
```

---

## Tray Controls

Right-click the fish icon in your system tray (bottom-right corner) to access:
- **Fish Species**: Solo Betta, Neon Tetra (x6/x10/x12)
- **Swimming Speed**: Super Slow, Slow, Normal, Fast
- **Fish Size**: Tiny to Very Large
- **Color Theme**: Various betta colors
- **Modules**: Health reminders, love notes, schedule, news
- **Sanctuary Zones**: Block fish from specific monitors
- **Feed Fish**: Ctrl+Alt+F
- **Toggle Visibility**: Ctrl+Alt+H

## Troubleshooting

**"Windows protected your PC" popup:**
Click "More info" → "Run anyway". This happens because the .exe isn't signed. It's safe.

**Fish not visible:**
Make sure no fullscreen apps are running. The fish swim on a transparent overlay that sits above your desktop but below fullscreen windows.

**No system tray icon:**
Click the ^ arrow in the bottom-right taskbar to find the hidden ZenFish icon.
