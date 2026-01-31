import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 1. SETUP KONEKSI GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 2. DATA USER ---
USERS = {"owner": "admin123", "kasir": "kasir123"}

# --- 3. FUNGSI AMBIL DATA ---
def get_data(worksheet_name):
    # Mengambil data dari sheet tertentu
    return conn.read(worksheet=worksheet_name, ttl=0)

# --- 4. LOGIKA LOGIN ---
if 'is_logged_in' not in st.session_state:
    st.session_state['is_logged_in'] = False
    st.session_state['user_role'] = None

if not st.session_state['is_logged_in']:
    st.title("🔒 Login POS Toko")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Masuk"):
        if u in USERS and USERS[u] == p:
            st.session_state['is_logged_in'] = True
            st.session_state['user_role'] = "owner" if u == "owner" else "kasir"
            st.rerun()
        else:
            st.error("Gagal!")
    st.stop()

# --- 5. TAMPILAN UTAMA ---
st.sidebar.title(f"Role: {st.session_state['user_role'].upper()}")
if st.sidebar.button("Logout"):
    st.session_state['is_logged_in'] = False
    st.rerun()

menu_options = ["🏪 Kasir"]
if st.session_state['user_role'] == "owner":
    menu_options += ["💸 Catat Belanja", "📈 Laporan"]

menu = st.sidebar.selectbox("Menu", menu_options)

# === HALAMAN KASIR ===
if menu == "🏪 Kasir":
    st.title("Mesin Kasir")
    # Contoh manual untuk menu (Nanti bisa dikembangkan untuk ambil dari Sheet Stok)
    menu_makanan = {"Siomay": 15000, "Es Teh": 5000, "Paket Hemat": 18000}
    
    item = st.selectbox("Pilih Menu", list(menu_makanan.keys()))
    harga = menu_makanan[item]
    qty = st.number_input("Jumlah", 1, 100, 1)
    diskon = st.number_input("Potongan Harga (Rp)", 0, harga*qty, 0)
    
    total = (harga * qty) - diskon
    st.header(f"Total: Rp{total:,}")
    
    if st.button("PROSES BAYAR"):
        # SIMPAN KE GOOGLE SHEETS (Sheet Penjualan)
        new_data = pd.DataFrame([{
            "Tanggal": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Keterangan": f"Jual {item} x{qty}",
            "Nominal": total,
            "Tipe": "MASUK"
        }])
        
        # Ambil data lama, gabung dengan baru, lalu tulis balik
        # LOGIKA SIMPAN DATA ANTI-GAGAL
        try:
            # 1. Baca data yang ada (jika gagal, buat dataframe kosong)
            try:
                existing_data = conn.read(worksheet="Sheet1", ttl=0)
            except:
                existing_data = pd.DataFrame(columns=["Tanggal", "Keterangan", "Nominal", "Tipe"])
            
            # 2. Gabungkan data baru
            if existing_data is not None and not existing_data.empty:
                # Pastikan format kolom sama
                updated_df = pd.concat([existing_data, new_data], ignore_index=True)
            else:
                updated_df = new_data
            
            # 3. Kirim balik ke Google Sheets
            conn.update(worksheet="Sheet1", data=updated_df)
            st.balloons()
            st.success("✅ Berhasil! Data sudah masuk ke Google Sheets.")
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Masalah Teknis: {e}")
            st.info("Saran: Pastikan akses Google Sheets sudah 'Editor' untuk 'Anyone with the link'.")
# === HALAMAN BELANJA ===
elif menu == "💸 Catat Belanja":
    st.title("Input Belanja Bahan")
    with st.form("belanja"):
        ket = st.text_input("Beli Apa?")
        nom = st.number_input("Habis Berapa?", min_value=0)
        if st.form_submit_button("Simpan"):
            new_exp = pd.DataFrame([{
                "Tanggal": datetime.now().strftime("%Y-%m-%d"),
                "Keterangan": ket,
                "Nominal": nom,
                "Tipe": "KELUAR"
            }])
            existing_data = conn.read(worksheet="Sheet1")
            updated_df = pd.concat([existing_data, new_exp], ignore_index=True)
            conn.update(worksheet="Sheet1", data=updated_df)
            st.success("Pengeluaran tercatat!")

# === HALAMAN LAPORAN ===
elif menu == "📈 Laporan":
    st.title("Laporan Keuangan (Real-time GSheets)")
    data = conn.read(worksheet="Sheet1")
    if not data.empty:
        st.dataframe(data)
        masuk = data[data['Tipe'] == 'MASUK']['Nominal'].sum()
        keluar = data[data['Tipe'] == 'KELUAR']['Nominal'].sum()
        st.metric("Untung Bersih", f"Rp {masuk - keluar:,}", delta=f"Omzet: {masuk:,}")