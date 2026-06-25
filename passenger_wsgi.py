import os
import sys

# Le chemin pointe maintenant vers repositories/tayseercard
path = '/home/exqxfpyq/repositories/tayseercard'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'tayseercard.settings'

from tayseercard.wsgi import application