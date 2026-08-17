<?php

namespace Database\Seeders;

use App\Models\WebsiteContent;
use Illuminate\Database\Seeder;

class BiobrassicaContentSeeder extends Seeder
{
    public function run(): void
    {
        WebsiteContent::query()->updateOrCreate(['id' => 1], [
            'company_legal_name' => 'Biobrassica, Lda.',
            'company_address' => 'R. dos Capelistas 121, 4700-215 Braga',
            'company_nif' => null,
            'support_email' => 'geral@biobrassica.pt',
            'whatsapp_number' => '+351938722638',
            'hero_title' => "Tudo que precisa para uma\nalimentação saudável",
            'hero_subtitle' => 'Conheça a nossa seleção de produtos biológicos disponíveis nas nossas lojas em Braga e Guimarães.',
            'about_title' => 'Do campo à sua mesa, com quem conhece a terra',
            'about_content' => $this->aboutContent(),
            'agriculture_title' => 'Agricultura Biológica',
            'agriculture_content' => $this->agricultureContent(),
            'contacts_title' => 'Encontre-nos',
            'contacts_content' => 'Visite-nos nas nossas lojas ou entre em contacto por telefone e email.',
            'footer_about' => 'Produtos biológicos selecionados no Minho.',
            'footer_address' => 'Lojas em Braga e Guimarães',
            'footer_email' => 'geral@biobrassica.pt',
            'footer_phone' => '+351 938 722 638',
            'seo_title' => 'Biobrassica — Produtos biológicos no Minho',
            'seo_description' => 'Biobrassica — produtos biológicos selecionados com cuidado no coração do Minho.',
            'seo_keywords' => 'biobrassica, biológico, agricultura biológica, produtos biológicos, Braga, Guimarães',
            'instagram_url' => 'https://www.instagram.com/biobrassica/',
            'privacy_policy_text' => $this->privacyText(),
            'terms_conditions_text' => $this->termsText(),
            'shop_coming_soon' => true,
        ]);
    }

    private function aboutContent(): string
    {
        return <<<'MARKDOWN'
## O que significa "Biobrassica"

O nome "Biobrassica" junta duas ideias que orientam tudo o que fazemos: Bio, pela agricultura biológica e por um modo de produção responsável, e brassica, em homenagem à família de hortícolas que simboliza a origem agrícola da nossa região.

## Como escolhemos os produtos

Somos, acima de tudo, uma loja. Escolhemos produtos de época com foco em frescura, origem e consistência, trabalhando com fornecedores e produtores de confiança alinhados com os nossos valores. A qualidade é acompanhada diariamente em loja, desde a receção ao acondicionamento e à exposição, para garantir produtos frescos, seguros e com origem clara para os nossos clientes.

## A nossa quinta biológica

A nossa quinta biológica é um projeto complementar, em pequena escala, que apoia a atividade da loja. Serve para reforçar alguns produtos e manter ligação direta à terra, sem substituir a nossa atividade principal: selecionar e disponibilizar, em loja, produtos de qualidade para a comunidade.
MARKDOWN;
    }

    private function agricultureContent(): string
    {
        return <<<'MARKDOWN'
A agricultura biológica é um sistema de produção que respeita os ciclos naturais, promove a biodiversidade e proíbe o uso de pesticidas e fertilizantes químicos de síntese. Na Biobrassica, estas práticas são o coração de tudo o que fazemos.

## Porquê biológico?

A agricultura biológica não é apenas uma forma de produzir alimentos — é uma filosofia de vida que respeita o equilíbrio natural dos ecossistemas. Ao evitar pesticidas e fertilizantes químicos, protegemos a biodiversidade, a qualidade da água e a saúde do solo.

Para o consumidor, os alimentos biológicos significam mais sabor, mais nutrientes e a garantia de que cada mordida está livre de resíduos químicos. É uma escolha consciente para a saúde da família e do planeta.

Na região do Minho, a riqueza do solo e o clima atlântico criam condições ideais para a agricultura biológica, permitindo-nos cultivar uma enorme variedade de produtos ao longo do ano.
MARKDOWN;
    }

    private function privacyText(): string
    {
        return 'A Biobrassica trata os dados pessoais de acordo com o Regulamento Geral sobre a Proteção de Dados (RGPD), apenas para gestão de contactos e comunicações relacionadas com os nossos serviços.';
    }

    private function termsText(): string
    {
        return 'Ao utilizar o website Biobrassica aceita as condições de utilização indicadas. O catálogo de produtos é meramente informativo. Para adquirir produtos, visite as nossas lojas físicas em Braga e Guimarães.';
    }
}
