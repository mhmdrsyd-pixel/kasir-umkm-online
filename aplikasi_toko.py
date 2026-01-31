import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 1. SETUP KONEKSI ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 2. LOGIN ---
USERS = {"owner": "admin123", "kasir": "kasir123"}
if 'is_logged_in' not in st.session_state:
    st.session_state['is_logged_in'] = False

if not st.session_state['is_logged_in']:
    st.title("🔒 Login POS")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Masuk"):
        if u in USERS and USERS[u] == p:
            st.session_state['is_logged_in'] = True
            st.session_state['user_role'] = "owner" if u == "owner" else "kasir"
            st.rerun()
        else: st.error("Akses Ditolak!")
    st.stop()

# --- 3. MENU ---
menu = st.sidebar.selectbox("Menu Utama", ["Kasir", "Laporan", "Belanja"])

if menu == "Kasir":
    st.title("🏪 Mesin Kasir")
    # Menu fleksibel
    items = {"Siomay": 15000, "Batagor": 15000, "Es Teh": 5000}
    pilihan = st.selectbox("Pilih Menu", list(items.keys()))
    qty = st.number_input("Jumlah Beli", 1, 100, 1)
    total = items[pilihan] * qty
    st.header(f"Total Bayar: Rp{total:,}")

    if st.button("PROSES BAYAR"):
        # Buat data baru dengan kolom Huruf Besar di awal
        new_row = pd.DataFrame([{
            "Tanggal": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Keterangan": f"Jual {pilihan} x{qty}",
            "Nominal": total,
            "Tipe": "MASUK"
        }])
        
        try:
            # Baca data dari Google Sheets
            try:
                df_existing = conn.read(worksheet="Sheet1", ttl=0)
            except:
                df_existing = pd.DataFrame(columns=["Tanggal", "Keterangan", "Nominal", "Tipe"])
            
            # Gabungkan data lama dan baru
            if df_existing is not None and not df_existing.empty:
                df_final = pd.concat([df_existing, new_row], ignore_index=True)
            else:
                df_final = new_row
            
            # Kirim balik ke Google Sheets
            conn.update(worksheet="Sheet1", data=df_final)
            st.balloons()
            st.success("✅ Penjualan Berhasil Dicatat!")
            st.rerun()
        except Exception as e:
            st.error(f"Gagal Simpan: {e}")

elif menu == "Laporan":
    st.title("📈 Laporan Keuangan")
    try:
        df = conn.read(worksheet="Sheet1", ttl=0)
        if df is not None and not df.empty:
            # Tampilkan tabel data
            st.dataframe(df, use_container_width=True)
            
            # Cek ketersediaan kolom secara aman (tidak peduli huruf besar/kecil)
            df.columns = [c.capitalize() for c in df.columns]
            
            if 'Nominal' in df.columns and 'Tipe' in df.columns:
                df['Nominal'] = pd.to_numeric(df['Nominal'], errors='coerce').fillna(0)
                masuk = df[df['Tipe'].str.upper() == 'MASUK']['Nominal'].sum()
                keluar = df[df['Tipe'].str.upper() == 'KELUAR']['Nominal'].sum()
                
                col1, col2 = st.columns(2)
                col1.metric("Total Pemasukan", f"Rp {masuk:,}")
                col2.metric("Untung Bersih", f"Rp {masuk - keluar:,}")
        else:
            st.info("Belum ada data transaksi.")
    except Exception as e:
        st.error(f"Gagal memuat laporan: {e}")

elif menu == "Belanja":
    st.title("💸 Pengeluaran / Belanja")
    with st.form("form_belanja"):
        ket = st.text_input("Keterangan Belanja")
        nom = st.number_input("Nominal (Rp)", 0)
        if st.form_submit_button("Simpan Pengeluaran"):
            new_exp = pd.DataFrame([{
                "Tanggal": datetime.now().strftime("%Y-%m-%d"), 
                "Keterangan": ket, 
                "Nominal": nom, 
                "Tipe": "KELUAR"
            }])
            try:
                df_old = conn.read(worksheet="Sheet1", ttl=0)
                df_up = pd.concat([df_old, new_exp], ignore_index=True)
                conn.update(worksheet="Sheet1", data=df_up)
                st.success("✅ Pengeluaran Tersimpan!")
            except:
                st.error("Gagal simpan data.")