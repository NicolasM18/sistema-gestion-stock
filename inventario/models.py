from django.db import models
from django.utils import timezone


class TipoProducto(models.Model):
    nombre = models.CharField(max_length=50)
    
    def __str__(self):
        return self.nombre

class Categoria(models.Model):
    nombre = models.CharField(max_length=50)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name_plural = "Categorías"

class SubCategoria(models.Model):
    nombre = models.CharField(max_length=50)
    
    def __str__(self):
        return self.nombre



class Producto(models.Model):
    codigo_barras = models.CharField(max_length=50, unique=True, verbose_name="Código de Barras")
    nombre = models.CharField(max_length=100)
    marca = models.CharField(max_length=50, null=True, blank=True)
    contenido_neto = models.CharField(max_length=50, null=True, blank=True, verbose_name="Contenido")
    
    # 3 NIVELES DE CLASIFICACIÓN
    tipo_producto = models.ForeignKey(TipoProducto, on_delete=models.SET_NULL, null=True, blank=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    subcategoria = models.ForeignKey(SubCategoria, on_delete=models.SET_NULL, null=True, blank=True)

    es_por_peso = models.BooleanField(default=False, verbose_name="¿Se vende por peso? (Kg)")
    
    precio = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio Venta") 
    precio_costo = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Precio Costo")
    
    stock_actual = models.DecimalField(max_digits=10, decimal_places=3, default=0.000)
    stock_minimo = models.DecimalField(max_digits=10, decimal_places=3, default=5.000)

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre

class Caja(models.Model):
    fecha_apertura = models.DateTimeField(auto_now_add=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    saldo_inicial = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    saldo_final = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # user que abrió la caja
    # usuario = models.ForeignKey(User, on_delete=models.CASCADE) 

    def __str__(self):
        estado = "Abierta" if not self.fecha_cierre else "Cerrada"
        return f"Caja #{self.id} ({estado}) - {self.fecha_apertura}"

# MODIFICAMOS VENTA
class Venta(models.Model):
    METODOS_PAGO = [
        ('efectivo', 'Efectivo'),
        ('tarjeta', 'Tarjeta'),
        ('transferencia', 'Transferencia'),
        ('cta_corriente', 'Cta. Corriente'),
    ]
    fecha = models.DateTimeField(default=timezone.now)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    metodo_pago = models.CharField(max_length=20, choices=METODOS_PAGO, default='efectivo')
    # null=True permite que existan ventas viejas sin caja asignada
    caja = models.ForeignKey(Caja, on_delete=models.SET_NULL, null=True, blank=True, related_name='ventas_caja')

    def __str__(self):
        return f"Venta #{self.id} - {self.fecha}"

class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, related_name='detalles', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.DecimalField(max_digits=10, decimal_places=3)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    precio_sub_total = models.DecimalField(max_digits=10, decimal_places=2)

class Proveedor(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    
    def __str__(self):
        return self.nombre

class Ingreso(models.Model):
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Ingreso #{self.id} - {self.fecha}"

class DetalleIngreso(models.Model):
    ingreso = models.ForeignKey(Ingreso, related_name='detalles_compra', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.DecimalField(max_digits=10, decimal_places=3)
    costo_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    costo_total = models.DecimalField(max_digits=10, decimal_places=2)
