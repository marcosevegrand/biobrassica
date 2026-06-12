<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <title>@yield('title', 'BioBrassica')</title>
    <meta name="description" content="@yield('meta_description', isset($websiteDefaults) && $websiteDefaults->seo_description ? $websiteDefaults->seo_description : 'BioBrassica - Agricultura Biológica de qualidade')">

    @if(isset($websiteDefaults) && $websiteDefaults->seo_keywords)
        <meta name="keywords" content="{{ $websiteDefaults->seo_keywords }}">
    @endif

    <link rel="icon" type="image/png" href="{{ asset('images/brand/favicon_green.png') }}">

    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link rel="preconnect" href="https://fonts.bunny.net">
    <link href="https://fonts.bunny.net/css?family=figtree:300,400,500,600,700&display=swap" rel="stylesheet" />
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500&display=swap" rel="stylesheet">

    <link rel="stylesheet" href="{{ asset('css/output.css') }}">

    <script src="https://unpkg.com/htmx.org@2.0.4"></script>

    @yield('extra_css')
</head>
<body class="bg-paper text-forest font-sans font-light antialiased">

    <x-navbar-website />

    <x-site-messages />

    <main>
        @yield('content')
    </main>

    <x-footer-website />

    <script src="{{ asset('js/navbar.js') }}"></script>
    @yield('extra_js')

    @if(isset($websiteDefaults) && $websiteDefaults->custom_js)
        <script>{!! $websiteDefaults->custom_js !!}</script>
    @endif

    @if(isset($websiteDefaults) && $websiteDefaults->google_analytics_id)
        <script async src="https://www.googletagmanager.com/gtag/js?id={{ $websiteDefaults->google_analytics_id }}"></script>
        <script>
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', '{{ $websiteDefaults->google_analytics_id }}');
        </script>
    @endif
</body>
</html>
