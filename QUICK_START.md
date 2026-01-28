fly# Quick Start Guide

## Starting the Server

1. **Activate your virtual environment:**
   ```bash
   source venv/bin/activate
   ```

2. **Install dependencies (if not already done):**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the server:**
   ```bash
   python3 mud_server.py
   ```

   You should see:
   ```
   Firebase initialized successfully.
   Starting web-based MUD server...
   WebSocket server started on localhost:5557
   ```

## Connecting to the Game

### Use the Web Client (Recommended)

1. **Open `web_client.html` in your browser**
   - Double-click the file, or
   - Right-click → Open With → Browser

2. **Enter WebSocket URL:**
   - Local: `ws://localhost:5557`
   - Remote: `ws://your-server-ip:5557`

3. **Click "Connect"**

4. **Enter your email and password when prompted**

5. **Start playing!**

## Troubleshooting

### "Port 5557 is not in use"
- **Server isn't running** - Start it with `python3 mud_server.py`
- Check for error messages during startup

### "Connection refused"
- Server isn't running
- Wrong port number
- Firewall blocking the port

### "websockets library is required"
- Install websockets: `pip install websockets`
- Make sure you're in the virtual environment
- Run: `pip install -r requirements.txt`

### "Firebase is required for authentication"
- Make sure `firebase-service-account.json` exists
- Install firebase-admin: `pip install firebase-admin`
- Check that Firebase modules can import

### Can't connect from browser
- Make sure server is running (check console output)
- Verify port 5557 is listening: `lsof -i :5557` (macOS/Linux) or `netstat -an | findstr 5557` (Windows)
- Check firewall settings
- For remote access, set `MUD_BIND_ADDRESS=0.0.0.0` environment variable

### Connection closes right after login (code 1001 "going away")
**Cause:** The **client** (browser/frontend) is closing the WebSocket. Common causes:
- **Full-page redirect or navigation after auth** – e.g. after `auth_success` the app does `window.location = '/game'` or a router push. The old page unloads and the browser closes the socket.
- **Component unmount** – the component that owns the WebSocket is torn down after login (e.g. "login" UI replaced by "game" UI in a way that destroys the socket).
- **Opening a second WebSocket** – e.g. login screen opens one socket, then game screen opens another; the first is closed or replaced.

**Fix (frontend):**
1. **Preferred:** Keep **one** WebSocket for the whole session. After `auth_success`, switch to the game UI **in place** (no navigation, no remount of the socket-owning component). Keep using the same socket for commands.
2. **Alternative:** If you must navigate after auth, have the **game** screen open a new WebSocket and send `{"type":"auth","token":"..."}` again. The backend accepts reconnects and will replace the old session. Ensure the game screen actually runs this connect+auth flow on load.

## Testing Checklist

- [ ] Server starts without errors
- [ ] See "WebSocket server started" message
- [ ] Can connect via web_client.html
- [ ] Can authenticate with email/password
- [ ] Can see game output in browser

---

**Need help?** Check the server output for error messages!
