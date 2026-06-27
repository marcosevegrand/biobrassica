@if(session('success'))
<div class="bg-green-50 border-b border-green-200">
    <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-3">
        <p class="text-sm text-green-800">{{ session('success') }}</p>
    </div>
</div>
@endif

@if(session('warning'))
<div class="bg-amber-50 border-b border-amber-200">
    <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-3">
        <p class="text-sm text-amber-800">{{ session('warning') }}</p>
    </div>
</div>
@endif

@if(session('error'))
<div class="bg-red-50 border-b border-red-200">
    <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-3">
        <p class="text-sm text-red-800">{{ session('error') }}</p>
    </div>
</div>
@endif
