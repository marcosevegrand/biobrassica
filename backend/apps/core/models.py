"""Core models module."""

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class ShopSettings(models.Model):
    """Singleton (pk=1) holding shop-wide operational configuration.

    Controls:
    - Shop active toggle (pause payments during deployments)
    - Brevemente mode (coming-soon page on loja.* subdomain, CTA changes on main site)
    - Minimum order total enforcement
    - Payment methods (MB WAY, bank transfer) availability toggles
    - Payment timeout and checkout reservation timeout
    """

    is_shop_active = models.BooleanField(
        _('loja ativa'),
        default=True,
        help_text=_(
            'Quando desativado, os clientes não conseguem avançar do carrinho para o pagamento. '
            'Ideal para pausar a loja entre deployments ou em períodos de inatividade.'
        ),
    )
    is_shop_brevemente = models.BooleanField(
        _('modo brevemente'),
        default=False,
        help_text=_(
            'Quando ativo, o subdomínio loja.* mostra uma página "Brevemente" e '
            'os botões da loja no site principal passam a dizer "Brevemente" em vez de linkarem para a loja.'
        ),
    )
    min_order_total = models.DecimalField(
        _('valor mínimo de encomenda (€)'),
        max_digits=8,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_('Encomendas com total inferior a este valor são bloqueadas no checkout.'),
    )

    mbway_enabled = models.BooleanField(_('aceitar MB WAY'), default=True)

    payment_timeout_minutes = models.PositiveIntegerField(
        _('tempo limite para pagamento (minutos)'),
        default=30,
        help_text=_('Após este tempo, o pagamento expirado é cancelado. A encomenda permanece pendente — o cliente pode reiniciar o pagamento. Defina 0 para desativar.'),
    )

    checkout_reservation_minutes = models.PositiveIntegerField(
        _('tempo limite para reserva no checkout (minutos)'),
        default=30,
        help_text=_('Quanto tempo o stock fica reservado enquanto o cliente preenche o checkout. Após expirar, o stock é libertado e o cliente tem de recomeçar. Defina 0 para desativar.'),
    )

    bank_transfer_enabled = models.BooleanField(_('aceitar transferência bancária'), default=False)

    updated_at = models.DateTimeField(_('atualizado em'), auto_now=True)

    class Meta:
        verbose_name = _('configurações da loja')
        verbose_name_plural = _('configurações da loja')
        constraints = [
            models.CheckConstraint(condition=models.Q(pk=1), name='core_shopsettings_singleton_pk_1'),
        ]

    def __str__(self):
        return 'Configurações da loja'

    def clean_fields(self, exclude=None):
        for field in self._meta.fields:
            value = getattr(self, field.attname, None)
            if isinstance(value, str):
                setattr(self, field.attname, value.strip())
        return super().clean_fields(exclude=exclude)

    def save(self, *args, **kwargs):
        self.pk = 1
        if kwargs.get('force_insert') and type(self).objects.filter(pk=1).exists():
            kwargs['force_insert'] = False
        self.full_clean(validate_unique=False, validate_constraints=False)
        return super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        instance, _created = cls.objects.get_or_create(pk=1)
        return instance
