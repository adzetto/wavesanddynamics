# wavesanddata.com yeniden kurulumu

Dr. Korkut Kaynardağ'ın kişisel akademik sitesinin Wix dışında yeniden kurulması.
Bağımsız, ücretli iş. Bu dosya işin kaydı: ne istendi, ne konuşuldu, ne karar verildi,
ne bekliyoruz.

Son güncelleme: 21 Eylül 2026 (taslak çözümlemesi + Dropbox içeriği)

---

## 1. Müşteri

**Dr. Korkut Kaynardağ**, Dr. Öğr. Üyesi, İYTE İnşaat Mühendisliği, Oda C220.
Tel 0232 750 6813, korkutkaynardag@iyte.edu.tr, WhatsApp +1 512 300 4065 (Amerikan numarası).
LinkedIn: linkedin.com/in/korkutkaynardag

Alanı: yapısal sağlık izleme, yapısal dinamik, akustik dalga yayılımı, sinyal işleme,
makine öğrenmesi, optimizasyon. Doktorası UT Austin'de, ray hatlarında kusur tespiti üzerine.

**Nasıl geldi:** Tolga Ercan Hoca aracı oldu (14 Eylül). 21 Eylül'de mail ile iletişime
geçildi, aynı gün WhatsApp'a taşındı.

---

## 2. Hocanın istedikleri

Kendi ifadeleriyle:

> "Ben tüm içeriği ve figürleri Claude'den hazırladım zaten, bir tek siteyi build etmesi
> kalıyor. Aynen Wix dışında kurmak istiyorum, bir de mümkün olduğu kadar yeni kontent
> eklemeyi kolay hale getirecek şekilde."

> "Bu taslağı beğenmiştim mesela, renkler dizayn falan, sol kısımda menü olacak hep."

> "İçerikleri Word olarak hazırladım, siteye koyarken belki PDF'e çevirip kimse PDF
> olduğunu anlamadan scroll down yapar, ya da siteye gömebilirsin. Backend'te hangisi daha
> güzel olacaksa. Bir tek bunları editlemem, ya da benzeri başka bir section siteye
> eklemem kolay olsun."

> "Bölüm dışı kendi sitem olduğu için, independent iş olarak alabilirsin, ücretini
> belirleyebileceğin bir şekilde."

Özet:
1. Wix'ten çıkmak. Şu an alan adını tutmak için ayda 400 dolar ödediğini söylüyor
   (rakam teyit edilmedi, yüksek duruyor).
2. Sol tarafta sabit menü. Beğendiği bir tasarım var, PPT'sinden Lovable'ın ürettiği.
3. Yeni bölüm eklemek ve mevcutları düzenlemek kolay olsun. Asıl şart bu.
4. İçerik hazır, Word dosyaları halinde, şekilleriyle birlikte.

---

## 3. Verilen kararlar

**PDF gömme değil, gerçek sayfa.** Hoca "sen karar ver, uzman sensin" dedi. Gerekçeler:
telefonda gömülü PDF okunmuyor ve ziyaretçilerin çoğu telefondan geliyor; PDF içindeki
metin Google'da doğru dürüst çıkmıyor, oysa bu eğitim bölümlerini insanlar öğrensin diye
yazdı, sitenin ona en büyük getirisi arama sonuçları olacak; gerçek sayfada bölüm
bağlantısı, sayfa içi içindekiler ve şekil referansı çalışıyor. Her bölümün başına
"PDF olarak indir" bağlantısı da konacak, ikisinden de vazgeçilmiyor.

**Statik site.** Astro düşünülüyor. Sayfalar önceden üretilir, sunucu tarafında iş yok.
Cloudflare Pages'te barındırma ücretsiz. Alan adı hocada kalır.

**İçerik formatı: Markdown, denklemler LaTeX (KaTeX).** Muhammet önce ".tex olarak gömeyim"
diye sordu, hoca "güzel göründüğü sürece sorun değil" dedi. Ama LaTeX'i düzenleme formatı
yapmak hocaya kolaylık değil yük olur, Word kullanıyor. Doğru bileşim: yapı Markdown,
sadece denklemler LaTeX yazımıyla.

**Tek kaynak Word.** Uzun bölümlerin aslı hocanın Word dosyası olur. Değişiklik Word'de
yapılır, panele yeniden yüklenir, site kendini günceller. Panelden doğrudan düzenleme
sadece küçük düzeltmeler için. Aksi halde hangi kopyanın güncel olduğu karışır.

**Panel ikinci aşama.** Önce site kurulup içerik yerleşsin, yükleme paneli sonra.
Aksi halde teslim uzar.

**Wix MCP kuruldu, giriş bekliyor.** `claude mcp add wix -- npx -y @wix/mcp --wixCliAuth`
çalıştırıldı. Kimlik doğrulaması OAuth ile: `npx @wix/cli login` tarayıcıda açılıyor ve
tokeni `~/.wix/auth/account.json` dosyasına yazıyor. Şifre paylaşımı gerektirmiyor. Giriş
Muhammet'in kendi Wix hesabına yapılır; hocanın sitesini görebilmek için hocanın onu
katkıda bulunan olarak davet etmesi gerekir. Muhtemelen gerek de kalmayacak, içerik zaten
elimizde.

**Wix şifresi alınmayacak.** Hoca şifresini vermeyi teklif etti. Kabul edilmedi: hesapta
fatura bilgileri var, sorumluluk doğurur, Wix de izin vermiyor. Gerekirse Wix panelinden
Roles and Permissions ile katkıda bulunan daveti istenecek. Zaten gerek kalmadı, aşağıya
bakınız.

---

## 4. Onaylanan tasarım: Lovable taslağı

Hoca 21 Eylül'de yedi video ve bir fotoğraf gönderdi, "Bu taslağı beğenmiştim mesela, renkler
dizayn falan, sol kısımda menü olacak hep" dedi. Hepsi telefonla monitörden çekilmiş, ekrandaki
saat 15 Eylül 2026, 10:07-10:09. 152 karenin hepsi tek tek okundu; çıktılar
`reference/analysis/` altında, ham medya `reference/design-mockup/` altında.

**Taslak Lovable'da duruyor.** Adres çubuğu v02'de baştan sona okunuyor:

```
https://lovable.dev/chats/9994de28-52ce-4af7-8d44-37ec65de63bb
       ?artifact=project%3A34000a66-3304-4430-a914-5c4a1656cce7
```

Proje adı **Korkut's Research Hub**, sohbet başlığı **"Build webpage with provided files"**.
Tarayıcı Edge, yan sekme Zimbra. Sohbet başlığı "sağlanan dosyalarla web sayfası kur" demek,
yani Word dosyaları o sohbete yüklenmiş durumda.

**Neden yarım kaldı.** Lovable panelindeki son mesajı: *"ok before going forward, can you publish
this free on wavesanddata.com"*. Lovable "ücretsiz link" ile "Plan custom-domain" seçeneklerini
önerdi; kendi alan adı ücretli planda. Publish düğmesi her karede "Publish" yazıyor,
"Publish changes" değil, yani proje hiç yayınlanmamış. Yanında duran "Upgrade" düğmesi de ücretsiz
planda olduğunu gösteriyor. Sonuç: dışarıdan erişilebilir bir URL yok, kaynak yalnız hocanın
hesabında. "Cok ilerlemedim zaten" dediği nokta tam burası.

**Taslakta sol menü yok — kabuk üstte.** Yedi videonun **233 karesi** yeniden tarandı
(3 fps, hepsi): **233/233'ünde** üstte ince bir şerit var — solda serif `Korkut Kaynardag, PhD`,
**sağ üstte** hamburger. Şerit sayfayla aynı tonda, altında saç teli çizgi. Hiçbir karede
kalıcı sol sütun yok, hiçbirinde üst menü bağlantıları yok: gezinme yalnız hamburgerde.

Fotoğraf (`image01.jpeg`) kalıcı sütun değil, **sayfanın üzerine soldan açılan çekmece**.
Üç bağımsız ölçüm:

1. Arkadaki giriş metni kelime ortasından kesiliyor ("PhD", "hings: mysel", "cs and physi")
   ama satır sonları tam ekran ana sayfayla birebir aynı — içerik daralmamış, üzeri örtülmüş.
2. Çekmecenin sağ kenarında x≈430'da zemin **213 → 172**'ye bir adımda düşüyor (%19).
   Düzgün bir aydınlatma eğimi bunu yapmaz: **karartma perdesi var** (bulanıklık yok, sadece
   karartma). Önceki "perde yok" tespiti yanlıştı.
3. Karede iki ayrı kaydırma çubuğu var.

Lovable baştan sona **masaüstü genişliğinde** açıktı; hamburger tam masaüstü genişliğinde
görünüyor, yani duyarlı daralmadan değil tasarım gereği öyle. **Telefon davranışı hakkında
elimizde hiçbir kare yok.**

Sonuç: hocanın *"sol kısımda menü olacak hep"* cümlesinin taslaktaki tek karşılığı bu çekmece —
menü hep solda açılıyor. Kalıcı sol sütun istiyorsa bu taslağa **ek** bir istek olur.
Tek cümleyle sorulacak.

**Sol menü (tek kaynak: fotoğraf).** Üstte dairesel fotoğraf, altında serif isim, sonra iki satır
unvan (Assistant Professor, Department of Civil Engineering / Izmir Institute of Technology).
Sonra düz bir liste:

Home · About Me · My Research Areas · Gallery · Vibrations and Waves ·
Signal Processing & Optimization (alt etiket: *System Identification · Estimation · Optimization*) ·
Machine Learning · Blog

Liste "Blog"tan sonra kesiliyor, kaydırma çubuğu altında devam olduğunu gösteriyor; Contact
görünmüyor ama sayfası var. Etkin satır üç işareti aynı anda taşıyor: kenardan kenara koyulaşan
zemin, sol kenara yapışık 3px tuğla kırmızısı çubuk, koyulaşan ve kalınlaşan yazı. Köşeler
kare, hap biçimi değil.

**Sayfalar ve rotalar** (rotalar Lovable'ın kendi rota alanından okundu):

| rota | ne var | durum |
|---|---|---|
| `/` (Homepage) | üst etiket "ACADEMIC & RESEARCH PORTFOLIO", H1, tanıtım + portre, `About me →` / `My research areas`, "Why the educational sections exist" (4 maddelik liste, *Aha!* moment), "Explore the topics" 3 kart | tam çekilmiş, altbilgi yok |
| `/about` | Scholar/LinkedIn/ResearchGate satırı, Biography, Download CV, "At a glance — September 2026", "Career timeline" | tam çekilmiş |
| `/research` | Overview, "Research areas" 2×2 kart, "Introductory documents" 4 indirme satırı, "Also on this site" | iki ayrı sürümü çekilmiş, alt %20-25'i görülmedi |
| `/vibrations-waves` | bölüm şablonu, aşağıya bakınız | tam çekilmiş |
| `/contact` | Contact, "Where to find me", "Elsewhere" | son görünen satıra kadar |
| Gallery, Signal Processing, Machine Learning, Blog | menüde var | **hiç çekilmemiş** |

**Bölüm şablonu.** `/vibrations-waves` boş bir sayfa değil, şablonun kendisi: giriş paragrafı →
*The big picture* → *How to learn this topic* → *Recommended books & resources* → *Documents*
(indirme satırı). Üç bölümün gövdesi de `[Content coming soon — …]`. Hocanın "benzeri başka bir
section eklemem kolay olsun" dediği şeyin birebir karşılığı bu. Astro içerik şeması bu dört
başlığı almalı; yeni bölüm eklemek şablonu doldurmak demek olur.

**Renk ve yazı — Word'ün beyaz sayfasıyla kalibre edildi.** Telefonla monitörden çekilmiş
karede mutlak renk okunamaz. Ama elimizde gerçek bir kalibrasyon hedefi var: **aynı oturumda,
aynı monitörde, iki dakika sonra çekilmiş Word videosu** (`15.49.02`) — Word'ün sayfa zemini
saf beyaz. Ölçüm: beyaz kağıt `(215,212,189)` çıkıyor, yani kameranın/monitörün **+26 R-B
sıcak sapması** var. Bu sapma çıkarıldığında:

- **Sayfa zemini: beyazın yalnızca bir tık altında, hafif sıcak fildişi** — yaklaşık `#FBF7F1`.
  Önceki okumadaki koyu krem (`#F5F1E7`) fazla koyu ve fazla sarıydı; **sapmanın kendisiydi.**
  Ana sayfada düğmenin yanındaki zemin, kalibrasyondan sonra doğrudan beyaza oturuyor.
- **Menü, üst şerit ve içerik tek ton.** Ayrı beyaz içerik paneli yok; ayrım yalnız saç teli çizgi.
- Başlıklar: koyu, **soğuk** arduvaz/lacivert, geçiş dönemi serif, normal ağırlık (kalın değil).
- Gövde: orta koyulukta gri, hümanist sans, satır aralığı bol (~1,75).
- **Tek dolu düğme:** ana sayfadaki `About me →`, **çelik/kot mavisi**. Ölçülen ham değer
  `(57,80,96)`, kalibre `#425E75`; ekran fotoğrafı doyumu düşürdüğü için gerçeği bir tık
  daha canlı, `#2F5D8A` civarı. Yanındaki `My research areas` çerçevesiz düz yazı.
- **Tuğla kırmızısı yalnızca küçük detayda:** iletişim ikonları (bina, zarf, iğne),
  *At a glance* rakamları (**12 / 2 / 8**), kariyer tarihleri, çekmecedeki etkin satır çubuğu.
- **Üst etiket kırmızı değil gri:** `ACADEMIC & RESEARCH PORTFOLIO` harf aralıklı gri sans.
- **Bağlantılar ne mavi ne altı çizili.** Kartlar dolgu ile değil saç teli çizgilerle ayrılıyor.
  Gölge yok, hareket yok, köşeler neredeyse kare.

Güvenilmeyecek kareler: `/research` ve `/vibrations-waves` videoları ağır moiré taşıyor
(pembe-yeşil girişim) ve kalibrasyondan sonra bile pembeye kaçıyor; renk için kullanılmadı.
Temiz kaynaklar: `/contact` (`15.47.20`) ve ana sayfa (`15.47.16_2`).

Düzeltme: PPT ikonlarının lacivert/bordosu (`#1B3A6B` / `#8C1A1A`) **Word belgelerinin**
paleti; sayfanın paleti bu değil.

**About sayfasındaki yeni veriler** (Wix'te yok):

- *At a glance — September 2026*: 12 yayımlanmış makale, 2 patent (1 granted, 1 pending), 8 ödül.
  Patentler başka hiçbir kaynakta geçmiyor, listelenmiyor da.
- *Career timeline*: 2026–şimdi Assistant Professor, İYTE (27 Ağustos 2026'dan beri) ·
  2024–2026 Senior AI Engineer, Renesas Electronics America, Maryland ·
  2023–2024 Applied Data Scientist, Transtek International Group, Florida ·
  2016–2023 doktora ve araştırma görevlisi, UT Austin ·
  2013–2016 yüksek lisans, proje ve araştırma görevlisi, Boğaziçi (lisans 2013).

**Wix'e göre ne değişiyor.** `/personal-resume` → `/about`, `/research-portfolio` → `/research`,
`/structural-dynamics-and-wave-propagation` → `/vibrations-waves`; hepsine yönlendirme gerekir.
`/signal-processing-optimization-ml` ikiye bölünüyor: **Signal Processing & Optimization** ve
**Machine Learning** ayrı sayfalar oluyor; bilgi mimarisindeki en büyük değişiklik bu ve ikisi de
hiç çekilmemiş. `/fullscreen-page` gidiyor. Hiçbir sayfada altbilgi yok. Yayın, patent ve ödül
sayılıyor ama hiçbir yerde listelenmiyor. Blog menüde duruyor ama ne liste ne yazı tasarımı var.

**v07: Machine Learning Word dosyası.** `Machine Learning - The Complete Picture and Guide_5`,
9.246 kelime, 12 numaralı bölüm, 40+ sayfa. Word'de MathType, Acrobat ve **Claude** eklentileri
kurulu, otomatik kaydetme kapalı, gövde iki yana yaslı. Dosya adındaki `_5` elle sürümleme, en
yenisini adıyla istemek gerekir. Dönüştürme açısından üç şey önemli:

- **Callout kutuları aslında tek hücreli Word tablosu**, gölgeli paragraf değil. Dönüştürücü
  1×1 tabloyu `<aside class="callout">` yapmalı, `<table>` değil.
- **Şekiller üç ayrı türde:** tablo olarak çizilmiş diyagramlar, gruplanmış Word şekilleri ve
  dışa aktarılmış grafik görselleri. Ortadakiler pandoc'ta da mammoth'ta da sessizce kayboluyor;
  o üç şekil SVG olarak yeniden çizilmeli.
- **Bu belgede denklem yok** ama diğer bölümlerde olacak. MathType denklemleri dışa aktarmadan
  önce Word'ün kendi biçimine (OMML) çevrilmeli, yoksa EMF görsele düşüyor.

Ayrıca metin içinde sürekli "Section 5.3", "Figure 7" göndermeleri var; sitenin Word'e göre en
büyük kazancı bunları çalışan bağlantıya çevirmek olacak.

---

## 4b. KESİN KAYNAK: hocanın kendi sunumu (NEW WAVES AND DATA.pptx)

22 Eylül'de fark edildi: Dropbox'taki **3 slaytlık `NEW WAVES AND DATA.pptx`** hocanın
sitenin kendi maketi. Tahmin değil, ölçüm — OOXML'den birebir çıkarıldı. Tartışmaları bitiriyor.

**Sol menü kesin.** Slaytların metni iki yerde açıkça söylüyor:
> *"You'll find these documents under the three sections in the **Gallery menu on the left**."*
> *"…and similar sections **on left menu**?"*

Ve üç slaytın hepsinde aynı kabuk var:

| öğe | ölçülen (13,33 × 7,5 inç slayt) | web karşılığı |
|---|---|---|
| sol menü sütunu | x 0 → 2,23 in | **genişliğin %16,7'si**, tam yükseklik |
| menü bloğu | `accent1 lumMod 75%` | **`#104862`** beyaz, kalın, **ortalanmış** yazı |
| etkin sayfa | `accent2 lumMod 50%` | **`#80350E`** (slayt 2'de About Me, slayt 3'te My Research Areas) |
| kart / kutu | `bg1 lumMod 95%` + kenar `bg2 lumMod 90%` | **`#F2F2F2`** dolgu, **`#D1D1D1`** kenar, yuvarlak köşe |
| sayfa zemini | `bg1` | **beyaz** |
| üst şerit | 13,33 × 0,50 in, `noFill` | boş nefes payı, renkli bant değil |

Menü sırası (hocanın yazdığı gibi, **Home yok** — isim/fotoğraf bloğu ana sayfaya gider):
About Me · My Research Areas · Gallery · Vibrations and Waves ·
Signal Processing, System Identification, Estimation, Optimization · Machine Learning ·
Blog · Contact

**Slayt 3 = "4 kutucuk".** WhatsApp'taki *"tiklayabilcegin 4 box olmustu bunlar icin, altinda da
direk bunlari word olarak indirebilcekleri link"* isteğinin birebir maketi. y=5,57 in'de yan yana
dört yuvarlak kutu, **etiket üstte, ikon altta**:

1. Structural Health Monitoring / Non-destructive Testing (Short) — `image4.png`
2. Extended SHM / NDT document — `image6.png`
3. Sound Wave Tracking — `image5.png`
4. Extensive ppt regarding my MSc and PhD Research — `image3.png`

**Kesilen cümle bulundu.** Lovable videosunda ekran dışında kalan */research* paragrafının
tamamı slayt 3'te duruyor:
> *"Also, are you also asking about "vibrations and waves", "signal processing, system
> identification, estimation, optimization", and "machine learning" and similar sections on left
> menu? In this webpage, I also explain such topics in similar sense (overall picture, the
> intuition, how different topics are connected, how to learn them) based on my research and
> industry experience. Thus, after checking my research topics, if you are interested, and
> especially if you are a newcomer for those topics, please give them a look."*

**Önceki iki okuma geçersiz.** Lovable taslağındaki üst şerit + hamburger, hocanın istediği kabuk
değildi; Lovable o slaytları tam karşılayamamıştı. Krem/fildişi palet de geçersiz: hocanın
kendi paleti **beyaz zemin + `#104862` menü**.

**Açık kalan:** "the three sections in the Gallery menu" hangi üç bölüm? Dört kutu var,
metin "three documents + a presentation" diyor. Galeri alt menüsü kurulmadı, hocaya sorulacak.

---

## 4c. Wix'te yayın ve site üreteci

**Yayın yolu.** Wix'in statik site yükleme akışı (`headless-business-setup`, Path B): anonim site
oluştur → dosyaları yükle → release. Sınırlar: **3 MB/dosya, 20 MB/site**, yalnız statik dosya.
Görseller WebP'ye çevriliyor (17,1 MB → ~3,3 MB).

**Bir saatlik pencere.** Anonim kayıt, **oluşturulmasından 1 saat sonra** düşer; o süre içinde
aynı id'lerle aynı URL güncellenebilir ve hesaba alınabilir (claim), sonra ikisi de çalışmaz.
22 Eylül'de iki anonim site yayınlandı (ilki öğleden sonra, ikincisi 20:17); ikisi de hesaba
alınmadan süresi doldu. **Bir sonraki yayın, turun en sonunda yeni bir siteye yapılacak** ve
kullanıcıya claim için bir saat kalacak.

**Kimlikler depoda değil.** `anonymousId` bir claim token'ıdır: Wix'e girişli kim açarsa site onun
hesabına geçer. Bu yüzden `site/.wix/` altında ve `.gitignore`'da; bu dosyaya yazılmaz.

**Üreteç repoda.** 22 Eylül akşamı oturum geçici dizinini kaybetti; site çalışması repoya taşındı:

```
site/build.py        üreteç. python site/build.py [--out DIR] [--strict]
site/preview.py      Ricos JSON -> HTML (belge sayfaları)
site/parts/*.py      bölüm modülleri: theme, hero, topics, rboxes, gallery, about, docs
site/design/         CONTRACT.md, BRIEF2.md, DESIGN_BRIEF.md (bağlayıcı), PALETTE.css
site/dist/           derlenmiş site (gitignore)
site/.wix/           Wix anonim kimlikleri (gitignore)
```

`--out`, eşzamanlı çalışan ajanlar birbirinin çıktısını silmesin diye var (build önce çıktı
dizinini siler). `--strict`, gezinme sayfalarında tek bir em dash kalırsa build'i reddeder.

**Round 2 tasarım kararları** (`site/design/DESIGN_BRIEF.md`, ölçümlerle):
- Deck'teki `#104862` / `#80350E`, **Microsoft Office'in varsayılan teması**ndan türemiş
  (`accent1=156082`, `accent2=E97132`). Hocanın kararı "koyu mavi sütun + sıcak vurgu", hex'ler
  değil. Palet OKLCH'de yeniden üretildi: sütun H 248, vurgu H 52, sıcak kâğıt `#FBF9F6`.
- Eski etkin menü işareti `#80350E` üstü `#104862` = **1,14:1** kontrast: WCAG ihlali. Yerine
  4,90:1'lik bir kenar rayı.
- Satır uzunluğu **101,7 karakter**ti (`72ch`, sıfırın genişliği); 608 px ile ~70'e iniyor.
- Inter bırakılıyor: Source Serif 4 gövde (19 px), Source Sans 3 arayüz.
- Hocanın fotoğrafı menüden kalkıyor, yalnız hero'da kalıyor.
- Hover'da `translateY`, gölge değişimi ve renk tonu değişimi yasak.

**Word indirmeleri.** Hocanın "4 kutunun altında Word linki" isteği bu turda canlıya çıkıyor, ama
yalnız denetimden geçen üç belge için: Brochure (0,11 MB), Understanding (0,95 MB), Sound
(0,27 MB) — içlerinde e-posta, yorum ya da izlenen değişiklik yok. Yayınlanmayanlar ve nedeni:
Signal Processing hocanın kişisel Gmail'ini içeriyor; From_Bridges Word yorumları içeriyor;
Dynamical (3,97 MB) ve Machine Learning (10,29 MB) dosya başına 3 MB sınırını aşıyor.

**Gizlilik.** Hocanın kişisel Gmail'i üç rehberin disclaimer kutusunda geçiyor; web sayfalarında
Contact sayfasına bağlantıya çevriliyor. Kurumsal adres: `korkutkaynardag@iyte.edu.tr`.

---

## 5. Dropbox geldi: içeriğin tamamı

21 Eylül 17:20'de sekiz dosya geldi, 206 MB, `Downloads/Transfer` klasörüne. 196 MB'lık sunum
dışındakiler `content/source/` altına alındı. Hoca aynı anda WhatsApp'tan şunu yazdı:

> "İki ve daha uzun sayfalık NDT SHM dökümanları, sound wave localization, ve PPT, slide'da
> gösterdiğim gibi, My Research section'a gidecek."
>
> "Videoda hem tıklayabileceğin 4 box olmuştu bunlar için, altında da direkt bunları Word
> olarak indirebilecekleri link olursa güzel olur."

**`NEW WAVES AND DATA.pptx` sitenin asıl kaynağı.** Üç slayt, hocanın kendi elinden; Lovable'ın
çevirdiği şey bu. Her slaytta solda aynı sekiz dikdörtgen menü var: About Me · My Research
Areas · Gallery · Vibrations and Waves · Signal Processing System Identification Estimation
Optimization · Machine Learning · Blog · Contact. **"Home" PPT'de yok**, onu Lovable ekledi.
Slayt 1 ana sayfa, slayt 2 About, **slayt 3 tam olarak `/research` sayfası** ve hocanın
"4 box" dediği şeyi kesinleştiriyor. Hoca sonradan bunu ayrıca teyit etti:

| kutu (PPT slayt 3'teki adıyla) | dosya | boyut |
|---|---|---|
| Structural Health Monitoring/Non-destructive Testing (Short) | `Brochure - SHM and NDT - 2 pages.docx` | 587 kelime, 8 görsel, 6 tablo |
| Extended Structural Health Monitoring/Non-destructive Testing document | `Understanding_SHM_and_NDT.docx` | 4.037 kelime, 11 sayfa, 6 şekil |
| Sound Wave Tracking | **yok** | — |
| Extensive ppt regarding my MSc and PhD Research | `PhD_MsC_entire_Review_ppt.pptx` | 177 slayt, 19.864 kelime, 537 medya, 196 MB |

**Sound Wave Tracking belgesi gelmedi.** Hoca listede saydı ama Dropbox'ta yok. İstenecek.

Sol menüdeki üç eğitim bölümünün kaynakları da geldi:

| menü maddesi | dosya | kelime | sayfa | şekil | tablo |
|---|---|---|---|---|---|
| Vibrations and Waves | `Dynamical_Behavior_of_Engineering_Structures_and_Acoustic_Wave_Propagation.docx` | 7.260 | 20 | 26 | 2 |
| Signal Processing & Optimization | `Signal Processing, System Identification, and Optimization.docx` | 7.108 | 18 | 26 | 1 |
| Machine Learning | `Machine Learning - The Complete Picture and Guide_5.docx` | 18.192 | 44 | 30 | 28 |

Hepsinde gerçek `Heading1`/`Heading2` stilleri kullanılmış, on ya da on bir bölüm başlığı var.
Dynamical Behavior belgesi 21 Eylül sabahki halinden büyümüş: 16 şekilden 26 şekle çıkmış.
Machine Learning belgesi de videoda görünen 9.246 kelimeden 18.192'ye çıkmış, yani 15 Eylül'den
beri neredeyse ikiye katlanmış. Signal Processing belgesinde dört dış bağlantı var (Wikipedia,
Medium, ruder.io, pediaa); bunlar korunmalı.

**`From_Bridges_to_Photons.docx` fazladan geldi.** Yaklaşık 900 kelime, dört alt başlık, çift
yarık deneyini mod şekli problemi olarak okuyan bir deneme. Ne PPT'de ne taslakta yeri var.
Nereye konacağı sorulacak; en uygunu ya Vibrations and Waves altında bir ek ya da blog yazısı.

**Dönüştürme açısından üç iyi haber.**

1. **Gerçek Word stilleri kullanılmış.** Başlıklar elle biçimlendirilmemiş, `Heading1`/`Heading2`
   stilinde. Yani stil eşlemesi çalışır, dönüşüm otomatikleşebilir. En kritik belirsizlik buydu.
2. **Hiçbir belgede denklem nesnesi yok.** Ne OMML ne MathType. 98 şeklin hepsi PNG. MathType
   dönüştürme adımı gerekmiyor; "Dönüştürme hattı" bölümündeki uyarı bu dosyalar için geçersiz.
   Denklemler resmin içinde. KaTeX yalnızca sonradan yazılacak metinler için gerekir.
3. **Palet artık kesin.** PPT'nin içindeki dört ikon 1024×1024 PNG, sıkıştırılmamış. Renkler
   doğrudan pikselden okundu, kameradan değil:

   | jeton | değer | nerede |
   |---|---|---|
   | `--navy` | **`#1B3A6B`** | ana yapı rengi, başlıklar, ikon gövdeleri |
   | `--maroon` | **`#8C1A1A`** | vurgu: çatlak, dalga, etkin menü çubuğu |
   | `--rose` | `#A54C4B` | ikinci dalga halkası |
   | `--rose-light` | `#C48B8A` | üçüncü dalga halkası |
   | `--slate` | `#8B9AB2` | pasif, soluk çizgiler |
   | `--white` | `#FDFCFB` | ikon zemini |

   Taslaktan tahmin edilen "tuğla kırmızısı" işte bu: `#8C1A1A`. Vurgu rengi tartışması bitti,
   bordo, mavi değil. Lavanta-pembe degrade (`#EFEFF6` → `#F6ECEF`) ikonların kendi zemini,
   sayfa zemini değil.

   Tam çözünürlüklü vesikalık da PPT'nin içinden çıktı:
   `content/source/ppt-icons/headshot-708.png`, 708×691. Dört kutu ikonu da elimizde ve siteye
   doğrudan konabilir: `image3` kısa SHM/NDT broşürü (belge + grafik + büyüteç), `image4`
   kirişte dalga izleme, `image5` üç sensörle ses kaynağı konumlandırma (Sound Wave Tracking),
   `image6` çatlak üzerinde büyüteç.

**196 MB sorunu.** `PhD_MsC_entire_Review_ppt.pptx` içinde 537 medya dosyası ve beş mp4 var.
Cloudflare Pages dosya başına 25 MiB sınır koyuyor, bu dosya doğrudan indirme olarak konulamaz.
Üç seçenek: PowerPoint'in kendi görsel sıkıştırmasıyla küçültmek, PDF'e çevirip koymak, ya da
R2 gibi ayrı bir depoya koyup oradan bağlamak. En pratiği: sıkıştırılmış sürüm siteye, tam
sürüm için ayrı bağlantı.

**Hocanın istediği davranış:** dört kutunun her biri tıklanınca belgenin site içindeki
sayfasına gidecek; kutunun altında da belgeyi Word olarak indiren ayrı bir bağlantı olacak.
Yani her belge hem okunacak hem inecek.

---

## 6. Elimizde ne var

Bu klasörde:

```
content/dynamical-behavior/
  source.docx          hocanın gönderdiği belge
  figures/             içinden çıkarılmış 16 şekil, tam çözünürlük
  text.txt             belgenin düz metni, bölüm bölüm
reference/wix-site/    mevcut sitenin her sayfasının HTML kopyası, blog yazıları dahil
reference/wix-media/   sitedeki 103 görselin orijinali, 105 MB
reference/design-mockup/   hocanın gönderdiği 7 video + 1 fotoğraf, ve 152 çıkarılmış kare
reference/analysis/    taslağın çözümlemesi (aşağıya bakınız)
reference/chat.md      WhatsApp yazışması, 21 Eylül 16:45'e kadar
tools/docx2page.py     Word'den sayfaya dönüştürücü, yazılmaya başlandı
tools/inspect.py       dönüşüm çıktısını denetleyen yardımcı
```

`reference/analysis/` içeriği:

```
designSpec.md          kurulabilir tasarım şartnamesi: renk jetonları, yazı ölçeği,
                       sol menü ölçüleri, bileşenler, kırılma noktası, Astro notları
contentInventory.md    sayfa sayfa içerik dökümü, Wix'le karşılaştırma, elde olmayanlar
toolForensics.md       taslağın Lovable'da olduğunun kanıtı, adres, hocadan ne isteneceği
completenessCritic.md  bu kanıtla bilinemeyecekler ve çelişkiler, önem sırasına dizili
clips.json             yedi videonun kare kare ham okuması, denetçi notlarıyla
still.json             sol menü fotoğrafının okuması
```

**Görseller kurtarıldı.** Wix'in görselleri `static.wixstatic.com` üzerinden hesap
gerektirmeden orijinal boyutta iniyor. 103 dosyanın hepsi indirildi, hiçbiri başarısız
olmadı. Galeri sayfasındaki 27 fotoğraf da bunların içinde. Yani Wix aboneliği
kapatıldığında hiçbir şey kaybolmayacak.

**Blog yazıları ekran görüntüsü.** Hoca haklı: "Sanırım böyle Word'ten screenshot alıp
koymuştum siteye." Sekiz yazının HTML'inde sadece 121 ile 263 kelime arası gerçek metin var,
geri kalanı resim, yazı başına 3 ile 12 arası. Yani yazıların gövdesi görsellerin içinde.
O görsellerin hepsi indirilen 103 dosyanın içinde, dolayısıyla Wix erişimi olmadan da
metinleri geri çıkarabiliriz. `tools/blog_check.py` sayımı yapıyor.

| yazı | metin | görsel |
|---|---|---|
| impulsive noise detection with SOM neural networks | 174 | 6 |
| laser doppler vibrometer | 186 | 10 |
| literature review for finite element model updating | 263 | 5 |
| comparison of multi objective optimization algorithms | 182 | 4 |
| impulse outlier detection | 152 | 12 |
| multi objective optimization | 151 | 4 |
| stationary wavelet package transformation | 121 | 6 |
| wind turbine literature review | 195 | 3 |

---

## 7. Mevcut sitenin durumu

wavesanddata.com, Wix üzerinde. Sayfa yapısı:

```
/                                        ana sayfa
├── /personal-resume                     özgeçmiş, 12 makale, 6 bildiri, 4 konuşma
├── /research-portfolio                  126 kelime, galeri JavaScript ile geliyor, HTML boş
├── /structural-dynamics-and-wave-propagation    3.268 kelime, 19 şekil
├── /signal-processing-optimization-ml           3.321 kelime, 24 şekil
├── /contact                             form, UT Austin adresi
├── /gallery                             14 set, 27 fotoğraf
├── /blog → 8 yazı                       hepsi Şubat-Nisan 2022
└── More ▸ /fullscreen-page              Wix şablonundan kalma yetim sayfa, 431 KB
```

Yeni sitede düzeltilecek olanlar:

1. Dokuz sayfanın yedisinde `<title>` hiç değiştirilmemiş: "Athletics | Pearson",
   "Admissions | Pearson", "Gallery | My Site". Görünen metinde de şablon kalıntıları var:
   "Blog: Blog2", "Contact: Section Title".
2. Sayfa başına 104-158 KB sıkıştırılmış HTML, içinde 122-341 KB gömülü CSS. Galeri
   sayfası 41 istek ve 2,9 MB. 11-13 harici script, üçü render'ı bloke ediyor.
3. Research Portfolio sayfası HTML'de boş. Scholar ve LinkedIn bağlantıları bir iframe
   widget'ının içinde, yani taranamıyor. ORCID hiç yok.
4. 3.268 kelimelik eğitim sayfasında tek başlık var, h1 yok, içindekiler yok, denklemler
   resim olarak duruyor.
5. Bilgiler eski, site en son 30 Ekim 2024'te düzenlenmiş: UT Austin adresi, "Ph.D. 2016 to present", utexas.edu maili.
   Hoca da "Wix'teki bilgiler eski, educational sectionlar dahil" dedi, yenilerini
   gönderecek.

Kaybedilmemesi gerekenler: yayın listesi ve ortak yazar yazımları, 27 galeri fotoğrafı
ve altyazıları, iki "The Books" okuma listesi, birinci tekil şahıs üslubu, adın iki
yazımı (Kaynardağ ve Kaynardag, Google Scholar indekslemesi için).

---

## 8. Gönderdiği belgenin içeriği

"Dynamical Behavior of Engineering Structures and Acoustic Wave Propagation", 109 paragraf,
16 şekil, bir tablo. Bölümler:

1. Conventional Structural Dynamics and Vibration based SHM
2. Why Resonance Happens: Interference of Travelling Waves
3. Wave Propagation in a Beam with More Depth: Dispersion Curves
4. What Happens then in Periodically Supported and Multi Span Beams?
5. Case Study: Wave Propagation in Rails
6. Case Study: Wave Propagation in Buildings During Earthquakes
7. Beyond Beams: Plates, Shells, and Pipes
8. What kind of waves are used in Acoustic Wave Based NDT?
9. Closing Thoughts
10. Recommended Books

Belgede kendi notu: "Claude (Anthropic's AI) was used for fact checking, proofreading,
and the preparation of several figures in this document." Yani AI kullanımına bakışı rahat.

Şekiller belgenin içinde resim olarak duruyor, denklemlerin bir kısmı da resim.
Bu haliyle siteye konacak, yeniden çizilmeyecek. Çözünürlükleri yeterli.

---

## 9. Dönüştürme hattı

Kurulu ve denendi: pandoc, MiKTeX (pdflatex, lualatex), Node.js, Python (PIL, PyMuPDF).

`pandoc source.docx -t html5 --extract-media=. --katex` komutu belgeyi temiz çeviriyor:
16 şekil `<img>` olarak çıkıyor, altyazılar hemen altında italik paragraf olarak geliyor,
başlıklar korunuyor, tablo tablo olarak geliyor. Yani şekil ile altyazısını eşleştirmek
ve numaralandırmak makineyle yapılabiliyor.

`tools/docx2page.py` bunu yapıyor: Word'ün kendi içindekiler alanını atıyor, şekilleri
altyazılarıyla eşleştirip numaralandırıyor, metindeki "Figure 6 (d)" gibi göndermeleri
o şekle bağlantıya çeviriyor, başlıklardan sayfa içi içindekiler üretiyor. Henüz bitmedi,
sayfa şablonu yazılmadı.

---

## 10. Bekleyenler

**Hocadan, önem sırasına göre:**

1. **Lovable projesinin kaynağı.** Bunu almak aşağıdaki çoğu soruyu gereksiz kılar: gerçek
   CSS, gerçek renk değerleri, gerçek yazı tipleri, menünün tam listesi, tam çözünürlüklü
   portre. Üç yolu var, en iyiden en kötüye:
   - *Project settings → Git → GitHub → Connect.* Lovable özel bir depo açıp iki yönlü
     eşitler; sonra bizi depoya katkıcı olarak ekler. Depoyu sonradan yeniden adlandırmaması
     veya taşımaması gerektiğini söylemek lazım, eşitleme bozuluyor.
   - *Share → Invite people → Editor.* Lovable içinde düzenleyici olarak ekler.
   - *Share → Share preview → Create new preview link.* Yalnız görüntüleme; piksel eşlemek
     için işe yarar, kaynak vermez.
   - *Project settings → Git → Download codebase* ücretli planda, onda yok.
   Açıp bakması için doğrudan bağlantı: `https://lovable.dev/chats/9994de28-52ce-4af7-8d44-37ec65de63bb`
2. **Sound Wave Tracking belgesi.** `/research` sayfasındaki dört kutudan biri bu ve
   Dropbox'ta yok. Hoca listede saydığı halde göndermedi; muhtemelen unuttu.
3. Taslakta "coming soon" yazan her şey: **CV dosyası**, yayımlanacak **e-posta adresi**,
   **ofis bilgisi**, **Google Scholar / ResearchGate / ORCID** bağlantıları.

**Gelenler (21 Eylül 17:20):** Dropbox'taki sekiz dosya, PPT dahil. Tam çözünürlüklü
vesikalık da PPT'nin içinden çıktı, ayrıca istemeye gerek kalmadı. Ayrıntı 5. bölümde.

**Cevaplanmamış sorular:**
- `From_Bridges_to_Photons.docx` nereye girecek? Ne PPT'de ne taslakta yeri var.
- 196 MB'lık sunum nasıl servis edilecek? Sıkıştırılsın mı, PDF'e mi çevrilsin, ayrı depoya mı
  konsun? Cloudflare Pages dosya başına 25 MiB sınırı yüzünden olduğu gibi konamıyor.
- Sol menü: fotoğraftaki hali onayladığı son hal mi, yoksa videolardaki tasarımı beğenip
  menüyü ayrıca mı istiyor? "Bu taslağı beğenmiştim" dediği sekiz dosyadan hangisi belli
  değil. Kabuğu bu belirliyor, tek soruyla çözülür.
- Blog ne olacak: sekiz yazı taşınacak mı, arşive mi kalkacak, menüden mi çıkacak?
  Mockup'ta blog için hiçbir tasarım yok.
- Galeri ne olacak? Menüde var ama hiç çekilmemiş. PPT slayt 3'ün metni "You'll find these
  documents under the three sections in the Gallery menu on the left" diyor, yani Gallery'yi
  bir belge kitaplığı gibi kullanıyor olabilir. Üstelik `/research` metni "bu belgeleri
  Gallery bölümünde de bulursunuz" diyor, oysa Wix'teki galeri 27 fotoğraf. İki ayrı şey
  aynı adı taşıyor.
- Yayın, patent ve ödül sayıları (12 / 2 / 8) PPT slayt 2'den geliyor, hocanın kendi cümlesi:
  "As of September 2026, I have 12 published articles; 2 patents, one granted and the other
  pending; and 8 awards received through academic and industry-academia collaborative research
  grants." Kaynak belli ama listeleri yok. Sayı sabit yazılırsa eskir; liste istenecek mi?
- Türkçe karakterler: Kaynardag mı Kaynardağ mı, Izmir mi İzmir mi? Scholar indekslemesi
  için ikisi de geçmeli.
- Altbilgi olacak mı? Taslakta hiçbir sayfada yok.
- Site sadece İngilizce mi olacak?
- Yayın listesini kim güncelleyecek?
- Ayda 400 dolar rakamı doğru mu? Alan adı 2027 sonuna kadar ödenmiş göründüğüne göre bu
  rakam alan adı değil, Wix site planı olmalı.

**Fiyat:** Hoca "ücretini sen belirle" dedi, rakam verilmedi. İçeriğin tamamı görülmeden
verilmeyecek. İki eğitim bölümü 3.300'er kelime ve 19-24 şekil, yani her biri ayrı bir
uzun makale sayfası. Yapı önerisi: sabit fiyat artı ilk altı ay küçük güncellemeler dahil,
kapsam dışı kalanlar baştan yazılı (yeni bölüm ekleme, tasarım değişikliği).

---

## 11. Alan adı ve hesap

21 Eylül'de hocanın Wix hesabına girildi (kendi gönderdiği mail adresi ve kendi mailine
gelen kodla). Yapılan her şey okuma amaçlı, hesapta ve canlı sitede hiçbir değişiklik
yapılmadı.

**Site kaydı** (Wix Site List API):
- site id `36a33e18-0863-4d42-8bbd-70c189d86351`
- ad `wavesanddata`, görünen ad **"My Site"**, şablon başlıklarındaki "My Site" buradan geliyor
- kuruluş 5 Ekim 2021, **son düzenleme 30 Ekim 2024**
- yayında, premium plan açık, alan adı bağlı
- katkıda bulunan listesi boş, yani hesaba başka kimsenin erişimi yok

**Alan adı** (RDAP kaydı):
- kayıt firması **Wix.com Ltd.**, yani alan adı Wix üzerinden alınmış
- kayıt 13 Aralık 2021, **bitiş 13 Aralık 2027**, son değişiklik 13 Kasım 2025
- ad sunucuları `NS2.WIXDNS.NET`, `NS3.WIXDNS.NET`
- durum: **clientTransferProhibited, clientUpdateProhibited**, yani alan adı kilitli

Bunun iki sonucu var.

Birincisi, alan adı 2027 sonuna kadar ödenmiş. Yani aylık 400 dolar alan adı için değil,
Wix site planı için gidiyor olmalı. Hocaya sorulacak.

İkincisi, taşıma yolu seçilmeli:

- **Kolay yol:** alan adı Wix'te kalsın, sadece DNS kayıtları Wix panelinden yeni sunucuyu
  gösterecek şekilde değiştirilsin, site planı iptal edilsin. Kilitlerle uğraşmaya gerek
  kalmaz, kesinti olmaz.
- **Temiz yol:** alan adı Cloudflare Registrar gibi bir yere taşınsın. Önce Wix panelinden
  kilit kaldırılıp EPP kodu alınmalı, sonra 5-7 gün sürer. Uzun vadede daha ucuz ve
  Wix'e hiç bağlı kalmaz.

Öneri: önce kolay yolla siteyi yayına alın, taşımayı sonra yapın. Site çalışır haldeyken
taşıma yapmak risksiz.

---

## 12. Sıradaki adımlar

1. **Lovable kaynağını iste.** Tek mesajla halledilir ve tasarım tarafındaki bütün
   belirsizliği kapatır. Bunu beklemeden düzen kodu yazmak, sonradan atılacak iş demek.
2. Aynı mesajda sol menü sorusunu sor: fotoğraftaki hali mi, yoksa videolardaki tasarım artı
   menü mü?
3. Dropbox gelince içeriğin tamamını say: kaç bölüm, kaç kelime, kaç şekil.
4. Fiyatı ve teslim tarihini çıkar, hocaya yaz.
5. Kabuğu kur: sabit sol menü, `designSpec.md`'deki ölçülerle. Kırılma noktası 1024px,
   altında çekmece. Taslaktaki 1400px'lik kırılma yanlış, hocanın tek şartını ihlal ediyor.
6. Bölüm şablonunu Astro içerik koleksiyonu olarak kur: giriş → The big picture →
   How to learn this topic → Recommended books & resources → Documents.
7. `docx2page.py`'yi bitir. Eklenecekler: tek hücreli tabloyu callout'a çevirme, gruplanmış
   Word şekillerinin sessizce kaybolduğunu yakalayıp uyarma, şekil ve bölüm göndermelerini
   bağlantıya çevirme, MathType denklemlerini OMML'e çevirme adımı.
8. Bir bölümü uçtan uca üret ve hocaya göster.
9. Alan adı ve Wix aboneliği takvimini netleştir.
