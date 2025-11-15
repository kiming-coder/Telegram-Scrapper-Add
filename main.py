#!/usr/bin/env python3
import os
import sys
from activation_system import activation_system, activation_wizard
from core.account_setup import account_setup_wizard
from core.scraper import scraper_menu

def main_menu():
    print('🎯 MINGOS TELEGRAM MASS TOOL - PRO EDITION')
    print('=' * 60)
    
    # Cek aktivasi
    is_valid, message = activation_system.check_activation()
    status = '✅ TERAKTIVASI' if is_valid else '❌ BELUM AKTIVASI'
    
    print(f'Status: {status}')
    
    if is_valid:
        print(activation_system.get_activation_info())
    
    while True:
        print('\n📋 MENU UTAMA:')
        print('1. 🔐 Aktivasi Produk')
        print('2. 👥 Kelola Account')
        print('3. 🔍 Scrape Members')
        print('4. 🚀 Mass Invite')
        print('5. 📊 Lihat Stats')
        print('6. ❌ Keluar')
        
        choice = input('\nPilih opsi (1-6): ').strip()
        
        if choice == '1':
            activation_wizard()
        
        elif choice == '2':
            account_setup_wizard()
        
        elif choice == '3':
            scraper_menu()
        
        elif choice == '4':
            from core.multi_account_adder import run_multi_inviter
            run_multi_inviter()
        
        elif choice == '5':
            from core.multi_config import multi_manager
            print(f"\n📊 STATISTIK SISTEM:")
            print(f"👥 Total Account: {len(multi_manager.accounts['accounts'])}")
            print(f"🎯 Total Invites: {multi_manager.stats['total_invites_sent']}")
            print(f"📅 Last Run: {multi_manager.stats.get('last_run', 'Never')}")
            
            # Tampilkan daily stats
            if multi_manager.stats['daily_stats']:
                print(f"\n📈 STATISTIK HARIAN:")
                for date, stats in list(multi_manager.stats['daily_stats'].items())[-5:]:  # 5 hari terakhir
                    print(f"   {date}: {stats.get('invites_sent', 0)} invites")
        
        elif choice == '6':
            print('👋 Terima kasih telah menggunakan Telegram Mass Tool!')
            sys.exit(0)
        
        else:
            print('❌ Pilihan tidak valid!')

if __name__ == '__main__':
    try:
        main_menu()
    except KeyboardInterrupt:
        print('\n\n👋 Program dihentikan oleh user!')
    except Exception as e:
        print(f'\n❌ Error: {e}')
        input('Press Enter to continue...')
