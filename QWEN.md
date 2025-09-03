# Project Requirements

## Buatkan struktur proyek awal yang lengkap untuk aplikasi FastAPI menggunakan Python

Buatkan di direktori baru bernama 'insignia-be'.

Proyek ini harus memenuhi spesifikasi berikut:

### Framework Utama:
Gunakan FastAPI.

### Server Web:
Konfigurasikan proyek agar berjalan dengan 'uv' sebagai server ASGI.

### Database:
Integrasikan SQLAlchemy sebagai ORM untuk terhubung dengan database PostgreSQL.

Siapkan Alembic untuk menangani migrasi database.

Buatkan model SQLAlchemy untuk dua tabel berikut sesuai spesifikasi:

#### Tabel tasks:
Harus berisi kolom-kolom seperti:
- id (UUID, primary key)
- name (string)
- schedule (string untuk cron)
- webhook_url (string)
- payload (JSONB)
- max_retry (integer)
- status (string/enum)
- created_at (timestamp)
- updated_at (timestamp)

#### Tabel task_logs:
Harus berisi:
- id (UUID, primary key)
- task_id (foreign key ke tabel tasks)
- execution_time (timestamp)
- status (string/enum, misal: 'success', 'failed')
- retry_count (integer)
- message (text)
- created_at (timestamp)

Pastikan ada relasi one-to-many dari tabel tasks ke task_logs.

### Struktur Proyek:
Buat struktur modular dengan direktori dan file berikut:

```
/app
  /api (untuk router/endpoint API)
  /models (untuk model SQLAlchemy yang dibuat di atas)
  /schemas (untuk skema Pydantic yang sesuai dengan model)
  /core (untuk pengaturan konfigurasi)
  main.py (titik masuk aplikasi dengan endpoint sederhana '/' yang mengembalikan {'message': 'Hello World'})

/alembic (untuk skrip migrasi)
/tests (dengan tes dasar untuk endpoint '/' menggunakan pytest)
```

### Kontainerisasi:
Sediakan 'Dockerfile' multi-tahap yang dioptimalkan untuk production.

Buat file 'docker-compose.yml' untuk menjalankan dua layanan:
- 'backend' (aplikasi FastAPI ini)
- 'db' (menggunakan image resmi postgres:15-alpine)

Pengaturan ini harus bisa dijalankan dengan satu perintah.

### Konfigurasi:
Sertakan file '.env.example' dengan placeholder untuk:
- DATABASE_URL
- POSTGRES_USER
- POSTGRES_PASSWORD
- POSTGRES_DB

Gunakan manajemen Pengaturan (Settings) dari Pydantic untuk memuat variabel lingkungan.

### Dependensi:
Buat file 'requirements.txt' yang berisi semua paket yang dibutuhkan:
- fastapi
- uv
- sqlalchemy
- psycopg2-binary
- alembic
- python-dotenv
- pydantic-settings
- pytest

### Kualitas Kode:
Sertakan file konfigurasi untuk:
- 'black' (pyproject.toml)
- 'ruff' untuk format kode dan linting demi memastikan kode yang bersih dan mudah dikelola

Buatkan konten untuk setiap file tersebut.