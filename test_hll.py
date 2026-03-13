import random
from hyperloglog import HyperLogLog

# ============================================================
# TEST 1: Büyük Veri Simülasyonu ile Kardinalite Tahmini
# ============================================================
print("=" * 55)
print("  TEST 1: Büyük Veri Simülasyonu")
print("=" * 55)

# 0 ile 1.000.000 arasında rastgele 500.000 sayı üret (tekrar edebilir)
veri_sayisi = 500_000
aralik = 1_000_000
veri_seti = [random.randint(0, aralik) for _ in range(veri_sayisi)]

# Gerçek benzersiz eleman sayısını Python set ile bul (ground truth)
gercek_benzersiz = len(set(veri_seti))

# HLL nesnesi oluştur ve tüm veriyi ekle
hll = HyperLogLog(m=2048)
for eleman in veri_seti:
    hll.add(eleman)

# Kardinalite tahminini al
hll_tahmini = hll.count()

# Hata analizi
fark = abs(gercek_benzersiz - hll_tahmini)
hata_yuzdesi = (fark / gercek_benzersiz) * 100

print(f"  Üretilen toplam veri sayısı : {veri_sayisi:>10,}")
print(f"  Gerçek benzersiz eleman     : {gercek_benzersiz:>10,}")
print(f"  HLL tahmini                 : {hll_tahmini:>10,}")
print(f"  Fark                        : {fark:>10,}")
print(f"  Hata yüzdesi                : {hata_yuzdesi:>9.2f}%")
print()

# ============================================================
# TEST 2: Merge (Birleştirme) Testi
# ============================================================
print("=" * 55)
print("  TEST 2: Merge (Birleştirme) Testi")
print("=" * 55)

# Birinci HLL: 0 ile 50.000 arası tam sayılar
hll_birinci = HyperLogLog(m=2048)
for sayi in range(0, 50_000):
    hll_birinci.add(sayi)

# İkinci HLL: 50.000 ile 100.000 arası tam sayılar
hll_ikinci = HyperLogLog(m=2048)
for sayi in range(50_000, 100_000):
    hll_ikinci.add(sayi)

# Birleştirmeden önce bireysel tahminleri yazdır
tahmin_birinci = hll_birinci.count()
tahmin_ikinci  = hll_ikinci.count()

print(f"  HLL-1 tahmini (0–50.000)    : {tahmin_birinci:>10,}")
print(f"  HLL-2 tahmini (50.000–100.000): {tahmin_ikinci:>8,}")

# İki HLL'yi birleştir (merge)
hll_birinci.merge(hll_ikinci)
birlesik_tahmin = hll_birinci.count()

# Gerçek birleşik küme büyüklüğü: 100.000 (0'dan 99.999'a)
gercek_birlesik = 100_000
fark_merge = abs(gercek_birlesik - birlesik_tahmin)
hata_merge  = (fark_merge / gercek_birlesik) * 100

print(f"  Birleşik HLL tahmini        : {birlesik_tahmin:>10,}")
print(f"  Gerçek birleşik küme boyutu : {gercek_birlesik:>10,}")
print(f"  Fark                        : {fark_merge:>10,}")
print(f"  Hata yüzdesi                : {hata_merge:>9.2f}%")
print("=" * 55)
