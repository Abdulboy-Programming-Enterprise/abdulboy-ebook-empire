#!/bin/bash
# =============================================================================
# GENERATE SITEMAP SCRIPT - Create XML sitemap
# =============================================================================

set -e

OUTPUT_FILE="public/sitemap.xml"
BASE_URL="https://abdulboy-ebook.com"

echo '<?xml version="1.0" encoding="UTF-8"?>' > ${OUTPUT_FILE}
echo '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' >> ${OUTPUT_FILE}

# Static pages
for page in "" "ebook-site.html" "subscription-plans.html" "about.html" "contact.html" "faq.html"; do
    echo "<url><loc>${BASE_URL}/${page}</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>" >> ${OUTPUT_FILE}
done

# Dynamic pages - books
curl -s "${BASE_URL}/api/v1/books?limit=1000" | jq -r '.data.items[].slug' | while read slug; do
    echo "<url><loc>${BASE_URL}/book/${slug}</loc><changefreq>monthly</changefreq><priority>0.6</priority></url>" >> ${OUTPUT_FILE}
done

echo '</urlset>' >> ${OUTPUT_FILE}
echo "Sitemap generated: ${OUTPUT_FILE}"
