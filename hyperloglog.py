import hashlib
import math

class HyperLogLog:
    def __init__(self, m=2048):
        """
        HyperLogLog örneğini başlatır.

        :param m: Kova/yazmaç sayısı (2'nin kuvveti olmalıdır). Varsayılan değer 2048'dir.
        """
        # m'nin 2'nin kuvveti olup olmadığını kontrol et
        if not (m > 0 and (m & (m - 1)) == 0):
            raise ValueError("Kova sayısı (m) 2'nin kuvveti olmak zorundadır.")

        self.m = m  # Yazmaç (register) sayısı
        self.registers = [0] * m  # Tüm yazmaçları 0 ile başlat

        # Kova indeksini belirlemek için gereken bit sayısı (log2(m))
        # Örn: m=2048 → b=11 bit
        self.b = int(math.log2(m))

    def _hash(self, deger):
        """
        Girdi değerini SHA256 kullanarak hash'ler ve 64-bit tam sayı döndürür.

        :param deger: Hash'lenecek değer.
        :return: Girdi değerinin 64-bit tam sayı hash'i.
        """
        # Değeri string'e çevir ve UTF-8 ile bayta kodla
        deger_bayt = str(deger).encode('utf-8')

        # Değerin SHA256 hash'ini hesapla
        hash_bayt = hashlib.sha256(deger_bayt).digest()

        # Hash'in ilk 8 baytını 64-bit tam sayıya çevir
        hash_tam_sayi = int.from_bytes(hash_bayt[:8], byteorder='big')

        return hash_tam_sayi

    def add(self, eleman):
        """
        Veri kümesine yeni bir eleman ekler ve ilgili yazmacı günceller.

        :param eleman: Veri kümesine eklenecek eleman.
        """
        # Elemanı hash'le ve 64-bit tam sayı olarak al
        hash_degeri = self._hash(eleman)

        # İlk b biti alarak kova indeksini belirle
        # Örn: b=11 ise hash'in en yüksek 11 biti kova numarasını verir
        kova_indeksi = hash_degeri >> (64 - self.b)

        # Kova indeksi belirlendikten sonra kalan bitleri al
        # Kalan bitler: hash'in alt (64 - b) biti
        kalan_bitler = hash_degeri & ((1 << (64 - self.b)) - 1)

        # Kalan bitlerdeki baştan itibaren ardışık sıfır sayısını bul (Leading Zeros)
        # +1 eklenir çünkü HLL'de sıfır olmayan ilk bitin konumu sayılır
        if kalan_bitler == 0:
            # Tüm bitler sıfırsa maksimum değeri ata
            basta_sifir_sayisi = (64 - self.b) + 1
        else:
            # Kalan bitlerdeki bit uzunluğunu hesapla ve sıfır sayısını bul
            basta_sifir_sayisi = (64 - self.b) - kalan_bitler.bit_length() + 1

        # Bulunan sıfır sayısı, kovadaki mevcut değerden büyükse yazmacı güncelle
        # (Her kovada daima maksimum değer tutulur)
        if basta_sifir_sayisi > self.registers[kova_indeksi]:
            self.registers[kova_indeksi] = basta_sifir_sayisi

    def count(self):
        """
        Veri kümesindeki benzersiz eleman sayısını (kardinaliteyi) tahmin eder.

        :return: Tahmini kardinalite değeri (int).
        """
        # --- Alpha Sabiti ---
        # Alpha, HLL algoritmasının sistematik sapmasını düzelten bir katsayıdır.
        # m değerine göre standart sabitler veya genel formül kullanılır.
        if self.m == 16:
            alfa = 0.673
        elif self.m == 32:
            alfa = 0.697
        elif self.m == 64:
            alfa = 0.709
        else:
            # Büyük m değerleri için genel formül
            alfa = 0.7213 / (1.0 + 1.079 / self.m)

        # --- Harmonik Ortalama ile Ham Tahmin ---
        # Z = Σ 2^(-register[i]) toplamı hesaplanır
        z_toplami = sum(2.0 ** (-r) for r in self.registers)

        # Ham tahmin formülü: E = alpha * m^2 / Z
        ham_tahmin = alfa * (self.m ** 2) / z_toplami

        # --- Küçük Aralık Düzeltmesi (Small Range Correction) ---
        # Eğer ham tahmin 2.5 * m'den küçük veya eşitse Linear Counting kullan.
        # Bu durum, veri kümesinin çok küçük olduğu ve boş kova bulunduğu anlamına gelir.
        if ham_tahmin <= 2.5 * self.m:
            # Boş yazmaç (register) sayısını bul
            bos_kova_sayisi = self.registers.count(0)

            if bos_kova_sayisi > 0:
                # Linear Counting formülü: m * ln(m / V)
                # V: boş kova sayısı
                duzeltilmis_tahmin = self.m * math.log(self.m / bos_kova_sayisi)
            else:
                # Boş kova yoksa ham tahmini kullan
                duzeltilmis_tahmin = ham_tahmin

        # --- Büyük Aralık Düzeltmesi (Large Range Correction) ---
        # Hash uzayı 2^32 sınırına yaklaşıldığında çarpışma ihtimali artar.
        # Bu durumda logaritmik düzeltme uygulanır.
        elif ham_tahmin > (1.0 / 30.0) * (2 ** 32):
            duzeltilmis_tahmin = -(2 ** 32) * math.log(1.0 - ham_tahmin / (2 ** 32))

        # --- Orta Aralık: Düzeltme Gerekmez ---
        else:
            duzeltilmis_tahmin = ham_tahmin

        return int(duzeltilmis_tahmin)

    def merge(self, diger_hll):
        """
        Başka bir HyperLogLog nesnesini mevcut nesneyle birleştirir.
        Birleştirme sonucunda mevcut nesnenin yazmaçları güncellenir.

        :param diger_hll: Birleştirilecek diğer HyperLogLog nesnesi.
        :raises ValueError: İki HLL nesnesinin kova sayısı farklıysa hata fırlatılır.
        """
        # Birleştirilecek HLL nesnesinin kova sayısının aynı olup olmadığını kontrol et
        if self.m != diger_hll.m:
            raise ValueError(
                f"Birleştirilecek HLL nesnelerinin kova sayıları eşit olmalıdır. "
                f"Mevcut: {self.m}, Gelen: {diger_hll.m}"
            )

        # Her yazmaç için iki HLL'deki değerleri karşılaştır ve en büyüğünü al
        # En uzun sıfır serisini (dolayısıyla en büyük değeri) daima korumalıyız
        for indeks in range(self.m):
            self.registers[indeks] = max(self.registers[indeks], diger_hll.registers[indeks])