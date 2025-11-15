import json
import os
from datetime import datetime
from activation_system import activation_system

class MultiAccountManager:
    def __init__(self):
        self.accounts_file = "configs/multi_accounts.json"
        self.stats_file = "data/multi_stats.json"
        self.ensure_directories()
        self.load_accounts()
        self.load_stats()
    
    def ensure_directories(self):
        os.makedirs("configs", exist_ok=True)
        os.makedirs("sessions", exist_ok=True)
        os.makedirs("data", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
    
    def load_accounts(self):
        if os.path.exists(self.accounts_file):
            with open(self.accounts_file, 'r', encoding='utf-8') as f:
                self.accounts = json.load(f)
        else:
            self.accounts = {
                "target_group": "@fynerohub",
                "accounts": [],
                "settings": {
                    "max_daily_per_account": 80,
                    "delay_between_invites": 30,
                    "auto_rotate": True,
                    "max_concurrent_accounts": 5
                }
            }
            self.save_accounts()
    
    def load_stats(self):
        if os.path.exists(self.stats_file):
            with open(self.stats_file, 'r') as f:
                self.stats = json.load(f)
        else:
            self.stats = {
                "total_invites_sent": 0,
                "total_members_added": 0,
                "daily_stats": {},
                "account_stats": {},
                "last_run": ""
            }
    
    def save_accounts(self):
        with open(self.accounts_file, 'w', encoding='utf-8') as f:
            json.dump(self.accounts, f, indent=4, ensure_ascii=False)
    
    def save_stats(self):
        with open(self.stats_file, 'w') as f:
            json.dump(self.stats, f, indent=4)
    
    def add_account(self, account_data):
        # Cek limit aktivasi
        is_valid, message = activation_system.check_activation()
        if not is_valid:
            raise Exception(f"Aktivasi gagal: {message}")
        
        current_accounts = len(self.accounts['accounts'])
        max_accounts = activation_system.activation_data["max_accounts"]
        
        if current_accounts >= max_accounts:
            raise Exception(f"Limit account tercapai! Maksimal: {max_accounts} account")
        
        account_id = f"account{current_accounts + 1}"
        account_data['id'] = account_id
        account_data['created_date'] = datetime.now().isoformat()
        account_data['total_invites_sent'] = 0
        account_data['is_active'] = True
        
        self.accounts['accounts'].append(account_data)
        self.save_accounts()
        
        # Update counter di sistem aktivasi
        activation_system.increment_used_accounts()
        
        return account_id
    
    def get_active_accounts(self):
        return [acc for acc in self.accounts['accounts'] if acc.get('is_active', True)]

# Global instance
multi_manager = MultiAccountManager()
