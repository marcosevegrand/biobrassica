<?php

namespace App\Services;

use DOMDocument;
use DOMElement;
use DOMNode;

class HtmlSanitizer
{
    /**
     * Tags that are entirely removed along with their contents.
     */
    private const DANGEROUS_BLOCK_TAGS = [
        'script', 'style', 'iframe', 'object', 'embed',
        'form', 'input', 'textarea', 'button', 'select',
        'option', 'meta', 'link', 'applet', 'frame', 'frameset',
        'ilayer', 'layer',
    ];

    /**
     * Tags allowed to remain in the output (whitelist).
     */
    private const ALLOWED_TAGS = [
        'p', 'br', 'div', 'span',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'strong', 'b', 'em', 'i', 'u', 's',
        'ul', 'ol', 'li',
        'blockquote', 'pre', 'code', 'hr',
        'sub', 'sup',
        'a',
    ];

    /**
     * Attributes allowed on <a> tags.
     */
    private const ALLOWED_A_ATTRS = ['href', 'title', 'target', 'rel'];

    /**
     * Allowed URI schemes for href attributes.
     */
    private const ALLOWED_SCHEMES = ['http', 'https', 'mailto', 'tel'];

    /**
     * Sanitize an HTML string for safe display.
     *
     * Returns a clean HTML string with dangerous elements/attributes
     * removed. Returns an empty string for blank or null input.
     */
    public static function sanitize(?string $html): string
    {
        return (new self())->doSanitize($html);
    }

    /**
     * Internal instance method that performs the actual sanitization.
     */
    private function doSanitize(?string $html): string
    {
        if ($html === null || trim($html) === '') {
            return '';
        }

        $internalErrors = libxml_use_internal_errors(true);

        $dom = new DOMDocument('1.0', 'UTF-8');

        $wrapped = '<!DOCTYPE html><html><head><meta charset="UTF-8"></head><body>'
            . $html
            . '</body></html>';

        $loaded = $dom->loadHTML($wrapped, LIBXML_HTML_NOIMPLIED | LIBXML_HTML_NODEFDTD | LIBXML_NOERROR);

        libxml_use_internal_errors($internalErrors);
        libxml_clear_errors();

        if (! $loaded) {
            return htmlspecialchars($html, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
        }

        $body = $dom->getElementsByTagName('body')->item(0);
        if (! $body) {
            return '';
        }

        $this->walkAndSanitize($body);

        $result = $this->saveInnerHtml($body);

        return trim($result);
    }

    /**
     * Recursively walk the DOM, removing dangerous elements and
     * stripping disallowed attributes from allowed elements.
     */
    private function walkAndSanitize(DOMNode $node): void
    {
        $toRemove = [];

        // Snapshot child nodes to avoid live DOMNodeList mutation during unwrap
        $children = [];
        foreach ($node->childNodes as $child) {
            $children[] = $child;
        }

        foreach ($children as $child) {
            if ($child instanceof DOMElement) {
                $tag = strtolower($child->tagName);

                if (in_array($tag, self::DANGEROUS_BLOCK_TAGS, true)) {
                    $toRemove[] = $child;
                    continue;
                }

                if (! in_array($tag, self::ALLOWED_TAGS, true)) {
                    // Sanitize children of unknown tag before unwrapping,
                    // so dangerous content inside unknown tags is stripped.
                    $this->walkAndSanitize($child);
                    $this->unwrapNode($child, $node);
                    continue;
                }

                $this->sanitizeAttributes($child, $tag);
                $this->walkAndSanitize($child);
            }
        }

        foreach ($toRemove as $remove) {
            try {
                $node->removeChild($remove);
            } catch (\DOMException) {
                // Node may have already been removed
            }
        }
    }

    /**
     * Strip attributes from an allowed element.
     * For <a> tags, selectively allow safe attributes.
     */
    private function sanitizeAttributes(DOMElement $element, string $tag): void
    {
        if ($tag === 'a') {
            $this->sanitizeAnchorAttributes($element);
        } else {
            $this->stripAllAttributes($element);
        }
    }

    /**
     * Keep only allowed attributes on <a> and sanitize href.
     */
    private function sanitizeAnchorAttributes(DOMElement $a): void
    {
        $keepAttrs = [];

        if ($a->hasAttribute('href')) {
            $keepAttrs['href'] = $this->sanitizeHref($a->getAttribute('href'));
        }
        if ($a->hasAttribute('title')) {
            $keepAttrs['title'] = $a->getAttribute('title');
        }
        if ($a->hasAttribute('target')) {
            $keepAttrs['target'] = $a->getAttribute('target');
        }
        if ($a->hasAttribute('rel')) {
            $keepAttrs['rel'] = $this->sanitizeRel($a->getAttribute('rel'));
        }

        $this->stripAllAttributes($a);

        foreach ($keepAttrs as $name => $value) {
            if ($value !== null && $value !== '') {
                $a->setAttribute($name, $value);
            }
        }

        if (($keepAttrs['target'] ?? '') === '_blank') {
            $existingRel = $a->getAttribute('rel');
            $relParts = array_filter(explode(' ', $existingRel));
            $relParts = array_merge($relParts, ['noopener', 'noreferrer']);
            $a->setAttribute('rel', implode(' ', array_unique($relParts)));
        }
    }

    /**
     * Validate and clean an href value.
     * Returns the sanitized href or null if unsafe.
     */
    private function sanitizeHref(string $href): ?string
    {
        $href = trim($href);

        if ($href === '') {
            return '';
        }

        $decoded = html_entity_decode($href, ENT_QUOTES | ENT_HTML5, 'UTF-8');
        $decoded = trim($decoded);

        // Relative paths and anchors are safe
        if (str_starts_with($decoded, '/') || str_starts_with($decoded, '#') || str_starts_with($decoded, '?')) {
            return $decoded;
        }

        $scheme = parse_url($decoded, PHP_URL_SCHEME);

        if ($scheme === null || $scheme === false) {
            return $decoded;
        }

        $scheme = strtolower($scheme);

        $dangerous = ['javascript', 'data', 'vbscript', 'file'];
        if (in_array($scheme, $dangerous, true)) {
            return null;
        }

        if (in_array($scheme, self::ALLOWED_SCHEMES, true)) {
            return $decoded;
        }

        if (preg_match('/^(javascript|data|vbscript|file)\s*:/i', $decoded)) {
            return null;
        }

        return $decoded;
    }

    /**
     * Clean the rel attribute, keeping only values we trust.
     */
    private function sanitizeRel(string $rel): string
    {
        $allowedRels = ['nofollow', 'noopener', 'noreferrer', 'external', 'ugc', 'sponsored', 'me'];
        $parts = preg_split('/\s+/', $rel);
        $cleaned = array_intersect($parts, $allowedRels);

        return implode(' ', $cleaned);
    }

    /**
     * Remove all attributes from an element.
     */
    private function stripAllAttributes(DOMElement $element): void
    {
        $attributes = [];
        foreach ($element->attributes as $attr) {
            $attributes[] = $attr->name;
        }
        foreach ($attributes as $name) {
            $element->removeAttribute($name);
        }
    }

    /**
     * Unwrap a node: move its children before it, then remove the node.
     */
    private function unwrapNode(DOMNode $node, DOMNode $parent): void
    {
        // Snapshot child nodes before cloning to avoid live DOMNodeList mutation
        $children = [];
        foreach ($node->childNodes as $child) {
            $children[] = $child;
        }

        foreach ($children as $child) {
            $parent->insertBefore($child->cloneNode(true), $node);
        }

        try {
            $parent->removeChild($node);
        } catch (\DOMException) {
            // May already be removed
        }
    }

    /**
     * Save the inner HTML of a DOM node (all children as HTML string).
     */
    private function saveInnerHtml(DOMNode $node): string
    {
        $html = '';

        foreach ($node->childNodes as $child) {
            $html .= $node->ownerDocument->saveHTML($child);
        }

        return $html;
    }
}
