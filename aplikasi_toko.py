import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- 1. DATA USER ---
USERS = {
    "owner": "admin123", 
    "kasir": "kasir123"
}

# --- 2. DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('toko_umkm.db')
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS produk (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama_barang TEXT NOT NULL,
            stok INTEGER NOT NULL,
            harga_jual INTEGER NOT NULL
        )
    ''')
    
    # UPDATE TABEL TRANSAKSI: Menambah kolom diskon & total_akhir
    c.execute('''
        CREATE TABLE IF NOT EXISTS transaksi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tanggal TEXT,
            nama_barang TEXT,
            jumlah INTEGER,
            harga_normal INTEGER,
            diskon_per_item INTEGER, 
            total_akhir INTEGER,
            metode_pembayaran TEXT,
            kasir_name TEXT,
            group_id TEXT
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS pengeluaran (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tanggal TEXT,
            keterangan TEXT,
            nominal INTEGER
        )
    ''')
    conn.commit()
    return conn

def ambil_semua_barang(conn):
    return pd.read_sql_query("SELECT * FROM produk", conn)

# --- 3. LOGIKA SISTEM ---
if 'keranjang' not in st.session_state:
    st.session_state['keranjang'] = []
if 'is_logged_in' not in st.session_state:
    st.session_state['is_logged_in'] = False
if 'user_role' not in st.session_state:
    st.session_state['user_role'] = None
if 'username' not in st.session_state:
    st.session_state['username'] = None

def login(username, password):
    if username in USERS and USERS[username] == password:
        st.session_state['is_logged_in'] = True
        st.session_state['username'] = username
        st.session_state['user_role'] = "owner" if username == "owner" else "kasir"
        st.rerun()
    else:
        st.error("Login Gagal!")

def logout():
    st.session_state['is_logged_in'] = False
    st.session_state['user_role'] = None
    st.session_state['keranjang'] = []
    st.rerun()

def tambah_ke_keranjang(nama, harga_jual, jumlah):
    for item in st.session_state['keranjang']:
        if item['nama_barang'] == nama:
            item['jumlah'] += jumlah
            item['subtotal'] = item['jumlah'] * harga_jual
            return
    st.session_state['keranjang'].append({
        "nama_barang": nama,
        "harga_jual": harga_jual,
        "jumlah": jumlah,
        "subtotal": jumlah * harga_jual
    })

def proses_pembayaran_promo(conn, metode_bayar, total_diskon_transaksi):
    c = conn.cursor()
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        kasir_yg_jaga = st.session_state['username']
        # ID Unik untuk mengelompokkan item dalam satu struk
        group_id = f"TRX-{int(datetime.now().timestamp())}" 
        
        # Hitung total belanjaan kotor (sebelum diskon)
        total_kotor = sum(item['subtotal'] for item in st.session_state['keranjang'])
        
        # Jika diskon lebih besar dari total belanja, error
        if total_diskon_transaksi > total_kotor:
            raise Exception("Diskon tidak boleh lebih besar dari total belanja!")

        # Menghitung proporsi diskon per item (agar laporan rapi)
        # Diskon dipukul rata secara proporsional ke setiap item
        
        total_akhir_transaksi = 0
        
        for item in st.session_state['keranjang']:
            nama = item['nama_barang']
            qty = item['jumlah']
            subtotal_item = item['subtotal']
            
            # 1. Cek Stok
            c.execute("SELECT stok FROM produk WHERE nama_barang = ?", (nama,))
            result = c.fetchone()
            if not result: raise Exception(f"{nama} hilang!")
            
            stok_db = result[0]
            if stok_db < qty: raise Exception(f"Stok {nama} kurang!")
            
            # 2. Update Stok
            stok_baru = stok_db - qty
            c.execute("UPDATE produk SET stok = ? WHERE nama_barang = ?", (stok_baru, nama))
            
            # 3. Hitung Diskon Per Item (Proporsional)
            # Rumus: (Subtotal Item / Total Kotor) * Total Diskon
            porsi_diskon = int((subtotal_item / total_kotor) * total_diskon_transaksi)
            total_bersih_item = subtotal_item - porsi_diskon
            
            # 4. Simpan Transaksi
            c.execute('''
                INSERT INTO transaksi (tanggal, nama_barang, jumlah, harga_normal, diskon_per_item, total_akhir, metode_pembayaran, kasir_name, group_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (timestamp, nama, qty, subtotal_item, porsi_diskon, total_bersih_item, metode_bayar, kasir_yg_jaga, group_id))
            
            total_akhir_transaksi += total_bersih_item
            
        conn.commit()
        return True, total_akhir_transaksi
    except Exception as e:
        conn.rollback()
        return False, str(e)

# --- 4. TAMPILAN UI ---
st.set_page_config(page_title="Sistem POS Pro Promo", layout="wide")

if not st.session_state['is_logged_in']:
    st.title("🔒 Login Toko")
    with st.form("login_form"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            login(u, p)
    st.stop()

conn = init_db()

# Sidebar
st.sidebar.title(f"User: {st.session_state['username']}")
if st.sidebar.button("Logout"): logout()

pilihan_menu = ["🏪 Mesin Kasir"]
if st.session_state['user_role'] == "owner":
    pilihan_menu += ["💸 Catat Belanja", "📦 Stok Barang", "📈 Laporan Lengkap"]
    
menu = st.sidebar.selectbox("Menu", pilihan_menu)

# === MENU 1: KASIR DENGAN PROMO ===
if menu == "🏪 Mesin Kasir":
    st.title("Mesin Kasir + Promo")
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Katalog")
        df_barang = ambil_semua_barang(conn)
        if not df_barang.empty:
            pil = st.selectbox("Barang", df_barang['nama_barang'].tolist())
            info = df_barang[df_barang['nama_barang'] == pil].iloc[0]
            st.caption(f"Stok: {info['stok']} | Rp{info['harga_jual']:,}")
            qty = st.number_input("Qty", 1, int(info['stok']), 1)
            if st.button("Masuk Keranjang"):
                tambah_ke_keranjang(pil, int(info['harga_jual']), qty)
                st.rerun()
    
    with col2:
        st.subheader("🛒 Struk Belanja")
        if st.session_state['keranjang']:
            df_cart = pd.DataFrame(st.session_state['keranjang'])
            st.dataframe(df_cart, use_container_width=True)
            
            # HITUNGAN HARGA
            subtotal = df_cart['subtotal'].sum()
            st.write(f"Subtotal: **Rp{subtotal:,}**")
            
            st.divider()
            
            # --- FITUR BARU: PROMO / DISKON ---
            st.markdown("##### 🏷️ Potongan Harga / Promo")
            # Kasir input diskon manual (Misal: 5000 karena paket hemat)
            diskon_input = st.number_input("Masukkan Nominal Diskon (Rp)", min_value=0, max_value=subtotal, step=1000)
            
            total_final = subtotal - diskon_input
            
            # Tampilan Total Besar
            st.markdown(f"""
            <div style="background-color:#d4edda; padding:10px; border-radius:10px; text-align:center;">
                <h2 style="color:#155724; margin:0;">Total Bayar: Rp{total_final:,}</h2>
                <small>(Hemat: Rp{diskon_input:,})</small>
            </div>
            """, unsafe_allow_html=True)
            
            st.write("") # Spacer
            metode = st.selectbox("Metode Bayar", ["Cash", "QRIS", "Transfer"])
            
            if st.button("✅ PROSES PEMBAYARAN", type="primary"):
                sukses, hasil = proses_pembayaran_promo(conn, metode, diskon_input)
                if sukses:
                    st.balloons()
                    st.session_state['keranjang'] = []
                    st.success(f"Transaksi Sukses! Total Masuk: Rp{hasil:,}")
                    st.rerun()
                else:
                    st.error(f"Gagal: {hasil}")
            
            if st.button("Batal"):
                st.session_state['keranjang'] = []
                st.rerun()

elif menu == "💸 Catat Belanja":
    st.title("Catat Belanja Bahan")
    with st.form("belanja"):
        tgl = st.date_input("Tanggal")
        ket = st.text_input("Keterangan")
        nom = st.number_input("Nominal (Rp)", min_value=0)
        if st.form_submit_button("Simpan"):
            conn.execute("INSERT INTO pengeluaran (tanggal, keterangan, nominal) VALUES (?,?,?)", 
                         (tgl, ket, nom))
            conn.commit()
            st.success("Tersimpan!")

elif menu == "📦 Stok Barang":
    st.title("Kelola Stok")
    with st.form("stok"):
        nm = st.text_input("Nama")
        stk = st.number_input("Stok", 1)
        hrg = st.number_input("Harga Jual", 0)
        if st.form_submit_button("Simpan"):
            conn.execute("INSERT INTO produk (nama_barang, stok, harga_jual) VALUES (?,?,?)", (nm, stk, hrg))
            conn.commit()
            st.success("Barang ditambahkan!")
            st.rerun()
    st.dataframe(ambil_semua_barang(conn))

elif menu == "📈 Laporan Lengkap":
    st.title("📊 Laporan Keuangan & Pengeluaran")
    
    # Filter Tanggal
    tgl_pilih = st.date_input("Pilih Tanggal Laporan", datetime.now())
    tgl_str = tgl_pilih.strftime("%Y-%m-%d")
    
    # 1. AMBIL DATA TRANSAKSI (PENJUALAN)
    # Kita gunakan LIKE agar mencakup jam/menit di hari yang sama
    df_trx = pd.read_sql_query(f"SELECT * FROM transaksi WHERE tanggal LIKE '{tgl_str}%'", conn)
    
    # 2. AMBIL DATA PENGELUARAN (BELANJA)
    # Kita pastikan query mengambil semua kolom dari tabel pengeluaran
    df_out = pd.read_sql_query(f"SELECT * FROM pengeluaran WHERE tanggal LIKE '{tgl_str}%'", conn)
    
    # HITUNGAN RINGKASAN
    total_omzet = df_trx['total_akhir'].sum() if not df_trx.empty else 0
    total_keluar = df_out['nominal'].sum() if not df_out.empty else 0
    
    # TAMPILAN METRIC
    c1, c2, c3 = st.columns(3)
    c1.metric("Omzet Bersih (Pemasukan)", f"Rp {total_omzet:,}")
    c2.metric("Total Belanja (Pengeluaran)", f"Rp {total_keluar:,}", delta_color="inverse")
    c3.metric("Profit Bersih", f"Rp {total_omzet - total_keluar:,}")

    st.divider()

    # TABEL DETAIL
    tab_jual, tab_belanja = st.tabs(["🛒 Detail Penjualan", "💸 Detail Belanja Bahan"])
    
    with tab_jual:
        if not df_trx.empty:
            st.dataframe(df_trx[['tanggal', 'nama_barang', 'jumlah', 'total_akhir', 'kasir_name']], use_container_width=True)
        else:
            st.info("Tidak ada penjualan pada tanggal ini.")

    with tab_belanja:
        if not df_out.empty:
            # Mengubah urutan kolom agar lebih enak dibaca
            st.write(f"Daftar Belanja Tanggal {tgl_str}:")
            st.dataframe(df_out[['tanggal', 'keterangan', 'nominal']], use_container_width=True)
        else:
            st.warning("Data Belanja tidak ditemukan. Pastikan Anda sudah menginput di menu 'Catat Belanja'.")        