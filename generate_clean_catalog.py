import json

products = [
  {
    "id": "208-diplomatic-zipset-washed-camo",
    "name": "Washed Camo Utility Zipset",
    "price": 185,
    "comparePrice": 240,
    "category": "Sets",
    "badge": "Look 01",
    "isSet": True,
    "description": "Two-piece matching set engineered in 480 GSM cold-washed French terry. Features a boxy cropped full-zip hooded top with custom matte gunmetal double-ended hardware, dropped shoulders, and deconstructed raw seams. Accompanied by relaxed-fit utility bottoms with an elastic drawcord waist, deep cargo welt pockets, and toggle-cinched ankle hems.",
    "material": "480 GSM Double-Faced Heavyweight French Terry Cotton",
    "care": "Cold gentle machine wash inside out. Line dry in shade. Do not tumble dry.",
    "modelInfo": "Model is 6'1\" (185cm), 165 lbs (75kg), wearing size L for a slouchy architectural drape.",
    "weightGsm": 480,
    "brand": "OBSCURA",
    "sizes": ["S", "M", "L", "XL"],
    "sizeGuide": {
      "S": { "topChest": "124 cm", "topLength": "68 cm", "bottomWaist": "72 cm", "bottomLength": "104 cm" },
      "M": { "topChest": "128 cm", "topLength": "70 cm", "bottomWaist": "76 cm", "bottomLength": "106 cm" },
      "L": { "topChest": "132 cm", "topLength": "72 cm", "bottomWaist": "80 cm", "bottomLength": "108 cm" },
      "XL": { "topChest": "136 cm", "topLength": "74 cm", "bottomWaist": "84 cm", "bottomLength": "110 cm" }
    },
    "image": "/products/208-diplomatic-zipset-washed-camo/front.jpg",
    "hoverImage": "/products/208-diplomatic-zipset-washed-camo/back.jpg",
    "images": [
      "/products/208-diplomatic-zipset-washed-camo/front.jpg",
      "/products/208-diplomatic-zipset-washed-camo/back.jpg",
      "/products/208-diplomatic-zipset-washed-camo/lookbook_1.jpg",
      "/products/208-diplomatic-zipset-washed-camo/lookbook_2.jpg",
      "/products/208-diplomatic-zipset-washed-camo/detail_1.jpg",
      "/products/208-diplomatic-zipset-washed-camo/detail_2.jpg",
      "/products/208-diplomatic-zipset-washed-camo/detail_3.jpg",
      "/products/208-diplomatic-zipset-washed-camo/detail_4.jpg",
      "/products/208-diplomatic-zipset-washed-camo/detail_5.jpg",
      "/products/208-diplomatic-zipset-washed-camo/size_chart_1.jpg",
      "/products/208-diplomatic-zipset-washed-camo/size_chart_2.jpg"
    ],
    "sizeChart": "/products/208-diplomatic-zipset-washed-camo/size_chart_1.jpg",
    "colors": [
      { "name": "Mineral Camo", "hex": "#3b4238", "inStock": True }
    ],
    "stock": { "S": 45, "M": 50, "L": 55, "XL": 40 }
  },
  {
    "id": "hellstar-vintage-gradient-flare-sweatpants",
    "name": "Vintage Gradient Graphic Sweatpants",
    "price": 145,
    "comparePrice": 195,
    "category": "Bottoms",
    "badge": "New Arrival",
    "isSet": False,
    "description": "Heavyweight French terry relaxed sweatpants featuring archival gradient flame letterpress graphic down both outer legs. Finished with an elasticated waistband, custom cream elongated drawstrings, a rear patch pocket, and gathered elastic ankle cuffs.",
    "material": "460 GSM Heavyweight French Terry Cotton",
    "care": "Machine wash cold inside out. Hang dry in shade. Do not tumble dry or iron graphics.",
    "modelInfo": "Model is 6'1\" (185cm), 165 lbs (75kg), wearing size L for a relaxed drape.",
    "weightGsm": 460,
    "brand": "OBSCURA",
    "sizes": ["S", "M", "L", "XL"],
    "sizeGuide": {
      "S": { "length": "104 cm", "waist": "70 cm / 27.5 in", "hip": "90 cm / 35.4 in" },
      "M": { "length": "106 cm", "waist": "72 cm / 28.3 in", "hip": "94 cm / 37.0 in" },
      "L": { "length": "108 cm", "waist": "74 cm / 29.1 in", "hip": "98 cm / 38.6 in" },
      "XL": { "length": "110 cm", "waist": "76 cm / 29.9 in", "hip": "102 cm / 40.1 in" }
    },
    "image": "/products/hellstar-vintage-gradient-flare-sweatpants/front.jpg",
    "hoverImage": "/products/hellstar-vintage-gradient-flare-sweatpants/back.jpg",
    "images": [
      "/products/hellstar-vintage-gradient-flare-sweatpants/front.jpg",
      "/products/hellstar-vintage-gradient-flare-sweatpants/back.jpg",
      "/products/hellstar-vintage-gradient-flare-sweatpants/detail_1.jpg",
      "/products/hellstar-vintage-gradient-flare-sweatpants/detail_2.jpg",
      "/products/hellstar-vintage-gradient-flare-sweatpants/detail_3.jpg",
      "/products/hellstar-vintage-gradient-flare-sweatpants/detail_4.jpg",
      "/products/hellstar-vintage-gradient-flare-sweatpants/detail_5.jpg",
      "/products/hellstar-vintage-gradient-flare-sweatpants/size_chart.jpg"
    ],
    "sizeChart": "/products/hellstar-vintage-gradient-flare-sweatpants/size_chart.jpg",
    "colors": [
      { "name": "Washed Obsidian", "hex": "#1A1A1A", "inStock": True }
    ],
    "stock": { "S": 87, "M": 88, "L": 88, "XL": 88 }
  },
  {
    "id": "represent-owners-club-heavyweight-hoodie",
    "name": "Owners Club Heavyweight Boxy Hoodie",
    "price": 165,
    "comparePrice": 220,
    "category": "Outerwear",
    "badge": "Look 02",
    "isSet": False,
    "description": "Architectural boxy cropped hoodie knitted from ultra-dense 480 GSM loopback cotton fleece. Featuring dropped shoulders, double-layer structured hood with cobrax metal popper closure, ribbed cuffs and hem, and screen-printed archival branding across the reverse.",
    "material": "480 GSM Heavyweight Loopback Cotton Fleece",
    "care": "Hand wash or dry clean recommended. Cool iron on reverse.",
    "modelInfo": "Model is 6'1\" (185cm), 165 lbs (75kg), wearing size L.",
    "weightGsm": 480,
    "brand": "OBSCURA",
    "sizes": ["S", "M", "L", "XL"],
    "sizeGuide": {
      "S": { "chest": "122 cm", "length": "67 cm", "shoulder": "58 cm" },
      "M": { "chest": "126 cm", "length": "69 cm", "shoulder": "60 cm" },
      "L": { "chest": "130 cm", "length": "71 cm", "shoulder": "62 cm" },
      "XL": { "chest": "134 cm", "length": "73 cm", "shoulder": "64 cm" }
    },
    "image": "/products/represent-owners-club-heavyweight-hoodie/front.jpg",
    "hoverImage": "/products/represent-owners-club-heavyweight-hoodie/back.jpg",
    "images": [
      "/products/represent-owners-club-heavyweight-hoodie/front.jpg",
      "/products/represent-owners-club-heavyweight-hoodie/back.jpg",
      "/products/represent-owners-club-heavyweight-hoodie/lookbook_1.jpg",
      "/products/represent-owners-club-heavyweight-hoodie/lookbook_2.jpg",
      "/products/represent-owners-club-heavyweight-hoodie/detail_1.jpg",
      "/products/represent-owners-club-heavyweight-hoodie/detail_2.jpg",
      "/products/represent-owners-club-heavyweight-hoodie/detail_3.jpg",
      "/products/represent-owners-club-heavyweight-hoodie/size_chart.jpg"
    ],
    "sizeChart": "/products/represent-owners-club-heavyweight-hoodie/size_chart.jpg",
    "colors": [
      { "name": "Vintage Charcoal", "hex": "#242424", "inStock": True }
    ],
    "stock": { "S": 40, "M": 65, "L": 70, "XL": 35 }
  },
  {
    "id": "jil-sander-tailored-bomber-jacket",
    "name": "Structural Tailored Minimalist Bomber",
    "price": 210,
    "comparePrice": 285,
    "category": "Outerwear",
    "badge": "Look 03",
    "isSet": False,
    "description": "Precision-tailored minimalist bomber jacket engineered in high-density technical twill with a weather-repellent finish. High-neck funnel collar geometry, heavy-gauge two-way front zip fastening, internal storm flaps, and concealed seam hand pockets.",
    "material": "High-Density Technical Milled Twill with Cupro Lining",
    "care": "Specialist dry clean only.",
    "modelInfo": "Model is 6'1\" (185cm), 165 lbs (75kg), wearing size L.",
    "weightGsm": 420,
    "brand": "OBSCURA",
    "sizes": ["S", "M", "L", "XL"],
    "sizeGuide": {
      "S": { "chest": "118 cm", "length": "66 cm", "shoulder": "52 cm" },
      "M": { "chest": "122 cm", "length": "68 cm", "shoulder": "54 cm" },
      "L": { "chest": "126 cm", "length": "70 cm", "shoulder": "56 cm" },
      "XL": { "chest": "130 cm", "length": "72 cm", "shoulder": "58 cm" }
    },
    "image": "/products/jil-sander-tailored-bomber-jacket/front.jpg",
    "hoverImage": "/products/jil-sander-tailored-bomber-jacket/back.jpg",
    "images": [
      "/products/jil-sander-tailored-bomber-jacket/front.jpg",
      "/products/jil-sander-tailored-bomber-jacket/back.jpg",
      "/products/jil-sander-tailored-bomber-jacket/lookbook_1.jpg",
      "/products/jil-sander-tailored-bomber-jacket/lookbook_2.jpg",
      "/products/jil-sander-tailored-bomber-jacket/detail_1.jpg",
      "/products/jil-sander-tailored-bomber-jacket/detail_2.jpg",
      "/products/jil-sander-tailored-bomber-jacket/detail_3.jpg",
      "/products/jil-sander-tailored-bomber-jacket/size_chart.jpg"
    ],
    "sizeChart": "/products/jil-sander-tailored-bomber-jacket/size_chart.jpg",
    "colors": [
      { "name": "Stealth Noir", "hex": "#141414", "inStock": True }
    ],
    "stock": { "S": 25, "M": 45, "L": 50, "XL": 30 }
  },
  {
    "id": "essential-heavyweight-500gsm-tee",
    "name": "Heavyweight 500GSM Structural Boxy Tee",
    "price": 85,
    "comparePrice": 115,
    "category": "Tops",
    "badge": "Look 04",
    "isSet": False,
    "description": "Substantial 500 GSM double-combed compact jersey t-shirt. Engineered with a robust 3cm ribbed crewneck collar that maintains shape after extensive wear, wide relaxed sleeve openings, and drop-shoulder boxy construction.",
    "material": "500 GSM 100% Double-Combed Heavyweight Cotton",
    "care": "Machine wash cold inside out. Reshape while damp. Do not tumble dry.",
    "modelInfo": "Model is 6'1\" (185cm), 165 lbs (75kg), wearing size L.",
    "weightGsm": 500,
    "brand": "OBSCURA",
    "sizes": ["S", "M", "L", "XL"],
    "sizeGuide": {
      "S": { "chest": "116 cm", "length": "71 cm", "shoulder": "54 cm" },
      "M": { "chest": "120 cm", "length": "73 cm", "shoulder": "56 cm" },
      "L": { "chest": "124 cm", "length": "75 cm", "shoulder": "58 cm" },
      "XL": { "chest": "128 cm", "length": "77 cm", "shoulder": "60 cm" }
    },
    "image": "/products/essential-heavyweight-500gsm-tee/front.jpg",
    "hoverImage": "/products/essential-heavyweight-500gsm-tee/back.jpg",
    "images": [
      "/products/essential-heavyweight-500gsm-tee/front.jpg",
      "/products/essential-heavyweight-500gsm-tee/back.jpg",
      "/products/essential-heavyweight-500gsm-tee/lookbook_1.jpg",
      "/products/essential-heavyweight-500gsm-tee/lookbook_2.jpg",
      "/products/essential-heavyweight-500gsm-tee/detail_1.jpg",
      "/products/essential-heavyweight-500gsm-tee/detail_2.jpg"
    ],
    "sizeChart": "/products/essential-heavyweight-500gsm-tee/front.jpg",
    "colors": [
      { "name": "Chalk White", "hex": "#EDEBE6", "inStock": True }
    ],
    "stock": { "S": 60, "M": 85, "L": 90, "XL": 45 }
  },
  {
    "id": "palace-heritage-logo-baseball-cap",
    "name": "Heritage Logo Six-Panel Baseball Cap",
    "price": 65,
    "comparePrice": 85,
    "category": "Accessories",
    "badge": "Limited",
    "isSet": False,
    "description": "Classic unstructured six-panel baseball cap woven from heavy washed cotton twill. Detailed with contrast tonal high-density embroidery on the crown, embroidered ventilation eyelets, and an adjustable back strap with custom embossed brass buckle closure.",
    "material": "100% Heavy Washed Cotton Twill with Brass Hardware",
    "care": "Spot clean with damp cloth. Do not immerse in water.",
    "modelInfo": "Adjustable one-size strap fits head circumferences 54-61 cm.",
    "weightGsm": 180,
    "brand": "OBSCURA",
    "sizes": ["ONE SIZE"],
    "sizeGuide": {
      "ONE SIZE": { "circumference": "54 - 61 cm (Adjustable)", "brimLength": "7.5 cm", "crownHeight": "12 cm" }
    },
    "image": "/products/palace-heritage-logo-baseball-cap/front.jpg",
    "hoverImage": "/products/palace-heritage-logo-baseball-cap/back.jpg",
    "images": [
      "/products/palace-heritage-logo-baseball-cap/front.jpg",
      "/products/palace-heritage-logo-baseball-cap/back.jpg",
      "/products/palace-heritage-logo-baseball-cap/detail_1.jpg",
      "/products/palace-heritage-logo-baseball-cap/detail_2.jpg",
      "/products/palace-heritage-logo-baseball-cap/detail_3.jpg"
    ],
    "sizeChart": "/products/palace-heritage-logo-baseball-cap/front.jpg",
    "colors": [
      { "name": "Desert Sand", "hex": "#C8B9A6", "inStock": True }
    ],
    "stock": { "ONE SIZE": 120 }
  },
  {
    "id": "monogram-denim-slouch-hobo-bag",
    "name": "Denim Monogram Slouch Hobo Bag",
    "price": 195,
    "comparePrice": 260,
    "category": "Accessories",
    "badge": "Limited",
    "isSet": False,
    "description": "Sculptural slouch hobo bag crafted in washed indigo jacquard denim. Engineered with dual front utility flap pockets, polished brass push-lock clasps, a wide ergonomic shoulder strap with rivet reinforcement, and a soft microfiber-lined interior.",
    "material": "Washed Selvedge Indigo Denim Jacquard with Brass Hardware",
    "care": "Specialist leather & textile clean only.",
    "modelInfo": "Shoulder drop 32 cm. Bag dimensions: 38 cm W x 26 cm H x 12 cm D.",
    "weightGsm": 620,
    "brand": "OBSCURA",
    "sizes": ["ONE SIZE"],
    "sizeGuide": {
      "ONE SIZE": { "width": "38 cm", "height": "26 cm", "depth": "12 cm", "strapDrop": "32 cm" }
    },
    "image": "/products/monogram-denim-slouch-hobo-bag/front.jpg",
    "hoverImage": "/products/monogram-denim-slouch-hobo-bag/back.jpg",
    "images": [
      "/products/monogram-denim-slouch-hobo-bag/front.jpg",
      "/products/monogram-denim-slouch-hobo-bag/back.jpg",
      "/products/monogram-denim-slouch-hobo-bag/detail_1.jpg",
      "/products/monogram-denim-slouch-hobo-bag/detail_2.jpg",
      "/products/monogram-denim-slouch-hobo-bag/detail_3.jpg",
      "/products/monogram-denim-slouch-hobo-bag/detail_4.jpg"
    ],
    "sizeChart": "/products/monogram-denim-slouch-hobo-bag/front.jpg",
    "colors": [
      { "name": "Washed Indigo", "hex": "#3E5879", "inStock": True }
    ],
    "stock": { "ONE SIZE": 45 }
  },
  {
    "id": "corteiz-athletic-logo-tracksuit-set",
    "name": "Athletic Logo Double-Knit Tracksuit Set",
    "price": 175,
    "comparePrice": 230,
    "category": "Sets",
    "badge": "New Arrival",
    "isSet": True,
    "description": "Coordinated performance luxury tracksuit set in 420 GSM structured double-knit fleece. Consists of a pullover hooded sweatshirt with ergonomic raglan sleeves and screen-printed emblem, combined with tapered athletic joggers featuring zip-fastened side pockets and ribbed ankle cuffs.",
    "material": "420 GSM Double-Knit Cotton Interlock Fleece",
    "care": "Machine wash cold inside out with like colors. Line dry.",
    "modelInfo": "Model is 6'1\" (185cm), 165 lbs (75kg), wearing size L.",
    "weightGsm": 420,
    "brand": "OBSCURA",
    "sizes": ["S", "M", "L", "XL"],
    "sizeGuide": {
      "S": { "topChest": "118 cm", "topLength": "68 cm", "bottomWaist": "70 cm", "bottomLength": "102 cm" },
      "M": { "topChest": "122 cm", "topLength": "70 cm", "bottomWaist": "74 cm", "bottomLength": "104 cm" },
      "L": { "topChest": "126 cm", "topLength": "72 cm", "bottomWaist": "78 cm", "bottomLength": "106 cm" },
      "XL": { "topChest": "130 cm", "topLength": "74 cm", "bottomWaist": "82 cm", "bottomLength": "108 cm" }
    },
    "image": "/products/corteiz-athletic-logo-tracksuit-set/front.jpg",
    "hoverImage": "/products/corteiz-athletic-logo-tracksuit-set/back.jpg",
    "images": [
      "/products/corteiz-athletic-logo-tracksuit-set/front.jpg",
      "/products/corteiz-athletic-logo-tracksuit-set/back.jpg",
      "/products/corteiz-athletic-logo-tracksuit-set/lookbook_1.jpg",
      "/products/corteiz-athletic-logo-tracksuit-set/detail_1.jpg",
      "/products/corteiz-athletic-logo-tracksuit-set/detail_2.jpg",
      "/products/corteiz-athletic-logo-tracksuit-set/size_chart_1.jpg",
      "/products/corteiz-athletic-logo-tracksuit-set/size_chart_2.jpg"
    ],
    "sizeChart": "/products/corteiz-athletic-logo-tracksuit-set/size_chart_1.jpg",
    "colors": [
      { "name": "Carbon Black", "hex": "#1C1C1C", "inStock": True }
    ],
    "stock": { "S": 50, "M": 75, "L": 80, "XL": 40 }
  }
]

collections = [
  {
    "id": "urban-ritual",
    "name": "Urban Ritual",
    "description": "Architectural boxy hoodies, heavyweight French terry essentials, and brutalist drop-shoulder silhouettes.",
    "image": "/images/editorial_hero.jpg",
    "productCount": 3
  },
  {
    "id": "tech-noir",
    "name": "Tech Noir",
    "description": "Utilitarian cargo sets, performance double-knit tracksuits, and weather-sealed technical outerwear.",
    "image": "/images/main_hero_bg.jpg",
    "productCount": 3
  },
  {
    "id": "archive-objects",
    "name": "Archive Objects & Accessories",
    "description": "Curated six-panel technical headwear, jacquard denim bags, and sculptural accessories.",
    "image": "/images/editorial_hero.jpg",
    "productCount": 2
  }
]

outfits = [
  {
    "id": "runway-look-01",
    "name": "Washed Camo Diplomatic Ensemble",
    "description": "Cold-wash patina deconstructed zip hoodie with matching relaxed cargo trousers, accessorized with the heritage twill cap.",
    "image": "/products/208-diplomatic-zipset-washed-camo/lookbook_1.jpg",
    "images": [
      "/products/208-diplomatic-zipset-washed-camo/lookbook_1.jpg",
      "/products/208-diplomatic-zipset-washed-camo/lookbook_2.jpg"
    ],
    "price": 250,
    "tags": ["DROP 04", "RUNWAY", "FULL ENSEMBLE"],
    "products": [
      "208-diplomatic-zipset-washed-camo",
      "palace-heritage-logo-baseball-cap"
    ]
  },
  {
    "id": "runway-look-02",
    "name": "Architectural Heavyweight Uniform",
    "description": "480 GSM loopback boxy hoodie paired with vintage gradient graphic flare sweatpants and raw denim hobo bag.",
    "image": "/products/represent-owners-club-heavyweight-hoodie/lookbook_1.jpg",
    "images": [
      "/products/represent-owners-club-heavyweight-hoodie/lookbook_1.jpg",
      "/products/represent-owners-club-heavyweight-hoodie/lookbook_2.jpg"
    ],
    "price": 310,
    "tags": ["DROP 04", "ESSENTIALS", "HEAVYWEIGHT"],
    "products": [
      "represent-owners-club-heavyweight-hoodie",
      "hellstar-vintage-gradient-flare-sweatpants"
    ]
  }
]

js_content = f"""// OBSCURA Storefront Product Catalog
// Verified Curated Drops

export const DEMO_PRODUCTS = {json.dumps(products, indent=2)};

export const COLLECTIONS = {json.dumps(collections, indent=2)};

export const DEMO_OUTFITS = {json.dumps(outfits, indent=2)};
"""

with open("storefront/src/data/products.js", "w", encoding="utf-8") as f:
    f.write(js_content)

print(f"SUCCESS: wrote {len(products)} products to storefront/src/data/products.js")
