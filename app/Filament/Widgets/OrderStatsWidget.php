<?php

namespace App\Filament\Widgets;

use App\Models\Order;
use App\Models\Payment;
use App\Models\Product;
use Filament\Widgets\StatsOverviewWidget as BaseWidget;
use Filament\Widgets\StatsOverviewWidget\Stat;

class OrderStatsWidget extends BaseWidget
{
    protected function getStats(): array
    {
        $pendingOrders = Order::where('payment_state', 'pending')->count();
        $pendingPayments = Payment::where('status', 'pending')->count();
        $activeProducts = Product::where('is_active', true)->count();
        $todayOrders = Order::whereDate('created_at', today())->count();

        return [
            Stat::make('Pending Orders', $pendingOrders)
                ->description('Orders awaiting payment confirmation')
                ->descriptionIcon('heroicon-m-shopping-cart')
                ->color('warning'),
            Stat::make('Pending Payments', $pendingPayments)
                ->description('Payments to be processed')
                ->descriptionIcon('heroicon-m-credit-card')
                ->color('danger'),
            Stat::make('Active Products', $activeProducts)
                ->description('Products currently for sale')
                ->descriptionIcon('heroicon-m-shopping-bag')
                ->color('success'),
            Stat::make("Today's Orders", $todayOrders)
                ->description('Orders placed today')
                ->descriptionIcon('heroicon-m-calendar')
                ->color('info'),
        ];
    }
}
