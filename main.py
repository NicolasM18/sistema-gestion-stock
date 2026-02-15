import os
import sys
import webbrowser
from threading import Timer
import django
from waitress import serve
from django.core.wsgi import get_wsgi_application

# Configuración básica
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_stock.settings')

# Django
django.setup()

# Aplicación WSGI
application = get_wsgi_application()

def abrir_navegador():
    # Usamos 127.0.0.1:8080
    webbrowser.open('http://127.0.0.1:8080')

if __name__ == '__main__':
    # Timer para abrir navegador
    Timer(1, abrir_navegador).start()
    print("---------------------------------------")
    print(" SISTEMA DE STOCK - EJECUTANDO")
    print(" NO CIERRES ESTA VENTANA")
    print("---------------------------------------")
    # Waitress
    serve(application, host='0.0.0.0', port=8080)