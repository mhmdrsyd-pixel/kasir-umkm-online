import streamlit as st
import pandas as pd
from datetime import datetime

# --- SETUP KONEKSI SIMPLE ---
# Ganti link di bawah dengan Link Google Sheets Anda (Pastikan sudah 'Anyone with link' & 'Editor')
URL_SHEET = st.secrets["connections"]["gsheets"]["spreadsheet"]
CSV_URL = URL_SHEET.replace('/edit#gid=', '/export?format=csv&gid=')

# --- DATA LOGIN ---
USERS = {"owner": "admin123", "kasir": "kasir123"}
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- LOGIKA LOGIN ---
if not st.session_state['logged_in']:
    st.title("🔒 Login POS")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Masuk"):
        if u in USERS and USERS[u] == p:
            st.session_state['logged_in'] = True
            st.rerun()
        else: st.error("Salah!")
    st.stop()

# --- MENU ---
st.sidebar.title("Menu Toko")
menu = st.sidebar.radio("Pilih Halaman:", ["Kasir", "Laporan"])

if menu == "Kasir":
    st.title("🏪 Mesin Kasir")
    menu_makanan = {"Siomay": 15000, "Batagor": 15000, "Es Teh": 5000}
    pilihan = st.selectbox("Pilih Menu", list(menu_makanan.keys()))
    qty = st.number_input("Jumlah", 1, 100, 1)
    total = menu_makanan[pilihan] * qty
    st.header(f"Total: Rp{total:,}")
    
    if st.button("PROSES TRANSAKSI"):
        st.balloons()
        st.success("✅ Transaksi Berhasil di Layar!")
        st.info("Catatan: Untuk menyimpan ke Excel, silakan catat manual di Google Sheets Anda sementara kami memperbaiki koneksi otomatis.")

elif menu == "Laporan":
    st.title("📈 Laporan Penjualan")
    try:
        # Membaca data dengan proteksi error
        df = pd.read_csv(CSV_URL)
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Google Sheets Anda masih kosong.")
    except Exception as e:
        st.warning("⚠️ Aplikasi belum bisa membaca Google Sheets.")
        st.write("Pastikan di Google Sheets Anda sudah ada judul kolom: Tanggal, Keterangan, Nominal, Tipe.")