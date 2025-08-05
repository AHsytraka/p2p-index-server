import requests

response = requests.get('http://localhost:8000/api/tracker/peers/8b5819f545a6682d115a376d640a4e920352b3e1')
peers = response.json()
print('Peers found:', len(peers))
for p in peers:
    print(f"  Peer: {p['ip_address']}:{p['port']} (seeder: {p['is_seeder']})")
