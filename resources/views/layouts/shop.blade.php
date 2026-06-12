<!DOCTYPE html>
<html lang="{{ str_replace('_', '-', app()->getLocale()) }}" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>@yield('title', 'Loja | Biobrassica')</title>
    <link rel="icon" type="image/png" sizes="32x32" href="{{ asset('images/brand/favicon_green.png') }}">
    <meta name="description" content="@yield('meta_description', $websiteDefaults->seo_description ?? 'Loja online Biobrassica — produtos biológicos de Braga e Guimarães.')">
    <link rel="stylesheet" href="{{ asset('css/output.css') }}">
    <link rel="stylesheet" href="{{ asset('css/biobrassica-overrides.css') }}">
    <script src="{{ asset('js/htmx.min.js') }}" defer></script>
    @yield('head_extra')
</head>
<body class="min-h-screen flex flex-col bg-paper text-forest font-sans font-light">
    <x-navbar-shop />
    <x-site-messages />

    <main class="flex-1 pt-20">
        @yield('content')
    </main>

    <x-footer-shop />

    <script src="{{ asset('js/navbar.js') }}" defer></script>
    <script src="{{ asset('js/quantity-controls.js') }}" defer></script>
    @yield('extra_js')
</body>
</html>
