import os
import sys
import django
from django.core.wsgi import get_wsgi_application

# Define the project root directory
project_root = os.path.dirname(os.path.abspath(__file__))

# Add the project root to sys.path so django and apps can be imported
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Variable d'environnement pour les paramètres
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tayseercard.settings')

# Charger et initialiser le registre de Django
django.setup()

# Définir l'application pour Passenger
application = get_wsgi_application()
# Définir l'application pour Passenger
