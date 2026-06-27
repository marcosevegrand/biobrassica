<!DOCTYPE html>
<html lang="pt" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <title>@yield('title', 'BioBrassica')</title>
    <meta name="description" content="@yield('meta_description', isset($websiteDefaults) && $websiteDefaults->seo_description ? $websiteDefaults->seo_description : 'BioBrassica - Agricultura Biológica de qualidade')">

    @if(isset($websiteDefaults) && $websiteDefaults->seo_keywords)
        <meta name="keywords" content="{{ $websiteDefaults->seo_keywords }}">
    @endif

    <link rel="icon" type="image/png" href="{{ asset('images/brand/favicon_green.png') }}">

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

    @yield('extra_css')
</head>
<body class="min-h-screen flex flex-col bg-[#FBF9F6] text-[#2C3F2D] font-light antialiased">

    <x-navbar-website />

    <x-site-messages />

    <main class="flex-1">
        @yield('content')
    </main>

    <x-footer-website />

    <script src="{{ asset('js/navbar.js') }}" defer></script>
    @yield('extra_js')

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
