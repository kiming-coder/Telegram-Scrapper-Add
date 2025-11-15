from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty
import json
import os
from datetime import datetime
from activation_system import activation_system

class MemberScraper:
    def __init__(self):
        self.members_data = []
    
    def check_activation(self):
        is_valid, message = activation_system.check_activation()
        if not is_valid:
            print(f"❌ {message}")
            return False
        return True
    
    def get_client(self):
        # Gunakan account pertama untuk scraping
        from core.multi_config import multi_manager
        
        accounts = multi_manager.accounts['accounts']
        if not accounts:
            print("❌ Tidak ada account! Tambahkan account terlebih dahulu.")
            return None
        
        account = accounts[0]
        try:
            client = TelegramClient(
                f'sessions/{account["session_name"]}',
                account['api_id'],
                account['api_hash']
            )
            return client
        except Exception as e:
            print(f"❌ Error membuat client: {e}")
            return None
    
    def scrape_group_members(self, group_username):
        if not self.check_activation():
            return
        
        print(f"🎯 Memulai scraping members dari: {group_username}")
        
        client = self.get_client()
        if not client:
            return
        
        try:
            with client:
                # Dapatkan entity group
                group_entity = client.get_entity(group_username)
                print(f"📊 Group: {group_entity.title}")
                
                # Dapatkan semua members
                print("⏳ Mengumpulkan members...")
                all_participants = client.get_participants(group_entity, aggressive=True)
                
                print(f"✅ Ditemukan {len(all_participants)} members")
                
                # Simpan data members
                for participant in all_participants:
                    member_data = {
                        'id': participant.id,
                        'username': participant.username or '',
                        'first_name': participant.first_name or '',
                        'last_name': participant.last_name or '',
                        'phone': participant.phone or '',
                        'scraped_date': datetime.now().isoformat()
                    }
                    self.members_data.append(member_data)
                
                # Simpan ke file
                self.save_members(group_username)
                
        except Exception as e:
            print(f"❌ Error scraping: {e}")
    
    def save_members(self, group_username):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"exports/members_{group_username.replace('@', '')}_{timestamp}.json"
        
        os.makedirs('exports', exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.members_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Data disimpan: {filename}")
        print(f"📊 Total members dengan username: {len([m for m in self.members_data if m['username']])}")
    
    def list_groups(self):
        if not self.check_activation():
            return
        
        client = self.get_client()
        if not client:
            return
        
        try:
            with client:
                result = client(GetDialogsRequest(
                    offset_date=None,
                    offset_id=0,
                    offset_peer=InputPeerEmpty(),
                    limit=100,
                    hash=0
                ))
                
                groups = []
                for chat in result.chats:
                    if hasattr(chat, 'megagroup') and chat.megagroup:
                        groups.append({
                            'id': chat.id,
                            'title': chat.title,
                            'username': chat.username or 'N/A',
                            'participants_count': chat.participants_count
                        })
                
                print("\n📋 GRUP YANG TERSEDIA:")
                print("-" * 50)
                for i, group in enumerate(groups, 1):
                    print(f"{i}. {group['title']}")
                    print(f"   👥 {group['participants_count']} members")
                    print(f"   🔗 @{group['username']}")
                    print()
                
                return groups
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return []

def scraper_menu():
    scraper = MemberScraper()
    
    print("🔍 MEMBER SCRAPER TOOL")
    print("=" * 50)
    
    while True:
        print("\n📋 Menu Scraper:")
        print("1. 📋 List Grup Saya")
        print("2. 🎯 Scrape Members dari Grup")
        print("3. ↩️ Kembali")
        
        choice = input("\nPilih opsi (1-3): ").strip()
        
        if choice == "1":
            scraper.list_groups()
        
        elif choice == "2":
            group_username = input("Masukkan username grup (contoh: @namagrup): ").strip()
            if group_username:
                scraper.scrape_group_members(group_username)
            else:
                print("❌ Username tidak valid!")
        
        elif choice == "3":
            break
        
        else:
            print("❌ Pilihan tidak valid!")

if __name__ == "__main__":
    scraper_menu()
