"""
URL configuration for gestion_stock project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from inventario.views import (lista_productos, agregar_producto, editar_producto, eliminar_producto, movimiento_stock, 
    historial_ventas, historial_ingresos, agregar_al_carrito, ver_carrito, eliminar_del_carrito, limpiar_carrito, 
    confirmar_compra, agregar_al_ingreso, ver_ingresos, limpiar_ingresos, eliminar_item_ingreso, confirmar_ingresos,
    agregar_masivo, ingreso_masivo, eliminar_categoria, abrir_caja, cerrar_caja)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lista_productos, name='home'),
    path('agregar/', agregar_producto, name='agregar'),
    path('editar/<int:id>/', editar_producto, name='editar'),
    path('eliminar/<int:id>/', eliminar_producto, name='eliminar'),
    path('movimiento/<int:id>/', movimiento_stock, name='movimiento_stock'),
    path('historial/', historial_ventas, name='historial'),
    path('historial-ingresos/', historial_ingresos, name='historial_ingresos'),
    path('agregar-carrito/<int:id>/', agregar_al_carrito, name='agregar_carrito'),
    path('carrito/', ver_carrito, name='ver_carrito'),
    path('eliminar-item/<int:id>/', eliminar_del_carrito, name='eliminar_item'),
    path('limpiar/', limpiar_carrito, name='limpiar_carrito'),
    path('confirmar/', confirmar_compra, name='confirmar_compra'),
    path('agregar-ingreso/<int:id>/', agregar_al_ingreso, name='agregar_ingreso'),
    path('ver-ingresos/', ver_ingresos, name='ver_ingresos'),
    path('eliminar-ingreso/<int:id>/', eliminar_item_ingreso, name='eliminar_ingreso'),
    path('limpiar-ingresos/', limpiar_ingresos, name='limpiar_ingresos'),
    path('confirmar-ingresos/', confirmar_ingresos, name='confirmar_ingresos'),
    path('agregar-masivo/', agregar_masivo, name='agregar_masivo'),
    path('ingreso-masivo/', ingreso_masivo, name='ingreso_masivo'),
    path('eliminar-categoria/<int:id>/', eliminar_categoria, name='eliminar_categoria'),
    path('caja/abrir/', abrir_caja, name='abrir_caja'),
    path('caja/cerrar/', cerrar_caja, name='cerrar_caja'),
    path('ingreso_masivo/', ingreso_masivo, name='ingreso_masivo'),
    path('confirmar_ingresos/', confirmar_ingresos, name='confirmar_ingresos'),
    path('eliminar_item_ingreso/<int:id>/', eliminar_item_ingreso, name='eliminar_item_ingreso'),
    path('limpiar_ingresos/', limpiar_ingresos, name='limpiar_ingresos'),
]
