<?php

namespace App\Filament\Widgets;

use App\Models\BlogPost;
use App\Models\Order;
use App\Models\Payment;
use App\Models\Product;
use App\Models\Recipe;
use App\Models\User;
use Filament\Widgets\StatsOverviewWidget as BaseWidget;
use Filament\Widgets\StatsOverviewWidget\Stat;

class OrderStatsWidget extends BaseWidget
{
    protected function getStats(): array
    {
        $activeAccounts = User::query()->count();
        $paidOrders = Order::where('payment_state', Order::PAYMENT_CONFIRMED)->count();
        $revenue = Order::where('payment_state', Order::PAYMENT_CONFIRMED)->sum('total');
        $averageTicket = $paidOrders > 0 ? $revenue / $paidOrders : 0;
        $readyToPrepareOrders = Order::where('status', Order::STATUS_PENDING)
            ->where('payment_state', Order::PAYMENT_CONFIRMED)
            ->whereDoesntHave('payment', fn ($query) => $query->where('refund_state', Payment::REFUND_REQUESTED))
            ->count();
        $pendingPayments = Payment::where('status', Payment::STATUS_PENDING)->count();
        $requestedRefunds = Payment::where('refund_state', Payment::REFUND_REQUESTED)->count();
        $activeProducts = Product::where('is_active', true)->count();
        $todayOrders = Order::whereBetween('created_at', [today()->startOfDay(), today()->endOfDay()])->count();
        $lowStock = Product::where('is_active', true)->where('stock', '>', 0)->where('stock', '<=', 5)->count();
        $outOfStock = Product::where('is_active', true)->where('stock', '<=', 0)->count();
        $draftContent = BlogPost::where('is_published', false)->count() + Recipe::where('is_published', false)->count();

        return [
            Stat::make('Contas ativas', $activeAccounts)
                ->description('Clientes e staff registados')
                ->descriptionIcon('heroicon-m-users')
                ->color('info'),
            Stat::make('Encomendas pagas', $paidOrders)
                ->description('Pagamentos confirmados')
                ->descriptionIcon('heroicon-m-check-circle')
                ->color('success'),
            Stat::make('Total pago confirmado', '€'.number_format((float) $revenue, 2, ',', '.'))
                ->description('Exclui encomendas reembolsadas')
                ->descriptionIcon('heroicon-m-banknotes')
                ->color('success'),
            Stat::make('Ticket médio', '€'.number_format((float) $averageTicket, 2, ',', '.'))
                ->description('Valor médio pago')
                ->descriptionIcon('heroicon-m-chart-bar')
                ->color('info'),
            Stat::make('Prontas para preparar', $readyToPrepareOrders)
                ->description('Pagas e ainda pendentes')
                ->descriptionIcon('heroicon-m-shopping-cart')
                ->color('warning'),
            Stat::make('Pagamentos pendentes', $pendingPayments)
                ->description('A confirmar no backoffice')
                ->descriptionIcon('heroicon-m-credit-card')
                ->color('danger'),
            Stat::make('Reembolsos pedidos', $requestedRefunds)
                ->description('A aguardar tratamento manual')
                ->descriptionIcon('heroicon-m-arrow-uturn-left')
                ->color('warning'),
            Stat::make('Produtos ativos', $activeProducts)
                ->description('Produtos à venda')
                ->descriptionIcon('heroicon-m-shopping-bag')
                ->color('success'),
            Stat::make('Encomendas hoje', $todayOrders)
                ->description('Criadas hoje')
                ->descriptionIcon('heroicon-m-calendar')
                ->color('info'),
            Stat::make('Stock baixo', $lowStock)
                ->description('Produtos com 1 a 5 unidades')
                ->descriptionIcon('heroicon-m-exclamation-triangle')
                ->color('warning'),
            Stat::make('Sem stock', $outOfStock)
                ->description('Produtos ativos esgotados')
                ->descriptionIcon('heroicon-m-x-circle')
                ->color('danger'),
            Stat::make('Conteúdo em rascunho', $draftContent)
                ->description('Blog + receitas por publicar')
                ->descriptionIcon('heroicon-m-document-text')
                ->color('gray'),
        ];
    }
}
