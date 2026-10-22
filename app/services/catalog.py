"""Presentation taxonomy; plugins declare membership without changing bot policy."""

CATEGORY_KEYS = {
    "text": "catalog_text",
    "images": "catalog_images",
    "documents": "catalog_documents",
    "pdf": "catalog_pdf",
    "data": "catalog_data",
    "professional": "catalog_professional",
    "other": "catalog_other",
}


def ordered(rows, types):
    """One presentation order for customer and admin; retain stable fallback ties."""
    categories = {key: index for index, key in enumerate(CATEGORY_KEYS)}

    def key(row):
        plugin = types.get(row.slug)
        return (
            categories.get(getattr(plugin, "category", "other"), categories["other"]),
            getattr(plugin, "menu_order", 100),
        )

    return sorted(rows, key=key)
