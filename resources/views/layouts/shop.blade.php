<!DOCTYPE html>
<html lang="{{ str_replace('_', '-', app()->getLocale()) }}" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>@yield('title', 'Loja | Biobrassica')</title>
    <link rel="icon" type="image/png" sizes="32x32" href="{{ asset('images/brand/favicon_green.png') }}">
    <meta name="description" content="@yield('meta_description', $websiteDefaults->seo_description ?? 'Loja online Biobrassica — produtos biológicos de Braga e Guimarães.')">
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    colors: {
                        paper: '#FBF9F6',
                        forest: '#2C3F2D',
                        terracotta: '#B07850',
                        stone: '#D1D1CC',
                        muted: '#6B6B6B',
                    },
                    fontFamily: {
                        serif: ['Lora', 'serif'],
                        sans: ['Inter', 'sans-serif'],
                    },
                    maxWidth: {
                        '384': '96rem',
                        '6xl': '72rem',
                    },
                }
            }
        }
    </script>
    <link rel="stylesheet" href="{{ asset('css/biobrassica-overrides.css') }}">
    <script src="{{ asset('js/htmx.min.js') }}" defer></script>
    @yield('head_extra')
</head>
<body class="min-h-screen flex flex-col bg-[#FBF9F6] text-[#2C3F2D] font-light antialiased">
    <x-navbar-shop />
    <x-site-messages />

    <main class="flex-1 pt-20">
        @yield('content')
    </main>

    <x-footer-shop />

    <script src="{{ asset('js/navbar.js') }}" defer></script>
    <script src="{{ asset('js/quantity-controls.js') }}" defer></script>
    <script>
        document.body.addEventListener('cartError', function (event) {
            const message = event.detail && event.detail.message ? event.detail.message : 'Não foi possível atualizar o carrinho.';
            window.alert(message);
        });
    </script>
    @yield('extra_js')
</body>
</html>
