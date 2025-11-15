import json
import hashlib
import uuid
import os
from datetime import datetime, timedelta

class ActivationSystem:
    def __init__(self):
        self.activation_file = "configs/activation.json"
        self.ensure_directories()
        self.load_activation_data()
    
    def ensure_directories(self):
        os.makedirs("configs", exist_ok=True)
    
    def load_activation_data(self):
        if os.path.exists(self.activation_file):
            with open(self.activation_file, 'r') as f:
                self.activation_data = json.load(f)
        else:
            self.activation_data = {
                "activated": False,
                "license_key": "",
                "hardware_id": self.generate_hardware_id(),
                "activation_date": "",
                "expiry_date": "",
                "max_accounts": 0,
                "used_accounts": 0,
                "customer_email": "",
                "customer_name": "",
                "product_version": "PRO-1.0"
            }
            self.save_activation_data()
    
    def save_activation_data(self):
        with open(self.activation_file, 'w') as f:
            json.dump(self.activation_data, f, indent=4)
    
    def generate_hardware_id(self):
        # Generate unique hardware ID based on system information
        system_info = str(os.cpu_count()) + str(os.name) + str(os.getenv('COMPUTERNAME', ''))
        hardware_id = hashlib.md5(system_info.encode()).hexdigest()[:16].upper()
        return f"{hardware_id[:4]}-{hardware_id[4:8]}-{hardware_id[8:12]}-{hardware_id[12:16]}"
    
    def validate_license_key(self, license_key, customer_email):
        # Format: MTT-XXXX-XXXX-XXXX (16 karakter) 
        if not license_key.startswith("MTT-"):
            return False, "Format license key tidak valid! Harus dimulai dengan MTT-"
        
        # Validasi license key
        try:
            key_parts = license_key.split('-')
            if len(key_parts) < 3:
                return False, "Format license key salah! Contoh: MTT-BASIC-ABC123"
            
            # Validasi tipe license
            valid_types = ["TRIAL", "BASIC", "PRO", "BIZ", "ENT"]
            if key_parts[1] not in valid_types:
                return False, f"Tipe license tidak valid! Harus: {', '.join(valid_types)}"
            
            # Untuk demo, terima semua license key dengan format benar
            return True, "License key valid!"
            
        except Exception as e:
            return False, f"Error validasi: {str(e)}"
    
    def activate_product(self, license_key, customer_email, customer_name=""):
        print("🔐 PROSES AKTIVASI PRODUK")
        print("=" * 50)
        
        # Validasi license key
        is_valid, message = self.validate_license_key(license_key, customer_email)
        if not is_valid:
            return False, message
        
        # Set activation data
        self.activation_data["activated"] = True
        self.activation_data["license_key"] = license_key
        self.activation_data["customer_email"] = customer_email
        self.activation_data["customer_name"] = customer_name
        self.activation_data["activation_date"] = datetime.now().isoformat()
        
        # Set expiry date berdasarkan tipe license
        license_type = license_key.split('-')[1]
        if license_type == "TRIAL":
            expiry_days = 7
            max_accounts = 3
        elif license_type == "BASIC":
            expiry_days = 30
            max_accounts = 5
        elif license_type == "PRO":
            expiry_days = 30
            max_accounts = 15
        elif license_type == "BIZ":
            expiry_days = 30
            max_accounts = 50
        elif license_type == "ENT":
            expiry_days = 365
            max_accounts = 100
        else:
            expiry_days = 7
            max_accounts = 3
        
        expiry_date = datetime.now() + timedelta(days=expiry_days)
        self.activation_data["expiry_date"] = expiry_date.isoformat()
        self.activation_data["max_accounts"] = max_accounts
        
        self.save_activation_data()
        
        print(f"✅ AKTIVASI BERHASIL!")
        print(f"📧 Customer: {customer_email}")
        print(f"🔑 License: {license_key}")
        print(f"📦 Tipe: {license_type}")
        print(f"👥 Max Accounts: {max_accounts}")
        print(f"📅 Expiry: {expiry_date.strftime('%Y-%m-%d')}")
        print(f"⏰ Masa Aktif: {expiry_days} hari")
        
        return True, "Aktivasi berhasil!"
    
    def check_activation(self):
        if not self.activation_data["activated"]:
            return False, "Produk belum diaktivasi!"
        
        # Cek expiry
        if self.activation_data["expiry_date"]:
            expiry_date = datetime.fromisoformat(self.activation_data["expiry_date"])
            if datetime.now() > expiry_date:
                self.activation_data["activated"] = False
                self.save_activation_data()
                return False, "License telah expired!"
        
        # Cek account limit
        if self.activation_data["used_accounts"] >= self.activation_data["max_accounts"]:
            return False, "Limit account tercapai!"
        
        return True, "Aktivasi valid!"
    
    def get_activation_info(self):
        status = '✅ AKTIF' if self.activation_data['activated'] else '❌ NON-AKTIF'
        expiry = self.activation_data['expiry_date'] or 'N/A'
        if expiry != 'N/A':
            expiry = datetime.fromisoformat(expiry).strftime('%Y-%m-%d')
        
        info = f"""
📋 INFORMASI AKTIVASI:
├── Status: {status}
├── Produk: {self.activation_data['product_version']}
├── Customer: {self.activation_data['customer_name'] or 'N/A'}
├── Email: {self.activation_data['customer_email'] or 'N/A'}
├── License: {self.activation_data['license_key'] or 'N/A'}
├── Max Accounts: {self.activation_data['max_accounts']}
├── Used Accounts: {self.activation_data['used_accounts']}
└── Expiry: {expiry}
"""
        return info
    
    def increment_used_accounts(self):
        self.activation_data["used_accounts"] += 1
        self.save_activation_data()

# Global instance
activation_system = ActivationSystem()

def activation_wizard():
    system = ActivationSystem()
    
    print("🎯 TELEGRAM MASS TOOL - AKTIVASI")
    print("=" * 50)
    
    while True:
        print("\n📋 Menu Aktivasi:")
        print("1. 🔐 Aktivasi Produk")
        print("2. 📊 Cek Status")
        print("3. 🔑 Generate Trial License")
        print("4. 🚀 Lanjut ke Tool")
        
        choice = input("\nPilih opsi (1-4): ").strip()
        
        if choice == "1":
            print("\n🔐 MASUKKAN DATA AKTIVASI:")
            license_key = input("License Key: ").strip()
            customer_email = input("Email: ").strip()
            customer_name = input("Nama (opsional): ").strip()
            
            success, message = system.activate_product(license_key, customer_email, customer_name)
            print(f"\n{'✅' if success else '❌'} {message}")
            
            if success:
                break
        
        elif choice == "2":
            print(system.get_activation_info())
            is_valid, message = system.check_activation()
            print(f"Status: {'✅' if is_valid else '❌'} {message}")
        
        elif choice == "3":
            print("\n🎁 TRIAL LICENSE (7 Hari):")
            trial_key = f"MTT-TRIAL-{uuid.uuid4().hex[:6].upper()}"
            print(f"🔑 License Key: {trial_key}")
            print("📧 Email: trial@example.com")
            print("⏰ Masa aktif: 7 hari")
            print("👥 Max Accounts: 3")
            print("\n⚠️  Gunakan data di atas untuk aktivasi trial")
        
        elif choice == "4":
            is_valid, message = system.check_activation()
            if is_valid:
                print("✅ Produk teraktivasi, melanjutkan...")
                break
            else:
                print(f"❌ {message}")
                print("⚠️  Harap aktivasi terlebih dahulu!")
        else:
            print("❌ Pilihan tidak valid!")

if __name__ == "__main__":
    activation_wizard()
