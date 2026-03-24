from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from django.conf import settings
from django.db import models
from django.db.models import Q


class Cart(models.Model):
    if TYPE_CHECKING:
        items: models.Manager[CartItem]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='cart',
    )
    session_key = models.CharField(max_length=40, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'carrinho'
        verbose_name_plural = 'carrinhos'
        constraints = [
            models.UniqueConstraint(
                fields=['session_key'],
                condition=Q(session_key__isnull=False) & ~Q(session_key=''),
                name='cart_unique_non_empty_session_key',
            ),
        ]

    def __str__(self):
        if self.user:
            return f'Carrinho de {self.user.email}'
        return 'Carrinho (sessão)'

    @property
    def total(self) -> Decimal:
        return sum((item.subtotal for item in self.items.select_related('product')), Decimal('0'))

    @property
    def item_count(self) -> int:
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('catalog.Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = 'item do carrinho'
        verbose_name_plural = 'itens do carrinho'
        constraints = [
            models.UniqueConstraint(
                fields=['cart', 'product'],
                name='cart_unique_product_per_cart',
            ),
        ]

    def __str__(self):
        return f'{self.quantity}x {self.product}'

    @property
    def subtotal(self):
        return self.product.price * self.quantity
