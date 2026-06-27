@extends('layouts.website')

@section('title', 'Política de Privacidade - BioBrassica')
@section('meta_description', 'Política de Privacidade da BioBrassica. Saiba como tratamos e protegemos os seus dados pessoais.')

@section('content')
<section class="relative h-[40vh] flex items-center justify-center overflow-hidden bg-gradient-to-br from-forest via-forest/90 to-forest/70">
    <div class="relative z-10 text-center px-4">
        <h1 class="font-serif text-4xl md:text-5xl font-bold text-white mb-4 drop-shadow-lg">
            Política de Privacidade
        </h1>
        <p class="text-white/70 font-light">
            Como tratamos e protegemos os seus dados
        </p>
    </div>
</section>

<section class="py-20 bg-paper">
    <div class="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
        @if(isset($websiteContent) && $websiteContent->privacy_policy_text)
            <div class="prose prose-lg max-w-none font-light leading-relaxed text-muted
                        prose-headings:font-serif prose-headings:text-forest prose-headings:font-semibold
                        prose-h2:text-2xl prose-h2:mt-10 prose-h2:mb-4
                        prose-p:mb-4
                        prose-strong:text-forest prose-strong:font-medium
                        prose-a:text-terracotta prose-a:no-underline hover:prose-a:underline
                        prose-li:mb-2">
                {!! Str::markdown($websiteContent->privacy_policy_text, ['html_input' => 'strip', 'allow_unsafe_links' => false]) !!}
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

                <h2>1. Introdução</h2>
                <p>
                    A BioBrassica respeita a sua privacidade e está empenhada em proteger os seus dados pessoais.
                    Esta Política de Privacidade descreve como recolhemos, utilizamos e protegemos as suas informações
                    quando utiliza o nosso website e serviços.
                </p>

                <h2>2. Responsável pelo Tratamento</h2>
                <p>
                    O responsável pelo tratamento dos seus dados pessoais é:
                </p>
                @if(isset($websiteDefaults))
                    <ul>
                        <li><strong>Nome:</strong> {{ $websiteDefaults->company_legal_name ?? 'BioBrassica' }}</li>
                        @if($websiteDefaults->company_address)
                            <li><strong>Morada:</strong> {{ $websiteDefaults->company_address }}</li>
                        @endif
                        @if($websiteDefaults->company_nif)
                            <li><strong>NIF:</strong> {{ $websiteDefaults->company_nif }}</li>
                        @endif
                        @if($websiteDefaults->support_email)
                            <li><strong>Email:</strong> {{ $websiteDefaults->support_email }}</li>
                        @endif
                    </ul>
                @endif

                <h2>3. Dados Pessoais Recolhidos</h2>
                <p>Podemos recolher os seguintes tipos de dados pessoais:</p>
                <ul>
                    <li><strong>Dados de contacto:</strong> nome, email, telefone, morada</li>
                    <li><strong>Dados de encomenda:</strong> histórico de compras, produtos adquiridos</li>
                    <li><strong>Dados de navegação:</strong> endereço IP, tipo de browser, páginas visitadas</li>
                </ul>

                <h2>4. Finalidade do Tratamento</h2>
                <p>Utilizamos os seus dados pessoais para as seguintes finalidades:</p>
                <ul>
                    <li>Processamento e entrega de encomendas</li>
                    <li>Comunicação sobre o estado das encomendas</li>
                    <li>Envio de newsletters e informações promocionais (com o seu consentimento)</li>
                    <li>Melhoria dos nossos serviços e website</li>
                    <li>Cumprimento de obrigações legais</li>
                </ul>

                <h2>5. Conservação dos Dados</h2>
                <p>
                    Conservamos os seus dados pessoais apenas pelo período necessário para cumprir as finalidades
                    para as quais foram recolhidos, respeitando os prazos legais aplicáveis.
                </p>

                <h2>6. Partilha de Dados</h2>
                <p>
                    Não partilhamos os seus dados pessoais com terceiros, exceto quando necessário para
                    a prestação dos nossos serviços (ex.: transportadoras para entrega de encomendas) ou
                    para cumprimento de obrigações legais.
                </p>

                <h2>7. Direitos do Titular</h2>
                <p>Nos termos da legislação aplicável, tem os seguintes direitos:</p>
                <ul>
                    <li>Direito de acesso aos seus dados</li>
                    <li>Direito de retificação dos dados incorretos</li>
                    <li>Direito de apagamento (direito ao esquecimento)</li>
                    <li>Direito de limitação do tratamento</li>
                    <li>Direito de portabilidade dos dados</li>
                    <li>Direito de oposição ao tratamento</li>
                    <li>Direito de retirar o consentimento a qualquer momento</li>
                </ul>
                <p>
                    Para exercer qualquer um destes direitos, contacte-nos através do email
                    @if(isset($websiteDefaults) && $websiteDefaults->support_email)
                        <a href="mailto:{{ $websiteDefaults->support_email }}">{{ $websiteDefaults->support_email }}</a>.
                    @endif
                </p>

                <h2>8. Cookies</h2>
                <p>
                    O nosso website utiliza cookies para melhorar a experiência de navegação. Consulte a
                    nossa Política de Cookies para mais informações.
                </p>

                <h2>9. Medidas de Segurança</h2>
                <p>
                    Implementamos medidas técnicas e organizativas adequadas para proteger os seus dados
                    pessoais contra a perda, acesso não autorizado, divulgação ou destruição.
                </p>

                <h2>10. Contacto e Reclamações</h2>
                <p>
                    Para questões sobre esta Política de Privacidade ou sobre o tratamento dos seus dados,
                    contacte-nos através de:
                </p>
                @if(isset($websiteDefaults))
                    @if($websiteDefaults->support_email)
                        <p>Email: <a href="mailto:{{ $websiteDefaults->support_email }}">{{ $websiteDefaults->support_email }}</a></p>
                    @endif
                    @if($websiteDefaults->footer_address)
                        <p>Morada: {{ $websiteDefaults->footer_address }}</p>
                    @endif
                @endif
                <p>
                    Tem também o direito de apresentar reclamação à Comissão Nacional de Proteção de Dados (CNPD)
                    em <a href="https://www.cnpd.pt" target="_blank" rel="noopener noreferrer">www.cnpd.pt</a>.
                </p>
            </article>
        @endif
    </div>
</section>
@endsection
