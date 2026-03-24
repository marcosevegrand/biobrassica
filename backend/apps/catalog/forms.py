from django import forms
from django.utils.text import slugify

from apps.catalog.models import Product, ProductImage, ProductTranslation


class ProductAdminForm(forms.ModelForm):
    slug = forms.SlugField(
        required=False,
        help_text='Gerado automaticamente a partir do nome em Português e da quantidade, mas pode ser ajustado manualmente.',
    )

    class Meta:
        model = Product
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = self.fields['category'].queryset.filter(is_active=True).order_by('order', 'slug')
        self.fields['available_locations'].queryset = self.fields['available_locations'].queryset.filter(is_active=True).order_by('order', 'name')

        placeholders = {
            'brand': 'Ex: Biobrassica',
            'quantity': 'Ex: 500 g ou 6 x 330 ml',
            'bio_code': 'Ex: PT-BIO-03',
            'slug': 'Gerado automaticamente se deixar vazio',
        }
        for field_name, placeholder in placeholders.items():
            self.fields[field_name].widget.attrs.setdefault('placeholder', placeholder)

        self.fields['available_locations'].help_text = 'Escolha os pontos de venda onde o produto está disponível para levantamento.'
        self.fields['stock'].help_text = 'Atualize o stock real para evitar encomendas impossíveis de cumprir.'

    def clean_slug(self):
        slug = (self.cleaned_data.get('slug') or '').strip()
        return slugify(slug) if slug else ''


class ProductTranslationInlineForm(forms.ModelForm):
    class Meta:
        model = ProductTranslation
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['language'].help_text = 'Adicione apenas os idiomas realmente necessários. Português primeiro.'
        self.fields['name'].widget.attrs.setdefault('placeholder', 'Ex: Massa integral bio')
        self.fields['description'].widget.attrs.setdefault('rows', 4)
        self.fields['description'].widget.attrs.setdefault('placeholder', 'Descrição comercial curta e clara do produto.')
        self.fields['allergens'].widget.attrs.setdefault('placeholder', 'Ex: Contém glúten')
        self.fields['ingredients'].widget.attrs.setdefault('rows', 4)
        self.fields['ingredients'].widget.attrs.setdefault('placeholder', 'Lista completa de ingredientes.')


class ProductImageInlineForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].widget.attrs.setdefault('accept', 'image/*')
        self.fields['alt_text'].widget.attrs.setdefault('placeholder', 'Descrição curta para acessibilidade e SEO')
        self.fields['order'].help_text = 'Use a ordem para controlar a sequência da galeria.'
