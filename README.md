# Tyrant of the Dark Skies

A modern, web-based multiplayer text adventure (MUD) built with Python and WebSockets. Explore a persistent fantasy world, battle creatures, complete quests, and interact with other players in real-time.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![WebSocket](https://img.shields.io/badge/websocket-enabled-brightgreen.svg)

## ✨ Features

- **🌐 Web-Based**: Play directly in your browser - no installation required
- **👥 Multiplayer**: Real-time interaction with other players
- **⚔️ Combat System**: Turn-based combat with maneuvers and special abilities
- **📦 Inventory System**: Collect, use, and manage items
- **🗺️ Exploration**: Navigate through interconnected rooms and areas
- **💬 Real-time Chat**: Communicate with players in the same room
- **📊 Character Progression**: Deep leveling system with skills, attributes, and tiers
- **🎭 Character Creation**: Choose race, planet, starsign, and starting abilities
- **🏪 Shop System**: Buy, sell, and repair items with NPCs
- **⏰ Time System**: Dynamic world time affecting NPCs and shops
- **🔥 Firebase Integration**: Secure authentication and cloud data storage
- **📝 Community Contributions**: Easy-to-contribute JSON-based content system

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Firebase project (for authentication and data storage)
- `firebase-service-account.json` file (see [Firebase Setup](#firebase-setup))

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/tyrantofthedarkskies.git
   cd tyrantofthedarkskies
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up Firebase:**
   - Follow the [Firebase Setup Guide](FIREBASE_AUTH_SETUP.md)
   - Place your `firebase-service-account.json` in the project root
   - Set environment variable: `export FIREBASE_WEB_API_KEY=your_key_here`

5. **Start the server:**
   ```bash
   python3 mud_server.py
   ```

6. **Connect:**
   - Open `web_client.html` in your browser
   - Enter WebSocket URL: `ws://localhost:5557`
   - Click "Connect" and start playing!

For detailed setup instructions, see [QUICK_START.md](QUICK_START.md).

## 🎮 Gameplay

### Character Creation

1. **Choose Your Race**: Affects starting attributes and cultural traits
2. **Choose Your Planet**: Grants cosmic bonuses and a starting maneuver
3. **Choose Your Starsign**: Provides fate-based abilities
4. **Select Starting Maneuvers**: Pick from race, planet, and one additional maneuver
5. **Begin Your Adventure**: Start in New Cove and explore the world!

### Core Commands

- `look` or `l` - Look around the current room
- `move <direction>` or `go <direction>` - Move north/south/east/west
- `stats` - View your character sheet
- `skills` - View all your skills
- `inventory` or `i` - Check your inventory
- `attack <target>` - Attack a hostile creature
- `talk <npc> <keyword>` - Talk to NPCs
- `help` - Show all available commands

See the in-game `help` command for a complete list.

## 📁 Project Structure

```
tyrantofthedarkskies/
├── mud_server.py          # Main server file (5,108 lines - see STRUCTURE.md for refactoring plan)
├── player.py              # Player class
├── combat_system.py       # Combat mechanics
├── time_system.py         # World time system
├── character_creation.py  # Character creation flow
├── quest_system.py        # Quest management
├── web_client.html        # Web-based client
│
├── utils/                 # Utility modules
│   ├── formatter.py      # Text formatting utilities
│   └── logger.py         # Security logging
│
├── firebase/              # Firebase integration
│   ├── auth.py           # Authentication
│   ├── data_layer.py     # Data persistence
│   └── client.py         # Firebase client
│
├── contributions/         # Community-contributed content
│   ├── rooms/            # Room definitions
│   ├── npcs/             # NPC definitions
│   ├── items/            # Item definitions (weapons/armor/objects)
│   ├── races/            # Race definitions
│   ├── planets/          # Planet definitions
│   ├── starsigns/        # Starsign definitions
│   ├── maneuvers/        # Maneuver definitions
│   ├── weapons/          # Weapon templates
│   └── weapon_modifiers/ # Weapon modifiers
│
├── docs/                 # Game design documentation
├── scripts/              # Utility scripts (migration, data splitting)
└── mud_data/             # Runtime data (gitignored)
```

**Note**: See [STRUCTURE.md](STRUCTURE.md) for detailed analysis and refactoring recommendations.

## 🔧 Configuration

### Environment Variables

- `MUD_WEBSOCKET_PORT` - WebSocket server port (default: 5557)
- `MUD_BIND_ADDRESS` - Bind address (default: localhost, use 0.0.0.0 for public)
- `FIREBASE_WEB_API_KEY` - Firebase Web API key (required)

### Firebase Setup

1. Create a Firebase project at [Firebase Console](https://console.firebase.google.com)
2. Enable Authentication (Email/Password)
3. Create a service account and download `firebase-service-account.json`
4. Get your Web API Key from Project Settings
5. See [FIREBASE_AUTH_SETUP.md](FIREBASE_AUTH_SETUP.md) for detailed instructions

## 🚢 Deployment

### Free Deployment Options

- **Fly.io** (Recommended): Free tier with WebSocket support
- **Render**: Free tier (spins down after inactivity)
- **Railway**: Free tier with $5 credit/month

See [FREE_DEPLOYMENT.md](FREE_DEPLOYMENT.md) for zero-cost deployment options.

### Paid Deployment Options

- **Railway**: $5/month for always-on
- **Render**: $7/month for always-on
- **VPS**: $5-12/month (DigitalOcean, Linode, etc.)

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed deployment instructions.

## 🤝 Contributing

We welcome contributions! The game uses a JSON-based contribution system:

1. **Add Content**: Create JSON files in `contributions/` subdirectories
2. **Follow Format**: See README.md files in each contribution folder
3. **Submit PR**: Open a pull request with your additions

### Contribution Areas

- **Rooms**: Add new areas to explore
- **NPCs**: Create new characters and creatures
- **Items**: Design weapons, armor, and objects
- **Maneuvers**: Add new combat abilities
- **Races/Planets/Starsigns**: Expand character options

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## 📚 Documentation

- [Quick Start Guide](QUICK_START.md) - Get up and running quickly
- [WebSocket Setup](WEBSOCKET_SETUP.md) - Web client configuration
- [Firebase Setup](FIREBASE_AUTH_SETUP.md) - Authentication setup
- [Deployment Guide](DEPLOYMENT_GUIDE.md) - Deploy to production
- [Free Deployment](FREE_DEPLOYMENT.md) - Zero-cost hosting options
- [Game Design Docs](docs/) - Core game mechanics and systems

## 🛠️ Development

### Running Tests

```bash
# Run server in development mode
python3 mud_server.py
```

### Adding New Features

- Game logic: `mud_server.py`
- Player class: `player.py`
- Combat system: `combat_system.py`
- Time system: `time_system.py`
- Quest system: `quest_system.py`

### Room Editor

Use the built-in room editor:

```bash
python3 room_editor.py interactive
```

Or use in-game admin commands (if you're an admin).

## 📝 License

This project is open source. See [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with Python and WebSockets
- Uses Firebase for authentication and data storage
- Inspired by classic MUDs and text adventures

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/tyrantofthedarkskies/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/tyrantofthedarkskies/discussions)

## 🎯 Roadmap

- [ ] Mobile-responsive web client
- [ ] More quests and storylines
- [ ] Additional races and planets
- [ ] Guild system
- [ ] Trading system
- [ ] Player housing

---

**Ready to play?** Follow the [Quick Start Guide](QUICK_START.md) and begin your adventure!
