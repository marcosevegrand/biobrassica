<?php

namespace Database\Seeders;

use App\Models\Category;
use App\Models\CategoryPosition;
use App\Models\Location;
use App\Models\LocationPosition;
use App\Models\Product;
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
            'hero_cta_text' => 'Descubra os nossos produtos',
            'hero_cta_url' => '/catalogo',
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
        ]);

        $locations = [
            ['code' => 'braga', 'name' => 'Loja Braga', 'address' => "Avenida Doutor António Palha\nBraga", 'phone' => '253 271 187', 'image' => 'images/shop/loja-braga.webp', 'map' => 'https://maps.google.com/maps?q=Biobr%C3%A1ssica+Braga+Avenida+Doutor+Ant%C3%B3nio+Palha&t=&z=16&ie=UTF8&iwloc=&output=embed'],
            ['code' => 'guimaraes', 'name' => 'Loja Guimarães', 'address' => "Rua Calouste Gulbenkian\nGuimarães", 'phone' => '253 145 388', 'image' => 'images/shop/loja-guima.webp', 'map' => 'https://maps.google.com/maps?q=Biobr%C3%A1ssica+Guimar%C3%A3es+Rua+Calouste+Gulbenkian&t=&z=16&ie=UTF8&iwloc=&output=embed'],
        ];

        foreach ($locations as $index => $locationData) {
            $location = Location::query()->updateOrCreate(['pickup_location_code' => $locationData['code']], [
                'name' => $locationData['name'],
                'address' => $locationData['address'],
                'image' => $locationData['image'],
                'phone' => $locationData['phone'],
                'email' => 'geral@biobrassica.pt',
                'opening_hours' => "Segunda a Sábado\n9h00 – 19h30",
                'pickup_hours' => null,
                'map_embed_url' => $locationData['map'],
                'is_active' => true,
            ]);

            LocationPosition::query()->updateOrCreate(['location_id' => $location->id], ['position' => $index + 1]);
        }

        $categoryRows = [
            ['slug' => 'frescos-biologicos', 'name' => 'Frescos Biológicos', 'message' => 'Hortícolas e fruta de época selecionados com cuidado.'],
            ['slug' => 'mercearia-bio', 'name' => 'Mercearia Bio', 'message' => 'Essenciais biológicos para a despensa.'],
            ['slug' => 'cabazes', 'name' => 'Cabazes', 'message' => 'Seleções sazonais para simplificar a sua semana.'],
        ];

        $categories = [];
        foreach ($categoryRows as $index => $row) {
            $category = Category::query()->updateOrCreate(['slug' => $row['slug']], [
                'name' => $row['name'],
                'is_active' => true,
                'is_special' => $row['slug'] === 'cabazes',
                'featured_message' => $row['message'],
            ]);
            CategoryPosition::query()->updateOrCreate(['category_id' => $category->id], ['position' => $index + 1]);
            $categories[$row['slug']] = $category;
        }

        $products = [
            ['category' => 'frescos-biologicos', 'slug' => 'tomate-bio', 'name' => 'Tomate Bio', 'description' => 'Tomate biológico de época, selecionado pela frescura e sabor.', 'quantity' => '1 kg', 'image' => 'images/products/001.jpg'],
            ['category' => 'frescos-biologicos', 'slug' => 'brocolos-bio', 'name' => 'Brócolos Bio', 'description' => 'Brócolos biológicos frescos, ideais para refeições nutritivas.', 'quantity' => 'unidade', 'image' => 'images/products/002.jpg'],
            ['category' => 'mercearia-bio', 'slug' => 'massa-bio-500g', 'name' => 'Massa Bio', 'description' => 'Massa biológica para a sua mercearia do dia-a-dia.', 'quantity' => '500 g', 'image' => 'images/products/003.jpg'],
            ['category' => 'cabazes', 'slug' => 'cabaz-sazonal-bio', 'name' => 'Cabaz Sazonal Bio', 'description' => 'Cabaz com produtos biológicos selecionados de acordo com a época.', 'quantity' => 'cabaz', 'image' => 'images/products/006.jpg'],
        ];

        foreach ($products as $row) {
            Product::query()->updateOrCreate(['slug' => $row['slug']], [
                'category_id' => $categories[$row['category']]->id,
                'name' => $row['name'],
                'brand' => 'Biobrassica',
                'bio_code' => 'PT-BIO-03',
                'description' => $row['description'],
                'allergens' => 'Sem indicação de alergénicos',
                'quantity' => $row['quantity'],
                'is_active' => true,
                'is_highlight' => true,
                'image' => $row['image'],
            ]);
        }
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
