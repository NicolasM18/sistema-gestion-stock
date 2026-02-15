from django import forms
from .models import Producto, Categoria

class ProductoForm(forms.ModelForm):


    cantidad_a_agregar = forms.DecimalField(
        required=False, 
        initial=0, 
        min_value=0, 
        max_digits=10, 
        decimal_places=3,
        label="➕ Sumar Stock (Ajuste)",
        widget=forms.NumberInput(attrs={
            'class': 'form-control border-success text-success fw-bold', 
            'placeholder': '0',
            'step': 'any' # decimales si es por peso
        })
    )

    # TIPO
    nuevo_tipo = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control border-success', 'placeholder': 'Nuevo Tipo...', 'id': 'input_nuevo_tipo'
    }))
    
    # CATEGORIA
    nueva_categoria = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control border-success', 'placeholder': 'Nueva Categoría...', 'id': 'input_nueva_categoria'
    }))

    # SUBCATEGORIA
    nueva_subcategoria = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control border-success', 'placeholder': 'Nueva Subcategoría...', 'id': 'input_nueva_subcategoria'
    }))

    class Meta:
        model = Producto
        fields = [
            'codigo_barras', 
            'tipo_producto', 'categoria', 'subcategoria', # 3 selects
            'nombre', 'marca', 'contenido_neto', 
            'es_por_peso', 'precio', 'precio_costo', 'stock_actual', 'stock_minimo'
        ]
        
        widgets = {
            'codigo_barras': forms.TextInput(attrs={'class': 'form-control', 'autofocus': 'true', 'id': 'id_codigo_barras'}),
            # WIDGETS 3 SELECTS
            'tipo_producto': forms.Select(attrs={'class': 'form-select', 'id': 'select_tipo'}),
            'categoria': forms.Select(attrs={'class': 'form-select', 'id': 'select_categoria'}),
            'subcategoria': forms.Select(attrs={'class': 'form-select', 'id': 'select_subcategoria'}),

            'nombre': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_nombre'}),
            'marca': forms.TextInput(attrs={'class': 'form-control'}),
            'contenido_neto': forms.TextInput(attrs={'class': 'form-control'}),
            'es_por_peso': forms.CheckboxInput(attrs={'class': 'form-check-input', 'style': 'transform: scale(1.4); margin-left: 15px; cursor: pointer;'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'precio_costo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock_actual': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'stock_minimo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        
        # VALIDACIÓN TIPO
        nuevo_tipo = cleaned_data.get('nuevo_tipo')
        tipo_select = cleaned_data.get('tipo_producto')
        if nuevo_tipo:
            if 'tipo_producto' in self.errors: del self.errors['tipo_producto']
        elif not tipo_select:
            # obligatorio
            self.add_error('tipo_producto', 'Seleccione un tipo o cree uno.')

        # VALIDACIÓN CATEGORIA
        nueva_cat = cleaned_data.get('nueva_categoria')
        cat_select = cleaned_data.get('categoria')
        if nueva_cat:
            if 'categoria' in self.errors: del self.errors['categoria']
        elif not cat_select:
            self.add_error('categoria', 'Seleccione una categoría o cree una.')

        # VALIDACIÓN SUBCATEGORIA
        nueva_sub = cleaned_data.get('nueva_subcategoria')
        sub_select = cleaned_data.get('subcategoria')
        if nueva_sub:
            if 'subcategoria' in self.errors: del self.errors['subcategoria']
        # La subcategoría opcional

        return cleaned_data



class CantidadForm(forms.Form):
    cantidad = forms.DecimalField(
        min_value=0.001, 
        label="Cantidad", 
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Cant.', 'step': '0.001'})
    )
    costo_unitario = forms.DecimalField(
        required=False,
        label="Costo Unitario",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 500.00', 'step': '0.01'})
    )
    