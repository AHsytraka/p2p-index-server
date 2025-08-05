#!/usr/bin/env python3
"""
P2P BitTorrent Desktop Client
A GUI application for creating and downloading torrents
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import time
import os
import sys
import json
import requests
from pathlib import Path

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.torrent_generator import TorrentGenerator
from app.utils.download_manager import DownloadManager
from app.utils.bittorrent import BitTorrentUtils

class P2PDesktopClient:
    def __init__(self, root):
        self.root = root
        self.root.title("P2P BitTorrent Client")
        self.root.geometry("800x600")
        
        # Configuration
        self.tracker_url = "http://192.168.175.242:8000"
        self.download_directory = os.path.join(os.getcwd(), "downloads")
        os.makedirs(self.download_directory, exist_ok=True)
        
        # Variables
        self.torrents = []
        self.downloads = {}  # track active downloads
        
        self.setup_ui()
        self.refresh_torrents()
        
        # Auto-refresh every 10 seconds
        self.auto_refresh()
    
    def setup_ui(self):
        """Setup the user interface"""
        # Main notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_upload_tab()
        self.create_download_tab()
        self.create_torrents_tab()
        self.create_status_tab()
        
        # Status bar
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def create_upload_tab(self):
        """Create the file upload tab"""
        upload_frame = ttk.Frame(self.notebook)
        self.notebook.add(upload_frame, text="📤 Upload File")
        
        # Title
        title = ttk.Label(upload_frame, text="Create Torrent", font=("Arial", 16, "bold"))
        title.pack(pady=10)
        
        # File selection
        file_frame = ttk.LabelFrame(upload_frame, text="Select File", padding=10)
        file_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.selected_file_var = tk.StringVar()
        file_entry = ttk.Entry(file_frame, textvariable=self.selected_file_var, state="readonly")
        file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        browse_btn = ttk.Button(file_frame, text="Browse", command=self.browse_file)
        browse_btn.pack(side=tk.RIGHT)
        
        # Upload button
        upload_btn = ttk.Button(upload_frame, text="Create Torrent", command=self.create_torrent)
        upload_btn.pack(pady=20)
        
        # Progress
        self.upload_progress = ttk.Progressbar(upload_frame, mode='indeterminate')
        self.upload_progress.pack(fill=tk.X, padx=20, pady=10)
        
        # Results
        self.upload_result = tk.Text(upload_frame, height=10, wrap=tk.WORD)
        self.upload_result.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
    
    def create_download_tab(self):
        """Create the download tab"""
        download_frame = ttk.Frame(self.notebook)
        self.notebook.add(download_frame, text="📥 Download")
        
        # Title
        title = ttk.Label(download_frame, text="Download Torrent", font=("Arial", 16, "bold"))
        title.pack(pady=10)
        
        # Torrent file selection
        torrent_frame = ttk.LabelFrame(download_frame, text="Select Torrent File", padding=10)
        torrent_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.selected_torrent_var = tk.StringVar()
        torrent_entry = ttk.Entry(torrent_frame, textvariable=self.selected_torrent_var, state="readonly")
        torrent_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        browse_torrent_btn = ttk.Button(torrent_frame, text="Browse", command=self.browse_torrent)
        browse_torrent_btn.pack(side=tk.RIGHT)
        
        # Download button
        download_btn = ttk.Button(download_frame, text="Start Download", command=self.start_download)
        download_btn.pack(pady=20)
        
        # Downloads list
        downloads_frame = ttk.LabelFrame(download_frame, text="Active Downloads", padding=10)
        downloads_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Control buttons frame
        controls_frame = ttk.Frame(downloads_frame)
        controls_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.pause_btn = ttk.Button(controls_frame, text="⏸️ Pause", command=self.pause_download)
        self.pause_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.resume_btn = ttk.Button(controls_frame, text="▶️ Resume", command=self.resume_download)
        self.resume_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_btn = ttk.Button(controls_frame, text="⏹️ Stop", command=self.stop_download)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Initially disable control buttons
        self.pause_btn.config(state="disabled")
        self.resume_btn.config(state="disabled")
        self.stop_btn.config(state="disabled")
        
        # Downloads treeview
        columns = ("File", "Progress", "Speed", "Status")
        self.downloads_tree = ttk.Treeview(downloads_frame, columns=columns, show="headings", height=8)
        
        for col in columns:
            self.downloads_tree.heading(col, text=col)
            self.downloads_tree.column(col, width=150)
        
        downloads_scrollbar = ttk.Scrollbar(downloads_frame, orient=tk.VERTICAL, command=self.downloads_tree.yview)
        self.downloads_tree.configure(yscrollcommand=downloads_scrollbar.set)
        
        self.downloads_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        downloads_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection event for downloads
        self.downloads_tree.bind('<<TreeviewSelect>>', self.on_download_select)
    
    def create_torrents_tab(self):
        """Create the torrents list tab"""
        torrents_frame = ttk.Frame(self.notebook)
        self.notebook.add(torrents_frame, text="📁 Torrents")
        
        # Title and refresh
        header_frame = ttk.Frame(torrents_frame)
        header_frame.pack(fill=tk.X, padx=20, pady=10)
        
        title = ttk.Label(header_frame, text="Available Torrents", font=("Arial", 16, "bold"))
        title.pack(side=tk.LEFT)
        
        refresh_btn = ttk.Button(header_frame, text="🔄 Refresh", command=self.refresh_torrents)
        refresh_btn.pack(side=tk.RIGHT)
        
        # Torrents treeview
        columns = ("Name", "Size", "Seeders", "Leechers", "Created")
        self.torrents_tree = ttk.Treeview(torrents_frame, columns=columns, show="headings")
        
        for col in columns:
            self.torrents_tree.heading(col, text=col)
            self.torrents_tree.column(col, width=120)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(torrents_frame, orient=tk.VERTICAL, command=self.torrents_tree.yview)
        h_scrollbar = ttk.Scrollbar(torrents_frame, orient=tk.HORIZONTAL, command=self.torrents_tree.xview)
        self.torrents_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack treeview and scrollbars
        self.torrents_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(20, 0), pady=10)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X, padx=20)
        
        # Torrent details
        details_frame = ttk.LabelFrame(torrents_frame, text="Torrent Details", padding=10)
        details_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.torrent_details = tk.Text(details_frame, height=6, wrap=tk.WORD)
        self.torrent_details.pack(fill=tk.X)
        
        # Bind selection event
        self.torrents_tree.bind('<<TreeviewSelect>>', self.on_torrent_select)
    
    def create_status_tab(self):
        """Create the status/statistics tab"""
        status_frame = ttk.Frame(self.notebook)
        self.notebook.add(status_frame, text="📊 Status")
        
        # Title
        title = ttk.Label(status_frame, text="System Status", font=("Arial", 16, "bold"))
        title.pack(pady=10)
        
        # Stats frame
        stats_frame = ttk.LabelFrame(status_frame, text="Tracker Statistics", padding=10)
        stats_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.stats_text = tk.Text(stats_frame, height=8, wrap=tk.WORD)
        self.stats_text.pack(fill=tk.X)
        
        # Connection status
        conn_frame = ttk.LabelFrame(status_frame, text="Connection Status", padding=10)
        conn_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.connection_status = tk.Text(conn_frame, height=4, wrap=tk.WORD)
        self.connection_status.pack(fill=tk.X)
        
        # Settings
        settings_frame = ttk.LabelFrame(status_frame, text="Settings", padding=10)
        settings_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Tracker URL
        ttk.Label(settings_frame, text="Tracker URL:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.tracker_url_var = tk.StringVar(value=self.tracker_url)
        tracker_entry = ttk.Entry(settings_frame, textvariable=self.tracker_url_var, width=40)
        tracker_entry.grid(row=0, column=1, sticky=tk.W)
        
        # Download directory
        ttk.Label(settings_frame, text="Download Dir:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        self.download_dir_var = tk.StringVar(value=self.download_directory)
        dir_entry = ttk.Entry(settings_frame, textvariable=self.download_dir_var, width=30)
        dir_entry.grid(row=1, column=1, sticky=tk.W, pady=(10, 0))
        
        browse_dir_btn = ttk.Button(settings_frame, text="Browse", command=self.browse_download_dir)
        browse_dir_btn.grid(row=1, column=2, padx=(10, 0), pady=(10, 0))
        
        self.update_status()
    
    def browse_file(self):
        """Browse for file to upload"""
        filename = filedialog.askopenfilename(
            title="Select file to share",
            filetypes=[("All files", "*.*")]
        )
        if filename:
            self.selected_file_var.set(filename)
    
    def browse_torrent(self):
        """Browse for torrent file to download"""
        filename = filedialog.askopenfilename(
            title="Select torrent file",
            filetypes=[("Torrent files", "*.torrent"), ("All files", "*.*")]
        )
        if filename:
            self.selected_torrent_var.set(filename)
    
    def browse_download_dir(self):
        """Browse for download directory"""
        directory = filedialog.askdirectory(title="Select download directory")
        if directory:
            self.download_dir_var.set(directory)
            self.download_directory = directory
    
    def create_torrent(self):
        """Create torrent from selected file"""
        file_path = self.selected_file_var.get()
        if not file_path:
            messagebox.showerror("Error", "Please select a file first")
            return
        
        if not os.path.exists(file_path):
            messagebox.showerror("Error", "Selected file does not exist")
            return
        
        def upload_thread():
            try:
                self.root.after(0, lambda: self.upload_progress.start())
                self.root.after(0, lambda: self.set_status("Creating torrent..."))
                
                # Generate torrent metadata
                tracker_announce_url = f"{self.tracker_url}/api/tracker/announce"
                torrent_data = TorrentGenerator.create_torrent_metadata(file_path, tracker_announce_url)
                
                # Save torrent file with proper naming
                file_name = os.path.basename(file_path)
                base_name = os.path.splitext(file_name)[0]  # Remove file extension
                torrent_filename = f"{base_name}.torrent"
                
                # Create torrents directory if it doesn't exist
                torrents_dir = "torrents"
                os.makedirs(torrents_dir, exist_ok=True)
                torrent_path = os.path.join(torrents_dir, torrent_filename)
                
                TorrentGenerator.save_torrent_file(torrent_data, torrent_path)
                
                # Upload to tracker
                self.root.after(0, lambda: self.set_status("Uploading to tracker..."))
                
                with open(file_path, 'rb') as f:
                    files = {'file': (os.path.basename(file_path), f, 'application/octet-stream')}
                    response = requests.post(f"{self.tracker_url}/api/tracker/upload", files=files, timeout=30)
                
                if response.status_code == 200:
                    result_data = response.json()
                    result_text = f"✅ Torrent created successfully!\n\n"
                    result_text += f"File: {result_data['name']}\n"
                    result_text += f"Info Hash: {result_data['info_hash']}\n"
                    result_text += f"File Size: {BitTorrentUtils.format_bytes(result_data['file_size'])}\n"
                    result_text += f"Pieces: {result_data['num_pieces']}\n"
                    result_text += f"Torrent File: {torrent_path}\n\n"
                    result_text += "Your file is now available for download!"
                    
                    self.root.after(0, lambda: self.upload_result.delete(1.0, tk.END))
                    self.root.after(0, lambda: self.upload_result.insert(tk.END, result_text))
                    self.root.after(0, lambda: self.set_status("Torrent created successfully"))
                    self.root.after(0, self.refresh_torrents)
                else:
                    error_msg = f"❌ Upload failed: {response.text}"
                    self.root.after(0, lambda: self.upload_result.delete(1.0, tk.END))
                    self.root.after(0, lambda: self.upload_result.insert(tk.END, error_msg))
                    self.root.after(0, lambda: self.set_status("Upload failed"))
                
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                status_msg = f"Error: {str(e)}"
                self.root.after(0, lambda: self.upload_result.delete(1.0, tk.END))
                self.root.after(0, lambda: self.upload_result.insert(tk.END, error_msg))
                self.root.after(0, lambda: self.set_status(status_msg))
            finally:
                self.root.after(0, lambda: self.upload_progress.stop())
        
        threading.Thread(target=upload_thread, daemon=True).start()
    
    def start_download(self):
        """Start downloading from selected torrent"""
        torrent_path = self.selected_torrent_var.get()
        if not torrent_path:
            messagebox.showerror("Error", "Please select a torrent file first")
            return
        
        if not os.path.exists(torrent_path):
            messagebox.showerror("Error", "Selected torrent file does not exist")
            return
        
        try:
            # Load torrent data
            torrent_data = TorrentGenerator.load_torrent_file(torrent_path)
            torrent_name = torrent_data['info']['name']
            info_hash = torrent_data['info_hash']
            
            # Check if already downloading
            for download_id, download_info in self.downloads.items():
                if download_info['torrent_data']['info_hash'] == info_hash:
                    messagebox.showwarning("Already Downloading", f"{torrent_name} is already being downloaded")
                    return
            
            # Create download directory
            download_path = os.path.join(self.download_directory, torrent_name)
            
            # Add to downloads list
            download_id = len(self.downloads)
            self.downloads[download_id] = {
                'name': torrent_name,
                'torrent_data': torrent_data,
                'download_path': download_path,
                'status': 'Starting...',
                'progress': 0,
                'speed': 0,
                'download_manager': None
            }
            
            # Update downloads tree
            self.downloads_tree.insert('', tk.END, iid=download_id, values=(
                torrent_name, "0%", "0 KB/s", "Starting..."
            ))
            
            # Start actual download in background thread
            def download_thread():
                try:
                    self.root.after(0, lambda: self.set_status(f"Getting peers for {torrent_name}..."))
                    
                    # Get peers from tracker
                    peers = self._get_peers_from_tracker(info_hash)
                    if not peers:
                        self.downloads[download_id]['status'] = 'No peers found'
                        self.root.after(0, lambda: self.update_download_status(download_id))
                        self.root.after(0, lambda: self.set_status(f"No peers found for {torrent_name}"))
                        return
                    
                    self.root.after(0, lambda: self.set_status(f"Found {len(peers)} peers, starting download..."))
                    
                    # Create download manager
                    download_manager = DownloadManager(torrent_data, download_path)
                    self.downloads[download_id]['download_manager'] = download_manager
                    
                    # Add peers (limit to first 3 for stability)
                    connected_peers = 0
                    unique_peers = {}
                    
                    # Deduplicate peers by IP:port to avoid multiple connections to same seeder
                    for peer in peers:
                        peer_key = f"{peer['ip_address']}:{peer['port']}"
                        if peer_key not in unique_peers:
                            unique_peers[peer_key] = peer
                    
                    # Connect to unique peers only
                    for peer_key, peer in list(unique_peers.items())[:3]:  # Limit to 3 peers
                        if download_manager.add_peer(peer['peer_id'], peer['ip_address'], peer['port']):
                            connected_peers += 1
                    
                    if connected_peers == 0:
                        self.downloads[download_id]['status'] = 'Failed to connect to peers'
                        self.root.after(0, lambda: self.update_download_status(download_id))
                        self.root.after(0, lambda: self.set_status(f"Failed to connect to peers for {torrent_name}"))
                        return
                    
                    # Start download
                    download_manager.start_download()
                    self.downloads[download_id]['status'] = 'Downloading'
                    
                    self.root.after(0, lambda: self.set_status(f"Download started: {torrent_name}"))
                    
                    # Monitor progress
                    self._monitor_download(download_id)
                    
                except Exception as e:
                    error_status = f'Error: {str(e)}'
                    download_error_msg = f"Download error: {str(e)}"
                    self.downloads[download_id]['status'] = error_status
                    self.root.after(0, lambda: self.update_download_status(download_id))
                    self.root.after(0, lambda: self.set_status(download_error_msg))
            
            threading.Thread(target=download_thread, daemon=True).start()
            
            messagebox.showinfo("Download Started", f"Download started for {torrent_name}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start download: {str(e)}")
    
    def _get_peers_from_tracker(self, info_hash: str) -> list:
        """Get peer list from tracker for a specific torrent"""
        try:
            # First try to get peers directly
            response = requests.get(f"{self.tracker_url}/api/tracker/peers/{info_hash}", timeout=10)
            if response.status_code == 200:
                return response.json()
            
            # If no peers endpoint, try announce
            peer_id = BitTorrentUtils.generate_peer_id()
            announce_params = {
                'info_hash': info_hash,
                'peer_id': peer_id,
                'port': 6881,
                'uploaded': 0,
                'downloaded': 0,
                'left': 1000000,
                'event': 'started'
            }
            
            response = requests.get(f"{self.tracker_url}/api/tracker/announce", 
                                  params=announce_params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get('peers', [])
            
            return []
            
        except Exception as e:
            print(f"Error getting peers: {e}")
            return []
    
    def _monitor_download(self, download_id: int):
        """Monitor download progress and update UI"""
        def monitor_thread():
            download_info = self.downloads[download_id]
            download_manager = download_info['download_manager']
            
            while download_info['status'] in ['Downloading', 'Paused']:
                try:
                    progress = download_manager.get_progress()
                    current_status = download_manager.get_download_status()
                    
                    # Update download info
                    download_info['progress'] = progress['completion_percentage']
                    download_info['speed'] = progress['download_speed']
                    download_info['status'] = current_status
                    
                    # Update UI
                    self.root.after(0, lambda: self.update_download_status(download_id))
                    
                    # Check if complete
                    if progress['completion_percentage'] >= 100:
                        download_info['status'] = 'Completed'
                        self.root.after(0, lambda: self.update_download_status(download_id))
                        self.root.after(0, lambda: self.set_status(f"Download completed: {download_info['name']}"))
                        break
                    
                    # Check if stopped
                    if current_status == 'Stopped':
                        break
                    
                    time.sleep(1)  # Update every second
                    
                except Exception as e:
                    download_info['status'] = f'Error: {str(e)}'
                    self.root.after(0, lambda: self.update_download_status(download_id))
                    break
        
        threading.Thread(target=monitor_thread, daemon=True).start()
    
    def update_download_status(self, download_id: int):
        """Update download status in the UI"""
        if download_id not in self.downloads:
            return
        
        download_info = self.downloads[download_id]
        
        # Update treeview
        item_exists = self.downloads_tree.exists(download_id)
        if item_exists:
            progress_text = f"{download_info['progress']:.1f}%"
            speed_text = BitTorrentUtils.format_speed(download_info['speed'])
            
            self.downloads_tree.item(download_id, values=(
                download_info['name'],
                progress_text,
                speed_text,
                download_info['status']
            ))
    
    def refresh_torrents(self):
        """Refresh the torrents list from tracker"""
        def fetch_thread():
            try:
                response = requests.get(f"{self.tracker_url}/api/tracker/torrents", timeout=10)
                if response.status_code == 200:
                    self.torrents = response.json()
                    self.root.after(0, self.update_torrents_tree)
                else:
                    self.root.after(0, lambda: self.set_status("Failed to fetch torrents"))
            except Exception as e:
                error_msg = f"Connection error: {str(e)}"
                self.root.after(0, lambda: self.set_status(error_msg))
        
        threading.Thread(target=fetch_thread, daemon=True).start()
    
    def update_torrents_tree(self):
        """Update the torrents treeview"""
        # Clear existing items
        for item in self.torrents_tree.get_children():
            self.torrents_tree.delete(item)
        
        # Add torrents
        for torrent in self.torrents:
            file_size = BitTorrentUtils.format_bytes(torrent['file_size'])
            created_date = torrent['created_at'][:10]  # Just the date part
            
            self.torrents_tree.insert('', tk.END, values=(
                torrent['name'],
                file_size,
                torrent['seeders'],
                torrent['leechers'],
                created_date
            ), tags=(torrent['id'],))
    
    def on_torrent_select(self, event):
        """Handle torrent selection"""
        selection = self.torrents_tree.selection()
        if not selection:
            return
        
        item = self.torrents_tree.item(selection[0])
        torrent_id = int(item['tags'][0])
        
        # Find torrent by ID
        selected_torrent = None
        for torrent in self.torrents:
            if torrent['id'] == torrent_id:
                selected_torrent = torrent
                break
        
        if selected_torrent:
            details_text = f"Name: {selected_torrent['name']}\n"
            details_text += f"Info Hash: {selected_torrent['info_hash']}\n"
            details_text += f"File Size: {BitTorrentUtils.format_bytes(selected_torrent['file_size'])}\n"
            details_text += f"Pieces: {selected_torrent['num_pieces']}\n"
            details_text += f"Piece Length: {BitTorrentUtils.format_bytes(selected_torrent['piece_length'])}\n"
            details_text += f"Seeders: {selected_torrent['seeders']}\n"
            details_text += f"Leechers: {selected_torrent['leechers']}\n"
            details_text += f"Downloads: {selected_torrent['completed']}\n"
            details_text += f"Created: {selected_torrent['created_at']}\n"
            
            self.torrent_details.delete(1.0, tk.END)
            self.torrent_details.insert(tk.END, details_text)
    
    def update_status(self):
        """Update status information"""
        def fetch_status():
            try:
                # Get tracker stats
                response = requests.get(f"{self.tracker_url}/api/tracker/stats", timeout=5)
                if response.status_code == 200:
                    stats = response.json()
                    stats_text = f"📊 Tracker Statistics:\n\n"
                    stats_text += f"Total Torrents: {stats['total_torrents']}\n"
                    stats_text += f"Active Peers: {stats['active_peers']}\n"
                    stats_text += f"Total Peers: {stats['total_peers']}\n"
                    stats_text += f"Total Users: {stats['total_users']}\n"
                    
                    self.root.after(0, lambda: self.stats_text.delete(1.0, tk.END))
                    self.root.after(0, lambda: self.stats_text.insert(tk.END, stats_text))
                    
                    # Connection status
                    conn_text = f"🟢 Connected to tracker\n"
                    conn_text += f"Tracker URL: {self.tracker_url}\n"
                    conn_text += f"Download Directory: {self.download_directory}\n"
                    conn_text += f"Last Update: {time.strftime('%H:%M:%S')}"
                    
                    self.root.after(0, lambda: self.connection_status.delete(1.0, tk.END))
                    self.root.after(0, lambda: self.connection_status.insert(tk.END, conn_text))
                else:
                    conn_text = f"🔴 Cannot connect to tracker\n"
                    conn_text += f"Status Code: {response.status_code}\n"
                    conn_text += f"Tracker URL: {self.tracker_url}"
                    
                    self.root.after(0, lambda: self.connection_status.delete(1.0, tk.END))
                    self.root.after(0, lambda: self.connection_status.insert(tk.END, conn_text))
            except Exception as e:
                conn_text = f"🔴 Connection failed\n"
                conn_text += f"Error: {str(e)}\n"
                conn_text += f"Tracker URL: {self.tracker_url}"
                
                self.root.after(0, lambda: self.connection_status.delete(1.0, tk.END))
                self.root.after(0, lambda: self.connection_status.insert(tk.END, conn_text))
        
        threading.Thread(target=fetch_status, daemon=True).start()
    
    def set_status(self, message):
        """Set status bar message"""
        self.status_bar.config(text=message)
    
    def auto_refresh(self):
        """Auto-refresh data every 10 seconds"""
        self.refresh_torrents()
        self.update_status()
        self.root.after(10000, self.auto_refresh)  # 10 seconds
    
    def on_download_select(self, event):
        """Handle download selection"""
        selection = self.downloads_tree.selection()
        if selection:
            # Enable control buttons when a download is selected
            self.pause_btn.config(state="normal")
            self.resume_btn.config(state="normal")
            self.stop_btn.config(state="normal")
        else:
            # Disable control buttons when no download is selected
            self.pause_btn.config(state="disabled")
            self.resume_btn.config(state="disabled")
            self.stop_btn.config(state="disabled")
    
    def pause_download(self):
        """Pause the selected download"""
        selection = self.downloads_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a download to pause.")
            return
        
        try:
            item = selection[0]
            # Get download ID directly from tree item ID
            try:
                download_id = int(item)
            except ValueError:
                messagebox.showerror("Error", "Invalid download selection.")
                return
            
            if download_id in self.downloads:
                download_manager = self.downloads[download_id]['download_manager']
                if download_manager and download_manager.pause_download():
                    self.set_status(f"Paused download: {self.downloads[download_id]['name']}")
                else:
                    messagebox.showwarning("Cannot Pause", "Unable to pause this download.")
            else:
                messagebox.showerror("Error", "Download not found.")
        except Exception as e:
            error_msg = str(e)
            messagebox.showerror("Error", f"Failed to pause download: {error_msg}")
    
    def resume_download(self):
        """Resume the selected download"""
        selection = self.downloads_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a download to resume.")
            return
        
        try:
            item = selection[0]
            # Get download ID directly from tree item ID
            try:
                download_id = int(item)
            except ValueError:
                messagebox.showerror("Error", "Invalid download selection.")
                return
            
            if download_id in self.downloads:
                download_manager = self.downloads[download_id]['download_manager']
                if download_manager and download_manager.resume_download():
                    self.set_status(f"Resumed download: {self.downloads[download_id]['name']}")
                else:
                    messagebox.showwarning("Cannot Resume", "Unable to resume this download.")
            else:
                messagebox.showerror("Error", "Download not found.")
        except Exception as e:
            error_msg = str(e)
            messagebox.showerror("Error", f"Failed to resume download: {error_msg}")
    
    def stop_download(self):
        """Stop the selected download"""
        selection = self.downloads_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a download to stop.")
            return
        
        try:
            item = selection[0]
            # Get download ID directly from tree item ID
            try:
                download_id = int(item)
            except ValueError:
                messagebox.showerror("Error", "Invalid download selection.")
                return
            
            if download_id in self.downloads:
                filename = self.downloads[download_id]['name']
                result = messagebox.askyesno("Confirm Stop", 
                                           f"Are you sure you want to stop downloading '{filename}'?")
                if result:
                    download_manager = self.downloads[download_id]['download_manager']
                    if download_manager:
                        download_manager.stop_download()
                    
                    # Remove from downloads list
                    del self.downloads[download_id]
                    
                    # Remove from tree
                    self.downloads_tree.delete(item)
                    
                    self.set_status(f"Stopped download: {filename}")
            else:
                messagebox.showerror("Error", "Download not found.")
        except Exception as e:
            error_msg = str(e)
            messagebox.showerror("Error", f"Failed to stop download: {error_msg}")

def main():
    root = tk.Tk()
    app = P2PDesktopClient(root)
    root.mainloop()

if __name__ == "__main__":
    main()
