import json
import os
from core.multi_config import multi_manager
from activation_system import activation_system

def account_setup_wizard():
    print('👥 MULTI-ACCOUNT SETUP WIZARD')
    print('=' * 50)
    
    # Cek aktivasi
    is_valid, message = activation_system.check_activation()
    if not is_valid:
        print(f"❌ {message}")
        print("⚠️  Harap aktivasi produk terlebih dahulu!")
        return
    
    print(activation_system.get_activation_info())
    
    while True:
        print('\n📋 Manajemen Account:')
        print('1. ➕ Tambah Account Baru')
        print('2. 📋 Lihat Semua Account') 
        print('3. ⚙️ Edit Settings')
        print('4. 🚀 Start Mass Invite')
        print('5. 🔑 Info Aktivasi')
        print('6. ↩️ Kembali ke Menu Utama')
        
        choice = input('\nPilih opsi (1-6): ').strip()
        
        if choice == '1':
            add_account()
        elif choice == '2':
            list_accounts()
        elif choice == '3':
            edit_settings()
        elif choice == '4':
            from core.multi_account_adder import run_multi_inviter
            run_multi_inviter()
        elif choice == '5':
            print(activation_system.get_activation_info())
        elif choice == '6':
            break
        else:
            print('❌ Pilihan tidak valid!')

def add_account():
    print('\n➕ TAMBAH ACCOUNT BARU')
    print('-' * 30)
    
    # Tampilkan info limit
    max_accounts = activation_system.activation_data["max_accounts"]
    used_accounts = activation_system.activation_data["used_accounts"]
    remaining = max_accounts - used_accounts
    
    print(f"📊 Limit: {used_accounts}/{max_accounts} account (Sisa: {remaining})")
    
    if remaining <= 0:
        print("❌ Limit account tercapai! Upgrade license untuk menambah lebih banyak account.")
        return
    
    api_id = input('API ID: ').strip()
    api_hash = input('API Hash: ').strip()
    phone_number = input('Nomor Telepon: ').strip()
    session_name = input('Nama Session [opsional]: ').strip() or f"account{len(multi_manager.accounts['accounts']) + 1}"
    
    account_data = {
        'api_id': api_id,
        'api_hash': api_hash,
        'phone_number': phone_number,
        'session_name': session_name
    }
    
    try:
        account_id = multi_manager.add_account(account_data)
        print(f'✅ Account berhasil ditambahkan! ID: {account_id}')
        print(f'📱 Sisa slot: {remaining - 1}')
        
    except Exception as e:
        print(f'❌ Error: {e}')

def list_accounts():
    print('\n📋 DAFTAR ACCOUNT')
    print('-' * 40)
    
    accounts = multi_manager.accounts['accounts']
    if not accounts:
        print('❌ Tidak ada account ditemukan!')
        return
    
    for i, acc in enumerate(accounts, 1):
        status = '✅ AKTIF' if acc.get('is_active', True) else '❌ NON-AKTIF'
        print(f'{i}. {acc["phone_number"]} - {acc["session_name"]} - {status}')

def edit_settings():
    print('\n⚙️ PENGATURAN SISTEM')
    print('-' * 30)
    
    settings = multi_manager.accounts['settings']
    print(f'1. Max harian per account: {settings["max_daily_per_account"]}')
    print(f'2. Delay antar invite: {settings["delay_between_invites"]}s')
    print(f'3. Auto rotate accounts: {settings["auto_rotate"]}')
    print(f'4. Max concurrent accounts: {settings["max_concurrent_accounts"]}')
    print(f'5. Target group: {multi_manager.accounts["target_group"]}')
    
    choice = input('\nPilih setting untuk edit (1-5): ').strip()
    
    if choice == '1':
        new_value = input(f'Max harian baru [{settings["max_daily_per_account"]}]: ').strip()
        if new_value.isdigit():
            settings['max_daily_per_account'] = int(new_value)
    elif choice == '2':
        new_value = input(f'Delay baru [{settings["delay_between_invites"]}]: ').strip()
        if new_value.isdigit():
            settings['delay_between_invites'] = int(new_value)
    elif choice == '3':
        settings['auto_rotate'] = not settings['auto_rotate']
    elif choice == '4':
        new_value = input(f'Max concurrent baru [{settings["max_concurrent_accounts"]}]: ').strip()
        if new_value.isdigit():
            settings['max_concurrent_accounts'] = int(new_value)
    elif choice == '5':
        new_value = input(f'Target group baru [{multi_manager.accounts["target_group"]}]: ').strip()
        if new_value:
            multi_manager.accounts['target_group'] = new_value
    
    multi_manager.save_accounts()
    print('✅ Settings updated!')

if __name__ == '__main__':
    account_setup_wizard()
