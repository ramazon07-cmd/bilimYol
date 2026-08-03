# BilimYol’ni Contabo VPS’ga production deploy qilish

Ushbu yo‘riqnoma Ubuntu 22.04/24.04, Docker Compose, PostgreSQL 16, Django, Next.js, Nginx va Let’s Encrypt SSL uchun yozilgan.

## 0. Kerak bo‘ladigan ma’lumotlar

- Contabo VPS IPv4 manzili.
- VPS’da Ubuntu 22.04 yoki 24.04.
- Domen, masalan `bilimyol.uz`.
- Domen DNS boshqaruviga kirish.
- GitHub’dagi `ramazon07-cmd/bilimYol` repository’siga kirish.

Root parolni chat, GitHub yoki `.env` faylga yubormang.

## 1. Domenni VPS’ga yo‘naltirish

DNS panelda quyidagilarni yarating:

| Type | Name | Value |
|---|---|---|
| A | `@` | `CONTABO_IPV4` |
| A | `www` | `CONTABO_IPV4` |

DNS tekshiruvi:

```bash
dig +short bilimyol.uz
dig +short www.bilimyol.uz
```

Ikkalasi ham VPS IPv4 manzilini ko‘rsatmaguncha SSL bosqichiga o‘tmang.

## 2. VPS’ga kirish va xavfsiz foydalanuvchi yaratish

Mac terminalida:

```bash
ssh root@CONTABO_IPV4
```

Serverda:

```bash
apt update
apt upgrade -y
apt install -y ca-certificates curl gnupg git ufw
adduser deploy
usermod -aG sudo deploy
```

Firewall:

```bash
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
ufw status
```

`5432`, `8000` va `3000` portlarini internetga ochmang.

## 3. Docker Engine va Compose o‘rnatish

Root foydalanuvchida:

```bash
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" > /etc/apt/sources.list.d/docker.list
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
usermod -aG docker deploy
systemctl enable --now docker
```

Keyin yangi guruh ishlashi uchun sessiyadan chiqing:

```bash
exit
ssh deploy@CONTABO_IPV4
docker --version
docker compose version
```

## 4. Repository’ni serverga olish

```bash
sudo mkdir -p /opt/bilimyol
sudo chown deploy:deploy /opt/bilimyol
git clone https://github.com/ramazon07-cmd/bilimYol.git /opt/bilimyol
cd /opt/bilimyol
```

Patch alohida branchda bo‘lsa:

```bash
git fetch origin
git checkout BRANCH_NOMI
```

## 5. Production secretlarni yaratish

```bash
cd /opt/bilimyol
cp deploy/.env.production.example deploy/.env.production
openssl rand -hex 48
openssl rand -hex 32
nano deploy/.env.production
```

Birinchi qiymatni `SECRET_KEY`, ikkinchisini `POSTGRES_PASSWORD` sifatida qo‘ying. Domen qiymatlarini ham almashtiring:

```env
DOMAIN=bilimyol.uz
ALLOWED_HOSTS=bilimyol.uz,www.bilimyol.uz
CORS_ALLOWED_ORIGINS=https://bilimyol.uz,https://www.bilimyol.uz
CSRF_TRUSTED_ORIGINS=https://bilimyol.uz,https://www.bilimyol.uz
FRONTEND_PUBLIC_URL=https://bilimyol.uz
NEXT_PUBLIC_API_BASE_URL=/api
```

```bash
chmod 600 deploy/.env.production
```

## 6. Birinchi deploy

```bash
cd /opt/bilimyol
bash deploy/scripts/release.sh
```

Holat va loglar:

```bash
docker compose --env-file deploy/.env.production -f deploy/docker-compose.prod.yml ps
docker compose --env-file deploy/.env.production -f deploy/docker-compose.prod.yml logs --tail=100 backend
docker compose --env-file deploy/.env.production -f deploy/docker-compose.prod.yml logs --tail=100 frontend
docker compose --env-file deploy/.env.production -f deploy/docker-compose.prod.yml logs --tail=100 nginx
```

## 7. SSL sertifikat yoqish

DNS tayyor va Nginx ishlayotganidan keyin:

```bash
bash deploy/scripts/enable-ssl.sh bilimyol.uz admin@bilimyol.uz www.bilimyol.uz
```

Tekshiruv:

```bash
curl -I https://bilimyol.uz
curl https://bilimyol.uz/health/
```

Kutiladigan health javobi:

```json
{"status":"ok","service":"BilimYol API","database":"ok"}
```

## 8. Django administrator yaratish

```bash
docker compose --env-file deploy/.env.production -f deploy/docker-compose.prod.yml exec backend python manage.py createsuperuser
```

Admin panel: `https://bilimyol.uz/admin/`

## 9. Yangi baza uchun diagnostika ma’lumotlari

Faqat yangi va bo‘sh database’da bajaring. Avval backup oling:

```bash
bash deploy/scripts/backup.sh
docker compose --env-file deploy/.env.production -f deploy/docker-compose.prod.yml exec backend python manage.py seed_all_english_diagnostics
docker compose --env-file deploy/.env.production -f deploy/docker-compose.prod.yml exec backend python manage.py seed_math_diagnostics
```

`seed_demo` production’da ataylab bloklangan. Demo loginlarni real serverga qo‘ymang.

## 10. Eski SQLite ma’lumotlarini PostgreSQL’ga ko‘chirish

Bu bosqich faqat eski real foydalanuvchi va natijalar kerak bo‘lsa bajariladi.

Eski loyiha kompyuterida:

```bash
cd backend
source .venv/bin/activate
python manage.py dumpdata --natural-foreign --natural-primary \
  --exclude contenttypes --exclude auth.permission --exclude sessions \
  --indent 2 > bilimyol-data.json
```

Faylni serverga yuboring:

```bash
scp backend/bilimyol-data.json deploy@CONTABO_IPV4:/opt/bilimyol/backend/
```

Serverda:

```bash
cd /opt/bilimyol
bash deploy/scripts/backup.sh
docker compose --env-file deploy/.env.production -f deploy/docker-compose.prod.yml exec backend python manage.py loaddata bilimyol-data.json
```

Importdan keyin admin, o‘quvchi, test, natija va roadmaplarni qo‘lda tekshiring.

## 11. Keyingi yangilanishlarni deploy qilish

```bash
cd /opt/bilimyol
bash deploy/scripts/backup.sh
git pull --ff-only
bash deploy/scripts/release.sh
bash deploy/scripts/verify.sh
```

## 12. Backup

```bash
bash deploy/scripts/backup.sh
ls -lh deploy/backups/
```

Backupni VPS tashqarisida ham saqlang. Faqat bitta VPS ichidagi backup yetarli emas.

## 13. SSL avtomatik yangilanishi

`crontab -e` orqali qo‘shing:

```cron
17 3 * * * cd /opt/bilimyol && docker compose --env-file deploy/.env.production -f deploy/docker-compose.prod.yml run --rm certbot renew --quiet && docker compose --env-file deploy/.env.production -f deploy/docker-compose.prod.yml exec nginx nginx -s reload
```

## 14. Tez diagnostika

### Sayt ochilmasa

```bash
docker compose --env-file deploy/.env.production -f deploy/docker-compose.prod.yml ps
docker compose --env-file deploy/.env.production -f deploy/docker-compose.prod.yml logs --tail=200
ufw status
```

### Backend database’ga ulanmasa

```bash
docker compose --env-file deploy/.env.production -f deploy/docker-compose.prod.yml logs --tail=200 db backend
docker compose --env-file deploy/.env.production -f deploy/docker-compose.prod.yml exec db pg_isready
```

### Frontend eski versiyani ko‘rsatsa

```bash
docker compose --env-file deploy/.env.production -f deploy/docker-compose.prod.yml build --no-cache frontend
docker compose --env-file deploy/.env.production -f deploy/docker-compose.prod.yml up -d frontend nginx
```

### SSL olinmasa

- Domen A-recordi VPS IP bilan bir xil ekanini tekshiring.
- `80/tcp` firewall’da ochiq ekanini tekshiring.
- Nginx ishlayotganini tekshiring.
- Cloudflare ishlatilsa, birinchi sertifikat olishda proxy’ni vaqtincha `DNS only` qiling.

## 15. Yakuniy checklist

- [ ] `DEBUG=False`.
- [ ] PostgreSQL ishlayapti.
- [ ] `SECRET_KEY` default emas.
- [ ] Faqat 22, 80 va 443 portlar ochiq.
- [ ] HTTPS ishlayapti.
- [ ] `/health/` database `ok` qaytaryapti.
- [ ] Superuser yaratildi.
- [ ] Login va refresh tekshirildi.
- [ ] Refreshdan keyin akkauntdan chiqib ketmayapti.
- [ ] Backup yaratildi va VPS tashqarisiga nusxa olindi.
- [ ] GitHub Actions yashil.
