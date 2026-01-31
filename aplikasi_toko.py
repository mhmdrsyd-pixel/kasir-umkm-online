import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 1. SETUP KONEKSI ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 2. LOGIN DATA ---
USERS = {"owner": "admin123", "kasir": "kasir123"}

if 'is_logged_in' not in st.session_state:
    st.session_state['is_logged_in'] = False

# --- FUNGSI LOGIN ---
if not st.session_state['is_logged_in']:
    st.title("🔒 Login POS")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Masuk"):
        if u in USERS and USERS[u] == p:
            st.session_state['is_logged_in'] = True
            st.session_state['user_role'] = "owner" if u == "owner" else "kasir"
            st.rerun()
        else: st.error("Salah!")
    st.stop()

# --- 3. MENU ---
menu = st.sidebar.selectbox("Menu", ["Kasir", "Laporan"] if st.session_state['user_role'] == "kasir" else ["Kasir", "Laporan", "Belanja"])

if menu == "Kasir":
    st.title("🏪 Mesin Kasir")
    # Contoh menu sederhana
    items = {"Siomay": 15000, "Batagor": 15000, "Es Teh": 5000}
    pilihan = st.selectbox("Menu", list(items.keys()))
    qty = st.number_input("Jumlah", 1, 100, 1)
    total = items[pilihan] * qty
    st.header(f"Total: Rp{total:,}")

    if st.button("BAYAR"):
        new_row = pd.DataFrame([{
            "Tanggal": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Keterangan": f"Jual {pilihan} x{qty}",
            "Nominal": total,
            "Tipe": "MASUK"
        }])
        
        try:
            # Baca data (Gunakan try-except agar tidak error jika kolom belum ada)
            try:
                df_existing = conn.read(worksheet="Sheet1", ttl=0)
            except:
                df_existing = pd.DataFrame(columns=["Tanggal", "Keterangan", "Nominal", "Tipe"])
            
            # Gabung & Update
            df_final = pd.concat([df_existing, new_row], ignore_index=True)
            conn.update(worksheet="Sheet1", data=df_final)
            st.success("✅ Terjual & Tercatat!")
            st.balloons()
        except Exception as e:
            st.error(f"Error: {e}")

elif menu == "Laporan":
    st.title("📈 Laporan Keuangan")
    try:
        df = conn.read(worksheet="Sheet1", ttl=0)
        if not df.empty:
            st.dataframe(df)
            # Hitung aman dengan proteksi jika kolom 'Tipe' belum ada isinya
            if 'Tipe' in df.columns:
                masuk = df[df['Tipe'] == 'MASUK']['Nominal'].sum()
                keluar = df[df['Tipe'] == 'KELUAR']['Nominal'].sum()
                st.metric("Untung Bersih", f"Rp {masuk - keluar:,}")
        else:
            st.info("Belum ada data.")
    except:
        st.warning("Belum bisa membaca data. Silakan lakukan transaksi pertama.")