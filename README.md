# Ishchilar Tizimi

Hodimlarni boshqarish va ish vaqtini kuzatish tizimi (Django).

## Loyiha haqida

Bu tizim quyidagi imkoniyatlarni taqdim etadi:
- Hodimlarni ro'yxatdan o'tkazish va boshqarish
- Ish vaqtini kuzatish (check-in/check-out)
- Kechikish va erta ketishni hisoblash
- Oylik hisobotlar
- Google Sheets integratsiyasi
- RFID karta orqali identifikatsiya

## Texnologiyalar

- Python 3.12
- Django 5.1
- SQLite
- Bootstrap 5
- Google Sheets API

## O'rnatish

1. Repozitoriyani klonlash:
```bash
git clone https://github.com/abdurahmonovaoy/ishchilar_tizimi.git
cd ishchilar_tizimi/pbl
```

2. Virtual muhit yaratish:
```bash
python -m venv my_env
source my_env/bin/activate  # Linux/Mac
my_env\Scripts\activate     # Windows
```

3. Kerakli kutubxonalarni o'rnatish:
```bash
pip install -r requirements.txt
```

4. `.env` faylini yaratish:
```bash
cp .env.example .env
# .env faylini tahrirlang
```

5. Ma'lumotlar bazasini sozlash:
```bash
python manage.py migrate
```

6. Superuser yaratish:
```bash
python manage.py createsuperuser
```

7. Serverni ishga tushirish:
```bash
python manage.py runserver
```

## Tarmoqda ishga tushirish

Lokal tarmoqda boshqa qurilmalardan foydalanish uchun:
```bash
python manage.py runserver 0.0.0.0:8000
```

## Loyiha tuzilishi

```
pbl/
├── hodimlar/           # Asosiy ilova
│   ├── models.py       # Ma'lumotlar modellari
│   ├── views.py        # Ko'rinishlar
│   ├── forms.py        # Formalar
│   ├── urls.py         # URL yo'nalishlari
│   └── templates/      # HTML shablonlar
├── ishchilar_tizimi/   # Loyiha sozlamalari
│   ├── settings.py
│   └── urls.py
└── manage.py
```

## Asosiy funksiyalar

### Hodimlar
- Hodim qo'shish/tahrirlash/o'chirish
- Lavozimlar: Tikuvchi, Kesuvchi, Mexanik, Ish boshqaruvchi
- Telefon raqami validatsiyasi (+998 format)
- RFID karta UID orqali identifikatsiya

### Ish vaqti
- Check-in/Check-out qayd etish
- Kechikish hisoblash (08:00 dan keyin)
- Erta ketish hisoblash (17:00 dan oldin)
- Ortiqcha ish vaqtini hisoblash

### Hisobotlar
- Kunlik holat
- Oylik hisobotlar
- Google Sheets ga eksport

## Litsenziya

MIT License
