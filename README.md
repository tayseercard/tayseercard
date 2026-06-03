# VoucherApp — Django QR Voucher System

## 🚀 Setup rapide (local)

```bash
# 1. Cloner et installer
cd voucher_project
pip install -r requirements.txt

# 2. Variables d'environnement (créer un fichier .env)
DB_NAME=voucher_db
DB_USER=postgres
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_PORT=5432

# 3. Base de données
createdb voucher_db
python manage.py migrate

# 4. Créer le compte ADMIN (votre client)
python manage.py createsuperuser
# → choisir role: ADMIN depuis le shell ou admin Django

# 5. Lancer
python manage.py runserver
```

---

## 👥 Rôles utilisateurs

| Rôle | Créé par | Accès |
|---|---|---|
| **ADMIN** | Vous (createsuperuser) | Tout voir — toutes les boutiques |
| **MANAGER** | Admin Django | Dashboard, créer vouchers, gérer caissiers |
| **CAISSIER** | Son manager (via app) | Scanner QR, voir historique, stats jour |

### Créer un manager (store owner)
1. Aller sur `/admin/`
2. Users → Add User
3. Remplir username/password, cocher **role = MANAGER**
4. Stores → Add Store → sélectionner ce manager

### Le manager crée ses caissiers lui-même
→ Dashboard → "Ajouter caissier"

---

## 🗂️ Structure

```
voucher_project/
├── apps/
│   ├── accounts/     # Auth, rôles, dashboards
│   ├── stores/       # Modèle Store
│   ├── vouchers/     # Vouchers + QR generation
│   └── scanning/     # Scanner QR + validation AJAX
├── templates/
│   ├── base.html     # Layout sidebar Bootstrap 5
│   ├── accounts/     # Login, dashboards
│   ├── vouchers/     # Liste, détail, impression
│   └── scanning/     # Scanner caméra
├── static/
├── requirements.txt
└── manage.py
```

---

## 🖥️ Deploy VPS (Nginx + Gunicorn)

```bash
# Sur le VPS Hetzner/Contabo
pip install -r requirements.txt
python manage.py collectstatic
python manage.py migrate

# Gunicorn
gunicorn voucher_project.wsgi:application --bind 0.0.0.0:8000 --workers 3

# Nginx config
# proxy_pass http://127.0.0.1:8000;
```

---

## 📱 Mobile
L'app est **responsive Bootstrap 5** — fonctionne sur téléphone directement.
Le scanner QR utilise la caméra du téléphone via `html5-qrcode`.
