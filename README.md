# 🌊 Website Penjualan Tanah Labuan Bajo

Website profesional untuk listing dan penjualan tanah di Labuan Bajo, Nusa Tenggara Timur.

## Fitur Lengkap

- ✅ **Halaman Publik** — Tampilkan semua listing tanah dengan desain premium
- ✅ **Detail Tanah** — Foto gallery, peta lokasi, info legal, tombol WA langsung
- ✅ **Login Admin** — Dua level: Superadmin & Admin
- ✅ **Upload Tanah** — Judul, lokasi, luas, harga, sertifikat, foto, dsb
- ✅ **Pin Lokasi di Peta** — Klik peta Leaflet untuk titik koordinat akurat
- ✅ **Ganti Background** — Warna solid atau upload gambar latar
- ✅ **Tombol WhatsApp** — Pesan otomatis ke nomor admin
- ✅ **Kelola Admin** — Superadmin bisa tambah/hapus akun admin

## Cara Menjalankan

### 1. Install Python (3.8+)
Pastikan Python sudah terinstall di komputer Anda.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Jalankan Aplikasi
```bash
python app.py
```

### 4. Buka di Browser
```
http://localhost:5000
```

## Akun Default

| Username    | Password  | Role       | Akses                        |
|-------------|-----------|------------|------------------------------|
| superadmin  | admin123  | Superadmin | Semua fitur + kelola admin   |
| admin       | admin456  | Admin      | Kelola listing + pengaturan  |

> ⚠️ **Ganti password setelah pertama login!** (edit di database atau buat akun baru)

## Struktur Folder

```
labuan-bajo-land/
├── app.py                 # Aplikasi utama Flask
├── requirements.txt       # Dependensi Python
├── land.db                # Database SQLite (dibuat otomatis)
├── static/
│   ├── uploads/           # Foto-foto tanah
│   └── backgrounds/       # Gambar latar belakang
└── templates/
    ├── base.html          # Template dasar publik
    ├── index.html         # Halaman beranda
    ├── detail.html        # Detail tanah
    └── admin/
        ├── login.html     # Halaman login
        ├── base_admin.html
        ├── dashboard.html
        ├── add_land.html
        ├── edit_land.html
        ├── settings.html
        └── users.html
```

## Teknologi

- **Backend**: Python Flask
- **Database**: SQLite
- **Peta**: Leaflet.js + OpenStreetMap
- **Icon**: Font Awesome
- **Font**: Playfair Display + DM Sans
- **WhatsApp**: wa.me deep link

## Deploy ke Server (opsional)

Untuk deploy ke VPS/server:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

---
*Dibuat dengan ❤️ untuk Labuan Bajo, NTT*
