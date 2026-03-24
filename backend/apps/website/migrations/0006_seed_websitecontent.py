from django.db import migrations


def seed_website_content(apps, schema_editor):
    WebsiteContent = apps.get_model('website', 'WebsiteContent')

    if WebsiteContent.objects.exists():
        return

    WebsiteContent.objects.create(
        home_hero_title_line1='Tudo que precisa para uma',
        home_hero_title_line2='alimentação saudável',
        home_hero_tagline='Produtos biológicos, saudáveis para si, bons para o ambiente.',
        home_quote_text=(
            'Temos conseguido ao longo destes anos oferecer cada vez mais produtos frescos, '
            'colhidos no próprio dia, vindos das mãos de produtores que se levantam às 5h da manhã '
            'num esforço último de transmitir a vitalidade e qualidade das suas terras aos consumidores '
            'que já se haviam esquecido do sabor e do cheiro dos legumes acabados de colher!'
        ),
        home_quote_author='Engª Ângela Pereira',
        home_quote_role='Fundadora',
        home_shop_cta_title='Descubra os nossos produtos',
        home_shop_cta_body='Entrega em todo o Portugal continental ou levantamento nas nossas lojas em Braga e Guimarães.',
        about_hero_title='Do campo à sua mesa, com quem conhece a terra',
        about_hero_subtitle='Pessoas reais, produtos de confiança',
        about_meaning_title='O que significa "Biobrassica"',
        about_meaning_body=(
            'O nome "Biobrassica" junta duas ideias que orientam tudo o que fazemos: Bio, pela '
            'agricultura biológica e por um modo de produção responsável, e brassica, em homenagem '
            'à família de hortícolas que simboliza a origem agrícola da nossa região.'
        ),
        about_selection_title='Como escolhemos os produtos',
        about_selection_body=(
            'Somos, acima de tudo, uma loja. Escolhemos produtos de época com foco em frescura, origem e '
            'consistência, trabalhando com fornecedores e produtores de confiança alinhados com os nossos valores. '
            'A qualidade é acompanhada diariamente em loja, desde a receção ao acondicionamento e à exposição, '
            'para garantir produtos frescos, seguros e com origem clara para os nossos clientes.'
        ),
        about_farm_title='A nossa quinta biológica',
        about_farm_body=(
            'A nossa quinta biológica é um projeto complementar, em pequena escala, que apoia a atividade da loja. '
            'Serve para reforçar alguns produtos e manter ligação direta à terra, sem substituir a nossa atividade principal: '
            'selecionar e disponibilizar, em loja, produtos de qualidade para a comunidade.'
        ),
        about_video_title='Conheça os nossos espaços',
        about_video_body='Visite as nossas lojas em Braga e Guimarães para conhecer os nossos produtos e a nossa equipa.',
        agriculture_intro_text=(
            'A agricultura biológica é um sistema de produção que respeita os ciclos naturais, promove a biodiversidade '
            'e proíbe o uso de pesticidas e fertilizantes químicos de síntese. Na Biobrassica, estas práticas são o coração '
            'de tudo o que fazemos.'
        ),
        agriculture_why_title='Porquê biológico?',
        agriculture_why_body=(
            'A agricultura biológica não é apenas uma forma de produzir alimentos — é uma filosofia de vida que respeita o '
            'equilíbrio natural dos ecossistemas. Ao evitar pesticidas e fertilizantes químicos, protegemos a biodiversidade, '
            'a qualidade da água e a saúde do solo.\n\n'
            'Para o consumidor, os alimentos biológicos significam mais sabor, mais nutrientes e a garantia de que cada mordida '
            'está livre de resíduos químicos. É uma escolha consciente para a saúde da família e do planeta.\n\n'
            'Na região do Minho, a riqueza do solo e o clima atlântico criam condições ideais para a agricultura biológica, '
            'permitindo-nos cultivar uma enorme variedade de produtos ao longo do ano.'
        ),
        contacts_hero_title='Encontre-nos',
        contacts_hero_body='Visite-nos nas nossas lojas ou entre em contacto por telefone e email.',
        whatsapp_number='+351938722638',
    )


def unseed_website_content(apps, schema_editor):
    WebsiteContent = apps.get_model('website', 'WebsiteContent')
    WebsiteContent.objects.filter(
        home_hero_title_line1='Tudo que precisa para uma',
        home_hero_title_line2='alimentação saudável',
        home_quote_author='Engª Ângela Pereira',
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0005_websitecontent'),
    ]

    operations = [
        migrations.RunPython(seed_website_content, unseed_website_content),
    ]