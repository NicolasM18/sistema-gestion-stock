from django.contrib import admin
from .models import Categoria, Producto, Venta, Ingreso, DetalleVenta, DetalleIngreso, SubCategoria, TipoProducto, Caja

class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'precio', 'stock_actual', 'stock_minimo')
    search_fields = ('nombre',)
    list_filter = ('categoria',)

class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 0  # filas vacías extra
    readonly_fields = ('producto', 'cantidad', 'precio_unitario', 'precio_sub_total')

# VENTA
class VentaAdmin(admin.ModelAdmin):
    # campos que existen en Venta
    list_display = ('id', 'fecha', 'total') 
    list_filter = ('fecha',)
    inlines = [DetalleVentaInline] # detalle

@admin.register(Venta)  # menú
class VentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'fecha', 'total')
    inlines = [DetalleVentaInline] # tabla de productos dentro de la venta

class DetalleCompraInline(admin.TabularInline):
    model = DetalleIngreso
    extra = 0
    readonly_fields = ('producto', 'cantidad', 'costo_unitario', 'costo_total')

@admin.register(Ingreso)
class CompraAdmin(admin.ModelAdmin):
    list_display = ('id', 'fecha', 'total')
    list_filter = ('fecha',)
    inlines = [DetalleCompraInline]


# Registramos
admin.site.register(Categoria)
admin.site.register(SubCategoria)
admin.site.register(TipoProducto)
admin.site.register(Caja)
admin.site.register(Producto, ProductoAdmin)