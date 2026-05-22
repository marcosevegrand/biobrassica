<?php

namespace App\Http\Controllers;

use App\Models\Category;
use App\Models\CategoryPosition;
use App\Models\Location;
use App\Models\LocationPosition;
use App\Models\Product;
use App\Models\WebsiteContent;
use Illuminate\Http\Request;

class CatalogController extends Controller
{
    public function shopHome()
    {
        $featuredCategories = Category::query()
            ->select('categories.*')
            ->join('category_positions', 'categories.id', '=', 'category_positions.category_id')
            ->where('categories.is_active', true)
            ->orderBy('category_positions.position')
            ->get();

        $highlightedProducts = Product::with('category')
            ->where('is_highlight', true)
            ->where('is_active', true)
            ->orderBy('id')
            ->take(8)
            ->get();

        $contactLocations = Location::query()
            ->select('locations.*')
            ->join('location_positions', 'locations.id', '=', 'location_positions.location_id')
            ->where('locations.is_active', true)
            ->orderBy('location_positions.position')
            ->get();

        $websiteDefaults = WebsiteContent::first();

        return view('catalog.shop-home', compact(
            'featuredCategories',
            'highlightedProducts',
            'contactLocations',
            'websiteDefaults'
        ));
    }

    public function productList(Request $request)
    {
        $query = Product::with('category')
            ->where('is_active', true);

        if ($request->filled('category')) {
            $query->where('category_id', $request->input('category'));
        }

        if ($request->filled('q')) {
            $search = $request->input('q');
            $query->where(function ($q) use ($search) {
                $q->where('name', 'like', "%{$search}%")
                  ->orWhere('description', 'like', "%{$search}%")
                  ->orWhere('brand', 'like', "%{$search}%")
                  ->orWhere('bio_code', 'like', "%{$search}%");
            });
        }

        $products = $query->orderBy('name')->paginate(12);

        $categories = Category::where('is_active', true)
            ->orderBy('name')
            ->get();

        return view('catalog.product-list', compact('products', 'categories'));
    }

    public function productDetail($slug)
    {
        $product = Product::with(['category', 'pickupLocations'])
            ->where('slug', $slug)
            ->where('is_active', true)
            ->firstOrFail();

        $relatedProducts = Product::with('category')
            ->where('category_id', $product->category_id)
            ->where('id', '!=', $product->id)
            ->where('is_active', true)
            ->take(4)
            ->get();

        return view('catalog.product-detail', compact('product', 'relatedProducts'));
    }

    public function categoryDetail($slug)
    {
        $category = Category::where('slug', $slug)
            ->where('is_active', true)
            ->firstOrFail();

        $products = Product::where('category_id', $category->id)
            ->where('is_active', true)
            ->orderBy('name')
            ->paginate(12);

        return view('catalog.category-detail', compact('category', 'products'));
    }
}
