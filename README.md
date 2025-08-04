# P2P BitTorrent-like File Sharing System

A Python-based peer-to-peer file sharing application inspired by the BitTorrent protocol, implementing a complete MVP with tracker server, web frontend, and desktop client.

## Features ✨

### MVP Implementation (Completed)
- ✅ **File Upload & Torrent Generation**: Upload files and automatically generate .torrent-like metadata
- ✅ **File Chunking & Hashing**: Automatic file splitting into pieces with SHA-1 integrity verification
- ✅ **Tracker Server**: FastAPI-based tracker for peer coordination and torrent management
- ✅ **Web Frontend**: React-based web interface for managing torrents
- ✅ **Desktop Client**: Python Tkinter GUI application
- ✅ **P2P Communication**: TCP-based peer-to-peer protocol for file transfer
- ✅ **Peer Management**: Automatic peer discovery and connection management
- ✅ **Progress Tracking**: Real-time download progress and statistics
- ✅ **Seeder/Leecher Support**: Automatic transition to seeder state upon completion

### Architecture
- **Tracker Server**: FastAPI with SQLAlchemy (SQLite database)
- **Web Frontend**: React + Vite with TailwindCSS
- **Desktop Client**: Python Tkinter GUI
- **P2P Protocol**: Custom TCP-based protocol with handshake and piece exchange
- **Client**: Command-line interface for creating and downloading torrents
- **Database**: SQLite for storing torrents, peers, and user information

## Quick Start 🚀

### 1. Installation

```powershell
# Install Python dependencies
pip install -r requirements.txt
```

### 2. Start the Tracker Server

```powershell
# Start the tracker server
uvicorn app.main:app --reload

# Server will be available at:
# - API: http://127.0.0.1:8000
# - Documentation: http://127.0.0.1:8000/docs
```

### 3. Choose Your Interface

#### Option A: Web Frontend (React)
```powershell
# Run the launcher (installs dependencies automatically)
start_frontend.bat

# Or manually:
cd frontend
npm install
npm run dev

# Access at: http://localhost:3000
```

#### Option B: Desktop Client (Python GUI)
```powershell
# Run the launcher (installs dependencies automatically)
start_desktop_client.bat

# Or manually:
pip install -r desktop_client/requirements.txt
python desktop_client/main.py
```

#### Option C: Command Line Interface
```powershell
# Create a torrent for a file
python client.py create "path\to\your\file.txt"

# Download using a torrent file
python client.py download "file.txt.torrent"
```

## User Interfaces 🖥️

### 1. Web Frontend (React + Vite)
- **Modern React Interface**: Built with Vite for fast development
- **Responsive Design**: TailwindCSS for mobile-friendly UI
- **File Upload**: Drag-and-drop file uploads with progress bars
- **Torrent Management**: View, filter, and manage torrents
- **Peer Monitoring**: Real-time peer status and statistics
- **Live Updates**: Auto-refreshing data every 10 seconds

**Features:**
- 📤 Upload files and create torrents
- 📁 Browse available torrents with details
- 👥 View active peers for each torrent
- 📊 Tracker statistics and system status
- 🔄 Real-time updates

### 2. Desktop Client (Python Tkinter)
- **Native GUI**: Cross-platform desktop application
- **Tabbed Interface**: Organized workflow with multiple tabs
- **File Browser**: Native file dialogs for easy file selection
- **Download Manager**: Track multiple downloads simultaneously
- **Settings Panel**: Configure tracker URL and download directory

**Features:**
- 📤 Create torrents from local files
- 📥 Download torrents with progress tracking
- 📁 Browse and manage available torrents
- 📊 System status and connection monitoring
- ⚙️ Settings configuration

### 3. Command Line Interface
- **Script-based**: Simple commands for automation
- **Headless Operation**: Perfect for servers or scripts
- **Direct Integration**: Uses the same backend modules

## Project Structure 📁

```
├── app/                     # FastAPI Backend
│   ├── main.py             # Application entry point
│   ├── api/                # API endpoints
│   ├── models/             # Database models
│   ├── schemas/            # Pydantic schemas
│   ├── services/           # Business logic
│   └── utils/              # P2P utilities
├── frontend/               # React Web Frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── services/       # API integration
│   │   └── App.jsx         # Main application
│   ├── package.json        # Dependencies
│   └── vite.config.js      # Vite configuration
├── desktop_client/         # Python Desktop Client
│   ├── main.py             # Tkinter GUI application
│   └── requirements.txt    # Desktop dependencies
├── client.py               # CLI client
├── demo.py                 # Demo script
├── requirements.txt        # Python dependencies
├── start_frontend.bat      # Frontend launcher
└── start_desktop_client.bat # Desktop launcher
```

## API Endpoints 📡

### Torrent Management
- `POST /api/tracker/upload` - Upload file and create torrent
- `GET /api/tracker/torrents` - List all torrents
- `GET /api/tracker/torrents/{info_hash}` - Get specific torrent

### Peer Tracking
- `GET/POST /api/tracker/announce` - Peer announce (BitTorrent protocol)
- `GET /api/tracker/peers/{info_hash}` - Get peers for torrent

### Statistics
- `GET /api/tracker/stats` - Tracker statistics
- `GET /health` - Health check

## Usage Examples 💡

### Example 1: Web Interface Workflow
1. Start tracker: `uvicorn app.main:app --reload`
2. Start web frontend: `start_frontend.bat`
3. Open browser to `http://localhost:3000`
4. Upload file via drag-and-drop
5. Share generated torrent with others

### Example 2: Desktop Client Workflow
1. Start tracker: `uvicorn app.main:app --reload`
2. Start desktop client: `start_desktop_client.bat`
3. Use "Upload File" tab to create torrents
4. Use "Download" tab to download torrents
5. Monitor progress in "Torrents" tab

### Example 3: Multi-User Scenario
```powershell
# User 1 (Web): Upload file
# 1. Open http://localhost:3000
# 2. Upload "document.pdf"
# 3. Share the generated .torrent file

# User 2 (Desktop): Download file
# 1. Run desktop client
# 2. Select the .torrent file
# 3. Start download

# User 3 (CLI): Download file
python client.py download "document.pdf.torrent"
```

## Technical Details 🔧

### Frontend Technologies
- **React 18**: Modern React with hooks
- **Vite**: Fast build tool and dev server
- **TailwindCSS**: Utility-first CSS framework
- **Axios**: HTTP client for API calls
- **Lucide React**: Modern icon library
- **React Dropzone**: File upload component

### Desktop Client Features
- **Tkinter**: Built-in Python GUI framework
- **Threaded Operations**: Non-blocking file operations
- **Auto-refresh**: Live data updates
- **Cross-platform**: Works on Windows, Mac, Linux

### BitTorrent Protocol Implementation
- **Piece Size**: 256KB (configurable)
- **Hash Algorithm**: SHA-1 for file and piece integrity
- **Peer ID**: 20-character unique identifier
- **Info Hash**: 40-character hex string (SHA-1)

## Development & Testing 🧪

### Start All Components
```powershell
# Terminal 1: Tracker Server
uvicorn app.main:app --reload

# Terminal 2: Web Frontend
start_frontend.bat

# Terminal 3: Desktop Client
start_desktop_client.bat
```

### Test Different Scenarios
1. **File Upload**: Test with various file sizes and types
2. **Multi-peer Downloads**: Simulate multiple clients
3. **Network Issues**: Test connection handling
4. **Concurrent Operations**: Multiple uploads/downloads

## Troubleshooting 🔧

### Common Issues

**Frontend not starting:**
```powershell
cd frontend
npm install
npm run dev
```

**Desktop client crashes:**
```powershell
pip install -r desktop_client/requirements.txt
python desktop_client/main.py
```

**API connection issues:**
- Ensure tracker server is running on port 8000
- Check firewall settings
- Verify network connectivity

**File upload failures:**
- Check file permissions
- Ensure sufficient disk space
- Verify file path exists

## Screenshots 📸

### Web Frontend
- **Upload Page**: Drag-and-drop file upload with progress
- **Torrents Page**: Grid view of available torrents
- **Peers Page**: Real-time peer monitoring
- **Statistics Page**: System overview and metrics

### Desktop Client
- **Upload Tab**: File selection and torrent creation
- **Download Tab**: Torrent selection and download management
- **Torrents Tab**: List view with detailed information
- **Status Tab**: Connection status and settings

## Future Enhancements 🚀

### Planned Features
- **Mobile App**: React Native mobile client
- **Electron App**: Desktop web app wrapper
- **DHT Support**: Distributed hash table implementation
- **Encryption**: Secure peer-to-peer communication
- **Resume Downloads**: Pause and resume functionality
- **Bandwidth Control**: Upload/download rate limiting
- **User Authentication**: User accounts and permissions

## Contributing 🤝

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License 📝

This project is for educational purposes. Implement proper security and error handling before production use.

## API Endpoints 📡

### Torrent Management
- `POST /api/tracker/upload` - Upload file and create torrent
- `GET /api/tracker/torrents` - List all torrents
- `GET /api/tracker/torrents/{info_hash}` - Get specific torrent

### Peer Tracking
- `GET/POST /api/tracker/announce` - Peer announce (BitTorrent protocol)
- `GET /api/tracker/peers/{info_hash}` - Get peers for torrent

### Statistics
- `GET /api/tracker/stats` - Tracker statistics
- `GET /health` - Health check

## Project Structure 📁

```
app/
├── main.py              # FastAPI application entry point
├── core/
│   └── config.py        # Configuration settings
├── db/
│   ├── base.py         # SQLAlchemy base
│   └── session.py      # Database session management
├── models/
│   ├── torrent.py      # Torrent database model
│   ├── peer.py         # Peer database model
│   └── user.py         # User database model
├── schemas/
│   ├── torrent.py      # Torrent Pydantic schemas
│   ├── peer.py         # Peer Pydantic schemas
│   └── user.py         # User Pydantic schemas
├── api/
│   └── tracker.py      # Tracker API endpoints
├── services/
│   └── tracker_service.py  # Business logic
└── utils/
    ├── torrent_generator.py  # Torrent creation utilities
    ├── file_manager.py       # File handling utilities
    ├── piece_manager.py      # Piece tracking utilities
    ├── p2p_protocol.py       # P2P communication protocol
    ├── download_manager.py   # Download coordination
    └── bittorrent.py         # BitTorrent utilities

client.py                # Command-line P2P client
requirements.txt         # Python dependencies
```

## Technical Details 🔧

### BitTorrent Protocol Implementation
- **Piece Size**: 256KB (configurable)
- **Hash Algorithm**: SHA-1 for file and piece integrity
- **Peer ID**: 20-character unique identifier
- **Info Hash**: 40-character hex string (SHA-1)

### Database Schema
- **Torrents**: Store metadata, piece information, and statistics
- **Peers**: Track active connections and transfer statistics  
- **Users**: User management with peer ID association

### P2P Communication
- **Handshake Protocol**: Info hash verification and peer identification
- **Message Types**: Choke, unchoke, interested, have, request, piece
- **Connection Management**: Automatic peer discovery and connection handling

## Usage Examples 💡

### Example 1: Share a Document
```powershell
# 1. Start tracker
uvicorn app.main:app --reload

# 2. Create torrent for document
python client.py create "document.pdf"

# 3. Share the generated .torrent file
# Others can download using:
python client.py download "document.pdf.torrent"
```

### Example 2: Multiple Peers
```powershell
# Terminal 1 (Seeder)
python client.py create "video.mp4"

# Terminal 2 (Leecher 1) 
python client.py download "video.mp4.torrent"

# Terminal 3 (Leecher 2)
python client.py download "video.mp4.torrent"

# The video will be downloaded from the seeder and shared between leechers
```

## Development & Testing 🧪

### Run the Tracker
```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Test API Endpoints
Visit `http://localhost:8000/docs` for interactive API documentation.

### Database
SQLite database is created automatically at `app/db/p2p.db`.

## Future Enhancements 🚀

### Planned Features (Beyond MVP)
- **DHT (Distributed Hash Table)**: Reduce dependency on tracker
- **Encryption**: Secure peer-to-peer communication  
- **Web Interface**: Browser-based client interface
- **Multi-file Torrents**: Support for directory torrents
- **Peer Reputation System**: Quality of service tracking
- **Magnet Links**: Simplified torrent sharing
- **Resume Support**: Pause and resume downloads

## Contributing 🤝

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License 📝

This project is for educational purposes. Implement proper security and error handling before production use.

## Troubleshooting 🔧

### Common Issues

**Tracker not starting:**
```powershell
# Ensure FastAPI is installed
pip install "fastapi[standard]"
```

**Port conflicts:**
```powershell
# Use different port
uvicorn app.main:app --port 8001
```

**Peer connection issues:**
- Ensure tracker is running
- Check firewall settings
- Verify correct tracker URL in client

**Database issues:**
- Delete `app/db/p2p.db` to reset database
- Restart tracker to recreate tables
