NetShare — Network Folder Notification Overlay
===============================================
Version 1.0  |  Built on Ohverlay v4.0 architecture

WHAT IT DOES
------------
NetShare solves the "drop a file and go tell them manually" problem.

When someone leaves a file for you in their shared folder, NetShare
pops a floating bubble notification on your screen and a tray balloon.
Click the balloon to open their folder immediately.
Both sides are logged so you have a full trace of who sent what and when.

HOW IT WORKS (no IT changes needed)
------------------------------------
Each person has their own shared folder others can READ but NOT WRITE.

  \\server\shared\john\          <- John's folder (others can read)
      _ohverlay\
          notify_maria_20260401_120000.json   <- John notified Maria
          ack_to_john_20260401_120500.json    <- Maria confirmed receipt

When John wants to tell Maria a file is ready:
  1. John drops the file in his folder (or a subfolder named after her)
  2. John right-clicks the NetShare tray icon → Notify a Peer → Maria
  3. John types the filename + optional message → OK
  4. Maria's NetShare sees the notify file and shows a bubble on her screen
  5. Maria clicks the tray balloon → John's folder opens in Explorer
  6. NetShare writes an ack so John's overlay confirms: "Maria opened your file"

INSTALLATION (each PC)
-----------------------
1. Copy the NetShare folder to any location (e.g. Desktop or C:\Tools\)
2. Double-click NetShare.exe
3. A folder icon appears in the system tray (bottom-right clock area)
4. Right-click → "Configure My Shared Folder..."
5. Enter:
     • Your own shared folder path  (e.g. \\server\shared\yourname)
     • Your username                (e.g. yourname)
     • Your peers, one per line:    maria=\\server\shared\maria
6. Right-click → "Enable Notifications" to turn it on
7. Done. NetShare runs silently in the background.

ADDING TO WINDOWS STARTUP (optional, no admin needed)
-------------------------------------------------------
Press Win+R, type:  shell:startup
Copy a shortcut to NetShare.exe into that folder.
NetShare will start automatically when you log in.

PROTOTYPE / IT APPROVAL NOTE
------------------------------
This prototype only reads from network shared folders your account can
already access. It does NOT:
  - Install any services or drivers
  - Require admin rights
  - Open any network ports
  - Transmit data outside your local network

The _ohverlay\ subfolder it creates is a plain folder with small JSON
text files (a few hundred bytes each). Safe to delete at any time.

ACTIVITY LOG
-------------
All send/receive/open events are saved to:
  %USERPROFILE%\.netshare\config.json     <- your settings
  %USERPROFILE%\.netshare\net_share_log.jsonl  <- activity log

Right-click tray → "View Activity Log..." opens it in Notepad.

BUILD FROM SOURCE
------------------
Requires: Python 3.10+, PySide6, loguru, pyinstaller

  pip install PySide6 loguru pyinstaller
  build_netshare.bat

Output: dist\NetShare\NetShare.exe
