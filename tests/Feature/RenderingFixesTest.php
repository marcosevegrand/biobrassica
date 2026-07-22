<?php

namespace Tests\Feature;

use App\Models\Category;
use App\Models\Location;
use App\Models\Product;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class RenderingFixesTest extends TestCase
{
    use RefreshDatabase;

    // -----------------------------------------------------------------
    // 1) Category images
    // -----------------------------------------------------------------

    public function test_category_card_shows_image_when_present(): void
    {
        $category = Category::create([
            'slug' => 'frutas',
            'name' => 'Frutas',
            'image' => 'images/categories/frutas.jpg',
            'is_active' => true,
        ]);

        $response = $this->get(route('shop.home'));

        $response->assertOk()
            ->assertSee(asset('images/categories/frutas.jpg'), false)
            ->assertSee('alt="Frutas"', false)
            ->assertSee('object-cover', false);
    }

    public function test_category_card_with_storage_image_uses_asset_storage(): void
    {
        $category = Category::create([
            'slug' => 'legumes',
            'name' => 'Legumes',
            'image' => 'categories/legumes.jpg',
            'is_active' => true,
        ]);

        $response = $this->get(route('shop.home'));

        $response->assertOk()
            ->assertSee(asset('storage/categories/legumes.jpg'), false);
    }

    public function test_category_card_without_image_shows_svg_placeholder(): void
    {
        $category = Category::create([
            'slug' => 'temperos',
            'name' => 'Temperos',
            'image' => null,
            'is_active' => true,
        ]);

        $response = $this->get(route('shop.home'));

        $response->assertOk()
            ->assertSee('<svg', false);
    }

    // -----------------------------------------------------------------
    // 3) Product description rich HTML
    // -----------------------------------------------------------------

    public function test_product_detail_renders_rich_html_description(): void
    {
        $category = Category::create([
            'slug' => 'frutas',
            'name' => 'Frutas',
            'is_active' => true,
        ]);

        $product = Product::create([
            'category_id' => $category->id,
            'slug' => 'maca-bio',
            'name' => 'Maçã Bio',
            'is_active' => true,
            'description' => '<p>Maçã <strong>biológica</strong> da região.</p><ul><li>Sem pesticidas</li><li>Colheita manual</li></ul>',
        ]);

        $response = $this->get(route('catalog.product', ['slug' => 'maca-bio']));

        $response->assertOk()
            // Rendered as HTML, not escaped
            ->assertSee('<strong>biológica</strong>', false)
            ->assertSee('<ul>', false)
            ->assertSee('<li>Sem pesticidas</li>', false)
            ->assertDontSee('&lt;strong&gt;', false);
    }

    public function test_product_without_description_hides_section(): void
    {
        $category = Category::create([
            'slug' => 'frutas',
            'name' => 'Frutas',
            'is_active' => true,
        ]);

        $product = Product::create([
            'category_id' => $category->id,
            'slug' => 'pera-bio',
            'name' => 'Pera Bio',
            'is_active' => true,
            'description' => null,
        ]);

        $response = $this->get(route('catalog.product', ['slug' => 'pera-bio']));

        $response->assertOk()
            ->assertDontSee('Descrição', false);
    }

    public function test_product_description_strips_script_tags(): void
    {
        $category = Category::create([
            'slug' => 'frutas',
            'name' => 'Frutas',
            'is_active' => true,
        ]);

        $product = Product::create([
            'category_id' => $category->id,
            'slug' => 'xss-1',
            'name' => 'XSS Test',
            'is_active' => true,
            'description' => '<p>Hello</p><script>alert("xss")</script><p>World</p>',
        ]);

        $response = $this->get(route('catalog.product', ['slug' => 'xss-1']));

        $response->assertOk()
            ->assertDontSee('alert("xss")', false)
            ->assertSee('<p>Hello</p>', false)
            ->assertSee('<p>World</p>', false);
    }

    public function test_product_description_strips_event_handlers(): void
    {
        $category = Category::create([
            'slug' => 'frutas',
            'name' => 'Frutas',
            'is_active' => true,
        ]);

        $product = Product::create([
            'category_id' => $category->id,
            'slug' => 'xss-2',
            'name' => 'XSS Test 2',
            'is_active' => true,
            'description' => '<p onerror="console.log(\'XSS_EVENT_PAYLOAD_1\')">Bad</p><div onclick="console.log(\'XSS_EVENT_PAYLOAD_2\')">Click</div>',
        ]);

        $response = $this->get(route('catalog.product', ['slug' => 'xss-2']));

        $response->assertOk()
            // The unique XSS payload markers must not appear on the page
            ->assertDontSee('XSS_EVENT_PAYLOAD', false)
            // Sanitized text content still rendered
            ->assertSee('Bad', false)
            ->assertSee('Click', false);
    }

    public function test_product_description_strips_javascript_href(): void
    {
        $category = Category::create([
            'slug' => 'frutas',
            'name' => 'Frutas',
            'is_active' => true,
        ]);

        $product = Product::create([
            'category_id' => $category->id,
            'slug' => 'xss-3',
            'name' => 'XSS Test 3',
            'is_active' => true,
            'description' => '<a href="javascript:alert(1)">Click</a><a href="https://safe.com">Safe</a>',
        ]);

        $response = $this->get(route('catalog.product', ['slug' => 'xss-3']));

        $response->assertOk()
            ->assertDontSee('javascript:', false)
            ->assertSee('href="https://safe.com"', false);
    }

    public function test_product_description_preserves_rich_html(): void
    {
        $category = Category::create([
            'slug' => 'frutas',
            'name' => 'Frutas',
            'is_active' => true,
        ]);

        $desc = '<h1>Título</h1><p><strong>Negrito</strong> e <em>itálico</em> e <u>sublinhado</u>.</p>'
            . '<ul><li>Item 1</li><li>Item 2</li></ul>'
            . '<ol><li>Primeiro</li><li>Segundo</li></ol>'
            . '<blockquote>Citação</blockquote>'
            . '<pre><code>code block</code></pre>'
            . '<hr><sub>sub</sub><sup>sup</sup>'
            . '<a href="https://example.com">link</a>';

        $product = Product::create([
            'category_id' => $category->id,
            'slug' => 'rich-test',
            'name' => 'Rich Test',
            'is_active' => true,
            'description' => $desc,
        ]);

        $response = $this->get(route('catalog.product', ['slug' => 'rich-test']));

        $response->assertOk()
            ->assertSee('<strong>Negrito</strong>', false)
            ->assertSee('<em>itálico</em>', false)
            ->assertSee('<u>sublinhado</u>', false)
            ->assertSee('<ul>', false)
            ->assertSee('<li>Item 1</li>', false)
            ->assertSee('<ol>', false)
            ->assertSee('<li>Primeiro</li>', false)
            ->assertSee('<blockquote>', false)
            ->assertSee('<pre>', false)
            ->assertSee('<code>code block</code>', false)
            ->assertSee('<hr>', false)
            ->assertSee('<sub>sub</sub>', false)
            ->assertSee('<sup>sup</sup>', false)
            ->assertSee('href="https://example.com"', false);
    }

    public function test_product_description_sanitizes_iframe_and_object(): void
    {
        $category = Category::create([
            'slug' => 'frutas',
            'name' => 'Frutas',
            'is_active' => true,
        ]);

        $product = Product::create([
            'category_id' => $category->id,
            'slug' => 'xss-iframe',
            'name' => 'Iframe Test',
            'is_active' => true,
            'description' => '<p>Before</p><iframe src="evil"></iframe><object data="evil"></object><p>After</p>',
        ]);

        $response = $this->get(route('catalog.product', ['slug' => 'xss-iframe']));

        $response->assertOk()
            ->assertDontSee('<iframe', false)
            ->assertDontSee('<object', false)
            ->assertSee('<p>Before</p>', false)
            ->assertSee('<p>After</p>', false);
    }

    public function test_product_description_adds_noopener_for_target_blank(): void
    {
        $category = Category::create([
            'slug' => 'frutas',
            'name' => 'Frutas',
            'is_active' => true,
        ]);

        $product = Product::create([
            'category_id' => $category->id,
            'slug' => 'target-blank',
            'name' => 'Target Blank',
            'is_active' => true,
            'description' => '<a href="https://ext.com" target="_blank">External</a>',
        ]);

        $response = $this->get(route('catalog.product', ['slug' => 'target-blank']));

        $response->assertOk()
            ->assertSee('rel="noopener noreferrer"', false);
    }

    public function test_product_description_allows_mailto_and_tel_href(): void
    {
        $category = Category::create([
            'slug' => 'frutas',
            'name' => 'Frutas',
            'is_active' => true,
        ]);

        $product = Product::create([
            'category_id' => $category->id,
            'slug' => 'mailto-tel',
            'name' => 'Mailto and Tel',
            'is_active' => true,
            'description' => '<a href="mailto:info@example.com">Email</a> <a href="tel:+351123456789">Call</a>',
        ]);

        $response = $this->get(route('catalog.product', ['slug' => 'mailto-tel']));

        $response->assertOk()
            ->assertSee('href="mailto:info@example.com"', false)
            ->assertSee('href="tel:+351123456789"', false);
    }

    // -----------------------------------------------------------------
    // 3.5) Unknown tag unwrap sanitization (XSS bypass fix)
    // -----------------------------------------------------------------

    public function test_sanitizer_unwrap_strips_script_in_unknown_tag(): void
    {
        $category = Category::create([
            'slug' => 'frutas',
            'name' => 'Frutas',
            'is_active' => true,
        ]);

        // Unique markers to avoid matching legitimate page scripts
        $payload = 'XSS_UNWRAP_SCRIPT_' . uniqid();

        $product = Product::create([
            'category_id' => $category->id,
            'slug' => 'unwrap-xss-script',
            'name' => 'Unwrap Script XSS',
            'is_active' => true,
            'description' => '<custom><script>' . $payload . '</script></custom>',
        ]);

        $response = $this->get(route('catalog.product', ['slug' => 'unwrap-xss-script']));

        $response->assertOk()
            ->assertDontSee($payload, false);
    }

    public function test_sanitizer_unwrap_strips_iframe_and_object_in_unknown_tag(): void
    {
        $category = Category::create([
            'slug' => 'frutas',
            'name' => 'Frutas',
            'is_active' => true,
        ]);

        // Unique markers to avoid matching legitimate page elements
        $iframePayload = 'XSS_UNWRAP_IFRAME_' . uniqid();
        $objectPayload = 'XSS_UNWRAP_OBJECT_' . uniqid();
        $stylePayload = 'XSS_UNWRAP_STYLE_' . uniqid();

        $product = Product::create([
            'category_id' => $category->id,
            'slug' => 'unwrap-xss-iframe',
            'name' => 'Unwrap Iframe XSS',
            'is_active' => true,
            'description' => '<x><iframe src="' . $iframePayload . '"></iframe><object data="' . $objectPayload . '"></object><style>' . $stylePayload . '</style></x>',
        ]);

        $response = $this->get(route('catalog.product', ['slug' => 'unwrap-xss-iframe']));

        $response->assertOk()
            ->assertDontSee($iframePayload, false)
            ->assertDontSee($objectPayload, false)
            ->assertDontSee($stylePayload, false);
    }

    public function test_sanitizer_unwrap_strips_event_handlers_in_unknown_tag(): void
    {
        $category = Category::create([
            'slug' => 'frutas',
            'name' => 'Frutas',
            'is_active' => true,
        ]);

        $payload = 'XSS_UNWRAP_EVENT_' . uniqid();

        $product = Product::create([
            'category_id' => $category->id,
            'slug' => 'unwrap-xss-event',
            'name' => 'Unwrap Event XSS',
            'is_active' => true,
            'description' => '<x><div onclick="' . $payload . '">click</div></x>',
        ]);

        $response = $this->get(route('catalog.product', ['slug' => 'unwrap-xss-event']));

        $response->assertOk()
            ->assertDontSee($payload, false)
            // Safe text content preserved
            ->assertSee('click', false);
    }

    public function test_sanitizer_unwrap_strips_javascript_href_in_unknown_tag(): void
    {
        $category = Category::create([
            'slug' => 'frutas',
            'name' => 'Frutas',
            'is_active' => true,
        ]);

        $payload = 'XSS_UNWRAP_JSHREF_' . uniqid();

        $product = Product::create([
            'category_id' => $category->id,
            'slug' => 'unwrap-xss-js-href',
            'name' => 'Unwrap JS Href XSS',
            'is_active' => true,
            'description' => '<x><a href="javascript:' . $payload . '">link</a></x>',
        ]);

        $response = $this->get(route('catalog.product', ['slug' => 'unwrap-xss-js-href']));

        $response->assertOk()
            ->assertDontSee($payload, false)
            // Link text preserved, but href stripped
            ->assertSee('link', false);
    }

    public function test_sanitizer_unwrap_nested_unknown_tags(): void
    {
        $category = Category::create([
            'slug' => 'frutas',
            'name' => 'Frutas',
            'is_active' => true,
        ]);

        $payload = 'XSS_UNWRAP_NESTED_' . uniqid();

        $product = Product::create([
            'category_id' => $category->id,
            'slug' => 'unwrap-xss-nested',
            'name' => 'Unwrap Nested XSS',
            'is_active' => true,
            'description' => '<x><y><script>' . $payload . '</script></y></x>',
        ]);

        $response = $this->get(route('catalog.product', ['slug' => 'unwrap-xss-nested']));

        $response->assertOk()
            ->assertDontSee($payload, false);
    }

    public function test_sanitizer_unwrap_preserves_safe_text_and_allowed_tags(): void
    {
        $category = Category::create([
            'slug' => 'frutas',
            'name' => 'Frutas',
            'is_active' => true,
        ]);

        $product = Product::create([
            'category_id' => $category->id,
            'slug' => 'unwrap-safe-text',
            'name' => 'Unwrap Safe Text',
            'is_active' => true,
            'description' => '<custom>Hello <b>World</b></custom>',
        ]);

        $response = $this->get(route('catalog.product', ['slug' => 'unwrap-safe-text']));

        $response->assertOk()
            ->assertDontSee('<custom', false)
            // Safe text and allowed tags preserved after unwrap
            ->assertSee('Hello', false)
            ->assertSee('<b>World</b>', false);
    }

    // -----------------------------------------------------------------
    // 4) Contacts page and footer with hardcoded stores (no DB records)
    // -----------------------------------------------------------------

    public function test_contacts_page_renders_with_fallback_stores(): void
    {
        // No Location records in DB
        $this->assertDatabaseCount('locations', 0);

        $response = $this->get(route('website.contacts'));

        $response->assertOk()
            ->assertSee('Loja Braga', false)
            ->assertSee('Loja Guimarães', false)
            ->assertSee('253 271 187', false)
            ->assertSee('253 145 388', false);
    }

    public function test_location_stores_returns_hardcoded_collection(): void
    {
        $stores = Location::stores();

        $this->assertCount(2, $stores);
        $this->assertSame('Loja Braga', $stores[0]->name);
        $this->assertSame('Loja Guimarães', $stores[1]->name);
        $this->assertSame('braga', $stores[0]->pickup_location_code);
        $this->assertSame('guimaraes', $stores[1]->pickup_location_code);
    }

    public function test_location_stores_does_not_query_database(): void
    {
        // Create a Location record to prove stores() ignores DB
        Location::create([
            'name' => 'DB Store',
            'is_active' => true,
        ]);

        $stores = Location::stores();

        // Should still return exactly 2 hardcoded stores
        $this->assertCount(2, $stores);
        $this->assertSame('Loja Braga', $stores[0]->name);
        $this->assertSame('Loja Guimarães', $stores[1]->name);

        // DB store should not appear
        $dbNames = $stores->pluck('name')->all();
        $this->assertNotContains('DB Store', $dbNames);
    }
}
