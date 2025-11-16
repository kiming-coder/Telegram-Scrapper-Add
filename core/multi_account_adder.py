from telethon.sync import TelegramClient
from telethon.tl.functions.channels import InviteToChannelRequest
import json
import time
import random
import threading
import os
import asyncio
from datetime import datetime
from core.multi_config import multi_manager

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
    
    def load_members(self):
        member_files = [f for f in os.listdir('exports') if f.startswith('members_')]
        if not member_files:
            print('❌ No member files found! Run scraper first.')
            return []
        
        member_files.sort(reverse=True)
        selected_file = f'exports/{member_files[0]}'
        
        try:
            with open(selected_file, 'r', encoding='utf-8') as f:
                members = json.load(f)
            
            target_members = [m for m in members if m.get('username')]
            print(f'🎯 Loaded {len(target_members)} members with username')
            return target_members
            
        except Exception as e:
            print(f'❌ Error loading members: {e}')
            return []
    
    def run_account_worker(self, account, members_chunk, target_group, worker_id):
        """Run async function in a new event loop for each thread"""
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(
                self.account_worker(account, members_chunk, target_group, worker_id)
            )
        finally:
            loop.close()
    
    async def account_worker(self, account, members_chunk, target_group, worker_id):
        print(f'👤 Worker {worker_id} started: {account["phone_number"]}')
        print(f'   📊 Processing {len(members_chunk)} members')
        
        account_success = 0
        account_failed = 0
        account_rate_limited = 0
        
        try:
            async with TelegramClient(
                f'sessions/{account["session_name"]}', 
                account['api_id'], 
                account['api_hash']
            ) as client:
                
                # Test connection
                me = await client.get_me()
                print(f'[{worker_id}] ✅ Connected as: {me.first_name} ({me.phone})')
                
                target_entity = await client.get_entity(target_group)
                print(f'[{worker_id}] 🎯 Target group: {target_group}')
                
                for i, member in enumerate(members_chunk):
                    username = member.get('username')
                    if not username:
                        continue
                    
                    try:
                        # Check daily limit
                        if account_success >= self.manager.accounts['settings']['max_daily_per_account']:
                            print(f'[{worker_id}] 🛑 Daily limit reached ({account_success})')
                            break
                        
                        print(f'[{worker_id}] [{i+1}/{len(members_chunk)}] Inviting @{username}...')
                        
                        # Get user entity
                        user_entity = await client.get_entity(username)
                        
                        # Send invite
                        result = await client(InviteToChannelRequest(
                            channel=target_entity,
                            users=[user_entity]
                        ))
                        
                        account_success += 1
                        print(f'[{worker_id}] ✅ Success: @{username} ({account_success})')
                        
                        with self.lock:
                            self.results['success'] += 1
                        
                    except Exception as e:
                        error_msg = str(e)
                        
                        if 'Too many requests' in error_msg or 'FLOOD_WAIT' in error_msg:
                            print(f'[{worker_id}] 🚫 Rate limit - cooling down 5 minutes')
                            account_rate_limited += 1
                            with self.lock:
                                self.results['rate_limited'] += 1
                            await asyncio.sleep(300)  # 5 minutes
                            continue
                            
                        elif 'USER_ALREADY_PARTICIPANT' in error_msg:
                            print(f'[{worker_id}] ⚠️ Already member: @{username}')
                            # Don't count as failure
                            continue
                            
                        elif 'USER_PRIVACY_RESTRICTED' in error_msg:
                            print(f'[{worker_id}] 🔒 Privacy restricted: @{username}')
                            account_failed += 1
                            
                        elif 'USER_NOT_MUTUAL_CONTACT' in error_msg:
                            print(f'[{worker_id}] 📞 Not mutual contact: @{username}')
                            account_failed += 1
                            
                        elif 'Cannot add' in error_msg:
                            print(f'[{worker_id}] 🚫 Cannot add: @{username}')
                            account_failed += 1
                            
                        else:
                            print(f'[{worker_id}] ❌ Failed: @{username} - {error_msg}')
                            account_failed += 1
                        
                        with self.lock:
                            self.results['failed'] += 1
                    
                    # Random delay between invites
                    delay = random.randint(25, 45)
                    print(f'[{worker_id}] ⏳ Waiting {delay}s...')
                    await asyncio.sleep(delay)
                
                print(f'🎉 Worker {worker_id} finished: {account_success}✅ {account_failed}❌ {account_rate_limited}🚫')
                
        except Exception as e:
            print(f'❌ Worker {worker_id} error: {e}')
            import traceback
            traceback.print_exc()
        
        with self.lock:
            self.results['completed_accounts'] += 1
    
    def start_mass_invite(self):
        print('🚀 MASS INVITER - MULTI-ACCOUNT SYSTEM')
        print('=' * 60)
        
        active_accounts = self.manager.get_active_accounts()
        if not active_accounts:
            print('❌ No active accounts found! Add accounts first.')
            return
        
        print(f'👥 Active accounts: {len(active_accounts)}')
        for acc in active_accounts:
            print(f'   📱 {acc["phone_number"]} ({acc["session_name"]})')
        
        target_members = self.load_members()
        if not target_members:
            return
        
        print(f'🎯 Total members to invite: {len(target_members)}')
        
        # Split members evenly among accounts
        members_per_account = len(target_members) // len(active_accounts)
        member_chunks = []
        
        for i in range(len(active_accounts)):
            start_idx = i * members_per_account
            if i == len(active_accounts) - 1:
                # Last account gets remaining members
                end_idx = len(target_members)
            else:
                end_idx = start_idx + members_per_account
            member_chunks.append(target_members[start_idx:end_idx])
        
        print(f'📊 Members per account: ~{members_per_account}')
        
        target_group = self.manager.accounts['target_group']
        print(f'🎯 Target group: {target_group}')
        
        confirm = input(f'\n⚠️  START MASS INVITE WITH {len(active_accounts)} ACCOUNTS? (y/N): ').strip().lower()
        if confirm != 'y':
            print('❌ Cancelled!')
            return
        
        threads = []
        start_time = time.time()
        
        print(f'\n🚀 STARTING {len(active_accounts)} WORKERS...')
        print('=' * 60)
        
        # Start threads with staggered delay
        for i, account in enumerate(active_accounts):
            thread = threading.Thread(
                target=self.run_account_worker,
                args=(account, member_chunks[i], target_group, i+1)
            )
            threads.append(thread)
            thread.start()
            
            # Stagger thread starts to avoid rate limits
            if i < len(active_accounts) - 1:
                print(f'⏰ Starting next worker in 15 seconds...')
                time.sleep(15)
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        self.generate_report(total_time, len(target_members))
    
    def generate_report(self, total_time, total_members):
        print(f'\n🎉 MASS INVITE COMPLETED!')
        print('=' * 60)
        print(f'📈 FINAL RESULTS:')
        print(f'   ✅ Successfully invited: {self.results["success"]}')
        print(f'   ❌ Failed: {self.results["failed"]}')
        print(f'   🚫 Rate limited: {self.results["rate_limited"]}')
        print(f'   👥 Accounts completed: {self.results["completed_accounts"]}')
        
        if total_members > 0:
            success_rate = (self.results["success"]/total_members)*100
        else:
            success_rate = 0
            
        print(f'   📊 Success rate: {success_rate:.1f}%')
        print(f'   ⏰ Total time: {total_time/60:.1f} minutes')
        
        if total_time > 0:
            speed = self.results["success"]/(total_time/60)
        else:
            speed = 0
            
        print(f'   🚀 Speed: {speed:.1f} invites/minute')
        print('=' * 60)
        
        # Update statistics
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
