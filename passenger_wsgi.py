import os
import sys
import django
from django.core.wsgi import get_wsgi_application

# Définir la racine du projet
project_root = os.path.dirname(os.path.abspath(__file__))

# Ajouter le chemin pour les imports Django
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Configurer les variables d'environnement pour votre projet Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tayseercard.settings')

# Initialiser Django
django.setup()

# Point d'entrée pour Passenger
application = get_wsgi_application()