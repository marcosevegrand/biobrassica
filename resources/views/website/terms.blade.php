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
                    A utilização deste website e a aquisição de produtos através do mesmo estão sujeitas
                    aos presentes Termos e Condições. Ao navegar no website, o utilizador aceita
                    integralmente estes Termos e Condições.
                </p>

                <h2>2. Produtos e Preços</h2>
                <p>
                    Todos os produtos apresentados no website estão sujeitos à disponibilidade de stock.
                    Os preços são apresentados em euros e incluem o IVA à taxa legal em vigor, salvo indicação em contrário.
                </p>
                <p>
                    A BioBrassica reserva-se o direito de alterar os preços e produtos a qualquer momento,
                    sem aviso prévio. No entanto, as encomendas já confirmadas serão honradas ao preço acordado.
                </p>

                <h2>3. Encomendas</h2>
                <p>Ao efetuar uma encomenda, o cliente declara:</p>
                <ul>
                    <li>Ser maior de idade e ter capacidade legal para contratar</li>
                    <li>Que os dados fornecidos são verdadeiros e completos</li>
                    <li>Aceitar os presentes Termos e Condições</li>
                </ul>
                <p>
                    A BioBrassica reserva-se o direito de não aceitar uma encomenda, nomeadamente
                    em caso de incumprimento destes Termos, falta de stock, impossibilidade de entrega
                    ou suspeita de fraude.
                </p>

                <h2>4. Pagamentos</h2>
                <p>
                    Os pagamentos podem ser efetuados através dos meios disponibilizados no website.
                    Todas as transações são encriptadas e processadas de forma segura. A encomenda
                    só será processada após confirmação do pagamento.
                </p>

                <h2>5. Entregas</h2>
                <p>
                    As entregas são efetuadas nas zonas geográficas indicadas no website. Os prazos
                    de entrega são indicados no momento da encomenda e podem variar consoante a
                    disponibilidade dos produtos e a localização de entrega.
                </p>
                <p>
                    O risco de perda ou dano dos produtos transfere-se para o cliente no momento
                    da entrega. Qualquer dano visível na embalagem deve ser reportado no momento
                    da receção.
                </p>

                <h2>6. Devoluções e Reembolsos</h2>
                <p>
                    Nos termos da legislação aplicável, o consumidor tem o direito de livre resolução
                    do contrato no prazo de 14 dias a contar da receção dos produtos, sem necessidade
                    de indicar o motivo.
                </p>
                <p>
                    Para exercer este direito, o cliente deve comunicar a sua decisão à BioBrassica
                    por escrito, através dos contactos disponibilizados, e devolver os produtos nas
                    mesmas condições em que os recebeu. Os custos de devolução são suportados pelo cliente.
                </p>

                <h2>7. Propriedade Intelectual</h2>
                <p>
                    Todos os conteúdos do website (textos, imagens, logótipos, marcas, etc.)
                    são propriedade da BioBrassica ou de terceiros que autorizaram a sua utilização.
                    É proibida a reprodução, distribuição ou modificação dos conteúdos sem autorização prévia.
                </p>

                <h2>8. Responsabilidade</h2>
                <p>
                    A BioBrassica não se responsabiliza por danos causados por utilizações indevidas
                    dos produtos, interrupções no website, vírus informáticos ou outros elementos nocivos,
                    ou informações prestadas por terceiros.
                </p>

                <h2>9. Proteção de Dados</h2>
                <p>
                    O tratamento dos dados pessoais dos clientes é efetuado de acordo com a nossa
                    <a href="{{ route('website.privacy') }}">Política de Privacidade</a> e com a legislação
                    de proteção de dados aplicável.
                </p>

                <h2>10. Lei Aplicável e Foro Competente</h2>
                <p>
                    Os presentes Termos e Condições são regidos pela lei portuguesa. Para a resolução
                    de quaisquer litígios emergentes, é competente o foro da comarca de Guimarães,
                    com expressa renúncia a qualquer outro.
                </p>

                <h2>11. Alterações</h2>
                <p>
                    A BioBrassica reserva-se o direito de alterar estes Termos e Condições a qualquer
                    momento. As alterações serão publicadas no website e, no caso de encomendas já
                    efetuadas, aplicam-se os Termos em vigor na data da encomenda.
                </p>
            </article>
        @endif
    </div>
</section>
@endsection
