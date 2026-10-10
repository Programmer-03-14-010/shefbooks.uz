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
