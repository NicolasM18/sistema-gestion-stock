from django.shortcuts import render, redirect, get_object_or_404
from .models import Producto, Venta, Ingreso, DetalleVenta, DetalleIngreso, Categoria, SubCategoria, TipoProducto, Caja, Proveedor
from .forms import ProductoForm, CantidadForm
from django.db.models import Q, Sum, F
from django.contrib import messages, redirects
from django.db import transaction
from django.urls import reverse
from decimal import Decimal
from django.db.models import Q, Sum
from django.utils import timezone
from decimal import Decimal
import uuid
import os
import sys
import hashlib



def obtener_id_pc():
    # Obtiene la dirección MAC y la convierte a string
    return str(uuid.getnode())

def verificar_licencia():
    nombre_archivo = 'licencia.secret'
    id_actual = obtener_id_pc()
    
    # Encriptamos el ID
    hash_actual = hashlib.sha256(id_actual.encode()).hexdigest()

    if not os.path.exists(nombre_archivo):
        try:
            with open(nombre_archivo, 'w') as f:
                f.write(hash_actual)
            print("Licencia activada para este equipo exitosamente.")
            return True
        except:
            print("Error al guardar licencia.")
            return False

    else:
        # verificamos
        with open(nombre_archivo, 'r') as f:
            licencia_guardada = f.read().strip()
        
        if licencia_guardada == hash_actual:
            return True # misma PC
        else:
            return False # otra PC

if verificar_licencia():
    print("Iniciando sistema...")
else:
    print("ERROR: Esta copia no está autorizada para este equipo.")
    input("Presione enter para salir...")
    sys.exit()














def lista_productos(request):
    busqueda = request.GET.get("buscar")
    modo = request.GET.get("modo", "venta") 
    
    if busqueda:
        # texto ingresado coincide?
        productos = Producto.objects.filter(
            Q(nombre__icontains=busqueda) | 
            Q(marca__icontains=busqueda) |
            Q(codigo_barras__icontains=busqueda) |
            Q(categoria__nombre__icontains=busqueda) |
            Q(subcategoria__nombre__icontains=busqueda) |
            Q(tipo_producto__nombre__icontains=busqueda)
        )
    else:
        productos = Producto.objects.none()
    carrito = request.session.get('carrito', {})
    total_carrito = 0
    if modo == 'venta':
        for item in carrito.values():
            total_carrito += float(item['subtotal'])
    
    lista_compras = request.session.get('lista_compras', {})
    total_compras = sum(float(item['subtotal']) for item in lista_compras.values())
    proveedores = Proveedor.objects.all().order_by('nombre')

    return render(request, 'inventario/lista_productos.html', {
        'productos': productos,
        'modo': modo,
        'carrito': carrito,          
        'total_carrito': total_carrito, 
        'lista_compras': lista_compras,
        'total_compras': total_compras,
        'proveedores': proveedores
    })




def agregar_producto(request):
    modo_origen = request.GET.get('modo', 'venta') 

    if request.method == 'POST':
        form = ProductoForm(request.POST)
        
        if form.is_valid():
            producto = form.save(commit=False)
            
            # TIPO PRODUCTO
            nombre_nuevo_tipo = form.cleaned_data.get('nuevo_tipo')
            tipo_elegido = form.cleaned_data.get('tipo_producto')
            if nombre_nuevo_tipo:
                tipo_obj, _ = TipoProducto.objects.get_or_create(nombre=nombre_nuevo_tipo)
                producto.tipo_producto = tipo_obj
            else:
                producto.tipo_producto = tipo_elegido

            # LÓGICA CATEGORÍA
            nombre_nueva_cat = form.cleaned_data.get('nueva_categoria')
            cat_elegida = form.cleaned_data.get('categoria')
            if nombre_nueva_cat:
                cat_obj, _ = Categoria.objects.get_or_create(nombre=nombre_nueva_cat)
                producto.categoria = cat_obj
            else:
                producto.categoria = cat_elegida

            # LÓGICA SUBCATEGORÍA
            nombre_nueva_sub = form.cleaned_data.get('nueva_subcategoria')
            sub_elegida = form.cleaned_data.get('subcategoria')
            if nombre_nueva_sub:
                sub_obj, _ = SubCategoria.objects.get_or_create(nombre=nombre_nueva_sub)
                producto.subcategoria = sub_obj
            else:
                producto.subcategoria = sub_elegida
            
            producto.save()
            messages.success(request, f"Producto '{producto.nombre}' agregado.")
            return redirect(f"{reverse('home')}?modo={modo_origen}")
    else:
        form = ProductoForm()

    return render(request, 'inventario/formulario_producto.html', {'form': form, 'modo': modo_origen})





@transaction.atomic # asegurar que se guarden ambas cosas o ninguna
def editar_producto(request, id):
    producto = get_object_or_404(Producto, pk=id)
    
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            # datos normales
            prod_editado = form.save(commit=False)
            # ajuste de Stock
            cant_extra = form.cleaned_data.get('cantidad_a_agregar')
            
            if cant_extra and cant_extra > 0:
                # Sumamos al stock actual
                prod_editado.stock_actual += cant_extra
                # Creamos el registro de ingreso
                # Como es un ajuste, el proveedor queda en None
                total_costo_ajuste = prod_editado.precio_costo * cant_extra
                nuevo_ingreso = Ingreso.objects.create(
                    total=total_costo_ajuste,
                    proveedor=None # Sin proveedor
                )
                DetalleIngreso.objects.create(
                    ingreso=nuevo_ingreso,
                    producto=prod_editado,
                    cantidad=cant_extra,
                    costo_unitario=prod_editado.precio_costo,
                    costo_total=total_costo_ajuste
                )
                messages.success(request, f"Se agregaron {cant_extra} al stock correctamente.")
            prod_editado.save()
            return redirect('home')
    else:
        form = ProductoForm(instance=producto)
    return render(request, 'inventario/formulario_producto.html', {'form': form, 'modo': request.GET.get('modo', 'venta')})






def eliminar_producto(request, id):
    producto = get_object_or_404(Producto, pk=id)
    
    if request.method == 'POST':
        producto.delete()
        return redirect('home')
    # página de confirmación
    return render(request, 'inventario/confirmar_eliminar.html', {'producto': producto})







def movimiento_stock(request, id):
    producto = get_object_or_404(Producto, pk=id)
    
    if request.method == 'POST':
        form = CantidadForm(request.POST)
        
        if form.is_valid():
            cantidad = form.cleaned_data['cantidad']
            
            # Detectamos qué botón apretó el usuario
            if 'entrada' in request.POST:
                costo = form.cleaned_data['costo_unitario']
                if costo:
                    # Actualizar Stock
                    producto.stock_actual += cantidad
                    producto.save()
                    costo_total_calculado = costo * cantidad
                    # Crear Cabecera INGRESO
                    nuevo_ingreso = Ingreso.objects.create(total=costo_total_calculado)
                    # Crear Detalle
                    DetalleIngreso.objects.create(
                        ingreso=nuevo_ingreso, # Vinculamos con la cabecera
                        producto=producto,
                        cantidad=cantidad,
                        costo_unitario=costo,
                        costo_total=costo_total_calculado
                    )
                    return redirect('home')
                else:
                    # Error
                    form.add_error('costo_unitario', "Debes ingresar el costo unitario para agregar stock.")
                
            elif 'salida' in request.POST:
                # Validamos que no quede en negativo
                if producto.stock_actual >= cantidad:
                    producto.stock_actual -= cantidad
                    producto.save()
                    total = producto.precio * cantidad
                    nueva_venta = Venta.objects.create(total=total)
                    DetalleVenta.objects.create(
                        venta=nueva_venta,
                        producto=producto,
                        cantidad=cantidad,
                        precio_unitario=producto.precio,
                        precio_sub_total=total
                    )
                    return redirect('home')
                else:
                    # Si no hay suficiente stock, agregamos un error al formulario
                    form.add_error('cantidad', f"No hay suficiente stock. Solo tienes {producto.stock_actual}.")
    else:
        form = CantidadForm()

    return render(request, 'inventario/movimiento_stock.html', {'producto': producto, 'form': form})









def historial_ventas(request):
    # Obtener parámetros
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    # Consultas Base
    cajas = Caja.objects.prefetch_related('ventas_caja__detalles__producto').order_by('-fecha_apertura')
    ventas_sueltas = Venta.objects.filter(caja__isnull=True).prefetch_related('detalles__producto').order_by('-fecha')

    # Aplicar Filtros de Precisión
    if fecha_inicio:
        cajas = cajas.filter(fecha_apertura__gte=fecha_inicio)
        ventas_sueltas = ventas_sueltas.filter(fecha__gte=fecha_inicio)
    if fecha_fin:
        cajas = cajas.filter(fecha_apertura__lte=fecha_fin)
        ventas_sueltas = ventas_sueltas.filter(fecha__lte=fecha_fin)
    total_general = 0
    # cálculo por Caja
    for caja in cajas:
        ventas = caja.ventas_caja.all()
        caja.t_efectivo = sum(v.total for v in ventas if v.metodo_pago == 'efectivo')
        caja.t_tarjeta = sum(v.total for v in ventas if v.metodo_pago == 'tarjeta')
        caja.t_transf = sum(v.total for v in ventas if v.metodo_pago == 'transferencia')
        caja.t_cta = sum(v.total for v in ventas if v.metodo_pago == 'cta_corriente')
        caja.total_calculado = sum(v.total for v in ventas)
        total_general += caja.total_calculado
    total_sueltas = sum(v.total for v in ventas_sueltas)
    sueltas_efectivo = sum(v.total for v in ventas_sueltas if v.metodo_pago == 'efectivo')
    sueltas_tarjeta = sum(v.total for v in ventas_sueltas if v.metodo_pago == 'tarjeta')
    sueltas_transf = sum(v.total for v in ventas_sueltas if v.metodo_pago == 'transferencia')
    sueltas_cta = sum(v.total for v in ventas_sueltas if v.metodo_pago == 'cta_corriente')
    total_general += total_sueltas
    caja_abierta = Caja.objects.filter(fecha_cierre__isnull=True).first()
    return render(request, 'inventario/historial_ventas.html', {
        'cajas': cajas,
        'ventas_sueltas': ventas_sueltas,
        'caja_abierta': caja_abierta,
        'total_general': total_general,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'resumen_sueltas': {
            'total': total_sueltas,
            'efectivo': sueltas_efectivo,
            'tarjeta': sueltas_tarjeta,
            'transf': sueltas_transf,
            'cta': sueltas_cta
        }
    })






def historial_ingresos(request):
    # Capturar filtros
    proveedor_id = request.GET.get('proveedor')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    # Consulta Base
    compras = Ingreso.objects.select_related('proveedor').prefetch_related('detalles_compra__producto').order_by('-fecha')

    # Aplicar Filtro de Proveedor
    if proveedor_id:
        if proveedor_id == 'sin_proveedor':
            compras = compras.filter(proveedor__isnull=True)
        else:
            compras = compras.filter(proveedor_id=proveedor_id)

    # Aplicar Filtro
    if fecha_inicio:
        compras = compras.filter(fecha__gte=fecha_inicio)
    
    if fecha_fin:
        compras = compras.filter(fecha__lte=fecha_fin)

    # Cálculos de Totales (Patrimonio)
    valor_stock_costo = Producto.objects.aggregate(total=Sum(F('stock_actual') * F('precio_costo')))['total'] or 0
    valor_stock_venta = Producto.objects.aggregate(total=Sum(F('stock_actual') * F('precio')))['total'] or 0
    ganancia_potencial = valor_stock_venta - valor_stock_costo

    proveedores = Proveedor.objects.all().order_by('nombre')

    return render(request, 'inventario/historial_ingresos.html', {
        'compras': compras,
        'proveedores': proveedores,
        'proveedor_seleccionado': proveedor_id,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,       
        'valor_stock_costo': valor_stock_costo,
        'valor_stock_venta': valor_stock_venta,
        'ganancia_potencial': ganancia_potencial
    })












def agregar_al_carrito(request, id):
    producto = get_object_or_404(Producto, pk=id)
    carrito = request.session.get('carrito', {})
    str_id = str(id)

    cantidad_a_agregar = float(request.POST.get('cantidad', 1))

    if producto.stock_actual >= Decimal(str(cantidad_a_agregar)):
        
        producto.stock_actual -= Decimal(str(cantidad_a_agregar))
        producto.save()

        if str_id in carrito:
            carrito[str_id]['cantidad'] += cantidad_a_agregar
            carrito[str_id]['subtotal'] = float(producto.precio) * carrito[str_id]['cantidad']
        else:
            # Evita error si es None
            nom_tipo = producto.tipo_producto.nombre if producto.tipo_producto else "-"
            nom_cat = producto.categoria.nombre if producto.categoria else "-"
            nom_sub = producto.subcategoria.nombre if producto.subcategoria else "-"

            carrito[str_id] = {
                'producto_id': producto.id,
                'nombre': producto.nombre,
                'marca': producto.marca if producto.marca else '-',
                'contenido_neto': producto.contenido_neto if producto.contenido_neto else '',
                # GUARDAMOS LOS 3 NIVELES
                'tipo': nom_tipo,
                'categoria': nom_cat,
                'subcategoria': nom_sub,

                'precio': float(producto.precio),
                'cantidad': cantidad_a_agregar,
                'subtotal': float(producto.precio) * cantidad_a_agregar,
                'es_por_peso': producto.es_por_peso
            }
        
        request.session['carrito'] = carrito
        messages.success(request, f"Reservado: {producto.nombre}")
    else:
        messages.error(request, f"No hay suficiente stock. Disponibles: {producto.stock_actual}")

    return redirect(request.META.get('HTTP_REFERER', 'home'))







# ver la página del carrito
def ver_carrito(request):
    carrito = request.session.get('carrito', {})
    total = 0
    
    # Calculamos el precio final sumando los subtotales
    for item in carrito.values():
        total += item['subtotal']

    return render(request, 'inventario/carrito.html', {'carrito': carrito, 'total': total})








def eliminar_del_carrito(request, id):
    carrito = request.session.get('carrito', {})
    str_id = str(id)

    if str_id in carrito:
        item = carrito[str_id]
        try:
            producto = Producto.objects.get(pk=item['producto_id'])
            producto.stock_actual += Decimal(str(item['cantidad']))
            producto.save()
        except Producto.DoesNotExist:
            pass

        del carrito[str_id]
        request.session['carrito'] = carrito
        messages.info(request, "Producto eliminado y stock restaurado.")

    busqueda = request.GET.get('buscar', '')
    url_destino = f"{reverse('home')}?modo=venta"
    
    if busqueda:
        url_destino += f"&buscar={busqueda}"
        
    return redirect(url_destino)







def limpiar_carrito(request):
    carrito = request.session.get('carrito', {})

    # Devolvemos stock
    for key, item in carrito.items():
        try:
            producto = Producto.objects.get(pk=item['producto_id'])
            producto.stock_actual += Decimal(str(item['cantidad']))
            producto.save()
        except Producto.DoesNotExist:
            continue

    request.session['carrito'] = {} 
    messages.info(request, "Venta cancelada. Stock restaurado.")
    # Volvemos a la misma pantalla
    return redirect(f"{reverse('home')}?modo=venta")












@transaction.atomic 
def confirmar_compra(request):
    carrito = request.session.get('carrito', {})
    if not carrito:
        return redirect(f"{reverse('home')}?modo=venta")

    metodo_pago_elegido = request.POST.get('metodo_pago', 'efectivo')
    total_acumulado = 0
    for item in carrito.values():
        total_acumulado += float(item['subtotal'])

    # BUSCAR SI HAY CAJA ABIERTA
    caja_abierta = Caja.objects.filter(fecha_cierre__isnull=True).first()

    # Creamos la venta asignándole la caja
    nueva_venta = Venta.objects.create(
        total=total_acumulado,
        metodo_pago=metodo_pago_elegido,
        caja=caja_abierta
    )

    for key, item in carrito.items():
        try:
            producto = Producto.objects.get(pk=item['producto_id'])
            DetalleVenta.objects.create(
                venta=nueva_venta,
                producto=producto,
                cantidad=item['cantidad'],
                precio_unitario=item['precio'],
                precio_sub_total=item['subtotal']
            )
        except Producto.DoesNotExist:
            pass

    request.session['carrito'] = {}
    messages.success(request, f"¡Venta #{nueva_venta.id} confirmada! (Caja: {'Abierta' if caja_abierta else 'CERRADA - Ojo'})")
    return redirect(f"{reverse('home')}?modo=venta")







@transaction.atomic 
def confirmar_ingresos(request):
    lista_compras = request.session.get('lista_compras', {})
    
    if not lista_compras:
        return redirect(f"{reverse('home')}?modo=compra")

    # Lógica de Proveedor
    proveedor_id = request.POST.get('proveedor_id')
    nuevo_proveedor_nombre = request.POST.get('nuevo_proveedor_nombre')
    proveedor_final = None

    if nuevo_proveedor_nombre:
        proveedor_final, created = Proveedor.objects.get_or_create(nombre=nuevo_proveedor_nombre)
    elif proveedor_id and proveedor_id != 'crear_nuevo_magic':
        try:
            proveedor_final = Proveedor.objects.get(id=proveedor_id)
        except Proveedor.DoesNotExist:
            proveedor_final = None

    total_general = sum(float(item['subtotal']) for item in lista_compras.values())

    # Crear Cabecera
    nuevo_ingreso = Ingreso.objects.create(
        total=total_general,
        proveedor=proveedor_final
    )

    # Crear Detalles y ACTUALIZAR PRECIOS
    for item in lista_compras.values():
        producto = get_object_or_404(Producto, pk=item['producto_id'])
        
        costo_nuevo = Decimal(str(item['costo']))
        markup = Decimal(str(item.get('markup', 1.0)))
        producto.precio_costo = costo_nuevo
        nuevo_precio_venta = costo_nuevo * markup
        producto.precio = nuevo_precio_venta
        
        producto.save()
        DetalleIngreso.objects.create(
            ingreso=nuevo_ingreso,
            producto=producto,
            cantidad=item['cantidad'],
            costo_unitario=item['costo'],
            costo_total=item['subtotal']
        )

    request.session['lista_compras'] = {} 
    
    nom_prov = proveedor_final.nombre if proveedor_final else "Sin Proveedor"
    messages.success(request, f"¡Ingreso confirmado! Precios de venta actualizados. (Prov: {nom_prov})")
    
    return redirect(f"{reverse('home')}?modo=compra")












# Agregar ítem a la lista de compras
def agregar_al_ingreso(request, id):
    producto = get_object_or_404(Producto, pk=id)
    lista_compras = request.session.get('lista_compras', {})

    cantidad = float(request.POST.get('cantidad', 1))
    costo = float(request.POST.get('costo', 0)) # Recibimos el costo

    if str(id) in lista_compras:
        lista_compras[str(id)]['cantidad'] += cantidad
        lista_compras[str(id)]['costo'] = costo 
        lista_compras[str(id)]['subtotal'] = costo * lista_compras[str(id)]['cantidad']
    else:
        lista_compras[str(id)] = {
            'producto_id': producto.id,
            'nombre': producto.nombre,
            'categoria': producto.categoria.nombre,
            'costo': costo,
            'cantidad': cantidad,
            'subtotal': costo * cantidad
        }
    request.session['lista_compras'] = lista_compras
    messages.success(request, f"Agredado a la lista de compra: {producto.nombre}")
    # Mantenemos el modo compra
    return redirect('/?modo=compra') 






# Ver la lista de compras antes de confirmar
def ver_ingresos(request):
    lista_compras = request.session.get('lista_compras', {})
    total = sum(item['subtotal'] for item in lista_compras.values())
    return render(request, 'inventario/ver_ingresos.html', {'lista_compras': lista_compras, 'total': total})






def eliminar_item_ingreso(request, id):
    lista_compras = request.session.get('lista_compras', {})
    str_id = str(id)

    if str_id in lista_compras:
        item = lista_compras[str_id]
        try:
            producto = Producto.objects.get(pk=item['producto_id'])
            cantidad_decimal = Decimal(str(item['cantidad']))
            producto.stock_actual -= cantidad_decimal 
            producto.save()
        except Producto.DoesNotExist:
            pass

        del lista_compras[str_id]
        request.session['lista_compras'] = lista_compras

    busqueda = request.GET.get('buscar', '') 
    url_destino = f"{reverse('home')}?modo=compra"
    
    if busqueda:
        url_destino += f"&buscar={busqueda}"
        
    return redirect(url_destino)





def limpiar_ingresos(request):
    lista_compras = request.session.get('lista_compras', {})
    
    for item in lista_compras.values():
        try:
            producto = Producto.objects.get(pk=item['producto_id'])
            # Convertimos a Decimal
            cantidad_decimal = Decimal(str(item['cantidad']))
            producto.stock_actual -= cantidad_decimal # Restamos el stock que íbamos a sumar
            producto.save()
        except Producto.DoesNotExist:
            continue

    request.session['lista_compras'] = {}
    return redirect(f"{reverse('home')}?modo=compra")




def agregar_masivo(request):
    if request.method == 'POST':
        carrito = request.session.get('carrito', {})
        algo_se_agrego = False
        busqueda = request.POST.get('busqueda_actual', '') 
        
        for key, value in request.POST.items():
            if key.startswith('cant_') and value:
                try:
                    producto_id = int(key.split('_')[1])
                    cantidad = float(value)
                except ValueError:
                    continue 
                
                if cantidad > 0:
                    producto = get_object_or_404(Producto, pk=producto_id)
                    str_id = str(producto_id)
                    
                    if producto.stock_actual >= Decimal(str(cantidad)):
                        producto.stock_actual -= Decimal(str(cantidad))
                        producto.save()
                        
                        if str_id in carrito:
                            carrito[str_id]['cantidad'] += cantidad
                            carrito[str_id]['subtotal'] = float(producto.precio) * carrito[str_id]['cantidad']
                        else:
                            nom_tipo = producto.tipo_producto.nombre if producto.tipo_producto else "-"
                            nom_cat = producto.categoria.nombre if producto.categoria else "-"
                            nom_sub = producto.subcategoria.nombre if producto.subcategoria else "-"

                            carrito[str_id] = {
                                'producto_id': producto.id,
                                'nombre': producto.nombre,
                                'marca': producto.marca if producto.marca else '-', 
                                'contenido_neto': producto.contenido_neto if producto.contenido_neto else '',
                                'tipo': nom_tipo,
                                'categoria': nom_cat,
                                'subcategoria': nom_sub,
                                'precio': float(producto.precio),
                                'cantidad': cantidad,
                                'subtotal': float(producto.precio) * cantidad,
                                'es_por_peso': producto.es_por_peso
                            }
                        algo_se_agrego = True
                    else:
                        messages.error(request, f"Stock insuficiente de {producto.nombre}.")

        if algo_se_agrego:
            request.session['carrito'] = carrito
            messages.success(request, "Productos agregados.")
        else:
            # errores de stock previos
            if not messages.get_messages(request):
                messages.warning(request, "No se seleccionaron cantidades válidas.")
        url_destino = f"{reverse('home')}?modo=venta"
        if busqueda:
            url_destino += f"&buscar={busqueda}"
            
        return redirect(url_destino)

    return redirect('home')






def ingreso_masivo(request):
    if request.method == 'POST':
        lista_compras = request.session.get('lista_compras', {})
        algo_se_agrego = False
        busqueda = request.POST.get('busqueda_actual', '')
        
        for key, value in request.POST.items():
            if key.startswith('cant_ingreso_') and value:
                try:
                    producto_id = int(key.split('_')[2])
                    cantidad = float(value)
                    
                    costo_key = f"costo_ingreso_{producto_id}"
                    markup_key = f"markup_ingreso_{producto_id}"
                    
                    costo = float(request.POST.get(costo_key, 0))
                    markup = float(request.POST.get(markup_key, 1.0))
                    
                except (ValueError, TypeError):
                    continue 
                
                if cantidad > 0 and costo > 0:
                    producto = get_object_or_404(Producto, pk=producto_id)
                    str_id = str(producto_id)
                    
                    precio_venta_estimado = costo * markup

                    producto.stock_actual += Decimal(str(cantidad))
                    producto.save()

                    if str_id in lista_compras:
                        lista_compras[str_id]['cantidad'] += cantidad
                        lista_compras[str_id]['costo'] = costo
                        lista_compras[str_id]['markup'] = markup
                        lista_compras[str_id]['nuevo_precio'] = precio_venta_estimado 
                        lista_compras[str_id]['subtotal'] = costo * lista_compras[str_id]['cantidad']
                    else:
                        lista_compras[str_id] = {
                            'producto_id': producto.id,
                            'nombre': producto.nombre,
                            'categoria': producto.categoria.nombre if producto.categoria else '-',
                            'costo': costo,
                            'markup': markup,
                            'nuevo_precio': precio_venta_estimado,
                            'cantidad': cantidad,
                            'subtotal': costo * cantidad
                        }
                    
                    algo_se_agrego = True

        if algo_se_agrego:
            request.session['lista_compras'] = lista_compras
            messages.success(request, "Productos agregados a la lista de ingreso.")
        else:
            messages.warning(request, "Datos incompletos o inválidos.")
        url_destino = f"{reverse('home')}?modo=compra"
        if busqueda:
            url_destino += f"&buscar={busqueda}"
            
        return redirect(url_destino)

    return redirect('home')






def eliminar_categoria(request, id):
    categoria = get_object_or_404(Categoria, pk=id) 
    # Guardamos el nombre para el mensaje
    nombre = categoria.nombre
    categoria.delete()
    messages.success(request, f"Categoría '{nombre}' y sus productos eliminados.")
    return redirect(request.META.get('HTTP_REFERER', 'agregar'))





def abrir_caja(request):
    # Verificamos si ya hay una abierta
    caja_abierta = Caja.objects.filter(fecha_cierre__isnull=True).exists()
    
    if caja_abierta:
        messages.warning(request, "Ya hay una caja abierta. Debes cerrarla primero.")
    else:
        # Creamos una nueva caja
        Caja.objects.create(saldo_inicial=0) 
        messages.success(request, "✅ Caja ABIERTA correctamente.")
    
    return redirect('historial') # Volvemos al historial

def cerrar_caja(request):
    try:
        # Buscamos la caja abierta
        caja = Caja.objects.get(fecha_cierre__isnull=True)
        # Calculamos el total vendido en esta sesión
        total_vendido = caja.ventas_caja.aggregate(total=Sum('total'))['total'] or 0
        caja.fecha_cierre = timezone.now()
        caja.saldo_final = total_vendido
        caja.save()
        messages.success(request, f"⛔ Caja CERRADA. Total vendido: ${total_vendido}")
    except Caja.DoesNotExist:
        messages.error(request, "No hay ninguna caja abierta para cerrar.")
    return redirect('historial')
