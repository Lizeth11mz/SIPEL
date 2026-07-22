from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from .models import Estudiante, Curso, Instructor, Inscripcion, Evaluacion

# --- DEFINICIÓN DE OPCIONES COMUNES ---
ESTADO_CHOICES = [
    ('Activo', 'Activo'),
    ('Inactivo', 'Inactivo'),
    ('Cancelado', 'Cancelado'),
    ('Pendiente', 'Pendiente'),
    ('Pagado', 'Pagado'),
]

# --- FORMULARIOS ---

class UsuarioForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class CambiarContrasenaAdminForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})

class EstudianteForm(forms.ModelForm):
    estado = forms.ChoiceField(
        choices=[('Activo', 'Activo'), ('Inactivo', 'Inactivo')], 
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Estudiante
        exclude = ['contrasena', 'usuario_auth']
        widgets = {
            'usuario': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre_completo': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_documento': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_documento': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'numero_documento' in self.fields:
            self.fields['numero_documento'].required = False

    def save(self, commit=True):
        estudiante = super().save(commit=False)
        
        if commit:
            if estudiante.pk:
                # Obtenemos dinámicamente el nombre correcto de la llave primaria de la BD (estudiante_id)
                nombre_pk = Estudiante._meta.pk.column
                
                from django.db import connection
                with connection.cursor() as cursor:
                    cursor.execute(f"""
                        UPDATE Estudiantes 
                        SET usuario = %s, 
                            nombre_completo = %s, 
                            email = %s, 
                            telefono = %s, 
                            direccion = %s, 
                            tipo_documento = %s, 
                            estado = %s
                        WHERE {nombre_pk} = %s
                    """, [
                        estudiante.usuario,
                        estudiante.nombre_completo,
                        estudiante.email,
                        estudiante.telefono,
                        estudiante.direccion,
                        estudiante.tipo_documento,
                        estudiante.estado,
                        estudiante.pk
                    ])
            else:
                if not estudiante.contrasena:
                    estudiante.contrasena = b''
                estudiante.save()
            
            self.save_m2m()
            
        return estudiante

class CursoForm(forms.ModelForm):
    estado = forms.ChoiceField(
        choices=[('Activo', 'Activo'), ('Inactivo', 'Inactivo')], 
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Curso
        fields = ['nombre_curso', 'categoria', 'instructor', 'duracion_horas', 'costo', 'estado', 'cupo_maximo']
        widgets = {
            'nombre_curso': forms.TextInput(attrs={'class': 'form-control'}),
            'categoria': forms.TextInput(attrs={'class': 'form-control'}),
            'instructor': forms.Select(attrs={'class': 'form-control'}),
            'duracion_horas': forms.NumberInput(attrs={'class': 'form-control'}),
            'costo': forms.NumberInput(attrs={'class': 'form-control'}),
            'cupo_maximo': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class InstructorForm(forms.ModelForm):
    estado = forms.ChoiceField(
        choices=[('Activo', 'Activo'), ('Inactivo', 'Inactivo')], 
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Instructor
        fields = ['nombre_completo', 'especialidad', 'usuario', 'estado', 'cedula_profesional']
        widgets = {
            'nombre_completo': forms.TextInput(attrs={'class': 'form-control'}),
            'especialidad': forms.TextInput(attrs={'class': 'form-control'}),
            'usuario': forms.TextInput(attrs={'class': 'form-control'}),
            'cedula_profesional': forms.TextInput(attrs={'class': 'form-control'}),
        }

class InscripcionForm(forms.ModelForm):
    estado = forms.ChoiceField(choices=ESTADO_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))
    
    class Meta:
        model = Inscripcion
        fields = ['estudiante', 'curso', 'instructor', 'folio_inscripcion', 'estado', 'total_pago']
        widgets = {
            'estudiante': forms.Select(attrs={'class': 'form-control'}),
            'curso': forms.Select(attrs={'class': 'form-control'}),
            'instructor': forms.Select(attrs={'class': 'form-control'}),
            'folio_inscripcion': forms.TextInput(attrs={'class': 'form-control'}),
            'total_pago': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class EvaluacionForm(forms.ModelForm):
    class Meta:
        model = Evaluacion
        fields = ['inscripcion', 'calificacion', 'comentarios']
        widgets = {
            'inscripcion': forms.Select(attrs={'class': 'form-control'}),
            'calificacion': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'comentarios': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }