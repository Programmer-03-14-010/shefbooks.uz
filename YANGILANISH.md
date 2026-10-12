# SHEFBOOKS — 2-yangilanish: promokod, vaqtli aksiya, formatlar, audio

## Ishga tushirish (muhim)
```
python manage.py migrate
python manage.py collectstatic --noinput
```
`migrate` yangi jadvallarni yaratadi va **SHEF15 (15%)** hamda **AKROMXOJA20 (20%)** promokodlarini qo'shadi.
Ularni admin panelda **Promokodlar** bo'limidan o'zgartirish yoki o'chirish mumkin.

## Admin panelda nimalar qilinadi
**1. Promokod yaratish** — Promokodlar → Qo'shish. Foiz yoki aniq summa, minimal buyurtma summasi, umumiy limit, muddat, "bitta foydalanuvchi 1 marta" tanlanadi. Ishlatilgan soni avtomatik sanaladi.

**2. Vaqtli aksiya (taymerli banner)** — Vaqtli aksiyalar → Qo'shish: nom, chegirma %, to'plamdagi kitoblar, boshlanish/tugash vaqti. Aksiya davomida bosh sahifada taymerli banner chiqadi.
- "To'plamni olish" tugmasi barcha kitoblarni savatga soladi, chegirma savatda avtomatik qo'llanadi (barcha kitoblar savatda bo'lsa).
- Bitta kitob olib tashlansa chegirma yo'qoladi va savatda "to'plamni to'ldiring" taklifi chiqadi.
- Vaqt tugagach banner o'zi yo'qoladi.

**3. Kitobga audio / e-kitob / parcha / mundarija** — Kitoblar → kitobni oching:
- *Audio kitob*: narxni kiriting va faylni yuklang (mp3, m4a, wav...). Ixtiyoriy qisqa **audio parcha** hamma uchun tinglanadi.
- *E-kitob*: narx + PDF/EPUB.
- *Parcha* va *Mundarija* (har bo'lim yangi qatordan).
Narx kiritilgan formatlar kitob sahifasida va "Tez ko'rish" oynasida tanlov sifatida paydo bo'ladi.

**4. Fikrlar** — foydalanuvchi bir kitobga 5 tagacha izoh qoldiradi va o'zinikini o'chira oladi. Admin hamma izohlarni ko'radi/o'chiradi.

## Xaridorlar uchun
- Kitob kartochkasida **Tez ko'rish**: formatlar, sharh/tavsif, parcha, mundarija, savatga qo'shish.
- Savatda **promokod** maydoni; chegirma avval to'plamga, keyin promokodga qo'llanadi.
- E-kitob/audio sotib olinsa yetkazib berish punkti so'ralmaydi. Admin to'lovni tasdiqlagach (buyurtmada "To'langan" belgisi) fayllar **Kutubxonam** sahifasida ochiladi.

## Xavfsizlik va server
- To'liq audio va e-kitoblar `private_media/` papkasida saqlanadi, **ochiq URL yo'q**; faqat to'lovi tasdiqlangan egasi (yoki admin) ochadi. Veb-serverda (nginx) bu papkani hech qachon ochiq qilmang va zaxira nusxasiga qo'shing.
- Katta audio yuklash uchun nginx'da `client_max_body_size 200M;` kabi limitni oshiring.
- Admin sahifasida yuklangan audio/e-kitob yonidagi "Hozirgi fayl" havolasi ochilmaydi (fayl yopiq saqlangani uchun) — bu normal.

## Telefon uchun moslik
360, 390 va 430px kenglikda 11 ta asosiy sahifa va "Tez ko'rish" oynasi tekshirildi, gorizontal siljish yo'q.

## Tuzatilgan xato
Birinchi kitob savatga qo'shilganda sarlavhadagi savat soni 0 bo'lib qolardi (animatsiya skripti bilan to'qnashuv) — tuzatildi.

---

# SHEFBOOKS — yangi dizayn: o'rnatish yo'riqnomasi

## 1. Qanday o'rnatiladi
1. Eski loyiha papkangizni zaxiraga oling.
2. Ushbu zip ichidagi fayllarni loyiha ustiga ko'chiring. **`.env` va `media/` papkasini o'zingizniki bilan qoldiring** (zipda ular yo'q).
3. Terminalda:
   ```
   python manage.py migrate          # yangi maydonlar (muallif, eski narx, reyting...) qo'shiladi
   python manage.py collectstatic --noinput
   python manage.py runserver
   ```
4. Admin panelda (`/hahaha/`) kitoblarga **muallif, nashriyot, eski narx (chegirma uchun), "Bosh sahifada ko'rsatish"** maydonlarini to'ldiring — bosh sahifa shu ma'lumotlar bilan boyiydi.

## 2. Ixtiyoriy sozlamalar (.env ga qo'shish mumkin; bo'lmasa avvalgi qiymatlar ishlaydi)
```
SHOP_PHONE=+998 95 897 54 52
SHOP_EMAIL=support@domain.com
SHOP_INSTAGRAM=https://www.instagram.com/shefbooks/
SHOP_YOUTUBE=https://www.youtube.com/@Shefbooks
SHOP_TELEGRAM=https://t.me/...
UZPOST_DELIVERY_FEE=20000
PAYMENT_CARD_NUMBER=5614 6812 5665 1260
PAYMENT_CARD_HOLDER=IBROHIMOV AKROMXO'JA
```

## 3. Nimalar o'zgardi
**Dizayn:** qora–sariq yangi tizim (`assets/css/shef.css`), "SHEFBOOKS" sariq yozuv qora fonda, barcha sahifalar qayta yozildi, mobil pastki menyu, savatga AJAX qo'shish, toast xabarlar.

**Yangi funksiyalar:** qidiruv (nom/muallif/nashriyot), saralash, narx/til/mavjudlik filtri, chegirma belgisi, "oz qoldi" ogohlantirishi, kitob reytingi va fikrlar, o'xshash kitoblar, mini-savat, buyurtma holati (timeline), muvaffaqiyat sahifasi, "Biz haqimizda" sahifasi.

**Xatolar tuzatildi / xavfsizlik:**
- To'lov va muvaffaqiyat sahifasini endi faqat buyurtma egasi ocha oladi (oldin istalgan buyurtma raqami bilan ochilardi).
- `next` orqali boshqa saytga yo'naltirish yopildi.
- Savat/xohish o'zgarishlari faqat POST orqali (CSRF himoyasi).
- Savatdagi jami summa miqdorni hisobga oladi; ombor qoldig'i buyurtma paytida qayta tekshiriladi.
- UZPOST uchun pochta to'lovi cheki endi haqiqatan so'raladi (oldin formada yo'q edi).
- Telefon raqam tekshiriladi va `+998...` ko'rinishiga keltiriladi.
- Kitob sahifasi havolasi (`get_absolute_url`) va blogdagi kirish yo'naltirishi tuzatildi.
- Yetkazib berish punktlari (592 ta) `assets/js/pickup-data.js` fayliga ko'chirildi, ma'lumot o'zgarmagan.

## 4. Eslatma
- Eski `assets/css/style.css`, `assets/libs/...` fayllari endi ishlatilmaydi; xohlasangiz o'chirib tashlashingiz mumkin.
- Shriftlar Google Fonts orqali yuklanadi (Playfair Display + Manrope).
