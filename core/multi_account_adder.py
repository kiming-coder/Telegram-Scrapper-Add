from telethon.sync import TelegramClient
from telethon.tl.functions.channels import InviteToChannelRequest
import json
import time
import random
import threading
import os
from datetime import datetime
from core.multi_config import multi_manager
from activation_system import activation_system

class MultiAccountInviter:
    def __init__(self):
        self.manager = multi_manager
        self.results = {
            'success': 0,
            'failed': 0,
            'rate_limited': 0,
            'completed_accounts': 0
        }
        self.lock = threading.Lock()
    
    def check_activation(self):
        is_valid, message = activation_system.check_activation()
        if not is_valid:
            print(f"❌ {message}")
            return False
        return True
    
    def load_members(self):
        member_files = [f for f in os.listdir('exports') if f.startswith('members_')]
        if not member_files:
            print('❌ Tidak ada file members! Jalankan scraper terlebih dahulu.')
            return []
        
        member_files.sort(reverse=True)
        selected_file = f'exports/{member_files[0]}'
        
        try:
            with open(selected_file, 'r', encoding='utf-8') as f:
                members = json.load(f)
            
            target_members = [m for m in members if m.get('username')]
            print(f'🎯 Memuat {len(target_members)} members dengan username')
            return target_members
            
        except Exception as e:
            print(f'❌ Error memuat members: {e}')
            return []
    
    def account_worker(self, account, members_chunk, target_group, worker_id):
        print(f'👤 Worker {worker_id} dimulai: {account["phone_number"]}')
        print(f'   📊 Memproses {len(members_chunk)} members')
        
        account_success = 0
        account_failed = 0
        account_rate_limited = 0
        
        try:
            with TelegramClient(f'sessions/{account["session_name"]}', 
                              account['api_id'], 
                              account['api_hash']) as client:
                
                target_entity = client.get_entity(target_group)
                
                for i, member in enumerate(members_chunk):
                    username = member.get('username')
                    if not username:
                        continue
                    
                    try:
                        if account_success >= self.manager.accounts['settings']['max_daily_per_account']:
                            print(f'[{worker_id}] 🛑 Limit harian tercapai')
                            break
                        
                        print(f'[{worker_id}] [{i+1}/{len(members_chunk)}] Mengundang @{username}...')
                        
                        user_entity = client.get_entity(username)
                        result = client(InviteToChannelRequest(
                            channel=target_entity,
                            users=[user_entity]
                        ))
                        
                        account_success += 1
                        print(f'[{worker_id}] ✅ Berhasil: @{username}')
                        
                        with self.lock:
                            self.results['success'] += 1
                        
                    except Exception as e:
                        error_msg = str(e)
                        
                        if 'Too many requests' in error_msg:
                            print(f'[{worker_id}] 🚫 Rate limit - cooling down')
                            account_rate_limited += 1
                            time.sleep(300)
                            continue
                            
                        elif 'USER_ALREADY_PARTICIPANT' in error_msg:
                            print(f'[{worker_id}] ⚠️ Sudah member: @{username}')
                            
                        elif 'USER_PRIVACY_RESTRICTED' in error_msg:
                            print(f'[{worker_id}] 🔒 Privacy restricted: @{username}')
                            account_failed += 1
                            
                        else:
                            print(f'[{worker_id}] ❌ Gagal: @{username} - {error_msg}')
                            account_failed += 1
                        
                        with self.lock:
                            self.results['failed'] += 1
                    
                    delay = random.randint(20, 40)
                    time.sleep(delay)
                
                print(f'🎉 Worker {worker_id} selesai: {account_success}✅ {account_failed}❌ {account_rate_limited}🚫')
                
        except Exception as e:
            print(f'❌ Worker {worker_id} error: {e}')
        
        with self.lock:
            self.results['completed_accounts'] += 1
    
    def start_mass_invite(self):
        # Cek aktivasi
        if not self.check_activation():
            return
        
        print('🚀 MASS INVITER - MULTI-ACCOUNT SYSTEM')
        print('=' * 60)
        
        active_accounts = self.manager.get_active_accounts()
        if not active_accounts:
            print('❌ Tidak ada account aktif! Tambahkan account terlebih dahulu.')
            return
        
        print(f'👥 Account aktif: {len(active_accounts)}')
        for acc in active_accounts:
            print(f'   📱 {acc["phone_number"]}')
        
        target_members = self.load_members()
        if not target_members:
            return
        
        print(f'🎯 Total members diundang: {len(target_members)}')
        
        members_per_account = len(target_members) // len(active_accounts)
        member_chunks = []
        
        for i in range(len(active_accounts)):
            start_idx = i * members_per_account
            end_idx = start_idx + members_per_account if i < len(active_accounts) - 1 else len(target_members)
            member_chunks.append(target_members[start_idx:end_idx])
        
        print(f'📊 Members per account: ~{members_per_account}')
        
        target_group = self.manager.accounts['target_group']
        print(f'🎯 Target group: {target_group}')
        
        confirm = input(f'\n⚠️  MULAI MASS INVITE DENGAN {len(active_accounts)} ACCOUNT? (y/N): ').strip().lower()
        if confirm != 'y':
            print('❌ Dibatalkan!')
            return
        
        threads = []
        start_time = time.time()
        
        print(f'\n🚀 MENJALANKAN {len(active_accounts)} WORKERS...')
        print('=' * 60)
        
        for i, account in enumerate(active_accounts):
            thread = threading.Thread(
                target=self.account_worker,
                args=(account, member_chunks[i], target_group, i+1)
            )
            threads.append(thread)
            thread.start()
            time.sleep(10)
        
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        self.generate_report(total_time, len(target_members))
    
    def generate_report(self, total_time, total_members):
        print(f'\n🎉 MASS INVITE SELESAI!')
        print('=' * 60)
        print(f'📈 HASIL AKHIR:')
        print(f'   ✅ Berhasil diundang: {self.results["success"]}')
        print(f'   ❌ Gagal: {self.results["failed"]}')
        print(f'   🚫 Rate limited: {self.results["rate_limited"]}')
        print(f'   👥 Account selesai: {self.results["completed_accounts"]}')
        print(f'   📊 Success rate: {(self.results["success"]/total_members)*100:.1f}%')
        print(f'   ⏰ Total waktu: {total_time/60:.1f} menit')
        print(f'   🚀 Kecepatan: {self.results["success"]/(total_time/60):.1f} invites/menit')
        print('=' * 60)
        
        today = datetime.now().strftime('%Y-%m-%d')
        if today not in self.manager.stats['daily_stats']:
            self.manager.stats['daily_stats'][today] = {}
        
        self.manager.stats['daily_stats'][today]['invites_sent'] = self.results['success']
        self.manager.stats['daily_stats'][today]['accounts_used'] = self.results['completed_accounts']
        self.manager.stats['total_invites_sent'] += self.results['success']
        self.manager.stats['last_run'] = datetime.now().isoformat()
        
        self.manager.save_stats()

def run_multi_inviter():
    inviter = MultiAccountInviter()
    inviter.start_mass_invite()

if __name__ == '__main__':
    run_multi_inviter()
