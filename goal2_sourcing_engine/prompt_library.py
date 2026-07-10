"""
Prompt Library — Copy-Paste-Ready Ad Prompts for All Product Categories
=======================================================================
Organized by product type and ad format. Used by flow_bridge.py to
batch-generate ads without manual prompt writing.

Each prompt includes the multi-reference instruction:
  - Reference image 1-5: Character sheet (model angles)
  - Reference image 6+: Product photos
"""

# ==========================================
# 2026 ANTI-AI BLINDNESS FILTERS (Imperfection)
# ==========================================
# Append these to prompts to make them look like "real" human photos.
CANDID_FILTERS = (
    "Slightly smudged camera lens, subtle lens flare from overhead light, "
    "natural iPhone 15 grain, authentic skin imperfections, visible pores, "
    "un-manicured cuticles, messy background with realistic clutter (a stray "
    "charging cable, a half-empty water bottle), candid motion blur, "
    "non-symmetrical lighting, high ISO noise in shadows. "
    "Do NOT use 'perfect', 'flawless', or 'cinematic' keywords. "
    "Aesthetic: Raw, unfiltered, user-generated content from 2026."
)

# ==========================================
# CLOTHING PROMPTS
# ==========================================
CLOTHING_PROMPTS = {
    "mirror_selfie": (
        "Using this exact person from the first reference image, generate a "
        "hyperrealistic mirror selfie of her wearing this exact garment from "
        "the second reference image. The face, hair, eye color, freckles, and "
        "skin features must match the first reference EXACTLY. The garment must "
        "match the second reference EXACTLY — same color, same fabric texture, "
        "same fit, same design details. Standing in a modern apartment bathroom "
        "with large mirror, natural overhead LED lighting. Shot on iPhone 15 Pro. "
        "Relaxed expression, one hand holding phone, other hand on hip. Natural "
        "glowing skin, visible pores, no heavy makeup. The clothing drapes "
        "naturally on her body with realistic folds and wrinkles. Authentic "
        "Instagram Stories aesthetic, not posed or professional. RAW photo style."
    ),
    "ootd_street": (
        "Using this exact person from the first reference image, generate a "
        "hyperrealistic full-body OOTD photo of her wearing this exact outfit "
        "from the second reference image. Her features must match the first "
        "reference EXACTLY. The garment must match the second reference EXACTLY "
        "— same color, pattern, fabric, design. Late afternoon golden hour, "
        "urban sidewalk with clean concrete wall behind. Shot on 85mm lens at "
        "f/1.8, shallow depth of field with blurred background. Slight motion "
        "blur on one leg mid-stride. Natural skin texture, subtle freckles. "
        "Streetwear editorial photography, candid and authentic. RAW photo style."
    ),
    "flat_lay_concrete_luxury": (
        "Using this exact garment from the reference image, generate a high-end luxury streetwear "
        "flat lay photograph. The garment must match the reference EXACTLY — same color, fabric texture, and pattern. "
        "Styled on a textured, raw polished concrete floor. Cinematic, dramatic side lighting from the left "
        "creating deep, rich shadows that highlight the tactile quality and weave of the fabric. "
        "The garment is styled with 'stuffed volume' so it looks three-dimensional and premium, not flat. "
        "Asymmetrical composition using the Rule of Odds: styled alongside premium subtle props (a thick silver "
        "chain necklace, a heavy brushed-steel mechanical watch, and a matte black sunglasses case). "
        "Shot from directly overhead on a 50mm lens, f/8 for sharp edge-to-edge focus. Moody, sensory, elite streetwear aesthetic."
    ),
    "flat_lay_editorial_dark": (
        "Using this exact garment from the reference image, generate a moody, high-fashion editorial flat lay. "
        "The garment must match the reference EXACTLY. Placed on a matte charcoal slate background. "
        "A single soft spotlight illuminates the garment from the top right, leaving the bottom left in deep, "
        "cinematic shadow (chiaroscuro). The fabric is artfully folded to show the label and inner lining. "
        "Minimalist and emotional layout with significant negative space. Shot on a medium format camera, "
        "100mm macro lens, capturing micro-details of the stitching and material. Luxury archive aesthetic."
    ),
    "flat_lay_street_culture": (
        "Using this exact garment from the reference image, generate a premium hype-culture product shot. "
        "The garment must match the reference EXACTLY. Styled casually but intentionally on a piece of vintage "
        "weathered wood or distressed flight case. Soft diffused window light creates a natural, authentic vibe. "
        "Surrounded by curated lifestyle elements: a vintage film camera, a stack of art/design magazines, "
        "and a pair of hyped sneakers partially in frame. Shot from a slight 45-degree top-down angle, "
        "shallow depth of field. High-energy, curated streetwear lifestyle."
    ),
    "lifestyle_action": (
        "Using this exact person from the first reference image, generate a "
        "hyperrealistic photo of her in an active lifestyle moment wearing this "
        "exact outfit from the second reference image. Features and garment match "
        "references EXACTLY. Park or outdoor setting, morning light, natural "
        "movement. Shot on 50mm lens. Authentic, not overly posed. Visible skin "
        "texture, no AI smoothing."
    ),
    "grwm_getting_dressed": (
        "Using this exact person from the first reference image, generate a "
        "candid hyperrealistic photo of her putting on this exact garment from "
        "the second reference image. Getting dressed in a bedroom, warm lamp "
        "lighting from the side. Shot on smartphone, slightly blurry background. "
        "Natural body language, adjusting the collar. Features and garment match "
        "references EXACTLY. UGC aesthetic."
    ),
    "simple_vton_grwm": "Put the exact garment from the second image on the lady from the first image in a grwm style photo.",
    "simple_vton_mirror": "Put the exact garment from the second image on the person from the first image in a mirror selfie.",
    "simple_vton_street": "Put the exact clothing from the second image on the person from the first image walking down the street.",
}

# ==========================================
# SHOE PROMPTS
# ==========================================
SHOE_PROMPTS = {
    "top_down_flex_concrete": (
        "Using this exact shoe from the reference image, generate a hyperrealistic "
        "top-down POV photo looking at own feet wearing these exact sneakers. "
        "Standing on premium textured architectural concrete. Cinematic afternoon "
        "sunlight casting long, dramatic shadows. The shoes must match the reference "
        "EXACTLY — same colorway, same logo placement, same sole design, same laces. "
        "Wearing premium ribbed crew socks and heavy washed denim pooling at the ankle. "
        "Shot on 35mm lens, high-end editorial streetwear aesthetic. 8K detail."
    ),
    "on_feet_lifestyle_moody": (
        "Using this exact shoe from the reference image, generate a hyperrealistic "
        "photo of someone sitting on the edge of an open vintage car door or concrete barrier, "
        "legs extended casually, showcasing these exact sneakers on feet. "
        "Shoes must match reference EXACTLY. Moody, cinematic twilight lighting "
        "with a soft neon glow in the blurred background. Shot on 85mm lens f/1.4. "
        "Premium archive streetwear style."
    ),
    "product_hero_floating": (
        "Using this exact shoe from the reference image, generate an elite product hero shot. "
        "The single shoe appears to be floating mid-air or resting on a raw stone pedestal "
        "against a seamless matte dark grey background. Dramatic chiaroscuro side lighting "
        "creating razor-sharp details of the suede, leather, or mesh textures. "
        "Shoe matches reference EXACTLY. Commercial luxury product photography, "
        "100mm macro lens, ultra-premium aesthetic."
    ),
    "unboxing_tactile": (
        "Hyperrealistic first-person POV photo of hands holding these exact shoes "
        "from the reference image. The shoes are resting on premium crinkled matte black "
        "tissue paper inside a heavy matte box. Shoes match reference EXACTLY. "
        "Soft directional lighting highlighting the textures of the shoe materials "
        "and the crispness of the tissue paper. Luxury unboxing experience."
    ),
}

# ==========================================
# GHOST MANNEQUIN PROMPTS (Invisible Form Product Shots)
# ==========================================
GHOST_MANNEQUIN_PROMPTS = {
    "invisible_form_clean": (
        "Using this exact garment from the reference image, generate a professional "
        "ghost mannequin e-commerce product photograph. The garment appears worn by an "
        "invisible form, showing its natural 3D shape, drape, and fit as if on a body. "
        "Garment matches reference EXACTLY — same color, fabric texture, pattern, all details. "
        "Clean white background. No visible mannequin, no person, just the floating garment shape. "
        "Soft diffused studio lighting from above and both sides. Razor-sharp focus on fabric details. "
        "Professional e-commerce product photography, 85mm lens."
    ),
    "invisible_form_dark": (
        "Using this exact garment from the reference image, generate a premium "
        "ghost mannequin product shot. The garment appears to float in space, worn by an "
        "invisible form showing natural drape and silhouette. Garment matches reference EXACTLY. "
        "Matte charcoal background with single dramatic side light creating depth and texture contrast. "
        "No visible mannequin or person. The garment's construction details, stitching, and fabric "
        "weave are clearly visible. Shot on medium format camera, luxury archive aesthetic."
    ),
    "invisible_form_back": (
        "Using this exact garment from the reference image, generate a ghost mannequin "
        "back view. The garment is shown from behind on an invisible form, displaying the "
        "back construction, seams, label area, and rear fit. Garment matches reference EXACTLY. "
        "Clean white background, even studio lighting. Professional e-commerce back view."
    ),
}

# ==========================================
# HANGER PROMPTS (Premium Hung Garment Shots)
# ==========================================
HANGER_PROMPTS = {
    "wood_hanger_clean": (
        "Using this exact garment from the reference image, generate a premium "
        "product photo hung on a thick natural wood hanger against a clean matte off-white "
        "backdrop. Garment matches reference EXACTLY — same color, fabric, design details. "
        "The garment hangs naturally showing its true silhouette and drape. Soft diffused studio "
        "lighting from above. No person, no mannequin. Shot on 85mm lens, shallow depth of field "
        "with the hanger hook slightly soft. Minimal, luxury retail display aesthetic."
    ),
    "velvet_hanger_moody": (
        "Using this exact garment from the reference image, generate a moody product shot "
        "hung on a slim black velvet hanger against a deep charcoal textured wall backdrop. "
        "Garment matches reference EXACTLY. Single warm spotlight from the upper left creates "
        "dramatic shadows. The fabric texture catches the light beautifully. No person. "
        "Premium boutique display aesthetic, shot on 50mm lens. Archive fashion mood."
    ),
}

# ==========================================
# SET FLAT LAY PROMPTS (Co-ordinated Outfit Sets)
# ==========================================
SET_FLAT_LAY_PROMPTS = {
    "full_set_concrete": (
        "Using these exact garments from the reference images, generate a luxury flat lay "
        "showing the COMPLETE SET styled together as one coordinated outfit. Top piece positioned "
        "above, bottom piece below, arranged as if worn together. Both garments match references "
        "EXACTLY — same colors, fabrics, details. Styled on raw polished concrete surface. "
        "Dramatic side lighting from the left creating rich shadows. The garments are styled with "
        "stuffed volume so they look three-dimensional and premium. Shot from directly overhead, "
        "50mm lens, f/8 for sharp focus. Premium streetwear set aesthetic."
    ),
    "full_set_dark_slate": (
        "Using these exact garments from the reference images, generate a high-fashion flat lay "
        "of the complete matching set. Top positioned above, bottom below, showing the full "
        "co-ordinated look. Both pieces match references EXACTLY. Placed on matte dark slate surface. "
        "Soft overhead spotlight with deep shadows at the edges. Minimalist layout with intentional "
        "negative space. The fabric folds are artful and deliberate. Medium format overhead shot. "
        "Luxury archive aesthetic."
    ),
    "full_set_lifestyle": (
        "Using these exact garments from the reference images, generate a lifestyle flat lay "
        "of the complete set. Top and bottom styled together on a vintage weathered wood surface. "
        "Both pieces match references EXACTLY. Surrounded by minimal lifestyle props: a watch, "
        "sunglasses, a single sneaker partially in frame. Natural window light, warm tones. "
        "45-degree top-down angle. Curated streetwear lifestyle content."
    ),
}

# ==========================================
# DETAIL CLOSEUP PROMPTS (Macro Construction Shots)
# ==========================================
DETAIL_CLOSEUP_PROMPTS = {
    "fabric_macro": (
        "Using this exact garment from the reference image, generate an extreme macro "
        "close-up photograph showcasing the fabric texture, weave pattern, and material quality. "
        "Garment matches reference EXACTLY. Shot on 100mm macro lens at f/2.8 with razor-thin "
        "depth of field. Soft studio side lighting reveals every thread and fiber. The quality of "
        "construction is clearly visible. No person, no mannequin. Luxury textile inspection aesthetic."
    ),
    "collar_detail": (
        "Using this exact garment from the reference image, generate a detailed close-up "
        "of the collar, neckline, and label area. Garment matches reference EXACTLY. "
        "Sharp focus on the stitching quality, label typography, and collar construction. "
        "Clean neutral background, soft directional studio light. 100mm macro lens. "
        "Premium quality inspection shot."
    ),
    "hardware_detail": (
        "Using this exact garment from the reference image, generate a macro close-up "
        "focusing on the hardware details — zippers, buttons, snaps, drawstrings, or metal eyelets. "
        "Garment matches reference EXACTLY. Dramatic angled light catches the metallic surfaces. "
        "Extreme shallow depth of field. The craftsmanship and material quality are the hero. "
        "Shot on macro lens. Luxury construction detail aesthetic."
    ),
}

# ==========================================
# ACCESSORY PROMPTS (Jewelry, Watches, Sunglasses)
# ==========================================
ACCESSORY_PROMPTS = {
    "selfie_flex": (
        "Using this exact person from the first reference image, generate a "
        "hyperrealistic close-up selfie of her wearing this exact accessory from "
        "the second reference image. The accessory must match the reference EXACTLY "
        "— same shape, color, design details. Sitting in a car, natural window light "
        "hitting the accessory creating a subtle glow. Visible skin texture, light "
        "freckles. Shot on iPhone front camera. Instagram-ready casual vibe."
    ),
    "wrist_shot": (
        "Using this exact watch/bracelet from the reference image, generate a "
        "hyperrealistic macro close-up of a wrist wearing this exact piece. Must "
        "match reference EXACTLY — same dial, same band, same case design. Hand "
        "resting on a marble table next to espresso. Natural cafe lighting. Shallow "
        "depth of field. Shot on 50mm macro lens. Luxury lifestyle aesthetic."
    ),
    "neck_detail": (
        "Using this exact necklace/chain from the reference image, generate a "
        "hyperrealistic close-up of a woman's neckline wearing this exact piece. "
        "Must match reference EXACTLY — same link style, color, pendant. Wearing "
        "a simple black v-neck top. Soft studio lighting creating gentle sparkle. "
        "Natural skin texture with subtle highlights. Shot on 85mm portrait lens. "
        "Minimalist luxury jewelry editorial."
    ),
    "hand_shot": (
        "Using this exact ring/bracelet from the reference image, generate a "
        "hyperrealistic close-up of a woman's hand wearing this exact piece. Must "
        "match reference EXACTLY — same metal, stone, design. Hand resting on "
        "white marble table holding a champagne glass. Manicured nails in nude pink. "
        "Soft side lighting creating sparkle. Shot on macro lens. Luxury brand aesthetic."
    ),
}

# ==========================================
# BEAUTY / FRAGRANCE PROMPTS
# ==========================================
BEAUTY_PROMPTS = {
    "perfume_ad": (
        "Using this exact person from the first reference image, generate a "
        "hyperrealistic beauty photo of her holding this exact perfume bottle "
        "from the second reference image near her neck. Eyes half-closed, "
        "breathing in the scent. Her face and features must match the first "
        "reference EXACTLY. The bottle must match the second reference EXACTLY. "
        "Soft golden studio lighting, 85mm portrait lens, creamy bokeh. "
        "Luxury fragrance campaign aesthetic, sensual and elegant."
    ),
    "skincare_glow": (
        "Using this exact person from the first reference image, generate a "
        "hyperrealistic dewy skin close-up of her with fresh glowing just-washed "
        "skin, gently touching her cheek. This exact product from the second "
        "reference image sits in soft focus in the foreground. Her face must match "
        "the first reference EXACTLY. Morning window light, water droplets on skin. "
        "Clean beauty brand aesthetic. Macro portrait lens."
    ),
    "makeup_tutorial": (
        "Using this exact person from the first reference image, generate a "
        "hyperrealistic photo of her applying makeup in a well-lit bathroom mirror. "
        "The exact product from the second reference image is in her hand. Features "
        "must match first reference EXACTLY. Product matches second reference EXACTLY. "
        "Ring light reflection visible in the mirror. Clean girl aesthetic, shot on "
        "iPhone 15 Pro. GRWM TikTok vibe, candid and natural."
    ),
    "lip_closeup": (
        "Using this exact person from the first reference image, generate a "
        "hyperrealistic extreme close-up of her lips wearing this exact lip product "
        "from the second reference image. Glossy, plump lips with visible texture. "
        "Soft studio lighting creating a natural shine. Features match reference "
        "EXACTLY. Product shade matches reference EXACTLY. Beauty editorial, "
        "macro lens, 8K detail."
    ),
}

# ==========================================
# WIG / HAIR PROMPTS
# ==========================================
WIG_PROMPTS = {
    "grwm_install": (
        "Using this exact person from the first reference image, generate a "
        "hyperrealistic GRWM photo of her installing this exact wig from the "
        "second reference image. She is looking into a bathroom mirror, hands "
        "adjusting the wig at the hairline. The wig must match the second "
        "reference EXACTLY — same color, length, texture, curl pattern. Her face "
        "must match the first reference EXACTLY. Warm bathroom lighting, shot on "
        "iPhone front camera. Authentic getting ready content, natural and real."
    ),
    "before_after": (
        "Generate a hyperrealistic two-panel split image. LEFT side: This exact "
        "person from the first reference image with a plain silk bonnet/cap, no "
        "makeup, simple background. RIGHT side: Same exact person now wearing this "
        "exact wig from the second reference image, light makeup, confident smile. "
        "Both panels have the same lighting and background. Dramatic transformation. "
        "Wig matches reference EXACTLY. Features match reference EXACTLY."
    ),
    "mirror_selfie_wig": (
        "Using this exact person from the first reference image, generate a "
        "hyperrealistic mirror selfie of her wearing this exact wig from the "
        "second reference image. Standing in a bedroom, phone in one hand, other "
        "hand touching the hair. The wig must match the second reference EXACTLY "
        "— same color, texture, length, parting style. Her face must match the "
        "first reference EXACTLY. Natural bedroom lighting, shot on iPhone. "
        "Confident pose, subtle smile. Authentic UGC aesthetic."
    ),
    "styling_shot": (
        "Using this exact person from the first reference image, generate a "
        "hyperrealistic photo of her styling this exact wig from the second "
        "reference image with a flat iron/curling wand. Sitting at a vanity, "
        "focused expression, one hand holding the styling tool. Wig matches "
        "reference EXACTLY — same hair type, color, density. Features match "
        "reference EXACTLY. Warm gold lighting, beauty content creator setup "
        "with ring light visible. Shot on 50mm lens."
    ),
    "outdoor_glam": (
        "Using this exact person from the first reference image, generate a "
        "hyperrealistic outdoor photo of her wearing this exact wig from the "
        "second reference image. Golden hour sunlight catching the hair, showing "
        "natural movement and texture. Standing on a city rooftop or park. Wig "
        "matches reference EXACTLY. Features match reference EXACTLY. Wind "
        "slightly catching the hair for natural movement. Fashion editorial "
        "photography, 85mm lens, shallow depth of field."
    ),
}

# ==========================================
# OUTERWEAR PROMPTS (Puffers, Bombers, Leather Jackets)
# ==========================================
OUTERWEAR_PROMPTS = {
    "puffer_streets": (
        "Using this exact person from the first reference image, generate a "
        "hyperrealistic photo of her wearing this exact puffer jacket from "
        "the second reference image. Features and puffer details must match "
        "references EXACTLY. Standing in a snow-dusted London street at dusk, "
        "glowing storefront lights in the blurred background. She is wearing the puffer "
        "zipped halfway, showcasing a cozy knit underneath. Shot on 85mm f/1.4 lens, "
        "rim light outlining the puffer's quilted silhouette. RAW photo quality."
    ),
    "bomber_candid": (
        "Using this exact person from the first reference image, generate a "
        "hyperrealistic candid photo of her wearing this exact bomber jacket from "
        "the second reference image. Features and jacket match references EXACTLY. "
        "She is leaning against a brick wall in a Brooklyn alleyway, checking her phone. "
        "Wearing a vintage wash tee underneath, classic street styling. Shot on 35mm "
        "lens with natural film grain, authentic UGC editorial aesthetic."
    ),
    "leather_campaign": (
        "Using this exact person from the first reference image, generate a "
        "hyperrealistic campaign photo of her wearing this exact leather jacket from "
        "the second reference image. Features and jacket match references EXACTLY. "
        "Standing in a concrete brutalist underground garage, dramatic high-contrast "
        "spotlight from the side highlighting the grain and texture of the distressed leather. "
        "Cool gaze directly at camera, hands in pockets. Hasselblad medium format quality."
    )
}

# ==========================================
# BAG & BACKPACK PROMPTS
# ==========================================
BAG_PROMPTS = {
    "shoulder_bag_street": (
        "Using this exact person from the first reference image, generate a "
        "hyperrealistic photo of her walking down a Soho street with this exact "
        "bag from the second reference image slung over her shoulder. Features and bag "
        "details (stitching, metal hardware, color) match references EXACTLY. "
        "Mid-stride pose, wind blowing her hair. Shot on 50mm f/1.8 lens. "
        "High-fashion street style snap, clean natural lighting."
    ),
    "backpack_flat_lay": (
        "Using this exact backpack from the reference image, generate an elite flat lay "
        "photography. The backpack matches the reference EXACTLY. Neatly styled on a "
        "polished concrete floor alongside a metal water bottle, a small journal, and "
        "wireless headphones. Overhead bird's-eye view, soft morning light from a window "
        "creating gentle shadows. Minimalist utility/gorpcore aesthetic."
    ),
    "handbag_reveal": (
        "Professional product photo of this exact handbag from the reference image. "
        "The bag is resting on a sleek black pedestal against a dark charcoal background. "
        "A sharp side spotlight illuminates the leather texture, metallic clasps, and "
        "brand logo. The bag matches the reference EXACTLY. Luxury e-commerce style, "
        "100mm macro lens focus."
    )
}

# ==========================================
# TECHWEAR & GORPCORE PROMPTS
# ==========================================
TECHWEAR_PROMPTS = {
    "cyberpunk_rain": (
        "Using this exact person from the first reference image, generate a "
        "hyperrealistic techwear campaign photo of her wearing this exact utility "
        "garment from the second reference image. Features and garment match references "
        "EXACTLY. Standing under heavy rain in a neon-lit Tokyo alleyway, "
        "raindrops visibly glistening on the water-resistant fabric. She is wearing a dark "
        "hood up, high collar zipped to the chin. Cool cyberpunk aesthetic, raw "
        "atmospheric shot on 35mm, cinema neon reflections."
    ),
    "gorpcore_mountain": (
        "Using this exact person from the first reference image, generate a "
        "hyperrealistic outdoor gorpcore shot of her wearing this exact technical shell "
        "jacket from the second reference image. Features and jacket match references "
        "EXACTLY. Standing on a rocky, misty mountain peak at sunrise, wind whipping the "
        "fabric. Shot on wide-angle lens, dramatic low perspective. Tactical hiking aesthetic, "
        "natural dawn light, epic scale."
    )
}

# ==========================================
# SEASONAL PROMPTS (Winter / Summer)
# ==========================================
SEASONAL_PROMPTS = {
    "winter_cozy": (
        "Using this exact person from the first reference image, generate a "
        "hyperrealistic winter photo of her wearing this exact heavy coat from the "
        "second reference image. Cozy winter outfit with scarf and gloves. "
        "Walking through a snow-covered park, breath visible in the frosty air. "
        "Soft overcast winter lighting. Features and coat match references EXACTLY."
    ),
    "summer_heat": (
        "Using this exact person from the first reference image, generate a "
        "hyperrealistic summer lifestyle photo of her wearing this exact summer item "
        "from the second reference image. Sitting poolside on a lounge chair, bright "
        "sunlight casting crisp shadows, a glass of iced tea on a side table. "
        "Vibrant warm tones, tropical plants in background. Features and garment match EXACTLY."
    )
}

# ==========================================
# MALE-SPECIFIC UGC PROMPTS
# ==========================================
MALE_UGC_PROMPTS = {
    "male_mirror_selfie": (
        "Using this exact man from the first reference image, generate a "
        "hyperrealistic mirror selfie of him wearing this exact garment from "
        "the second reference image. The face, hair, and build must match the first "
        "reference EXACTLY. The garment must match the second reference EXACTLY. "
        "Standing in a modern bedroom with a large full-length mirror, natural light. "
        "One hand holding the phone, casual confident posture. Authentic GRWM "
        "style, slight grain, RAW photo."
    ),
    "male_ootd_street": (
        "Using this exact man from the first reference image, generate a "
        "hyperrealistic OOTD photo of him wearing this exact outfit from the second "
        "reference image. Features and outfit match references EXACTLY. "
        "Walking down a rain-slicked London street, urban brick wall backdrop. "
        "Shot on 85mm f/1.8, shallow depth of field. Confident mid-stride pose, "
        "premium street style snap."
    ),
    "male_cafe_candid": (
        "Using this exact man from the first reference image, generate a "
        "hyperrealistic lifestyle photo of him sitting at a concrete table of an outdoor "
        "minimalist cafe, wearing this exact garment from the second reference image. "
        "One hand resting on a coffee cup, looking casually away from camera. "
        "Golden hour warm lighting, Sony A7IV look, authentic UGC vibe."
    )
}

# ==========================================
# THE HUMAN SHADOW — DOCUMENTARY PROMPTS
# ==========================================
DOCUMENTARY_PROMPTS = {
    "host_intro": (
        "Using this exact host from the first reference image, generate a "
        "cinematic close-up of him speaking to the camera in a dark, shadow-heavy "
        "study. A single warm light source hits half of his face, leaving the "
        "other half in deep shadow (chiaroscuro lighting). Background is filled "
        "with blurred antique books and a single glowing candle. 35mm film grain, "
        "A24 aesthetic, moody and philosophical. Features match reference EXACTLY."
    ),
    "cinematic_broll": (
        "Extreme close-up macro shot of an eye reflecting a flickering television "
        "screen in a dark room. Dust motes visible in a single shaft of light. "
        "Atmospheric, eerie, high-contrast black and white. 16mm film texture."
    ),
    "philosophical_scene": (
        "A lone figure (matching the host reference) standing on a misty cliffside "
        "at night, looking into a vast dark abyss. The figure is a small silhouette "
        "against an overwhelming nature. Cinematic wide shot, deep blues and blacks, "
        "grainy texture, haunting atmosphere."
    ),
}

# ==========================================
# VIDEO PROMPTS (Veo 3)
# ==========================================
VIDEO_PROMPTS = {
    "model_walk": (
        "3-second cinematic slow motion video of a confident woman walking toward "
        "the camera wearing this outfit. Urban sidewalk, golden hour, shallow depth "
        "of field with bokeh background. Hair bouncing naturally, fabric swaying with "
        "each step. Smooth camera, no shake. 9:16 vertical format. Authentic human "
        "movement, no uncanny valley."
    ),
    "slow_turn": (
        "3-second cinematic video of a fashion model slowly turning 180 degrees "
        "from front to back, showing all angles of the garment. Neutral studio "
        "backdrop, soft diffused lighting. The fabric moves naturally with the turn. "
        "24fps cinematic look. 9:16 vertical."
    ),
    "product_reveal": (
        "3-second cinematic close-up video of a hand slowly placing the product "
        "onto a marble surface. Camera slowly dollies in. Dramatic side lighting "
        "creating sharp shadows. The product rotates slightly showing texture. "
        "Smooth, satisfying reveal energy. Premium commercial aesthetic."
    ),
    "shoe_walk": (
        "3-second cinematic slow motion video shot from knee level. Person walking "
        "on clean concrete, showcasing the shoes with each step. Natural bounce and "
        "movement. Side lighting, slight motion blur on background. Sneaker commercial "
        "aesthetic. 9:16 vertical."
    ),
}

# ==========================================
# BEAUTY-MODEL QUALITY STANDARDS
# ==========================================
# What separates a "fashion model" from a generic AI face.
# The brain uses these to generate AND evaluate model quality.
BEAUTY_MODEL_STANDARDS = {
    "face_structure": [
        "symmetrical face with defined cheekbones",
        "clean jawline with subtle definition",
        "balanced facial proportions (forehead, midface, lower face)",
        "naturally full lips with visible cupid's bow",
        "defined but natural eyebrows (not over-groomed)",
    ],
    "skin_quality": [
        "visible pores on nose and cheeks (anti-AI)",
        "natural skin texture with micro-imperfections",
        "healthy glow without artificial shine",
        "subtle under-eye shadows (human, not retouched)",
        "no plastic surgery look — natural bone structure",
    ],
    "hair_quality": [
        "individual strands visible, not a smooth AI blob",
        "natural flyaways and baby hairs at hairline",
        "realistic hair shine with single highlight point",
        "natural root color variation",
    ],
    "body_language": [
        "relaxed shoulders, not stiff or posed",
        "natural hand position (not claw-like AI hands)",
        "weight shifted to one leg (natural stance)",
        "slight asymmetry in pose (human, not robotic)",
    ],
    "lighting_for_beauty": {
        "fair_skin": "soft butterfly lighting, diffused fill, warm tones",
        "medium_skin": "Rembrandt lighting, warm golden fill, rich contrast",
        "dark_skin": "rim lighting from behind, warm key light at 45°, avoid flat frontal",
        "all": "catch light in eyes, subtle nose shadow, defined cheekbone shadow",
    },
}


# ==========================================
# IDENTITY BLOCKS — Anchor-First System
# ==========================================
# Every character gets a fixed identity block that NEVER changes.
# This is prepended to EVERY prompt for that character.
def build_identity_block(preset: dict, model_id: str) -> str:
    """Build a fixed narrative identity descriptor for consistent FLUX character generation."""
    return (
        f"a normal, everyday {preset.get('age', '24')}-year-old {preset.get('gender', 'woman')} "
        f"with {preset['hair_desc']}, {preset['eye_desc']}, and {preset['skin_desc']}. "
        f"Structurally, they have an {preset.get('face_desc', 'average asymmetrical face with natural imperfections and soft jawline')}, "
        f"supported by a {preset.get('body_desc', 'natural candid build at 5 foot 5, with average proportions')}. "
        f"They wear small {preset.get('piercing', 'silver stud earrings')}."
    )


# ==========================================
# CHARACTER SHEET PROMPTS — Anchor-First Workflow
# ==========================================
# Step 1: Generate ANCHOR (front portrait, white bg, maximum detail)
# Step 2: Use anchor as reference for all other angles
# Step 3: Generate full body for outfit matching
CHARACTER_SHEET_PROMPTS = {
    "anchor_portrait": (
        "Hyperrealistic front-facing portrait photograph of {identity_block}. "
        "Clean white studio background, even Rembrandt lighting with soft fill. "
        "Sharp focus on the face, 85mm f/2.8 portrait lens. Catch light visible "
        "in both eyes. Natural expression — soft confidence, not smiling. No heavy "
        "makeup, only light mascara and lip balm. Visible pores on nose, natural "
        "eyebrow texture, individual eyelashes visible. Subtle under-eye shadows. "
        "Hair styled naturally, individual strands visible with baby hairs at "
        "hairline. This is the MASTER reference — every detail matters. "
        "Shot on Canon EOS R5, RAW photo, no retouching, no AI smoothing. "
        "Fashion model test shoot aesthetic. 8K resolution."
    ),
    "three_quarter_view": (
        "Using this EXACT person from the reference image, generate the SAME person "
        "from a three-quarter (45°) angle view. IDENTICAL face: same {identity_block}. "
        "Same eyes, same nose, same lips, same skin texture, same hair. "
        "Clean white studio background, matching lighting from the reference. "
        "Slight turn of the head showing ear and jawline profile. Same natural "
        "expression. Portrait photography, 85mm lens. The face MUST be identical "
        "to the reference — zero deviation in features. RAW photo style."
    ),
    "side_profile": (
        "Using this EXACT person from the reference image, generate the SAME person "
        "in a clean side profile (90° view). IDENTICAL features: same {identity_block}. "
        "Clean white studio background, rim light on the profile edge. Shows nose "
        "bridge, jawline shape, ear. Hair falls naturally. Same skin texture as "
        "reference. Portrait photography, 85mm lens. Features MUST match reference "
        "exactly. RAW photo style."
    ),
    "full_body": (
        "Using this EXACT person from the reference image, generate a full-body "
        "standing photo of the SAME person. IDENTICAL face and features: same "
        "{identity_block}. Wearing a simple white tank top and black leggings "
        "(neutral outfit for reference). Natural standing pose, weight on one leg, "
        "hands relaxed at sides. Clean white studio background. Full body visible "
        "from head to shoes. Shows body proportions and posture. Even studio "
        "lighting. Shot on 50mm lens. This is the body reference for all future "
        "outfit generations. RAW photo style."
    ),
    # Legacy compatibility
    "female_model": (
        "Hyperrealistic character reference sheet of a 24-year-old woman with "
        "{hair_desc}, {eye_desc}, {skin_desc}. Show her face in a clean "
        "front-facing portrait with a soft, natural smile. Even studio lighting, "
        "clean white background. No makeup except light mascara. Natural eyebrow "
        "shape, slightly full lips. Portrait photography, 85mm lens, sharp focus "
        "on the face. This image will be used as a consistent model reference for "
        "a fashion brand. RAW photo style, no AI smoothing, authentic skin texture."
    ),
    "male_model": (
        "Hyperrealistic character reference sheet of a 26-year-old man with "
        "{hair_desc}, {eye_desc}, {skin_desc}. Show his face in a clean "
        "front-facing portrait with a confident, relaxed expression. Even studio "
        "lighting, clean white background. No styling product in hair, natural look. "
        "Portrait photography, 85mm lens, sharp focus on the face. RAW photo style, "
        "no retouching."
    ),
    "angle_variation": (
        "Using this exact person from the reference image, generate the SAME person "
        "from a {angle} angle view. Same face, same hair, same eyes, same features, "
        "same skin. Clean white studio background, even lighting. Portrait photography, "
        "85mm lens. The face must be identical to the reference — do not change any "
        "features. {expression}"
    ),
}


# ==========================================
# HELPER: GET PROMPTS BY PRODUCT TYPE
# ==========================================
def get_prompts_for_product(product_type: str, is_set: bool = False) -> dict:
    """Return the appropriate prompt set based on product type.
    
    Returns a dict with:
      - 'product_shots': list of (prompt_dict, shot_key) for product-only photography
      - 'on_model': bool — whether on-model shots are allowed for this product alone
    
    Individual products NEVER get on-model shots (AI invents phantom clothes).
    On-model shots are ONLY generated for curated full outfits.
    """
    if is_set:
        return {
            "product_shots": [
                (SET_FLAT_LAY_PROMPTS, "set_flat_lay"),
                (GHOST_MANNEQUIN_PROMPTS, "ghost_mannequin"),
                (DETAIL_CLOSEUP_PROMPTS, "detail"),
            ],
            "on_model": False,  # Outfit page handles on-model
        }
    
    mapping = {
        "clothing": {
            "product_shots": [
                (CLOTHING_PROMPTS, "flat_lay"),  # Only flat lay prompts from CLOTHING_PROMPTS
                (GHOST_MANNEQUIN_PROMPTS, "ghost_mannequin"),
                (DETAIL_CLOSEUP_PROMPTS, "detail"),
            ],
            "on_model": False,
        },
        "tops": {
            "product_shots": [
                (CLOTHING_PROMPTS, "flat_lay"),
                (GHOST_MANNEQUIN_PROMPTS, "ghost_mannequin"),
                (HANGER_PROMPTS, "hanger"),
                (DETAIL_CLOSEUP_PROMPTS, "detail"),
            ],
            "on_model": False,
        },
        "bottoms": {
            "product_shots": [
                (CLOTHING_PROMPTS, "flat_lay"),
                (GHOST_MANNEQUIN_PROMPTS, "ghost_mannequin"),
                (DETAIL_CLOSEUP_PROMPTS, "detail"),
            ],
            "on_model": False,
        },
        "shoes": {
            "product_shots": [
                (SHOE_PROMPTS, "on_foot"),
                (SHOE_PROMPTS, "product_hero"),
                (SHOE_PROMPTS, "unboxing"),
                (DETAIL_CLOSEUP_PROMPTS, "detail"),
            ],
            "on_model": False,
        },
        "accessories": {
            "product_shots": [
                (ACCESSORY_PROMPTS, "product_closeup"),
                (DETAIL_CLOSEUP_PROMPTS, "detail"),
            ],
            "on_model": False,
        },
        "beauty": {
            "product_shots": [
                (BEAUTY_PROMPTS, "product_shot"),
                (DETAIL_CLOSEUP_PROMPTS, "detail"),
            ],
            "on_model": False,
        },
        "bags": {
            "product_shots": [
                (BAG_PROMPTS, "product_shot"),
                (DETAIL_CLOSEUP_PROMPTS, "detail"),
            ],
            "on_model": False,
        },
        "outfit": {
            "product_shots": [],  # No product-only shots needed
            "on_model": True,  # Full outfit = allowed on model
        },
    }
    
    return mapping.get(product_type, mapping["clothing"])


def get_flat_lay_only_prompts() -> dict:
    """Return only the flat lay prompts from CLOTHING_PROMPTS (no on-model prompts)."""
    flat_lay_keys = [k for k in CLOTHING_PROMPTS if 'flat_lay' in k]
    return {k: CLOTHING_PROMPTS[k] for k in flat_lay_keys}


def get_video_prompt(style: str = "model_walk") -> str:
    """Return a video generation prompt."""
    return VIDEO_PROMPTS.get(style, VIDEO_PROMPTS["model_walk"])


def get_character_sheet_prompt(step: str, identity_block: str = "", **kwargs) -> str:
    """Get a character sheet prompt with identity block filled in."""
    template = CHARACTER_SHEET_PROMPTS.get(step, CHARACTER_SHEET_PROMPTS["anchor_portrait"])
    return template.format(identity_block=identity_block, **kwargs)


# ==========================================
# MODEL PRESETS — Diverse, Beauty-Quality
# ==========================================
# Each preset defines a DISTINCT model with fashion-model quality features
MODEL_PRESETS = [
    {
        "id": "sophia_f1",
        "gender": "woman", "age": "23",
        "hair_desc": "honey blonde shoulder-length hair with natural waves and golden highlights",
        "eye_desc": "green-hazel eyes with gold flecks and long natural lashes",
        "skin_desc": "light warm-toned skin with natural freckles across nose and cheeks, visible pores, healthy glow",
        "face_desc": "Symmetrical oval face, high cheekbones, defined cupid's bow, natural arched eyebrows",
        "body_desc": "Slim athletic build, 5'9\", long neck, natural proportions",
        "piercing": "small gold hoop earrings",
        "best_for": ["streetwear", "luxury_casual", "minimalist"],
    },
    {
        "id": "amara_f2",
        "gender": "woman", "age": "25",
        "hair_desc": "rich dark brown box braids past shoulders with subtle auburn ends",
        "eye_desc": "deep warm brown eyes with dark limbal rings and thick natural lashes",
        "skin_desc": "deep brown glowing skin with warm undertones, natural highlights on cheekbones, visible skin texture",
        "face_desc": "Heart-shaped face, prominent cheekbones, full natural lips, defined jawline",
        "body_desc": "Tall athletic build, 5'10\", graceful posture",
        "piercing": "gold stud earrings and thin nose ring",
        "best_for": ["streetwear", "athleisure", "y2k"],
    },
    {
        "id": "luna_f3",
        "gender": "woman", "age": "22",
        "hair_desc": "jet black straight hair with center part falling to mid-back, blue-black sheen",
        "eye_desc": "dark brown almond-shaped eyes with subtle monolid, straight lashes",
        "skin_desc": "smooth light olive skin with porcelain quality, subtle warm undertones, natural blush on cheeks",
        "face_desc": "Delicate oval face, soft jawline, small nose, gently arched eyebrows, beauty mark near left eye",
        "body_desc": "Petite slim build, 5'5\", delicate frame",
        "piercing": "tiny silver stud earrings",
        "best_for": ["minimalist", "luxury_casual", "dark_aesthetic"],
    },
    {
        "id": "zara_f4",
        "gender": "woman", "age": "24",
        "hair_desc": "auburn red curly hair in a natural voluminous style, copper highlights catching light",
        "eye_desc": "striking blue-grey eyes with amber ring around pupil",
        "skin_desc": "fair celtic skin with light freckles across nose bridge and cheeks, visible pores, natural rosy flush",
        "face_desc": "Strong angular face, sharp cheekbones, defined jaw, natural thick eyebrows",
        "body_desc": "Lean model build, 5'8\", strong shoulders",
        "piercing": "multiple small silver ear piercings",
        "best_for": ["dark_aesthetic", "streetwear", "luxury_casual"],
    },
    {
        "id": "maya_f5",
        "gender": "woman", "age": "21",
        "hair_desc": "dark brown natural curls in a voluminous afro-textured style, defined curl pattern",
        "eye_desc": "large expressive dark brown eyes with long curled lashes",
        "skin_desc": "rich medium-brown skin with golden undertones, natural glow on forehead and cheekbones, visible texture",
        "face_desc": "Round face with soft features, full lips, wide-set eyes, button nose",
        "body_desc": "Curvy athletic build, 5'7\", hourglass proportions",
        "piercing": "gold hoop earrings",
        "best_for": ["athleisure", "y2k", "streetwear"],
    },
    {
        "id": "erik_m1",
        "gender": "man", "age": "26",
        "hair_desc": "dark brown textured fade with longer top styled to the side",
        "eye_desc": "green-brown hazel eyes with thick dark eyebrows",
        "skin_desc": "medium warm-toned skin with subtle stubble, visible pores, natural complexion",
        "face_desc": "Square jaw, prominent brow ridge, straight nose, defined chin",
        "body_desc": "Athletic mesomorph build, 6'1\", broad shoulders",
        "piercing": "no visible piercings",
        "best_for": ["streetwear", "luxury_casual", "athleisure"],
    },
    {
        "id": "kai_m2",
        "gender": "man", "age": "24",
        "hair_desc": "black tight buzz cut with sharp lineup, low skin fade",
        "eye_desc": "deep brown eyes with dark limbal rings, thick straight lashes",
        "skin_desc": "deep brown skin with warm mahogany undertones, natural sheen on forehead, visible pores",
        "face_desc": "Strong angular face, high cheekbones, full lips, broad nose, defined brow ridge",
        "body_desc": "Lean athletic build, 6'0\", defined arms, narrow waist",
        "piercing": "single diamond stud in left ear",
        "best_for": ["streetwear", "athleisure", "y2k"],
    },
    {
        "id": "nadia_f6",
        "gender": "woman", "age": "23",
        "hair_desc": "dark espresso brown loose waves falling past collarbones, subtle caramel balayage",
        "eye_desc": "warm amber-brown eyes with thick natural brows, subtle beauty mark below right eye",
        "skin_desc": "warm olive Mediterranean skin, natural tan, light freckles on shoulders, visible skin texture",
        "face_desc": "Oval face with strong nose, soft jawline, naturally arched thick eyebrows, slightly asymmetric smile",
        "body_desc": "Slim hourglass build, 5'7\", toned arms",
        "piercing": "thin gold chain necklace, small gold hoops",
        "best_for": ["luxury_casual", "minimalist", "dark_aesthetic"],
    },
    {
        "id": "chioma_f7",
        "gender": "woman", "age": "22",
        "hair_desc": "natural 4C coils in a high sculptural puff, defined edges, rich black color",
        "eye_desc": "large dark brown eyes with golden-brown flecks, long natural lashes",
        "skin_desc": "deep ebony skin with cool blue-black undertones, luminous highlight on cheekbones, clear texture",
        "face_desc": "Heart-shaped face, high forehead, prominent cheekbones, full bow-shaped lips, refined nose",
        "body_desc": "Tall willowy build, 5'10\", long limbs, graceful neck",
        "piercing": "subtle gold nose stud, thin gold stackable rings",
        "best_for": ["streetwear", "luxury_casual", "y2k", "dark_aesthetic"],
    },
    {
        "id": "jin_m3",
        "gender": "man", "age": "23",
        "hair_desc": "black middle-parted curtain bangs with soft texture, slight wave",
        "eye_desc": "dark brown monolid eyes with subtle double-fold, straight thick lashes",
        "skin_desc": "light warm-toned East Asian skin, smooth with visible pores on nose, natural blush on cheeks",
        "face_desc": "Oval face with soft jawline, straight nose bridge, defined lips, clean eyebrows",
        "body_desc": "Slim lean build, 5'11\", narrow shoulders, long torso",
        "piercing": "silver ear cuff on right ear",
        "best_for": ["minimalist", "luxury_casual", "dark_aesthetic", "y2k"],
    },
]


# ==========================================
# GLOBAL MARKETS — Regional Aesthetics
# ==========================================
# Defines lighting, environment, and camera style for specific regions.
GLOBAL_MARKETS = {
    "london_uk": {
        "scene": "london_mews",
        "lighting": "overcast soft light, diffused morning atmosphere",
        "camera": "film_editorial_grain", 
        "vibe": "effortless cool, utilitarian streetwear, moody urban"
    },
    "nyc_usa": {
        "scene": "brooklyn_brownstone",
        "lighting": "harsh afternoon sun, deep cinematic shadows, high contrast",
        "camera": "wide_editorial_full",
        "vibe": "high-energy, skyscraper backdrop, luxury street"
    },
    "paris_eu": {
        "scene": "paris_cafe",
        "lighting": "warm golden afternoon, romantic backlight",
        "camera": "editorial_portrait",
        "vibe": "chic, minimalist, timeless elegance, soft grain"
    },
    "milan_eu": {
        "scene": "modern_atrium",
        "lighting": "sharp luxury mall lighting, marble reflections",
        "camera": "pro_commercial_clean",
        "vibe": "ultra-luxury, pristine, sharp tailoring, high-fashion"
    },
    "default_global": {
        "scene": "studio_white",
        "lighting": "professional studio strobes, clean even light",
        "camera": "editorial_portrait",
        "vibe": "commercial, product-focused, clean"
    }
}

# ==========================================
# DIVERSITY MAP — Demographic Logic
# ==========================================
# Prevents cultural mismatch by pairing clothing styles with appropriate models.
DIVERSITY_MAP = {
    "streetwear": [
        "a stylish professional model with cool West African features, natural short hair",
        "a stylish model with Mediterranean features, olive skin, and dark wavy hair",
        "a fashion-forward model with East Asian features and sharp editorial look",
    ],
    "luxury_formal": [
        "a sophisticated model with elegant European features and sleek hair",
        "a dignified model with Middle Eastern features and impeccable grooming",
        "a professional model with South Asian features and graceful posture",
    ],
    "ugc_casual": [
        "a relatable person with diverse features, natural skin texture, everyday look",
        "a trendy individual with mixed-heritage features and a friendly expression",
    ],
    "high_fashion": [
        "a striking model with unique, diverse features and a bold editorial gaze",
        "an ethereal model with porcelain skin and sharp, futuristic features",
    ]
}


# ==========================================
# CAMERA PRESETS — Technical Photography Language
# ==========================================
# Using real camera specs makes AI images look like actual photographs.
# The brain picks the right preset based on the ad type.
CAMERA_PRESETS = {
    "ugc_selfie": (
        "Shot on iPhone 15 Pro, front camera, slightly grainy, "
        "natural indoor lighting, casual handheld angle, "
        "visible slight motion blur, Instagram Stories quality"
    ),
    "editorial_portrait": (
        "Shot on Canon EOS R5 with 85mm f/1.4 lens, shallow depth of field, "
        "bokeh background, Profoto B10 key light at 45 degrees with white "
        "reflector fill, studio backdrop, RAW photo, no retouching"
    ),
    "street_candid": (
        "Shot on 35mm Kodak Portra 400 film, natural daylight, slight warm "
        "color cast, subtle film grain, candid moment captured mid-stride, "
        "shallow depth of field f/2.0, soft background blur"
    ),
    "fashion_editorial": (
        "Shot on Phase One IQ4 150MP, 110mm f/2.8, editorial fashion lighting "
        "with large octabox key and strip lights on either side, "
        "Vogue-quality studio setup, tethered capture, 8K resolution"
    ),
    "golden_hour": (
        "Shot on Sony A7IV with 50mm f/1.2 lens, golden hour backlight, "
        "warm amber flares, rim light on hair and shoulders, "
        "soft amber fill from reflector, cinematic color grading"
    ),
    "dark_moody": (
        "Shot on Leica Q3 28mm f/1.7, single harsh side light, "
        "deep shadows, chiaroscuro lighting, dark backdrop, "
        "high contrast, minimal fill, dramatic and atmospheric"
    ),
    "flat_lay_overhead": (
        "Shot on 35mm lens from directly overhead, even diffused "
        "window light from left side, gentle shadows, clean white or "
        "neutral surface, product photography style, crisp detail"
    ),
    "product_macro": (
        "Shot on 100mm macro lens f/4, focus stacked, soft side lighting "
        "revealing texture and material quality, clean gradient backdrop, "
        "commercial product photography, razor-sharp detail"
    ),
    "noshoots_catalog_50mm": (
        "Shot on 50mm lens, eye-level, full-body catalog framing, "
        "razor-sharp focus on clothing texture, natural depth of field"
    ),
    "noshoots_candid_35mm": (
        "Shot on 35mm lens, candid eye-level perspective, "
        "slight motion blur in background only, realistic color grading with subtle grain"
    ),
    "noshoots_portrait_85mm": (
        "Shot on 85mm portrait lens with moderate depth of field, "
        "soft organic bokeh, high-fashion catalog styling"
    ),
}


# ==========================================
# FABRIC & MATERIAL MODIFIERS — Makes Clothing Look Real
# ==========================================
# Generic: "wearing a hoodie" → Pro: "wearing a heavyweight 420gsm brushed terry hoodie"
FABRIC_MODIFIERS = {
    "hoodie": "heavyweight 420gsm brushed French terry hoodie with ribbed cuffs",
    "t_shirt": "vintage-washed 200gsm cotton jersey tee with slight pilling at seams",
    "tank_top": "ribbed cotton tank with raw-cut edges and natural drape",
    "sweater": "chunky cable-knit merino wool sweater with natural heathered texture",
    "jacket": "washed cotton canvas jacket with visible wear at collar and elbows",
    "blazer": "tailored Italian wool-blend blazer with half-canvas construction",
    "jeans": "raw selvedge Japanese denim jeans with visible chain-stitch hemming",
    "joggers": "tapered brushed fleece joggers with elastic ribbed ankle cuffs",
    "cargo_pants": "relaxed-fit ripstop cotton cargo pants with utilitarian hardware",
    "mini_skirt": "high-waisted pleated gabardine mini skirt with pressed creases",
    "midi_dress": "flowing crinkled silk crepe midi dress with bias cut and raw hem",
    "bodysuit": "stretch ribbed modal bodysuit with snap closure",
    "puffer": "matte nylon quilted puffer jacket with recycled down fill",
    "leather_jacket": "distressed lambskin moto jacket with tarnished brass hardware",
    "sneakers": "premium tumbled leather sneakers with gum rubber outsole",
    "boots": "chunky-sole Chelsea boots in waxed suede with pull tabs",
    "crop_top": "cropped baby tee in washed cotton with lettuce-edge hem",
    "tracksuit": "matching velour tracksuit set with contrast piping details",
    "bomber": "heavyweight satin nylon bomber jacket with ribbed collar, cuffs, and hem, utility sleeve pocket",
    "parka": "weatherproof fishtail parka with drawstring waist, water-repellent shell, and metal hardware",
    "windbreaker": "lightweight crinkled nylon windbreaker with half-zip closure and adjustable toggle hood",
    "denim_jacket": "vintage-washed 14oz rigid denim jacket with dual chest pockets and branded metal shank buttons",
    "polo": "retro knit cotton polo shirt with open flat collar and ribbed cuffs",
    "henley": "waffle-knit cotton henley shirt with three-button placket and flatlock stitching",
}


# ==========================================
# ANTI-AI DETECTION V2 — Pro-Level Imperfection Layer
# ==========================================
# Three tiers: Subtle (editorial), Medium (UGC), Heavy (raw selfie)
ANTI_AI_SUBTLE = (
    "Visible skin pores on nose and forehead, natural under-eye shadows, "
    "asymmetric facial features, individual hair strands with one flyaway, "
    "subtle lip dryness, natural nail beds with cuticles, "
    "shot on analog camera with slight color cast."
)

ANTI_AI_MEDIUM = (
    "Film grain overlay, visible skin texture with pores and fine lines, "
    "slightly uneven skin tone across cheeks, two flyaway hair strands, "
    "micro-wrinkles near eyes when smiling, natural nail beds with cuticles, "
    "one barely visible blemish near jawline, shot on smartphone with "
    "slight lens distortion at edges, natural noise in shadow areas, "
    "not perfectly symmetrical face."
)

ANTI_AI_HEAVY = (
    "High ISO noise throughout image, visible skin texture with pores "
    "and redness, slightly oily T-zone, several flyaway hairs, "
    "micro-wrinkles near eyes and forehead, bitten nails on one hand, "
    "slight sunburn on nose, one small acne mark, "
    "shot on older smartphone in mixed indoor/outdoor lighting, "
    "slightly warm color cast from tungsten light, visible compression "
    "artifacts, casual composition with slightly off-center framing, "
    "background clutter (charging cable, half-drunk coffee). "
    "This looks like a real person took this, NOT an AI."
)


# ==========================================
# SCENE PRESETS — Ready-to-Use Backgrounds
# ==========================================
SCENE_PRESETS = {
    "brooklyn_brownstone": "standing in front of a sunlit Brooklyn brownstone doorway, warm brick, iron railing, morning light",
    "tokyo_street": "walking through a neon-lit Tokyo side street at dusk, wet pavement reflections, paper lanterns overhead",
    "paris_cafe": "seated at a small Parisian sidewalk café table, espresso and croissant, warm afternoon light filtering through awning",
    "la_poolside": "lounging on a cream poolside daybed at a mid-century modern LA home, palm trees, blue sky, golden hour",
    "london_mews": "standing on a cobblestone London mews street, pastel-colored house facades, overcast soft light",
    "dubai_mall": "walking through a gleaming modern shopping mall atrium, marble floors, ambient luxury lighting",
    "nyc_subway": "leaning against a tiled NYC subway wall, fluorescent lighting, gritty urban texture",
    "beach_sunset": "barefoot on wet sand at sunset, warm amber light, gentle waves in background, wind in hair",
    "studio_white": "clean white seamless studio backdrop, professional even lighting, fashion test shoot setup",
    "studio_dark": "dark charcoal backdrop with single dramatic side light, moody editorial atmosphere",
    "bedroom_morning": "in a sunny bedroom with unmade white linen bed, morning light through sheer curtains, cozy authentic mood",
    "gym_locker": "in a modern gym locker room, warm overhead lighting, workout bag on bench, post-workout glow",
    "rooftop_golden": "on an urban rooftop at golden hour, city skyline backdrop, warm side lighting, wind catching fabric",
    "vintage_car": "leaning against a vintage car hood (60s muscle car), parking lot, late afternoon shadows",

    # ====== NEW: Elite Creative Scenes (2026) ======
    "warehouse_shoot": (
        "standing in a converted industrial warehouse studio with exposed brick walls, "
        "concrete floor, and large steel-frame windows letting in diffused natural light. "
        "Vintage photography equipment visible in background. Raw, editorial atmosphere"
    ),
    "modelling_studio": (
        "posing in a professional modelling studio with large softbox lights visible, "
        "a grey seamless paper backdrop slightly wrinkled at the floor, "
        "a reflector stand to the side. Behind-the-scenes fashion campaign energy"
    ),
    "grwm_mirror": (
        "taking a mirror selfie in a well-lit modern apartment hallway with a full-length "
        "mirror, phone held at chest height, relaxed natural pose. Warm overhead LED light, "
        "a coat rack and shoes visible in background. Authentic GRWM Instagram content"
    ),
    "grwm_bathroom": (
        "getting ready in a modern bathroom with large round vanity mirror, ring light "
        "creating a warm glow, skincare products on the counter. Candid mid-outfit check "
        "moment, phone propped up recording. TikTok GRWM aesthetic"
    ),
    "home_couch": (
        "sitting casually on a cream bouclé couch in a minimalist living room, legs tucked "
        "under, warm afternoon light from large windows, a coffee table with candles and a "
        "book nearby. Cozy home content creator vibe, relaxed and authentic"
    ),
    "fitting_room": (
        "standing in a well-lit retail fitting room with soft warm lighting, "
        "multiple mirrors showing different angles, shopping bags on the bench. "
        "Authentic try-on haul aesthetic, candid and natural. Shot on iPhone"
    ),
    "coffee_shop": (
        "seated at a minimalist specialty coffee shop with exposed light bulbs, "
        "wooden tables, a latte in hand. Soft natural window light from the side, "
        "blurred customers in background. Casual lifestyle content"
    ),
    "car_interior": (
        "sitting in the passenger seat of a modern car with leather interior, "
        "natural daylight coming through the windshield, seatbelt on, looking "
        "toward the camera with a relaxed half-smile. Candid car selfie aesthetic"
    ),
    "snow_mountain": (
        "standing on a snow-covered mountain ridge at a luxury ski resort. "
        "Crisp, clear winter sunlight, blue sky, and majestic snow peaks in the background. "
        "High-end alpine fashion editorial, cinematic winter aesthetic. Visible breath in the cold air"
    ),
    "bed_fit_check": (
        "This is a flat-lay 'fit check' photo with NO human model. "
        "The garments are neatly laid out together on an unmade white linen bed. "
        "Overhead shot, warm natural bedroom light from the side. Authentic UGC style, "
        "like an influencer showing off their outfit for the day before putting it on."
    ),
    "floor_fit_check": (
        "This is a flat-lay 'fit check' photo with NO human model. "
        "The garments are styled together on a premium textured concrete or hardwood floor. "
        "Shot from directly above (bird's-eye view). Cinematic overhead lighting "
        "casting soft shadows. High-end streetwear archive presentation."
    ),
    "noshoots_minimal_studio": (
        "standing in a minimal studio setting, clean seamless background in soft gray or white, "
        "soft even lighting from large diffused sources, gentle shadow under feet, "
        "e-commerce lookbook aesthetic"
    ),
    "noshoots_soho_street": (
        "walking through Soho NYC, past premium boutique storefronts and cast-iron buildings, "
        "candid mid-step, overcast natural daylight, subtle film grain"
    ),
    "noshoots_beige_studio": (
        "in a minimalist studio environment with a seamless warm beige or light gray background, "
        "elegant artistic pose, soft diffused side lighting creating organic shadows"
    ),
}



def build_global_prompt(
    clothing_item: str,
    market: str = "london_uk",
    category: str = "streetwear",
    anti_ai_level: str = "medium",
) -> str:
    """Combines Market aesthetic + Diversity mapping for a globally-aware prompt."""
    
    # 1. Select the regional aesthetic
    market_cfg = GLOBAL_MARKETS.get(market, GLOBAL_MARKETS["default_global"])
    
    # 2. Select a diverse model based on the style category
    import random
    model_identity = random.choice(DIVERSITY_MAP.get(category, DIVERSITY_MAP["streetwear"]))
    
    # 3. Pull Fabric Detail
    fabric_detail = get_fabric_upgrade(clothing_item)
    
    # 4. Pull Scene & Lighting
    scene_desc = SCENE_PRESETS.get(market_cfg["scene"], market_cfg["scene"])
    anti_ai = {
        "subtle": ANTI_AI_SUBTLE,
        "medium": ANTI_AI_MEDIUM,
        "heavy": ANTI_AI_HEAVY,
    }.get(anti_ai_level, ANTI_AI_MEDIUM)
    
    # 5. Weave the Global Narrative
    prompt = (
        f"A professional global fashion photograph of {model_identity} at {scene_desc}. "
        f"They are wearing a {fabric_detail}. The {market_cfg['vibe']} aesthetic is captured "
        f"with {market_cfg['lighting']} using a {CAMERA_PRESETS[market_cfg['camera']] if market_cfg['camera'] in CAMERA_PRESETS else 'professional camera'}. "
        f"The image features {anti_ai}"
    )
    
    return prompt.replace("  ", " ")


# ==========================================
# PRO PROMPT BUILDER — Combines Identity + Scene + Camera + Anti-AI
# ==========================================
def build_pro_prompt(
    identity_block: str,
    scene: str = "studio_white",
    camera: str = "editorial_portrait",
    outfit_desc: str = "",
    anti_ai_level: str = "medium",
    extra: str = "",
) -> str:
    """Build a professional-grade prompt using FLUX-optimized natural language storytelling.
    
    This replaces the old bracket-driven format with cohesive sentences.
    """
    scene_desc = SCENE_PRESETS.get(scene, scene)
    camera_desc = CAMERA_PRESETS.get(camera, camera)
    
    anti_ai = {
        "subtle": ANTI_AI_SUBTLE,
        "medium": ANTI_AI_MEDIUM,
        "heavy": ANTI_AI_HEAVY,
    }.get(anti_ai_level, ANTI_AI_MEDIUM)
    
    outfit_text = f" They are dressed in a {outfit_desc}." if outfit_desc else ""
    extra_text = f" Additionally, {extra}." if extra else ""
    
    # Weave into a fluid paragraph
    prompt = (
        f"A hyper-realistic, authentic photograph capturing {identity_block} The subject is "
        f"{scene_desc}.{outfit_text} The scene is perfectly framed and {camera_desc}. "
        f"To ensure total photorealism, the image features {anti_ai}{extra_text}"
    )
    
    # Clean up any double spaces caused by concatenation
    return prompt.replace("  ", " ")


def get_random_scene() -> str:
    """Return a random scene preset key for variety."""
    import random
    return random.choice(list(SCENE_PRESETS.keys()))


def get_fabric_upgrade(basic_item: str) -> str:
    """Upgrade a basic clothing description to pro-level fabric detail."""
    basic_lower = basic_item.lower().strip()
    for key, upgrade in FABRIC_MODIFIERS.items():
        if key.replace("_", " ") in basic_lower or key in basic_lower:
            return upgrade
    return basic_item  # Return original if no match


# ==========================================
# VIDEO PROMPTS — Fashion-Specific Motion Templates
# ==========================================
# Used by video generation pipeline for editorial-quality fashion videos.
# Each prompt includes camera motion, lighting, and fabric movement descriptors.
VIDEO_PROMPTS = {
    "runway_walk": (
        "Model walking confidently toward camera on a dimly lit industrial runway, "
        "slow-motion fabric movement catching dramatic side lighting, long cinematic shadows, "
        "4K resolution, shallow depth of field tracking shot, fashion show energy, "
        "garment details visible with each stride, professional runway videography"
    ),
    "fabric_drape": (
        "Extreme close-up of {fabric_type} fabric falling in slow motion against dark background, "
        "catching warm golden hour sunlight, visible texture and weave detail, "
        "macro lens, 120fps slow motion, studio product video aesthetic, "
        "dust particles floating in light beam, luxurious tactile quality"
    ),
    "street_swagger": (
        "Model walking through rain-slicked city backstreet at night, "
        "neon reflections on wet concrete, outfit catching colored light, "
        "handheld camera following from behind at eye level, cinematic color grading, "
        "urban atmosphere, puddle reflections, breath visible in cold air"
    ),
    "product_reveal": (
        "Smooth dolly-in on garment laid flat on black marble surface, "
        "overhead camera slowly descending, dramatic single key light revealing fabric textures, "
        "studio product video aesthetic, slow reveal of design details, "
        "minimalist luxury presentation, no distractions"
    ),
    "lifestyle_vignette": (
        "Model sitting on concrete steps during golden hour, casually adjusting outfit, "
        "wind slightly moving fabric and hair, shallow depth of field with warm urban bokeh, "
        "natural candid energy, slight handheld camera drift, "
        "authentic street photography feel, not posed"
    ),
    "360_spin": (
        "Model doing slow 360-degree turn on minimalist platform, "
        "even studio lighting showing outfit from all angles, full-body framing, "
        "clean fashion e-commerce video style, neutral background, "
        "garment construction details visible at each angle"
    ),
    "power_walk": (
        "Slow-motion front-facing power walk, model striding with purpose through "
        "a brutalist concrete corridor, dramatic overhead lighting creating sharp shadows, "
        "wide-angle lens from low perspective, outfit billowing with movement, "
        "cinematic fashion film aesthetic, editorial energy"
    ),
    "detail_montage": (
        "Quick-cut montage of extreme close-ups: stitching detail, zipper pull, "
        "fabric texture, hardware closeup, label tag, button snap — "
        "each shot with shallow DOF and dramatic directional lighting, "
        "luxury product photography, macro lens, studio lit"
    ),
    "morning_routine": (
        "Soft morning light streaming through floor-to-ceiling windows, "
        "model casually getting dressed, pulling on the garment in real-time, "
        "intimate documentary feel, warm color temperature, "
        "bedroom/loft setting with minimal furniture, lifestyle UGC energy"
    ),
    "nightlife_entry": (
        "Model pushing through a heavy door into a dimly lit venue, "
        "strobe lights and warm amber tones, outfit catching flashes of light, "
        "slow-motion entrance, smoke/haze in background, "
        "nightlife fashion video, high contrast cinematic look"
    ),
    "rooftop_golden_hour": (
        "Model standing on urban rooftop during golden hour, city skyline behind, "
        "warm backlight creating rim lighting on outfit silhouette, "
        "gentle wind movement in fabric and hair, drone-style slow orbit shot, "
        "magic hour cinematography, editorial campaign energy"
    ),
    "try_on_haul": (
        "POV-style try-on video, model pulling garment from packaging, "
        "holding it up to camera showing details, then cut to wearing it, "
        "mirror visible in frame, natural bedroom lighting, "
        "authentic UGC try-on haul style, relatable and genuine"
    ),
}


# ==========================================
# NEGATIVE PROMPTS — Systematic Exclusion Lists
# ==========================================
# Append to generation prompts to prevent common AI artifacts and quality issues.
NEGATIVE_PROMPTS = {
    "universal": (
        "Do NOT generate: extra fingers, merged hands, floating limbs, "
        "text overlays, watermarks, logos not in the reference image, "
        "plastic-smooth skin, overly symmetrical faces, "
        "unnaturally perfect teeth, visible seams between AI-composited elements, "
        "backgrounds that bleed into the subject, clothing that defies gravity, "
        "mismatched shadows, inconsistent perspective"
    ),
    "anti_generic": (
        "Avoid: generic stock photo poses, perfectly centered composition, "
        "over-saturated neon colors, HDR glow effects, extreme portrait mode bokeh, "
        "identical twins in duo shots, robotic symmetrical standing poses, "
        "pure white void backgrounds, corporate headshot energy"
    ),
    "anti_ai_artifacts": (
        "Never: smooth plastic-doll skin texture, hyperrealistic uncanny valley faces, "
        "perfectly repeating fabric patterns, impossibly wrinkle-free clothing, "
        "floating disconnected shadows, inconsistent light direction between subject and background, "
        "melted jewelry or accessories, garbled text on clothing graphics, "
        "hands with wrong number of fingers, eyes looking in different directions"
    ),
    "anti_fashion_fail": (
        "Do not: mismatch shoe style with outfit aesthetic (no heels with streetwear), "
        "generate visible underwear lines, create impossible body proportions, "
        "show garment clipping through body, produce wrinkle-free fabric on a moving model, "
        "generate flat monotone fabrics without texture or depth, "
        "create backgrounds more interesting than the product"
    ),
    "video_specific": (
        "Avoid in video: temporal flickering between frames, morphing body parts, "
        "fabric that phases through body, background objects that shift position, "
        "unnatural walking gait, robotic head movements, "
        "hands that change shape between frames, hair that moves unnaturally"
    ),
}


def get_video_prompt(style: str, **kwargs) -> str:
    """Get a video prompt template and fill in any {placeholders} with kwargs."""
    template = VIDEO_PROMPTS.get(style, VIDEO_PROMPTS.get("lifestyle_vignette"))
    try:
        return template.format(**kwargs)
    except KeyError:
        return template


def get_negative_prompt(*categories: str) -> str:
    """Combine multiple negative prompt categories into a single string.
    
    Usage: get_negative_prompt('universal', 'anti_ai_artifacts', 'anti_fashion_fail')
    """
    if not categories:
        categories = ("universal", "anti_ai_artifacts")
    parts = [NEGATIVE_PROMPTS[cat] for cat in categories if cat in NEGATIVE_PROMPTS]
    return " ".join(parts)


# ==========================================
# TIERED PROMPT SYSTEM
# ==========================================
# Each prompt is tagged with a "tier" for carousel slide positioning.
# TIER_A = Hero close-up (waist-up, garment fills 60%+ of frame)
# TIER_B = Full-body lifestyle (shows fit + context)
# TIER_C = Detail/texture macro (fabric, stitching close-up)
# TIER_D = Product-only flat lay (no model, garment on surface)
# TIER_E = Outfit styling / Night out / Special context

PROMPT_TIERS = {
    "TIER_A": [
        # Hero Close-Up — garment is the STAR
        (
            "Photo 1, 2 and 3 are the model (face, body and sheet). Use image 4 and 5 as the product. "
            "Put the clothing from the product images on the model. "
            "Generate a hyperrealistic photo of the model posing with another friend in a photo shoot at a professional studio. "
            "The garment MUST occupy a prominent part of the frame. Sharp focus on the garment texture. "
            "Soft natural studio lighting, warm tones. Clean neutral background. "
            "They look directly at camera with a confident, relaxed expression. "
            "Shot on 85mm lens at f/2.0, shallow depth of field on background only. "
            "Skin has visible pores, natural imperfections. Premium fashion campaign look."
        ),
        (
            "Photo 1, 2 and 3 are the model (face, body and sheet). Use image 4 and 5 as the product. "
            "Put the clothing from the product images on the model. "
            "Generate a hyperrealistic photo of the model posing with another friend in a photo shoot at a studio. "
            "The garment is the focal point, filling the center of frame. "
            "Studio setting with overhead LED lighting and backdrop. "
            "Natural skin glow, visible pores. Authentic high-end aesthetic. "
            "Slight lens flare from studio light. RAW photo quality."
        ),
        (
            "Photo 1, 2 and 3 are the model (face, body and sheet). Use image 4 and 5 as the product. "
            "Put the clothing from the product images on the model. "
            "Generate a hyperrealistic upper-body photo of the model posing with another friend in a photo shoot at a studio. "
            "Framed from head to waist, the garment dominates the composition. "
            "They are standing in a modern studio setup, golden hour style studio light hitting the fabric. "
            "Expression is candid, mid-smile. Shot on Sony A7IV, 50mm f/1.4."
        ),
    ],
    "TIER_B": [
        # Full-Body Lifestyle — shows fit in context
        (
            "Put the exact outfit from the second image on the person from the first image. "
            "Generate a hyperrealistic full-body OOTD photo. "
            "Late afternoon golden hour, urban sidewalk with clean concrete wall. "
            "Shot on 85mm at f/1.8, shallow depth of field with blurred background. "
            "Natural confident mid-stride pose. "
            "iPhone camera roll aesthetic, slight film grain."
        ),
        (
            "Put the exact garment from the second image on the person from the first image. "
            "Generate a hyperrealistic lifestyle photo. She sits at a trendy minimalist cafe. "
            "Warm interior lighting, latte art on table, soft bokeh. Candid mid-laugh moment. "
            "Shot on iPhone 15 Pro Max. Natural colors, no heavy filters. "
            "Authentic UGC content creator aesthetic."
        ),
        (
            "Put the exact garment from the second image on the person from the first image. "
            "Generate a hyperrealistic TikTok-style fit check photo. "
            "Full body visible, standing in a well-lit bedroom. Ring light creates catch light in "
            "eyes. Hand-on-hip pose, confident smirk. "
            "Shot on iPhone front camera. Authentic Gen-Z aesthetic. Subtle room decor in background."
        ),
        (
            "Put the exact garment from the second image on the person from the first image. "
            "Generate a hyperrealistic outdoor editorial photo. "
            "Full body framing, standing in a luxury green park with dappled sunlight through trees. "
            "Wind gently moving her hair. "
            "Shot on Sony A7IV, 50mm f/1.4, creamy bokeh. Relaxed editorial pose. "
            "High-fashion magazine quality but authentic and approachable."
        ),
    ],
    "TIER_C": [
        # Detail / Texture Macro — fabric close-ups
        (
            "Extreme close-up macro photography of this EXACT garment from the product "
            "reference image, being worn by a person. Focus on a 6-inch section of the "
            "fabric showing the weave, texture, stitching, and material quality. The "
            "garment color and pattern match the reference EXACTLY. Soft natural side "
            "lighting revealing fabric depth. Shot on 100mm macro lens, f/4, razor sharp "
            "focus on textile fibers. Creamy bokeh on skin visible at edges. "
            "Premium e-commerce detail shot. 8K resolution quality."
        ),
        (
            "Close-up detail photograph of this EXACT garment from the product reference "
            "being worn. Camera focuses on the collar, zipper, or button area -- showing "
            "construction quality and design details. The garment color and design match "
            "EXACTLY. Natural soft lighting, clean composition. The person's chin and "
            "neck visible at top of frame for context. Shot on 85mm at f/2.8. "
            "Premium brand photography aesthetic. Sharp focus on garment hardware."
        ),
    ],
    "TIER_D": [
        # Product-Only Flat Lay — no model, just the garment
        (
            "Professional flat lay photography of this EXACT garment from the product "
            "reference image. The garment is neatly laid out on a clean white linen bed "
            "sheet. It is styled with complementary accessories -- a watch, sunglasses, "
            "and a small potted plant nearby. Overhead bird's-eye view. Soft diffused "
            "natural daylight from a nearby window. The garment color, pattern, and design "
            "match the reference EXACTLY. Clean, minimal, aspirational lifestyle aesthetic. "
            "Instagram fit check flat lay style. Shot on iPhone 15 Pro from above."
        ),
        (
            "Professional product-only photograph of this EXACT garment from the product "
            "reference image. The garment hangs on a minimal wooden hanger against a clean "
            "cream-colored wall. Soft directional window light. The full garment is visible "
            "-- every design detail, color, and texture matches the reference EXACTLY. "
            "Clean e-commerce photography style with lifestyle warmth. No model, no "
            "distractions. The garment is the sole focus. Shot on 50mm at f/2.8."
        ),
    ],
    "TIER_E": [
        # Night Out / Special Context
        (
            "Put the exact garment from the second image on the person from the first image. "
            "Generate a hyperrealistic night-out photo. "
            "Standing outside a trendy restaurant, warm ambient neon lights reflecting off wet pavement. "
            "Shot on iPhone 15 Pro night mode. Natural skin glow. Candid pose checking phone."
        ),
        (
            "Put the exact garment from the second image on the person from the first image. "
            "Generate a hyperrealistic cozy home content creator photo. "
            "Sitting casually on a cream couch in a minimalist living room, legs tucked under. "
            "Warm afternoon light from large windows. Coffee table with candles nearby. "
            "Shot on iPhone, natural warm tones. Authentic 'outfit of the day at home' aesthetic."
        ),
    ],
}

# Flatten for random selection (weighted toward hero + lifestyle)
ELITE_PROMPTS = (
    PROMPT_TIERS["TIER_A"] * 3 +   # 3x weight — hero shots most important
    PROMPT_TIERS["TIER_B"] * 2 +   # 2x weight — lifestyle context
    PROMPT_TIERS["TIER_C"] * 1 +   # 1x weight — detail shots
    PROMPT_TIERS["TIER_D"] * 1 +   # 1x weight — flat lays
    PROMPT_TIERS["TIER_E"] * 1     # 1x weight — special context
)

# ==========================================
# SEEDANCE 2.0 CONFIGURATION & TEMPLATES
# ==========================================
SEEDANCE_VIDEO_CONFIG = {
    "model": "Seedance 2.0",
    "resolutions": {
        "720p_HD": "RESOLUTION_720P",
    },
    "aspect_ratios": ["9:16", "16:9", "1:1", "4:3", "3:4", "21:9"],
    "best_for_tiktok": "9:16",
    "best_for_instagram_feed": "1:1",
    "best_for_instagram_reels": "9:16",
    "best_for_cinematic": "21:9",
}

SEEDANCE_VIDEO_PROMPTS = {
    "fashion_walk": "Cinematic fashion video, {gender} model walking confidently, wearing {garment}, high-fashion backdrop, slow motion",
    "product_reveal": "Smooth product reveal, {garment} rotating slowly, studio lighting, hyper-realistic details",
    "street_style": "Street style video, {gender} model in {location}, wearing {garment}, 4k resolution, cinematic look",
    "editorial_motion": "High-fashion editorial video with subtle wind machine movement, dramatic studio lighting",
}
