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
    ('Finalizado', 'Finalizado'),
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
    
    tipo_documento = forms.ChoiceField(
        choices=[
            ('INE', 'INE'),
            ('Pasaporte', 'Pasaporte'),
            ('CURP', 'CURP'),
            ('Cedula', 'Cédula Profesional')
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Estudiante
        exclude = ['usuario_auth'] 
        widgets = {
            'estudiante_id': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'usuario': forms.TextInput(attrs={'class': 'form-control'}),
            'contrasena': forms.PasswordInput(attrs={'class': 'form-control'}),
            'nombre_completo': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_documento': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_registro': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'contrasena' in self.fields:
            self.fields['contrasena'].required = False
        if 'numero_documento' in self.fields:
            self.fields['numero_documento'].required = False
        if 'estudiante_id' in self.fields:
            self.fields['estudiante_id'].required = False
        if 'fecha_registro' in self.fields:
            self.fields['fecha_registro'].required = False

    def save(self, commit=True):
        estudiante = super().save(commit=False)
        
        passwd_val = self.cleaned_data.get('contrasena')
        if passwd_val:
            if isinstance(passwd_val, str):
                estudiante.contrasena = passwd_val.encode('utf-8')
        else:
            if not estudiante.pk:
                estudiante.contrasena = b''

        doc_val = self.cleaned_data.get('numero_documento')
        if doc_val:
            if isinstance(doc_val, str):
                estudiante.numero_documento = doc_val.encode('utf-8')
        elif estudiante.pk:
            estudiante.numero_documento = Estudiante.objects.filter(pk=estudiante.pk).values_list('numero_documento', flat=True).first()
        
        if commit:
            estudiante.save()
            self.save_m2m()
            
        return estudiante

class CursoForm(forms.ModelForm):
    instructor = forms.ModelChoiceField(
        queryset=Instructor.objects.all(),
        to_field_name="instructor_id",
        empty_label="Seleccione un instructor",
        widget=forms.Select(attrs={
            'style': 'width: 100%; padding: 8px; background-color: #1a252f; border: 1px solid #34495e; color: white; box-sizing: border-box;'
        })
    )

    estado = forms.ChoiceField(
        choices=[
            ('Activo', 'Activo'),
            ('Inactivo', 'Inactivo'),
            ('Finalizado', 'Finalizado'),
        ],
        widget=forms.Select(attrs={
            'style': 'width: 100%; padding: 8px; background-color: #1a252f; border: 1px solid #34495e; color: white; box-sizing: border-box;'
        }),
    )

    class Meta:
        model = Curso
        fields = [
            'nombre_curso',
            'categoria',
            'instructor',
            'duracion_horas',
            'costo',
            'cupo_maximo',
            'estado',
        ]
        widgets = {
            'nombre_curso': forms.TextInput(attrs={
                'style': 'width: 100%; padding: 8px; background-color: #1a252f; border: 1px solid #34495e; color: white; box-sizing: border-box;'
            }),
            'categoria': forms.TextInput(attrs={
                'style': 'width: 100%; padding: 8px; background-color: #1a252f; border: 1px solid #34495e; color: white; box-sizing: border-box;'
            }),
            'duracion_horas': forms.NumberInput(attrs={
                'style': 'width: 100%; padding: 8px; background-color: #1a252f; border: 1px solid #34495e; color: white; box-sizing: border-box;'
            }),
            'costo': forms.NumberInput(attrs={
                'style': 'width: 100%; padding: 8px; background-color: #1a252f; border: 1px solid #34495e; color: white; box-sizing: border-box;'
            }),
            'cupo_maximo': forms.NumberInput(attrs={
                'style': 'width: 100%; padding: 8px; background-color: #1a252f; border: 1px solid #34495e; color: white; box-sizing: border-box;'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['instructor'].queryset = Instructor.objects.all()
class InstructorForm(forms.ModelForm):
    # Definimos la cédula manualmente para que aparezca vacía al editar
    cedula_profesional = forms.CharField(
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dejar en blanco para mantener la cédula actual'}),
        label="Cédula profesional"
    )
    
    # Declaramos usuario y contraseña aquí para controlarlos mejor
    usuario = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    contrasena = forms.CharField(required=False, widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    
    estado = forms.ChoiceField(
        choices=[('Activo', 'Activo'), ('Inactivo', 'Inactivo')], 
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Instructor
        fields = [
            'nombre_completo', 
            'especialidad', 
            'cedula_profesional', 
            'usuario', 
            'contrasena', 
            'email', 
            'telefono', 
            'direccion', 
            'estado'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['cedula_profesional'].initial = ''

    def save(self, commit=True):
        instructor = super().save(commit=False)
        nueva_cedula = self.cleaned_data.get('cedula_profesional')
        
        # Manejo de la cédula
        if nueva_cedula:
            instructor.cedula_profesional = nueva_cedula.encode('utf-8') 
        else:
            if self.instance.pk:
                instructor.cedula_profesional = self.instance.cedula_profesional
                
        # Si estamos editando y no escribieron nueva contraseña/usuario, conservamos los anteriores
        if self.instance.pk:
            if not self.cleaned_data.get('usuario'):
                instructor.usuario = self.instance.usuario
            if not self.cleaned_data.get('contrasena'):
                instructor.contrasena = self.instance.contrasena
        
        if commit:
            instructor.save()
        return instructor


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