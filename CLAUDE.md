# Proje notları

Bu dosya yeni oturumlarda tüm projeyi taramaya gerek kalmasın diye tutulur. Önemli bir karar veya durum değişince güncelle.

## Amaç

Kullanıcı Türkçe konuşan bir ortaokul matematik öğretmeni. Gönderdiği dikey videoyu veya ses kaydını, kendi sesine senkron matematik animasyonlarıyla Instagram Reels ve YouTube Shorts videosuna çeviren bir sistem geliştiriyoruz. Yanıtlar Türkçe ve sade olmalı.

## Durum (1 Kasım 2026)

- İlk sürüm hazır ve `main` dalında: https://github.com/aabdulmecitz/agentic-education-skill
- Akış yapay Türkçe sesli, kutulardan oluşan deneme videosuyla uçtan uca çalıştı. Deneme çıktısı: `../mathedu/videolar/deneme-test/video.mp4`
- **Sıradaki adım:** Kullanıcının gerçek videosuyla ilk test. Önerilen konu: `(-2)²` ile `-2²` farkı, 30-50 saniye.
- Henüz yapılmadı: gerçek öğretmen videosu testi, skill tetiklenme ölçümü (şimdilik `/matematik-reels` yazılmalı), efekt sesi ve müzik.
- Render'daki otomatik yeniden deneme henüz gerçek bir kesintiyle sınanmadı.

## Dosyalar

```text
skills/matematik-reels/
├── SKILL.md                    İş akışı; skill kullanılırken buradan başla
├── references/plan-format.md   plan.json biçimi ve tüm animasyon tipleri
├── references/teaching.md      Video yapısı, hook ve çocuk güvenliği kuralları
├── references/package.md       Instagram ve YouTube metinleri
├── scripts/setup.sh            Kurulum
├── scripts/prepare.py          Videoyu hazırlama, yazı dökümü, kare çıkarma
├── scripts/build.py            plan.json -> timeline.json, tüm kontroller
├── scripts/render.sh           Remotion render ve teslim
├── scripts/qa.py               Dosya kontrolü ve kare örnekleri
└── engine/src/                 Remotion: Reel.tsx (katmanlar), events.tsx (animasyonlar)
```

Akış: `prepare.py` -> `plan.json` yazılır -> `build.py` -> `render.sh` -> kareler incelenir -> `paket.md` yazılır.

## Bu bilgisayardaki kurulum

- `~/.claude/skills/matematik-reels` bu repodaki skill klasörüne sembolik bağlantıdır, ayrı kopya değildir.
- Çalışma ortamı repo dışında: `~/.local/share/matematik-reels/` (`venv`, `engine/node_modules`, `models`, `jobs/<iş>`).
- `render.sh`, `engine/src` içeriğini her çalıştırmada kopyalar. `engine/package.json` değişirse `setup.sh` yeniden çalıştırılmalı.
- Teslim klasörü `~/.local/share/matematik-reels/out_dir` dosyasında: `mathedu/videolar/`.
- Yazı dökümü: `large-v3-turbo`, RTX 4060 üzerinde CUDA. Model indi.
- `gh` kurulu değil. `git push` çalışıyor.

## Kararlar

- **Remotion:** Canvas + `MediaRecorder` yerine, çünkü kare kare ve komut satırından render alır.
- **Ses önce gelir:** Animasyonlar kelime zaman damgalarına bağlanır. `at` alanına konuşmadan ifade yazılır.
- **Hazır bileşenler:** LLM her videoda animasyon kodu yazmaz, `plan.json` üretir.
- **Hareket:** Doğrusal geçiş yok; spring veya cubic-bezier kullanılır. Koyu tema, hareketli grid ve glow, kullanıcının ilk isteğinden gelir.
- **Format:** 1080x1920, 30 FPS. Güvenli alan x 40-850, y 230-1440.
- **Matematik:** Gösterilen her işlem SymPy ile `checks` altında doğrulanır; hata render'ı durdurur.
- **Hedef kitle:** Önce 8. sınıf ve LGS. 5-6. sınıf içeriğinin ana kanalı YouTube, çünkü Instagram'da yaş sınırı 13.
- **Çocuk güvenliği:** DM çağrısı yok, öğrenci adı veya görüntüsü yok, LGS ve kitap soruları birebir kopyalanmaz. Hook hatayı hedef alır, öğrenciyi değil; korku dili yok.
- **Yayın:** Otomatik yayın yok, son onay öğretmende.
- **Ses:** Yapay ses üretilmez, öğretmenin kaydı kullanılır.

## Karşılaşılan sorunlar

- **PyAV:** faster-whisper'ın ses çözme yolu kurulu PyAV ile uyumsuz (`metadata_errors` hatası). Ses bu yüzden ffmpeg ile çözülüyor.
- **`ERR_NETWORK_CHANGED`:** Render bir kez kesildi, tekrar denemede geçti. Nedeni büyük olasılıkla WSL veya Docker ağ değişimi; kesin doğrulanmadı.
- **`ig-*` ve `yt-*` araçları:** İngilizceye göre yazılmış. `caption.py`, `#8sınıf` etiketini `#8s` okuyor ve Türkçe yorum çağrısını tanımıyor. Yalnızca uzunluk ve yapı kontrollerine güven.
- **`qa/sheet.jpg`:** Render başarısız olursa eski kalabilir. Karelere bakmadan önce render'ın çıkış kodunu kontrol et.

## Repo

- Public repo. Kişisel yol, öğrenci verisi veya video dosyası gönderme.
- `ig-*` ve `yt-*` skill'leri lisansları bilinmediği için repoya eklenmedi.
- Lisans dosyası yok; kullanıcı karar vermedi.
- Commit ve push yalnızca kullanıcı isteyince yapılır.
