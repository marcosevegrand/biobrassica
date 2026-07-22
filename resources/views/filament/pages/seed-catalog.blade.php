<x-filament-panels::page>
    <div class="space-y-6">
        <div class="p-6 rounded-xl bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700">
            <h2 class="text-lg font-medium mb-2">Povoar catálogo com dados de exemplo</h2>
            <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
                Este comando insere (ou atualiza) categorias, produtos, lojas e conteúdos padrão no banco de dados.
                É seguro executar várias vezes — os registos existentes são atualizados, não duplicados.
            </p>
            <x-filament::button
                wire:click="seed"
                wire:loading.attr="disabled"
                icon="heroicon-m-rocket-launch"
                color="primary">
                Executar seeder
            </x-filament::button>
        </div>

        <div
            x-data="{ show: false }"
            x-on:seed-completed.window="show = true; setTimeout(() => show = false, 5000)"
            x-show="show"
            x-transition
            class="p-4 rounded-xl bg-success-50 dark:bg-success-900 border border-success-200 dark:border-success-700 text-success-800 dark:text-success-200 text-sm">
            ✅ Seeder executado com sucesso!
        </div>
    </div>
</x-filament-panels::page>
