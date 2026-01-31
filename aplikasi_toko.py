import streamlit as st
import pandas as pd
from datetime import datetime
import requests

# --- 1. SETUP DATABASE SEDERHANA (Hanya menggunakan URL Public) ---
# Kita menggunakan trik Google Forms/Sheet agar tidak perlu autentikasi rumit
SHEET_ID = "13dQgRb2HX5FX8lHdoZt3xuvjqZIwJ9hC3c_HANiAxxw" # Tempel Kode Unik Anda di sini
SHEET_NAME = "Sheet1"
# URL untuk membaca data dalam format CSV
URL_READ = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

# --- 2. DATA USER ---
USERS = {"owner": "admin123", "kasir": "kasir123"}
if 'is_logged_in' not in st.session_state:
    st.session_state['is_logged_in'] = False

# --- 3. LOGIN ---
if not st.session_state['is_logged_in']:
    st.title("🔒 Login POS UMKM")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Masuk"):
        if u in USERS and USERS[u] == p:
            st.session_state['is_logged_in'] = True
            st.session_state['user_role'] = "owner" if u == "owner" else "kasir"
            st.rerun()
        else: st.error("Akses Ditolak!")
    st.stop()

# --- 4. MENU ---
menu = st.sidebar.selectbox("Menu", ["Kasir", "Laporan"])

if menu == "Kasir":
    st.title("🏪 Mesin Kasir")
    menu_item = {"Siomay": 15000, "Es Teh": 5000}
    pilihan = st.selectbox("Pilih Menu", list(menu_item.keys()))
    qty = st.number_input("Jumlah", 1, 100, 1)
    total = menu_item[pilihan] * qty
    st.header(f"Total: Rp{total:,}")

    st.warning("⚠️ Untuk versi ini, silakan salin data ke Google Sheets secara manual atau gunakan sistem log.")
    if st.button("KONFIRMASI PEMBAYARAN"):
        st.balloons()
        st.success(f"Transaksi {pilihan} x{qty} Berhasil!")
        st.info("Catatan: Gunakan fitur 'Laporan' untuk melihat histori.")

elif menu == "Laporan":
    st.title("📈 Laporan Keuangan")
    try:
        # Membaca data langsung dari link public CSV
        df = pd.read_csv(URL_READ)
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            # Menghitung total jika kolom Nominal tersedia
            if 'Nominal' in df.columns:
                st.metric("Total Omzet", f"Rp {df['Nominal'].sum():,}")
        else:
            st.info("Belum ada data di Google Sheets.")
    except Exception as e:
        st.error(f"Gagal memuat data: {e}")
        st.info("Pastikan link Google Sheets sudah di-set 'Anyone with the link' sebagai Editor.")