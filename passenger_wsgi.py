import os
import sys
import django
from django.core.management import call_command
from django.core.wsgi import get_wsgi_application

# 1. Ajouter le chemin de votre projet
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tayseercard'))

# 2. Variable d'environnement pour les paramètres
os.environ['DJANGO_SETTINGS_MODULE'] = 'tayseercard.settings'

# 3. Charger et initialiser le registre de Django (Règle le problème AppRegistryNotReady)
django.setup()

# 4. Lancer les migrations de manière sécurisée

# 5. Définir l'application pour Passenger
application = get_wsgi_application()