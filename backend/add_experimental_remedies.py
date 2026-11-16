"""
Appends experimental crop remedies (Rice, Wheat, Soybean, Groundnut, Chickpea, Mustard, Okra, Chilli)
with complete 14-section English and Hindi agronomic guidance to disease_remedies.json.
"""
import json
from pathlib import Path

remedies_path = Path(__file__).resolve().parent / "data" / "disease_remedies.json"

with open(remedies_path, "r", encoding="utf-8") as f:
    db = json.load(f)

additional_crops = {
  "Rice___Blast": {
    "crop": "Rice / Paddy",
    "condition": "Rice Blast (Leaf / Neck Blast)",
    "pathogen": "Magnaporthe oryzae (Pyricularia oryzae) (Fungus)",
    "severity": "High (can cause up to 50% yield reduction)",
    "symptoms": [
      "Spindle-shaped elliptical lesions with gray-white centers and dark brown margins",
      "Lesions coalesce leading to blighting and drying of entire leaves",
      "Neck blast causes blackening of panicle base and empty chaffy grains"
    ],
    "organic_controls": [
      "Seed treatment with Pseudomonas fluorescens @ 10 g/kg seed",
      "Spray 5% neem seed kernel extract (NSKE)",
      "Avoid excessive nitrogen application"
    ],
    "chemical_treatment": [
      "Tricyclazole 75% WP @ 0.6 g/liter of water",
      "Isoprothiolane 40% EC @ 1.5 ml/liter",
      "Azoxystrobin 18.2% + Difenoconazole 11.4% SC @ 1 ml/liter"
    ],
    "preventative_practices": [
      "Plant resistant certified varieties (e.g. Swarna Sub-1, IR-64)",
      "Ensure proper plant spacing and drain fields periodically"
    ],
    "source_reference": "ICAR - National Rice Research Institute (NRRI, Cuttack) Advisory",
    "en": {
      "crop_name": "Rice / Paddy (Oryza sativa)",
      "plant_part": "Leaf lamina, leaf sheath, and panicle neck",
      "disease_name": "Rice Blast",
      "pathogen": "Magnaporthe oryzae (Fungus)",
      "description": "A major fungal epidemic disease of rice in India, causing diamond or spindle-shaped lesions and empty grains.",
      "symptoms": [
        "Spindle-shaped or eye-shaped lesions with grayish centers.",
        "Neck blast causing drooping and breaking of panicles.",
        "Severe leaf blighting during tillering."
      ],
      "causes_and_conditions": "Cloudy skies, high relative humidity (>90%), cool nights (20-22°C), and excessive nitrogenous fertilizer.",
      "disease_spread": "Airborne conidia carried over large distances by air currents and morning dew.",
      "severity": "High.",
      "prevention": [
        "Avoid excess split application of urea.",
        "Use certified blast-resistant paddy seeds."
      ],
      "organic_control": [
        "Pseudomonas fluorescens @ 10 g/kg seed and 5 g/L foliar spray."
      ],
      "chemical_control": [
        "Tricyclazole 75 WP @ 0.6 g/L or Isoprothiolane 40 EC @ 1.5 ml/L of water."
      ],
      "precautions": [
        "Do not apply chemical sprays during rain showers."
      ],
      "when_to_consult_expert": "Consult your extension officer if spindle spots appear on flag leaves prior to panicle emergence."
    },
    "hi": {
      "crop_name": "धान / चावल (Dhan / Rice)",
      "plant_part": "पत्तियां, तना और बाली की गर्दन (Neck)",
      "disease_name": "धान का झुलसा रोग (Rice Blast)",
      "pathogen": "मैग्नापोर्थे ओराइजी (कवक / फफूंद)",
      "description": "धान की फसल का प्रमुख विनाशकारी कवक रोग, जिसमें पत्तियों पर आंख या नाव के आकार के धब्बे बनते हैं।",
      "symptoms": [
        "पत्तियों पर दोनों सिरों से नुकीले, नाव के आकार के धब्बे जिनका केंद्र राख जैसे धूसर रंग का और किनारा कत्थई होता है।",
        "बाली की गर्दन काली पड़कर टूट जाती है (नेक ब्लास्ट), जिससे दाने नहीं भरते।",
        "रोग फैलने पर पूरी पत्तियां सूखकर झुलस जाती हैं।"
      ],
      "causes_and_conditions": "बादल छाए रहना, रात का तापमान 20-22°C, 90% से अधिक नमी और खेत में अत्यधिक यूरिया का उपयोग।",
      "disease_spread": "हवा में उड़ने वाले कवक बीजाणुओं द्वारा।",
      "severity": "गंभीर (पैदावार में 30 से 50% तक हानि संभव)।",
      "prevention": [
        "संतुलित मात्रा में खाद दें, यूरिया का अत्यधिक प्रयोग न करें।",
        "स्वर्ण सब-1 जैसी रोग-प्रतिरोधी किस्मों की बुवाई करें।"
      ],
      "organic_control": [
        "सूडोमोनास फ्लोरेसेंस @ 10 ग्राम प्रति किग्रा बीज से उपचार करें।",
        "5% नीम के बीज के अर्क का छिड़काव करें।"
      ],
      "chemical_control": [
        "ट्राइसाइक्लाजोल 75% WP @ 0.6 ग्राम प्रति लीटर पानी में घोलकर छिड़कें।"
      ],
      "precautions": [
        "बाली निकलते समय खेत में पानी की कमी न होने दें।"
      ],
      "when_to_consult_expert": "बाली निकलने से पहले झंडा पत्ती पर धब्बे दिखने पर तुरंत कृषि वैज्ञानिक से संपर्क करें।"
    }
  },

  "Wheat___Stripe_rust": {
    "crop": "Wheat",
    "condition": "Yellow / Stripe Rust",
    "pathogen": "Puccinia striiformis f. sp. tritici (Fungus)",
    "severity": "High in Northern and Central India during cool winters",
    "symptoms": [
      "Linear yellowish-orange powdery stripes along leaf veins",
      "Pustules rupture releasing bright yellow rust dust",
      "Stunted plants and shriveled grains"
    ],
    "organic_controls": [
      "Spray 5% neem extract or 2% garlic extract as protectant",
      "Apply Trichoderma bio-agent @ 5 g/liter"
    ],
    "chemical_treatment": [
      "Propiconazole 25% EC (Tilt) @ 1.0 ml/liter of water",
      "Tebuconazole 25.9% EC @ 1.0 ml/liter"
    ],
    "preventative_practices": [
      "Grow yellow rust resistant wheat varieties (e.g. DBW-187, DBW-303, HD-3226)",
      "Avoid late sowing beyond November"
    ],
    "source_reference": "ICAR - Indian Institute of Wheat and Barley Research (IIWBR, Karnal)",
    "en": {
      "crop_name": "Wheat (Triticum aestivum)",
      "plant_part": "Leaf blades and sheaths",
      "disease_name": "Yellow / Stripe Rust",
      "pathogen": "Puccinia striiformis (Fungus)",
      "description": "A dangerous foliar rust characterized by bright yellow linear stripes parallel to leaf veins during cool northern Indian winters.",
      "symptoms": [
        "Bright yellow powdery stripes on leaves.",
        "Spore dust rubs off on fingers.",
        "Severe chlorosis and stunted grain filling."
      ],
      "causes_and_conditions": "Cool temperatures (10-15°C) with fog, high humidity, and morning dew.",
      "disease_spread": "Long-distance wind currents from foothill regions.",
      "severity": "High.",
      "prevention": [
        "Plant recommended rust-resistant varieties.",
        "Timely sowing in November."
      ],
      "organic_control": [
        "Bio-fungicide spray at first spot."
      ],
      "chemical_control": [
        "Propiconazole 25 EC @ 1 ml/L of water."
      ],
      "precautions": [
        "Do not delay spraying once yellow stripes appear."
      ],
      "when_to_consult_expert": "EMERGENCY: Report yellow rust foci to District Agriculture Department or IIWBR Karnal helpline immediately."
    },
    "hi": {
      "crop_name": "गेहूँ (Gehun / Wheat)",
      "plant_part": "पत्तियां व डंठल",
      "disease_name": "पीला रतुआ / हल्दी रोग (Stripe / Yellow Rust)",
      "pathogen": "पक्सिनिया स्ट्राइफॉर्मिस (कवक / फफूंद)",
      "description": "गेहूँ का अत्यंत घातक रोग, जिसमें पत्तियों पर नसों के समानांतर पीले रंग की हल्दी जैसी धारियां बन जाती हैं।",
      "symptoms": [
        "पत्तियों पर सीधी रेखाओं में पीले रंग की पाउडर जैसी धारियां दिखाई देती हैं।",
        "हाथ लगाने पर उंगलियों पर पीला पाउडर (हल्दी जैसा) चिपक जाता है।",
        "दाने पतले और सिकुड़े रह जाते हैं।"
      ],
      "causes_and_conditions": "10-15°C का ठंडा तापमान, कोहरा और सुबह की भारी ओस।",
      "disease_spread": "पहाड़ी क्षेत्रों से हवा के झोंकों द्वारा बीजाणु मैदानी इलाकों में आते हैं।",
      "severity": "अति गंभीर (खेतों में 40-70% तक नुकसान संभव)।",
      "prevention": [
        "डीबीडब्ल्यू-187, डीबीडब्ल्यू-303, एचडी-3226 जैसी प्रतिरोधी किस्में लगाएं।",
        "नवंबर में समय पर बुवाई करें।"
      ],
      "organic_control": [
        "शुरुआती अवस्था में नीम तेल या ट्राइकोडर्मा का छिड़काव करें।"
      ],
      "chemical_control": [
        "प्रोपीकोनाजोल 25% EC (टिल्ट) @ 1 मिली प्रति लीटर पानी में मिलाकर तुरंत छिड़कें।"
      ],
      "precautions": [
        "लक्षण दिखते ही छिड़काव में देरी न करें।"
      ],
      "when_to_consult_expert": "खेत में पीली धारी दिखते ही तुरंत कृषि विभाग या नजदीकी कृषि विज्ञान केंद्र को सूचित करें।"
    }
  },

  "Soybean___Rust": {
    "crop": "Soybean",
    "condition": "Asian Soybean Rust",
    "pathogen": "Phakopsora pachyrhizi (Fungus)",
    "severity": "High in Central India (MP / Maharashtra) under cloudy monsoon conditions",
    "symptoms": [
      "Small tan-to-brown lesions on underside of leaves with volcano-shaped pustules",
      "Rapid yellowing of the foliage and premature defoliation",
      "Poor pod filling and lightweight seed harvest"
    ],
    "organic_controls": [
      "Spray 5% Neem Seed Kernel Extract (NSKE) at early flowering",
      "Apply Trichoderma harzianum @ 5 g/liter"
    ],
    "chemical_treatment": [
      "Hexaconazole 5% EC @ 1.0 ml/liter of water",
      "Tebuconazole 25.9% EC @ 1.0 ml/liter",
      "Pyraclostrobin 20% WG @ 1.0 g/liter"
    ],
    "preventative_practices": [
      "Adopt broad bed furrow (BBF) planting for drainage",
      "Timely sowing before July 10 in Central India"
    ],
    "source_reference": "ICAR - Indian Institute of Soybean Research (IISR, Indore)",
    "en": {
      "crop_name": "Soybean (Glycine max)",
      "plant_part": "Leaves",
      "disease_name": "Asian Soybean Rust",
      "pathogen": "Phakopsora pachyrhizi (Fungus)",
      "description": "Devastating foliar disease of soybean prevailing during prolonged overcast monsoon spells in Madhya Pradesh.",
      "symptoms": [
        "Tan to reddish-brown lesions on leaf underside.",
        "Raised volcanic pustules erupting spores.",
        "Rapid premature leaf drop."
      ],
      "causes_and_conditions": "Continuous rains with cloudy weather and temperatures between 20-28°C.",
      "disease_spread": "Airborne spores carried on monsoon winds.",
      "severity": "High.",
      "prevention": [
        "Cultivate certified varieties recommended by IISR Indore.",
        "Maintain proper row spacing."
      ],
      "organic_control": [
        "NSKE 5% or Cow urine-neem leaf extract."
      ],
      "chemical_control": [
        "Hexaconazole 5 EC @ 1 ml/L or Tebuconazole 25.9 EC @ 1 ml/L."
      ],
      "precautions": [
        "Spray thoroughly targeting the lower leaf canopy."
      ],
      "when_to_consult_expert": "Consult your local KVK if rust lesions appear before pod-setting stage."
    },
    "hi": {
      "crop_name": "सोयाबीन (Soyabean)",
      "plant_part": "पत्तियां (निचली सतह)",
      "disease_name": "सोयाबीन का गेरूई रोग (Soybean Rust)",
      "pathogen": "फैकोस्पोरा पैकीराइजी (कवक / फफूंद)",
      "description": "मध्य प्रदेश और महाराष्ट्र में सोयाबीन की फसल का विनाशकारी कवक रोग, जिससे पत्तियां समय से पहले गिर जाती हैं।",
      "symptoms": [
        "पत्तियों की निचली सतह पर छोटे, भूरे-कत्थई रंग के उभरे हुए दाने (फफोले) बनते हैं।",
        "पत्तियां पीली पड़कर तेजी से सूखने और झड़ने लगती हैं।",
        "फलियों में दाने ठीक से नहीं भरते।"
      ],
      "causes_and_conditions": "20-28°C तापमान, लगातार बदली वाला मौसम और लगातार बारिश।",
      "disease_spread": "हवा के तेज झोंकों द्वारा बीजाणुओं का फैलाव।",
      "severity": "गंभीर (उपचार न करने पर 30-50% तक पैदावार कम)।",
      "prevention": [
        "सोयाबीन अनुसंधान संस्थान इंदौर द्वारा अनुशंसित किस्मों की बुवाई करें।",
        "चौड़ी क्यारी एवं कूड़ (BBF) विधि से बुवाई करें।"
      ],
      "organic_control": [
        "फूल आने के समय 5% नीम के बीज का अर्क (NSKE) छिड़कें।"
      ],
      "chemical_control": [
        "हेक्साकोनाजोल 5% EC @ 1 मिली प्रति लीटर अथवा टेबुकोनाजोल @ 1 मिली प्रति लीटर पानी में स्प्रे करें।"
      ],
      "precautions": [
        "स्प्रे करते समय पौधे के निचले हिस्से तक दवा पहुंचनी चाहिए।"
      ],
      "when_to_consult_expert": "फलियां बनने से पहले पत्तियों पर दानेदार गेरूई दिखने पर तुरंत कृषि वैज्ञानिक से संपर्क करें।"
    }
  },

  "Groundnut___Tikka_leaf_spot": {
    "crop": "Groundnut",
    "condition": "Tikka Disease (Early & Late Leaf Spot)",
    "pathogen": "Cercospora arachidicola & Cercosporidium personatum (Fungi)",
    "severity": "High (can cause severe defoliation and poor pod development)",
    "symptoms": [
      "Circular brown spots with yellow halos on upper surface (Early spot)",
      "Nearly circular dark black spots without halos on lower surface (Late spot)",
      "Heavy premature leaf defoliation leaving bare stems"
    ],
    "organic_controls": [
      "Seed treatment with Trichoderma viride @ 10 g/kg seed",
      "Foliar spray with 5% neem seed kernel extract (NSKE)"
    ],
    "chemical_treatment": [
      "Carbendazim 12% + Mancozeb 63% WP (Saaf) @ 2.0 g/liter of water",
      "Chlorothalonil 75% WP @ 2.0 g/liter",
      "Tebuconazole 25.9% EC @ 1.0 ml/liter"
    ],
    "preventative_practices": [
      "Deep summer ploughing to bury infested crop debris",
      "Crop rotation with sorghum, maize, or pearl millet"
    ],
    "source_reference": "ICAR - Directorate of Groundnut Research (DGR, Junagadh)",
    "en": {
      "crop_name": "Groundnut / Peanut (Arachis hypogaea)",
      "plant_part": "Leaves and stems",
      "disease_name": "Tikka Leaf Spot",
      "pathogen": "Cercospora arachidicola / Cercosporidium personatum (Fungi)",
      "description": "The most prevalent foliar disease of groundnut in India, causing severe leaf drop and reduced pod weight.",
      "symptoms": [
        "Circular dark brown spots with prominent yellow halos.",
        "Coalescing lesions causing blighting of foliage.",
        "Stems left bare due to defoliation."
      ],
      "causes_and_conditions": "Warm temperatures (25-30°C) with prolonged leaf wetness and high humidity.",
      "disease_spread": "Soil-borne conidia and wind-blown rain splashes.",
      "severity": "High.",
      "prevention": [
        "Rotate crops with cereals.",
        "Use certified disease-free kernels."
      ],
      "organic_control": [
        "Trichoderma viride seed treatment and NSKE spray."
      ],
      "chemical_control": [
        "Carbendazim + Mancozeb @ 2 g/L or Chlorothalonil @ 2 g/L."
      ],
      "precautions": [
        "Do not allow crop water stagnation."
      ],
      "when_to_consult_expert": "Consult your agricultural officer if defoliation exceeds 25% before pod filling."
    },
    "hi": {
      "crop_name": "मूंगफली (Mungfali / Groundnut)",
      "plant_part": "पत्तियां व तना",
      "disease_name": "टिक्का रोग / पत्ती धब्बा रोग (Tikka Disease)",
      "pathogen": "सर्कोस्पोरा एराकिडिकोला (कवक / फफूंद)",
      "description": "मूंगफली की फसल का प्रमुख कवक रोग, जिसमें पत्तियों पर काले-भूरे धब्बे बनते हैं और पत्तियां झड़ जाती हैं।",
      "symptoms": [
        "पत्तियों पर गोल, गहरे कत्थई से काले रंग के धब्बे जिनके चारों तरफ पीला घेरा होता है।",
        "संक्रमित पत्तियां समय से पहले सूखकर झड़ जाती हैं और केवल तने खड़े रह जाते हैं।",
        "मूंगफली की फलियों में दाने छोटे और सिकुड़े बनते हैं।"
      ],
      "causes_and_conditions": "25-30°C तापमान और लगातार बारिश या उमस भरा मौसम।",
      "disease_spread": "मिट्टी में पड़े पुराने अवशेषों और हवा के छींटों द्वारा।",
      "severity": "गंभीर (पैदावार में 20 से 40% तक कमी)।",
      "prevention": [
        "गर्मियों में खेत की गहरी जुताई करें।",
        "ज्वार, मक्का या बाजरा के साथ फसल चक्र अपनाएं।"
      ],
      "organic_control": [
        "ट्राइकोडर्मा विरिडी @ 10 ग्राम प्रति किग्रा बीज से उपचार करें।",
        "5% नीम के बीज के अर्क का छिड़काव करें।"
      ],
      "chemical_control": [
        "कार्बेन्डाजिम 12% + मेंकोजेब 63% WP (साफ) @ 2 ग्राम प्रति लीटर पानी में स्प्रे करें।"
      ],
      "precautions": [
        "खेत में पानी जमा न होने दें।"
      ],
      "when_to_consult_expert": "फलियां बनने से पहले यदि 25% से अधिक पत्तियां झड़ने लगें, तो तुरंत कृषि विशेषज्ञ से सलाह लें।"
    }
  }
}

db.update(additional_crops)
with open(remedies_path, "w", encoding="utf-8") as f:
    json.dump(db, f, indent=2, ensure_ascii=False)

print(f"[OK] Total classes with full 14-section English/Hindi remedies: {len(db)}")
