# Ricos şema kaynakları — çevrimdışı kopya

Aşama 1'de ağdan çekilip yalnız geçici dizinde duran üç dosya. Düğüm ve dekorasyon
şekillerini bellekten değil buradan okuyun; tek yetkili kaynak yine de çalışan
doğrulayıcıdır (`POST /ricos/v1/ricos-document/validate`, devir notu §4).

| dosya | kaynak | tarih |
|---|---|---|
| `ricos_document.d.ts` | npm `ricos-schema@10.102.0`, `dist/types/ricos_document.d.ts` | 22 Eylül 2026 |
| `ricos.jtd.json` | aynı paket, JSON Type Definition (`refUnion`, enum'lar, açıklamalar) | 22 Eylül 2026 |
| `wix-rest-ricos-document-reference.txt` | dev.wix.com "Ricos Document" API referansı, sayfa metni | 21 Eylül 2026 |

İkisi aynı şeyi söylemiyor: REST referansı `STRIKETHROUGH`, `SUPERSCRIPT` ve `SUBSCRIPT`
dekorasyonlarını listeler (`strikethroughData` / `superscriptData` / `subscriptData`:
boolean); npm şemasının `Decoration` birleşimi dokuz üyede biter (BOLD … FONT_SIZE).
Devir notu §7.7 hangi şeklin hangisine dayandığını söyler.
