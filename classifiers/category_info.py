"""
Enriched category information + fine-grained sub-category prompts.

Two things live here:

1. SUBCATEGORY_PROMPTS - a much larger, more specific set of CLIP prompts
   (e.g. "a photo of a mobile phone or smartphone" rather than just
   "a photo of electronic waste"). Classifying against ~20 specific
   subtypes instead of 5 broad categories is noticeably more accurate for
   CLIP zero-shot, because "electronic waste" alone is a fuzzy match for
   a phone photo, but "a mobile phone or smartphone" is not. Each
   subtype maps back to one of the 5 top-level bin categories.

2. CATEGORY_INFO - the extra detail shown in the Scan Item result:
   description, what to separate before disposal, and an illustrative
   environmental impact split.

   IMPORTANT: the "positive_impact_percent" / "negative_impact_percent"
   figures are ILLUSTRATIVE EDUCATIONAL ESTIMATES for awareness, not
   measured statistics from a study - say so in the UI (already handled
   in app.js) and in your submission write-up. Don't present them as
   precise scientific data.
"""

CATEGORIES = ["plastic", "paper", "organic", "e-waste", "hazardous"]

# label -> (parent_category, CLIP prompt)
SUBCATEGORY_PROMPTS = {
    # plastic
    "Plastic bottle": ("plastic", "a photo of a plastic bottle"),
    "Plastic bag or wrapper": ("plastic", "a photo of a plastic bag or plastic wrapper"),
    "Plastic container": ("plastic", "a photo of a plastic food container or plastic tub"),
    # paper
    "Cardboard box": ("paper", "a photo of a cardboard box or carton"),
    "Paper or newspaper": ("paper", "a photo of paper, a newspaper, or a paper document"),
    # organic
    "Food scraps": ("organic", "a photo of food scraps, fruit or vegetable peels, or leftover food"),
    "Plant or garden waste": ("organic", "a photo of plant matter, leaves, or garden waste"),
    # e-waste
    "Mobile phone or smartphone": ("e-waste", "a photo of a mobile phone or smartphone"),
    "Laptop or computer part": ("e-waste", "a photo of a laptop, computer, or computer part"),
    "Cable or charger": ("e-waste", "a photo of an electrical cable, wire, or charger"),
    "Battery": ("e-waste", "a photo of a battery"),
    # hazardous
    "Chemical or paint container": ("hazardous", "a photo of a chemical container, paint can, or cleaning product bottle"),
    "Broken glass or sharp object": ("hazardous", "a photo of broken glass or a sharp object"),
    "Medical waste": ("hazardous", "a photo of medical waste, like a syringe or medicine packaging"),
    # fallback / low-confidence catch-all
    "Unclear or mixed item": ("unknown", "a photo where the waste item is unclear, tiny, or mixed with a cluttered background"),
}

CATEGORY_INFO = {
    "unknown": {
        "bin": "Could not identify the item",
        "guidance": "Try again with one item centered, well lit, and filling most of the frame. If unsure, check your local waste guidance.",
        "separations": [],
        "description": "The scan could not confidently identify this item. Do not use a guess to decide how to dispose of hazardous or electronic waste.",
        "positive_impact_percent": 0,
        "negative_impact_percent": 0,
        "explanation": "A clear photo of a single item usually gives a more useful result.",
    },
    "plastic": {
        "bin": "Dry / recyclable waste bin",
        "guidance": "Rinse if needed (remove food residue), and place in the dry/recyclable bin.",
        "separations": [
            "Remove any food or liquid residue first",
            "Separate caps/lids if they're a different plastic type",
            "Flatten if possible to save space",
        ],
        "description": "Most plastics can be recycled, but they degrade in quality each time, "
                        "and only some types are accepted by local recyclers.",
        "positive_impact_percent": 60,
        "negative_impact_percent": 40,
        "explanation": "Recycling plastic saves energy and raw material versus making new plastic, "
                        "but the process itself still uses energy and water, and not all plastic "
                        "collected actually gets recycled in practice - so the net benefit is real "
                        "but partial, not close to 100%.",
    },
    "paper": {
        "bin": "Dry / recyclable waste bin",
        "guidance": "Place in the dry/recyclable bin. Remove any food residue, tape, or plastic film first.",
        "separations": [
            "Remove tape, plastic windows (e.g. envelope windows), or metal staples if easy to",
            "Keep it dry - wet/soiled paper often can't be recycled",
        ],
        "description": "Paper and cardboard are among the most efficiently recyclable materials, "
                        "and can typically be reprocessed several times before the fibers wear out.",
        "positive_impact_percent": 75,
        "negative_impact_percent": 25,
        "explanation": "Paper recycling is well-established and saves significant water and energy "
                        "compared to making new paper from wood pulp - the main downside is the fibers "
                        "shorten with each cycle, so it can only be recycled a limited number of times.",
    },
    "organic": {
        "bin": "Wet / organic waste bin",
        "guidance": "Place in the wet/organic waste bin for composting.",
        "separations": [
            "Remove any plastic packaging or wrapping first",
            "Keep separate from dry waste to avoid contaminating recyclables",
        ],
        "description": "Food and plant waste can be composted into nutrient-rich soil, but if it "
                        "ends up in a landfill instead, it decomposes without oxygen and releases methane.",
        "positive_impact_percent": 70,
        "negative_impact_percent": 30,
        "explanation": "Composting turns organic waste into something genuinely useful (soil), which is "
                        "a strong positive - but it does still require proper collection and processing; "
                        "if it's mixed into general landfill waste instead, the same material becomes a "
                        "meaningful source of methane, a potent greenhouse gas.",
    },
    "e-waste": {
        "bin": "Do NOT use a regular bin",
        "guidance": "Take to a designated e-waste collection point - never place electronics in regular bins.",
        "separations": [
            "Remove batteries if they're removable - they're often collected separately",
            "Wipe personal data from phones/laptops before disposal if applicable",
        ],
        "description": "Electronics contain both valuable recoverable materials (metals) and hazardous "
                        "substances (lead, mercury, certain flame retardants) that must be handled carefully.",
        "positive_impact_percent": 45,
        "negative_impact_percent": 55,
        "explanation": "Proper e-waste recycling recovers valuable metals, which is a real benefit - but "
                        "e-waste is disproportionately harmful if mishandled, since the hazardous "
                        "materials inside can contaminate soil and water if it ends up in general waste. "
                        "This is why it needs a dedicated collection point rather than a normal bin.",
    },
    "hazardous": {
        "bin": "Hazardous-waste drop-off point",
        "guidance": "Do not place in regular bins. Use a designated hazardous-waste drop-off point.",
        "separations": [
            "Keep in original container/packaging if possible, so it's identifiable",
            "Never mix different chemicals together",
        ],
        "description": "This category covers items that can be actively harmful if mixed with regular "
                        "waste - chemicals, broken glass, or medical items.",
        "positive_impact_percent": 30,
        "negative_impact_percent": 70,
        "explanation": "Hazardous waste has a high potential for harm if it ends up in regular waste "
                        "streams (contamination, injury to waste workers), so the priority here is safe, "
                        "separate handling rather than recycling benefit - proper disposal mainly prevents "
                        "harm rather than creating a strong positive.",
    },
}
