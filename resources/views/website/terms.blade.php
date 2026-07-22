@extends('layouts.website')

@section('title', 'Termos e Condições - BioBrassica')
@section('meta_description', 'Termos e Condições da BioBrassica. Condições gerais de utilização do website e de venda de produtos.')

@section('content')
<section class="relative h-[40vh] flex items-center justify-center overflow-hidden bg-gradient-to-br from-forest via-forest/90 to-forest/70">
    <div class="relative z-10 text-center px-4">
        <h1 class="font-serif text-4xl md:text-5xl font-bold text-white mb-4 drop-shadow-lg">
            Termos e Condições
        </h1>
        <p class="text-white/70 font-light">
            Condições gerais de utilização e venda
        </p>
    </div>
</section>

<section class="py-20 bg-paper">
    <div class="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
        @if(isset($websiteContent) && $websiteContent->terms_conditions_text)
            <div class="prose prose-lg max-w-none font-light leading-relaxed text-muted
                        prose-headings:font-serif prose-headings:text-forest prose-headings:font-semibold
                        prose-h2:text-2xl prose-h2:mt-10 prose-h2:mb-4
                        prose-p:mb-4
                        prose-strong:text-forest prose-strong:font-medium
                        prose-a:text-terracotta prose-a:no-underline hover:prose-a:underline
                        prose-li:mb-2">
                {!! Str::markdown($websiteContent->terms_conditions_text, ['html_input' => 'strip', 'allow_unsafe_links' => false]) !!}
            </div>
        @else
            <article class="prose prose-lg max-w-none font-light leading-relaxed text-muted
                           prose-headings:font-serif prose-headings:text-forest prose-headings:font-semibold
                           prose-h2:text-2xl prose-h2:mt-10 prose-h2:mb-4
                           prose-p:mb-4
                           prose-strong:text-forest prose-strong:font-medium
                           prose-a:text-terracotta prose-a:no-underline hover:prose-a:underline
                           prose-li:mb-2">
                <p><strong>Última atualização:</strong> {{ date('d/m/Y') }}</p>

                <h2>1. Informações Gerais</h2>
                @if(isset($websiteDefaults))
                    <p>
                        O presente website é propriedade de {{ $websiteDefaults->company_legal_name ?? 'BioBrassica' }}
                        @if($websiteDefaults->company_nif)
                            , com o NIF {{ $websiteDefaults->company_nif }}
                        @endif
                        @if($websiteDefaults->company_address)
                            , com sede em {{ $websiteDefaults->company_address }}.
                        @endif
                    </p>
                @endif
                <p>
                    A utilização deste website está sujeita aos presentes Termos e Condições.
                    Ao navegar no website, o utilizador aceita integralmente estes Termos e Condições.
                </p>

                <h2>2. Produtos e Informação</h2>
                <p>
                    O catálogo de produtos apresentado neste website é meramente informativo.
                    Para adquirir produtos, visite as nossas lojas físicas em Braga e Guimarães.
                </p>
                <p>
                    A BioBrassica reserva-se o direito de alterar os produtos e respetivas informações
                    a qualquer momento, sem aviso prévio.
                </p>

                <h2>3. Propriedade Intelectual</h2>
                <p>
                    Todos os conteúdos do website (textos, imagens, logótipos, marcas, etc.)
                    são propriedade da BioBrassica ou de terceiros que autorizaram a sua utilização.
                    É proibida a reprodução, distribuição ou modificação dos conteúdos sem autorização prévia.
                </p>

                <h2>4. Responsabilidade</h2>
                <p>
                    A BioBrassica não se responsabiliza por danos causados por interrupções no website,
                    vírus informáticos ou outros elementos nocivos, ou informações prestadas por terceiros.
                </p>

                <h2>5. Proteção de Dados</h2>
                <p>
                    O tratamento dos dados pessoais dos utilizadores é efetuado de acordo com a nossa
                    <a href="{{ route('website.privacy') }}">Política de Privacidade</a> e com a legislação
                    de proteção de dados aplicável.
                </p>

                <h2>6. Lei Aplicável e Foro Competente</h2>
                <p>
                    Os presentes Termos e Condições são regidos pela lei portuguesa. Para a resolução
                    de quaisquer litígios emergentes, é competente o foro da comarca de Guimarães,
                    com expressa renúncia a qualquer outro.
                </p>

                <h2>7. Alterações</h2>
                <p>
                    A BioBrassica reserva-se o direito de alterar estes Termos e Condições a qualquer
                    momento. As alterações serão publicadas no website.
                </p>
            </article>
        @endif
    </div>
</section>
@endsection
