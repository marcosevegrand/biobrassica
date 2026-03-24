#!/usr/bin/env python3
"""
Comprehensive translation fixer for Biobrassica .po files.
Fills in all missing website translations and corrects bad fuzzy entries.
"""
import os
import re

BASE = os.environ.get("LOCALE_BASE", "/app/locale")

# ---------------------------------------------------------------------------
# Helper: replace exactly one occurrence of a block in the file.
# A "block" is:  optional-flags\nmsgid "..."\nmsgstr "..."
# We match on magid_key and replace msgstr + optionally strip fuzzy flags.
# ---------------------------------------------------------------------------

def replace_entry(text, msgid_key, new_msgstr_lines, remove_fuzzy=True):
    """
    Find the block containing msgid_key and replace its msgstr section.
    msgid_key: a unique substring of the msgid (no need to match whole thing).
    new_msgstr_lines: list of strings, each will be wrapped in quotes on a new line.
                      If only one item, outputs  msgstr "single line"
                      If multiple items, outputs  msgstr ""\n"line1"\n"line2"...
    remove_fuzzy: if True, strip any preceding #, fuzzy or #, python-format, fuzzy line.
    Returns updated text.
    """
    escaped_key = re.escape(msgid_key)

    # Pattern: optional fuzzy comment, msgid block spanning one or more lines, then msgstr block
    pattern = (
        r'(#,\s*(?:python-format,\s*)?fuzzy\n)?'  # optional fuzzy flag
        r'((?:#\|[^\n]*\n)*)'                        # optional #| old msgid lines
        r'(msgid "(?:[^"\\]|\\.)*"(?:\n"(?:[^"\\]|\\.)*")*\n)'  # msgid (multiline)
        r'(msgstr "(?:[^"\\]|\\.)*"(?:\n"(?:[^"\\]|\\.)*")*)'    # msgstr (multiline)
    )

    def replacer(m):
        fuzzy_line = m.group(1) or ""
        old_ref = m.group(2)
        msgid_block = m.group(3)
        # Check that the msgid contains our key
        if msgid_key not in msgid_block:
            return m.group(0)  # not our target, skip

        new_fuzzy = "" if remove_fuzzy else fuzzy_line
        # Build new msgstr
        if len(new_msgstr_lines) == 1:
            # Single-line: check if it actually needs wrapping (gettext wraps at 80)
            line = new_msgstr_lines[0]
            if len('msgstr "' + line + '"') <= 80:
                new_msgstr = f'msgstr "{line}"'
            else:
                # wrap ourselves
                new_msgstr = 'msgstr ""\n' + _wrap_lines(line)
        else:
            new_msgstr = 'msgstr ""\n' + "\n".join(f'"{l}"' for l in new_msgstr_lines)

        return f'{new_fuzzy}{old_ref}{msgid_block}{new_msgstr}'

    new_text = re.sub(pattern, replacer, text, flags=re.DOTALL)
    if new_text == text:
        print(f"  WARNING: could not find entry with key: {msgid_key!r}")
    return new_text


def _wrap_lines(s):
    """Simple line-wrapper for long strings in .po files (80 char limit)."""
    words = s.split(" ")
    lines = []
    current = ""
    for w in words:
        if len(current) + len(w) + 1 <= 78:
            current = current + (" " if current else "") + w
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)
    return "\n".join(f'"{l}"' for l in lines)


def update_po(lang, updates):
    """
    Apply a list of (msgid_key, new_msgstr_lines, remove_fuzzy) tuples to a .po file.
    """
    path = os.path.join(BASE, lang, "LC_MESSAGES", "django.po")
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    for item in updates:
        if len(item) == 2:
            key, new_str = item
            remove_fuzzy = True
        else:
            key, new_str, remove_fuzzy = item

        if isinstance(new_str, str):
            new_str = [new_str]

        text = replace_entry(text, key, new_str, remove_fuzzy=remove_fuzzy)

    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"Updated {lang} ({len(updates)} entries)")


# ---------------------------------------------------------------------------
# Translation data
# ---------------------------------------------------------------------------

# ---- ENGLISH ---------------------------------------------------------------
EN_UPDATES = [
    # Base template meta descriptions
    ("Loja online Biobrassica — produtos biológicos de Braga e Guimarães.",
     "Biobrassica Online Shop — organic products from Braga and Guimarães."),

    # Existing with wrong short msgstr — fix to include "Biobrassica — " prefix
    # (It was already translated as "Organic products carefully selected..."
    #  which is missing the brand prefix — leave as-is since it's a meta desc)

    # Cart/order/payment messages
    ("Indique uma quantidade válida.", "Please enter a valid quantity."),
    ("A quantidade foi ajustada ao stock disponível.",
     "The quantity has been adjusted to the available stock."),
    ("Este carrinho contém produtos disponíveis apenas para levantamento em loja.",
     "This cart contains products available for in-store pickup only."),
    ("Preencha a morada de envio completa.", "Please fill in the full shipping address."),
    ("Use o formato 1234-123.", "Use the format 1234-123."),
    ("Selecione um método de pagamento válido.", "Please select a valid payment method."),
    ("Nenhum produto do seu carrinho tem stock disponível.",
     "None of the products in your cart have available stock."),
    ("Ajustámos o seu carrinho devido a limitações de stock.",
     ["We have adjusted your cart due to stock limitations. Please review the",
      " items below and try again."]),
    ("%(product)s: reduzido de %(requested)d para %(available)d unidades.",
     "%(product)s: reduced from %(requested)d to %(available)d units."),
    ("%(product)s: removido (sem stock disponível).",
     "%(product)s: removed (no stock available)."),
    ("Não foi possível validar os dados da encomenda.", "Unable to validate the order details."),
    ("Alguns produtos já não têm stock suficiente. Revise o carrinho",
     ["Some products no longer have sufficient stock. Please review your cart",
      " and try again."]),
    ("Não foi possível criar a encomenda. Verifique os dados",
     "Unable to create the order. Please check the details and try again."),
    ("Não foi possível iniciar o pagamento. Tente novamente.",
     "Unable to initiate payment. Please try again."),
    ("Não foi possível preparar o pagamento. Tente novamente.",
     "Unable to prepare payment. Please try again."),
    ("Ainda não existe um pagamento associado a esta encomenda.",
     "No payment has been associated with this order yet."),
    ("O pedido de pagamento expirou. Pode iniciar um novo pedido MB WAY.",
     "The payment request has expired. You can initiate a new MB WAY request."),
    ("Não foi possível atualizar o estado do pagamento. Tente novamente.",
     "Unable to update the payment status. Please try again."),
    ("O pagamento MB WAY não foi confirmado. Pode tentar novamente.",
     "The MB WAY payment was not confirmed. You can try again."),

    # Order history / accounts
    ("Envio:", "Shipping:"),

    # Product / catalog
    ("Envio disponível", "Delivery available"),
    ("Descrição", "Description"),
    ("Marca", "Brand"),
    ("Alergénicos", "Allergens"),
    ("Código Bio", "Organic Code"),

    # Recipes
    ("Prep", "Prep"),
    ("Encontre estes produtos na nossa loja online.", "Find these products in our online shop."),

    # Checkout / delivery
    ("Recolha numa das lojas disponíveis.", "Pick up at one of the available stores."),
    # Note: "Envio" as delivery method label (not "Envio:")
    # We identify it carefully by context — it appears right after "Levantamento"
    # Use unique enough key to avoid collision
    ("msgid \"Envio\"\nmsgstr \"\"",  # raw key trick – we'll handle this manually below
     "Delivery"),  # handled below with direct replace

    ("Entrega ao domicílio em Portugal continental.",
     "Home delivery to mainland Portugal."),
    ("Código Postal", "Postal Code"),
    ("foi confirmado.", "has been confirmed."),
    ("De momento, o pagamento está disponível apenas por MB WAY.",
     "At the moment, payment is only available via MB WAY."),
    ("Utilize os dados abaixo para concluir o pagamento.",
     ["Use the details below to complete the payment. The order is only",
      " confirmed after automatic validation."]),
    ("O pedido de pagamento foi enviado para o telemóvel indicado.",
     ["The payment request has been sent to the indicated mobile phone. After",
      " authorising in MB WAY, refresh this page."]),
    ("Telemóvel", "Mobile"),
    ("Se o pagamento ainda não estiver concluído",
     ["If the payment is not yet complete, reopen the secure operator page to",
      " finalise the transaction."]),
    ("Atualizar estado", "Refresh status"),
    ("Escolher outro método", "Choose another method"),
    ("Adicionar %(name)s", "Add %(name)s"),

    # Website pages — about
    ("Conheça a equipa que acompanha diariamente o atendimento",
     "Meet the team that looks after customer service, purchasing, and store curation every day."),

    # Website pages — agriculture (the "Porquê biológico?" body)
    ("A agricultura biológica não é apenas uma forma de produzir alimentos",
     [
         "Organic farming is not just a way of producing food \u2014 it is a life",
         " philosophy that respects the natural balance of ecosystems. By avoiding",
         " pesticides and chemical fertilisers, we protect biodiversity, water",
         " quality, and soil health.\\n",
         "\\n",
         "For the consumer, organic food means more flavour, more nutrients, and",
         " the assurance that every bite is free from chemical residues. It is a",
         " conscious choice for the health of the family and the planet.\\n",
         "\\n",
         "In the Minho region, the richness of the soil and the Atlantic climate",
         " create ideal conditions for organic farming, allowing us to grow an",
         " enormous variety of products throughout the year.",
     ]),

    # Website pages — contacts
    ("As localizações serão apresentadas aqui assim que forem configuradas no backoffice.",
     "Locations will be displayed here once they have been set up in the backoffice."),

    # Website pages — home hero
    ("Tudo que precisa para uma", "Everything you need for a"),
    ("alimentação saudável", "healthy diet"),

    # Privacy policy
    ("Os registos técnicos de callbacks de pagamento são minimizados",
     [
         "Technical payment callback records are minimised, with anonymised IP and",
         " internal retention limited to the strictly necessary operational period.",
     ]),
]

# ---- FRENCH ----------------------------------------------------------------
FR_UPDATES = [
    # Base template meta descriptions
    ("Loja online Biobrassica — produtos biológicos de Braga e Guimarães.",
     "Boutique en ligne Biobrassica — produits biologiques de Braga et Guimarães."),

    # Cart/order/payment messages
    ("Indique uma quantidade válida.", "Veuillez indiquer une quantité valide."),
    ("A quantidade foi ajustada ao stock disponível.",
     "La quantité a été ajustée au stock disponible."),
    ("Este carrinho contém produtos disponíveis apenas para levantamento em loja.",
     "Ce panier contient des produits disponibles uniquement en retrait en magasin."),
    ("Preencha a morada de envio completa.", "Veuillez remplir l'adresse de livraison complète."),
    ("Use o formato 1234-123.", "Utilisez le format 1234-123."),
    ("Selecione um método de pagamento válido.",
     "Veuillez sélectionner un mode de paiement valide."),
    ("Nenhum produto do seu carrinho tem stock disponível.",
     "Aucun produit de votre panier n'est disponible en stock."),
    ("Ajustámos o seu carrinho devido a limitações de stock.",
     ["Nous avons ajusté votre panier en raison de limitations de stock. Veuillez",
      " vérifier les articles ci-dessous et réessayer."]),
    ("%(product)s: reduzido de %(requested)d para %(available)d unidades.",
     "%(product)s : réduit de %(requested)d à %(available)d unités."),
    ("%(product)s: removido (sem stock disponível).",
     "%(product)s : retiré (aucun stock disponible)."),
    ("Não foi possível validar os dados da encomenda.",
     "Impossible de valider les données de la commande."),
    ("Alguns produtos já não têm stock suficiente. Revise o carrinho",
     ["Certains produits n'ont plus de stock suffisant. Veuillez vérifier votre",
      " panier et réessayer."]),
    ("Não foi possível criar a encomenda. Verifique os dados",
     "Impossible de créer la commande. Veuillez vérifier les données et réessayer."),
    ("Não foi possível iniciar o pagamento. Tente novamente.",
     "Impossible de lancer le paiement. Veuillez réessayer."),
    ("Não foi possível preparar o pagamento. Tente novamente.",
     "Impossible de préparer le paiement. Veuillez réessayer."),
    ("Ainda não existe um pagamento associado a esta encomenda.",
     "Aucun paiement n'est encore associé à cette commande."),
    ("O pedido de pagamento expirou. Pode iniciar um novo pedido MB WAY.",
     "La demande de paiement a expiré. Vous pouvez initier une nouvelle demande MB WAY."),
    ("Não foi possível atualizar o estado do pagamento. Tente novamente.",
     "Impossible de mettre à jour le statut du paiement. Veuillez réessayer."),
    ("O pagamento MB WAY não foi confirmado. Pode tentar novamente.",
     "Le paiement MB WAY n'a pas été confirmé. Vous pouvez réessayer."),

    # Order history
    ("Envio:", "Expédition :"),

    # Product / catalog
    ("Envio disponível", "Livraison disponible"),
    ("Descrição", "Description"),
    ("Marca", "Marque"),
    ("Alergénicos", "Allergènes"),
    ("Código Bio", "Code bio"),

    # Recipes
    ("Prep", "Prép."),
    ("Encontre estes produtos na nossa loja online.",
     "Retrouvez ces produits dans notre boutique en ligne."),

    # Checkout / delivery
    ("Recolha numa das lojas disponíveis.", "Retirez dans l'un des magasins disponibles."),
    ("Entrega ao domicílio em Portugal continental.",
     "Livraison à domicile au Portugal continental."),
    ("Código Postal", "Code postal"),
    ("foi confirmado.", "a été confirmé."),
    ("De momento, o pagamento está disponível apenas por MB WAY.",
     "Pour le moment, le paiement est disponible uniquement via MB WAY."),
    ("Utilize os dados abaixo para concluir o pagamento.",
     ["Utilisez les informations ci-dessous pour finaliser le paiement. La commande",
      " n'est confirmée qu'après validation automatique."]),
    ("O pedido de pagamento foi enviado para o telemóvel indicado.",
     ["La demande de paiement a été envoyée au numéro de téléphone indiqué. Après",
      " autorisation dans MB WAY, actualisez cette page."]),
    ("Telemóvel", "Téléphone"),
    ("Se o pagamento ainda não estiver concluído",
     ["Si le paiement n'est pas encore finalisé, rouvrez la page sécurisée de",
      " l'opérateur pour terminer la transaction."]),
    ("Atualizar estado", "Actualiser le statut"),
    ("Escolher outro método", "Choisir une autre méthode"),
    ("Adicionar %(name)s", "Ajouter %(name)s"),

    # Website pages — about
    ("Conheça a equipa que acompanha diariamente o atendimento",
     [
         "Rencontrez l'équipe qui s'occupe quotidiennement de l'accueil, de",
         " l'approvisionnement et de la curation du magasin.",
     ]),

    # Website pages — agriculture (the "Porquê biológico?" body)
    ("A agricultura biológica não é apenas uma forma de produzir alimentos",
     [
         "L'agriculture biologique n'est pas seulement une façon de produire des",
         " aliments \\u2014 c'est une philosophie de vie qui respecte l'équilibre naturel",
         " des écosystèmes. En évitant pesticides et engrais chimiques, nous",
         " protégeons la biodiversité, la qualité de l'eau et la santé des sols.\\n",
         "\\n",
         "Pour le consommateur, les aliments biologiques signifient plus de saveur,",
         " plus de nutriments et la garantie que chaque bouchée est exempte de",
         " résidus chimiques. C'est un choix conscient pour la santé de la famille",
         " et de la planète.\\n",
         "\\n",
         "Dans la région du Minho, la richesse des sols et le climat atlantique",
         " créent des conditions idéales pour l'agriculture biologique, nous",
         " permettant de cultiver une grande variété de produits tout au long de",
         " l'année.",
     ]),

    # Website pages — contacts
    ("As localizações serão apresentadas aqui assim que forem configuradas no backoffice.",
     ["Les emplacements seront affichés ici une fois configurés dans le",
      " back-office."]),

    # Website pages — home hero
    ("Tudo que precisa para uma", "Tout ce qu'il vous faut pour une"),
    ("alimentação saudável", "alimentation saine"),

    # Privacy policy
    ("Os registos técnicos de callbacks de pagamento são minimizados",
     [
         "Les enregistrements techniques des callbacks de paiement sont minimisés,",
         " avec IP anonymisée et rétention interne limitée à la durée opérationnelle",
         " strictement nécessaire.",
     ]),

    # Wrong fuzzy: "Fundadora" → "Fondatrice" (not "Fondée")
    ("Fundadora", "Fondatrice"),
]

# ---- PORTUGUESE (identity translations) -----------------------------------
PT_UPDATES = [
    # Base template meta descriptions
    ("Loja online Biobrassica — produtos biológicos de Braga e Guimarães.",
     "Loja online Biobrassica — produtos biológicos de Braga e Guimarães."),

    # Cart/order/payment messages
    ("Indique uma quantidade válida.", "Indique uma quantidade válida."),
    ("A quantidade foi ajustada ao stock disponível.",
     "A quantidade foi ajustada ao stock disponível."),
    ("Este carrinho contém produtos disponíveis apenas para levantamento em loja.",
     "Este carrinho contém produtos disponíveis apenas para levantamento em loja."),
    ("Preencha a morada de envio completa.", "Preencha a morada de envio completa."),
    ("Use o formato 1234-123.", "Use o formato 1234-123."),
    ("Selecione um método de pagamento válido.", "Selecione um método de pagamento válido."),
    ("Nenhum produto do seu carrinho tem stock disponível.",
     "Nenhum produto do seu carrinho tem stock disponível."),
    ("Ajustámos o seu carrinho devido a limitações de stock.",
     ["Ajustámos o seu carrinho devido a limitações de stock. Verifique os",
      " produtos abaixo e tente novamente."]),
    ("%(product)s: reduzido de %(requested)d para %(available)d unidades.",
     "%(product)s: reduzido de %(requested)d para %(available)d unidades."),
    ("%(product)s: removido (sem stock disponível).",
     "%(product)s: removido (sem stock disponível)."),
    ("Não foi possível validar os dados da encomenda.",
     "Não foi possível validar os dados da encomenda."),
    ("Alguns produtos já não têm stock suficiente. Revise o carrinho",
     ["Alguns produtos já não têm stock suficiente. Revise o carrinho e tente",
      " novamente."]),
    ("Não foi possível criar a encomenda. Verifique os dados",
     "Não foi possível criar a encomenda. Verifique os dados e tente novamente."),
    ("Não foi possível iniciar o pagamento. Tente novamente.",
     "Não foi possível iniciar o pagamento. Tente novamente."),
    ("Não foi possível preparar o pagamento. Tente novamente.",
     "Não foi possível preparar o pagamento. Tente novamente."),
    ("Ainda não existe um pagamento associado a esta encomenda.",
     "Ainda não existe um pagamento associado a esta encomenda."),
    ("O pedido de pagamento expirou. Pode iniciar um novo pedido MB WAY.",
     "O pedido de pagamento expirou. Pode iniciar um novo pedido MB WAY."),
    ("Não foi possível atualizar o estado do pagamento. Tente novamente.",
     "Não foi possível atualizar o estado do pagamento. Tente novamente."),
    ("O pagamento MB WAY não foi confirmado. Pode tentar novamente.",
     "O pagamento MB WAY não foi confirmado. Pode tentar novamente."),

    # Order history
    ("Envio:", "Envio:"),

    # Product / catalog
    ("Envio disponível", "Envio disponível"),
    ("Descrição", "Descrição"),
    ("Marca", "Marca"),
    ("Alergénicos", "Alergénicos"),
    ("Código Bio", "Código Bio"),

    # Recipes
    ("Prep", "Prep"),
    ("Encontre estes produtos na nossa loja online.",
     "Encontre estes produtos na nossa loja online."),

    # Checkout / delivery
    ("Recolha numa das lojas disponíveis.", "Recolha numa das lojas disponíveis."),
    ("Entrega ao domicílio em Portugal continental.",
     "Entrega ao domicílio em Portugal continental."),
    ("Código Postal", "Código Postal"),
    ("foi confirmado.", "foi confirmado."),
    ("De momento, o pagamento está disponível apenas por MB WAY.",
     "De momento, o pagamento está disponível apenas por MB WAY."),
    ("Utilize os dados abaixo para concluir o pagamento.",
     ["Utilize os dados abaixo para concluir o pagamento. A encomenda só fica",
      " confirmada após validação automática."]),
    ("O pedido de pagamento foi enviado para o telemóvel indicado.",
     ["O pedido de pagamento foi enviado para o telemóvel indicado. Depois de",
      " autorizar no MB WAY, atualize esta página."]),
    ("Telemóvel", "Telemóvel"),
    ("Se o pagamento ainda não estiver concluído",
     ["Se o pagamento ainda não estiver concluído, reabra a página segura do",
      " operador para finalizar a transação."]),
    ("Atualizar estado", "Atualizar estado"),
    ("Escolher outro método", "Escolher outro método"),
    ("Adicionar %(name)s", "Adicionar %(name)s"),

    # Website pages — about
    ("Conheça a equipa que acompanha diariamente o atendimento",
     ["Conheça a equipa que acompanha diariamente o atendimento, o",
      " aprovisionamento e a curadoria da loja."]),

    # Website pages — agriculture (identity)
    ("A agricultura biológica não é apenas uma forma de produzir alimentos",
     [
         "A agricultura biológica não é apenas uma forma de produzir alimentos",
         " \u2014 é uma filosofia de vida que respeita o equilíbrio natural dos",
         " ecossistemas. Ao evitar pesticidas e fertilizantes químicos, protegemos",
         " a biodiversidade, a qualidade da água e a saúde do solo.\\n",
         "\\n",
         "Para o consumidor, os alimentos biológicos significam mais sabor, mais",
         " nutrientes e a garantia de que cada mordida está livre de resíduos",
         " químicos. É uma escolha consciente para a saúde da família e do",
         " planeta.\\n",
         "\\n",
         "Na região do Minho, a riqueza do solo e o clima atlântico criam condições",
         " ideais para a agricultura biológica, permitindo-nos cultivar uma enorme",
         " variedade de produtos ao longo do ano.",
     ]),

    # Website pages — contacts
    ("As localizações serão apresentadas aqui assim que forem configuradas no backoffice.",
     "As localizações serão apresentadas aqui assim que forem configuradas no backoffice."),

    # Website pages — home hero
    ("Tudo que precisa para uma", "Tudo que precisa para uma"),
    ("alimentação saudável", "alimentação saudável"),

    # Privacy policy
    ("Os registos técnicos de callbacks de pagamento são minimizados",
     ["Os registos técnicos de callbacks de pagamento são minimizados, com IP",
      " anonimizado e retenção interna limitada ao período operacional",
      " estritamente necessário."]),
]

# ---------------------------------------------------------------------------
# Also do direct fixes for the "Envio" (delivery method) entry which has
# a very short unique msgid that could match in unexpected places.
# We handle it separately with a more precise pattern.
# ---------------------------------------------------------------------------

def fix_envio_method(lang, translation):
    """Fix the standalone 'Envio' delivery-method entry (not 'Envio:')."""
    path = os.path.join(BASE, lang, "LC_MESSAGES", "django.po")
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    # We want to match exactly:
    #   msgid "Envio"\n
    #   msgstr ""
    # but NOT "Envio:" or "Envio disponível" etc.
    pattern = r'(msgid "Envio"\n)(msgstr "")'
    replacement = rf'\1msgstr "{translation}"'
    new_text = re.sub(pattern, replacement, text, count=1)
    if new_text == text:
        print(f"  WARNING [{lang}]: could not fix standalone 'Envio' entry")
    else:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_text)
        print(f"  [{lang}] Fixed standalone 'Envio' entry")


# Also fix fuzzy wrong translations (they have wrong msgstr AND #, fuzzy)
# These need their fuzzy flag removed AND the correct msgstr set.
# The replace_entry function already handles fuzzy removal.

# Additional specific bad-fuzzy fixes for EN
EN_FUZZY_FIXES = [
    # Wrong fuzzy-derived msgstrs that are completely off
    ("Este produto está esgotado.", "This product is out of stock."),
    ("Selecione um local de levantamento.", "Select a pickup location."),
    ("O pagamento da sua encomenda", "The payment for your order"),
    ("Pagamento confirmado com sucesso.", "Payment confirmed successfully."),
    ("Instruções não disponíveis.", "Instructions not available."),
    ("Comprar Ingredientes", "Buy Ingredients"),
    ("Método de entrega", "Delivery Method"),
    ("Voltar ao checkout", "Back to checkout"),
    ("Estado do Pagamento", "Payment Status"),
    ("Referência Multibanco", "Multibanco Reference"),
    ("Quantidade", "Quantity"),
    ("Cidade", "City"),
    ("Morada (cont.)", "Address (cont.)"),
    ("Continuar pagamento", "Continue payment"),
    ("Apenas levantamento", "In-store pickup only"),
    ("Preço", "Price"),
    ("Explorar", "Browse"),
    ("Categoria em Destaque", "Featured Category"),
    ("Indique o número de telemóvel para MB WAY.", "Enter your mobile phone number for MB WAY."),
]

FR_FUZZY_FIXES = [
    ("Este produto está esgotado.", "Ce produit est épuisé."),
    ("Selecione um local de levantamento.", "Sélectionnez un lieu de retrait."),
    ("O pagamento da sua encomenda", "Le paiement de votre commande"),
    ("Pagamento confirmado com sucesso.", "Paiement confirmé avec succès."),
    ("Instruções não disponíveis.", "Instructions non disponibles."),
    ("Comprar Ingredientes", "Acheter les ingrédients"),
    ("Método de entrega", "Mode de livraison"),
    ("Voltar ao checkout", "Retour au paiement"),
    ("Estado do Pagamento", "Statut du paiement"),
    ("Referência Multibanco", "Référence Multibanco"),
    ("Quantidade", "Quantité"),
    ("Cidade", "Ville"),
    ("Morada (cont.)", "Adresse (suite)"),
    ("Continuar pagamento", "Continuer le paiement"),
    ("Apenas levantamento", "Retrait en magasin uniquement"),
    ("Preço", "Prix"),
    ("Explorar", "Parcourir"),
    ("Categoria em Destaque", "Catégorie en vedette"),
    ("Indique o número de telemóvel para MB WAY.", "Saisissez votre numéro de téléphone pour MB WAY."),
]

PT_FUZZY_FIXES = [
    ("Este produto está esgotado.", "Este produto está esgotado."),
    ("Selecione um local de levantamento.", "Selecione um local de levantamento."),
    ("O pagamento da sua encomenda", "O pagamento da sua encomenda"),
    ("Pagamento confirmado com sucesso.", "Pagamento confirmado com sucesso."),
    ("Instruções não disponíveis.", "Instruções não disponíveis."),
    ("Comprar Ingredientes", "Comprar Ingredientes"),
    ("Método de entrega", "Método de entrega"),
    ("Voltar ao checkout", "Voltar ao checkout"),
    ("Estado do Pagamento", "Estado do Pagamento"),
    ("Referência Multibanco", "Referência Multibanco"),
    ("Quantidade", "Quantidade"),
    ("Cidade", "Cidade"),
    ("Morada (cont.)", "Morada (cont.)"),
    ("Continuar pagamento", "Continuar pagamento"),
    ("Apenas levantamento", "Apenas levantamento"),
    ("Preço", "Preço"),
    ("Explorar", "Explorar"),
    ("Categoria em Destaque", "Categoria em Destaque"),
    ("Indique o número de telemóvel para MB WAY.", "Indique o número de telemóvel para MB WAY."),
]

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=== Updating EN ===")
    update_po("en", EN_UPDATES + EN_FUZZY_FIXES)

    print("=== Updating FR ===")
    update_po("fr", FR_UPDATES + FR_FUZZY_FIXES)

    print("=== Updating PT ===")
    update_po("pt", PT_UPDATES + PT_FUZZY_FIXES)

    # Fix standalone "Envio" (delivery method label)
    fix_envio_method("en", "Delivery")
    fix_envio_method("fr", "Livraison")
    fix_envio_method("pt", "Envio")

    print("=== Done ===")
