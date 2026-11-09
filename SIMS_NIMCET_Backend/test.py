

import os
import django
from django.conf import settings

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "SIMS_NIMCET_Backend.settings"
)

django.setup()


options = settings.MAILERS["default"]["OPTIONS"]

print("Host:", options["host"])
print("Port:", options["port"])
print("TLS:", options["use_tls"])
print("Username loaded:", bool(options["username"]))
print("Password loaded:", bool(options["password"]))