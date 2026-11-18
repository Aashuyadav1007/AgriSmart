import io
import json
from pathlib import Path
from typing import Dict, Any, Tuple
from PIL import Image
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import transforms, models

from path_config import BACKEND_DIR, DISEASE_MODEL_PATH, DISEASE_CLASSES_PATH
from services.image_pipeline import image_pipeline

REMEDIES_PATH = BACKEND_DIR / "data" / "disease_remedies.json"

class DiseaseClassifierService:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.class_names = []
        self.idx_to_class = {}
        self.remedies_db = {}
        self.transform = transforms.Compose([
            transforms.Resize((256, 256)),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        self.load_metadata_and_model()

    def load_metadata_and_model(self):
        # 1. Load Remedies
        if REMEDIES_PATH.exists():
            try:
                with open(REMEDIES_PATH, 'r', encoding='utf-8') as f:
                    self.remedies_db = json.load(f)
                print(f"[OK] Loaded {len(self.remedies_db)} verified disease remedies")
            except Exception as e:
                print(f"[ERROR] Failed loading remedies: {e}")
        
        # 2. Load Class Mapping
        if DISEASE_CLASSES_PATH.exists():
            try:
                with open(DISEASE_CLASSES_PATH, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                    self.class_names = meta.get("class_names", [])
                    self.idx_to_class = {int(k): v for k, v in meta.get("idx_to_class", {}).items()}
                print(f"[OK] Loaded {len(self.class_names)} disease classes")
            except Exception as e:
                print(f"[ERROR] Failed loading disease classes: {e}")

        # 3. Load PyTorch MobileNetV2
        if DISEASE_MODEL_PATH.exists() and self.class_names:
            try:
                model = models.mobilenet_v2(weights=None)
                num_ftrs = model.classifier[1].in_features
                model.classifier = nn.Sequential(
                    nn.Dropout(p=0.3),
                    nn.Linear(num_ftrs, 128),
                    nn.ReLU(),
                    nn.Dropout(p=0.2),
                    nn.Linear(128, len(self.class_names))
                )
                state_dict = torch.load(str(DISEASE_MODEL_PATH), map_location=self.device)
                model.load_state_dict(state_dict)
                model.to(self.device)
                model.eval()
                self.model = model
                print(f"[OK] PyTorch Disease Model loaded from {DISEASE_MODEL_PATH}")
            except Exception as e:
                print(f"[ERROR] Failed loading PyTorch model: {e}")

    def validate_image_bytes(self, image_bytes: bytes, max_mb: float = 10.0) -> Tuple[bool, str]:
        """Validates image bytes for size, format, and corruption."""
        size_mb = len(image_bytes) / (1024 * 1024)
        if size_mb > max_mb:
            return False, f"Image file exceeds maximum allowable size of {max_mb} MB (received {size_mb:.2f} MB)"
        
        try:
            im = Image.open(io.BytesIO(image_bytes))
            im.verify()
            if (im.format or "").upper() not in ["JPEG", "JPG", "PNG", "WEBP"]:
                return False, f"Unsupported image format: {im.format}. Allowed: JPEG, PNG, WEBP."
            return True, "Valid"
        except Exception as e:
            return False, f"Invalid or corrupted image file: {str(e)}"

    def predict_leaf_disease(self, image_bytes: bytes) -> Dict[str, Any]:
        if self.model is None:
            self.load_metadata_and_model()
            if self.model is None:
                raise RuntimeError("Plant Disease Model is not loaded. Please train or initialize the model first.")

        # Reopen image with PIL after verification
        try:
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except Exception as e:
            raise ValueError(f"Invalid or corrupted image file: {str(e)}")

        # ---------------------------------------------------------------------
        # 1. HIERARCHICAL PIPELINE STEP A: Image Quality Validation
        # ---------------------------------------------------------------------
        is_quality_valid, quality_msg, quality_report = image_pipeline.validate_quality(image_bytes)

        # ---------------------------------------------------------------------
        # 2. HIERARCHICAL PIPELINE STEP B: Plant vs Non-Plant Classification
        # ---------------------------------------------------------------------
        is_plant, plant_confidence, plant_msg = image_pipeline.classify_plant_presence(image)

        # ---------------------------------------------------------------------
        # 3. HIERARCHICAL PIPELINE STEP C: Plant Part Identification
        # ---------------------------------------------------------------------
        organ_info = image_pipeline.identify_plant_part(image)

        SUPPORTED_CROPS = ["Tomato", "Potato", "Corn", "Cotton"]

        # If image is non-plant (synthetic noise, furniture, road, tool)
        if not is_plant:
            return {
                "prediction": {
                    "class_name": "Non_Plant_Subject",
                    "crop": "Non-Plant / Unsupported Subject",
                    "condition": "Non-Plant Surface or Severe Background Noise",
                    "is_healthy": False,
                    "confidence_score": 0.05,
                    "confidence_percentage": 5.0,
                    "top_predictions": [
                        {"class_name": "Non_Plant_Subject", "confidence_percentage": 95.0}
                    ],
                    "is_supported_crop": False,
                    "is_uncertain": True,
                    "status": "unsupported_or_unknown",
                    "normalized_entropy": 0.98,
                    "recommended_action": plant_msg,
                    "supported_crops": SUPPORTED_CROPS,
                    "plant_part": "Non-Plant",
                    "is_plant": False,
                    "image_quality": quality_report
                },
                "pathology_and_remedies": {
                    "crop": "Non-Plant Subject",
                    "condition": "Non-Plant Image Detected",
                    "pathogen": "N/A",
                    "severity": "None",
                    "symptoms": ["The uploaded photograph does not exhibit green vegetative plant tissue or leaf foliage."],
                    "organic_controls": ["Please capture a direct, in-focus photograph of a living plant leaf or crop canopy."],
                    "chemical_treatment": ["No agricultural chemical treatment applicable."],
                    "preventative_practices": ["Position the camera 15-30 cm from the leaf surface with natural daylight."],
                    "source_reference": "AgriSmart Plant Presence Validation Engine"
                },
                "bilingual_advisory": {
                    "en": {
                        "crop_name": "Non-Plant Subject",
                        "plant_part": "Non-Plant",
                        "disease_name": "Non-Plant Image Detected",
                        "causal_organism": "None (Non-Plant Surface)",
                        "pathogen": "None",
                        "description": "The image does not contain sufficient green vegetative plant matter.",
                        "symptoms": ["No foliar symptoms found."],
                        "causes": "Non-plant subject or severe background artifact uploaded.",
                        "favourable_conditions": "N/A",
                        "disease_spread": "N/A",
                        "severity": "None",
                        "prevention": ["Upload a genuine crop leaf photo."],
                        "organic_control": ["N/A"],
                        "chemical_control": ["N/A"],
                        "precautions": ["Do not use for agricultural inputs."],
                        "when_to_consult_expert": "Consult extension officer with actual crop samples."
                    },
                    "hi": {
                        "crop_name": "गैर-पौधा विषय (Non-Plant)",
                        "plant_part": "पौधा नहीं",
                        "disease_name": "पौधे की पत्ती नहीं पाई गई",
                        "causal_organism": "कोई नहीं (गैर-पौधा सतह)",
                        "pathogen": "कोई नहीं",
                        "description": "अपलोड की गई तस्वीर में पौधे की हरी पत्ती या वानस्पतिक ऊतक नहीं दिखाई दे रहे हैं।",
                        "symptoms": ["कोई पादप लक्षण नहीं पाए गए।"],
                        "causes": "गैर-पौधे की वस्तु या पृष्ठभूमि अपलोड की गई।",
                        "favourable_conditions": "लागू नहीं",
                        "disease_spread": "लागू नहीं",
                        "severity": "शून्य",
                        "prevention": ["कृपया फसल की पत्ती की स्पष्ट फोटो अपलोड करें।"],
                        "organic_control": ["लागू नहीं"],
                        "chemical_control": ["लागू नहीं"],
                        "precautions": ["दवा का छिड़काव न करें।"],
                        "when_to_consult_expert": "वास्तविक पौधे के पत्ते के साथ कृषि विशेषज्ञ से संपर्क करें।"
                    }
                }
            }

        # If plant part is non-foliar (e.g. Potato Tuber / Root or Fruit / Pod)
        if not organ_info["is_foliar"]:
            return {
                "prediction": {
                    "class_name": f"Non_Foliar_Organ_{organ_info['part'].replace(' ', '_')}",
                    "crop": f"Detected Organ: {organ_info['part']}",
                    "condition": f"Organ Mismatch ({organ_info['part']})",
                    "is_healthy": False,
                    "confidence_score": 0.15,
                    "confidence_percentage": 15.0,
                    "top_predictions": [
                        {"class_name": organ_info['part'], "confidence_percentage": 85.0}
                    ],
                    "is_supported_crop": True,
                    "is_uncertain": True,
                    "status": "unsupported_or_unknown",
                    "normalized_entropy": 0.92,
                    "recommended_action": organ_info["message"],
                    "supported_crops": SUPPORTED_CROPS,
                    "plant_part": organ_info["part"],
                    "is_plant": True,
                    "image_quality": quality_report
                },
                "pathology_and_remedies": {
                    "crop": f"Crop {organ_info['part']}",
                    "condition": f"{organ_info['part']} Detected (Leaf Model Required)",
                    "pathogen": "Organ Specific (Non-Foliar)",
                    "severity": "Informational",
                    "symptoms": [organ_info["message"]],
                    "organic_controls": ["For foliar disease diagnosis, please photograph the crop's leaves."],
                    "chemical_treatment": ["Do not apply foliar fungicides to soil tubers without certified pathology tests."],
                    "preventative_practices": ["Check tubers/roots for soil rot or storage scab separately."],
                    "source_reference": "AgriSmart Plant Organ Discrimination Engine"
                },
                "bilingual_advisory": {
                    "en": {
                        "crop_name": f"Crop ({organ_info['part']})",
                        "plant_part": organ_info["part"],
                        "disease_name": f"Organ Mismatch: {organ_info['part']}",
                        "causal_organism": "Organ-specific (Foliar classifier not calibrated for this organ)",
                        "pathogen": "Organ-specific (Foliar classifier not calibrated for this organ)",
                        "description": organ_info["message"],
                        "symptoms": ["Non-foliar organ submitted."],
                        "causes": "Organ mismatch: the uploaded photograph represents a tuber, fruit, or root rather than a leaf.",
                        "favourable_conditions": "Foliar model requires leaf lamina.",
                        "disease_spread": "N/A",
                        "severity": "Informational",
                        "prevention": ["Photograph the green leaves of the plant."],
                        "organic_control": ["Inspect leaves for systemic symptoms."],
                        "chemical_control": ["No chemical treatment on unverified organ."],
                        "precautions": ["Avoid chemical sprays based on non-leaf images."],
                        "when_to_consult_expert": "Consult your local KVK or extension officer with the physical organ sample."
                    },
                    "hi": {
                        "crop_name": f"फसल ({organ_info['part']})",
                        "plant_part": organ_info["part"],
                        "disease_name": f"अंग बेमेल: {organ_info['part']}",
                        "causal_organism": "अंग-विशिष्ट (पत्ती रोग मॉडल इस अंग के लिए नहीं है)",
                        "pathogen": "अंग-विशिष्ट (पत्ती रोग मॉडल इस अंग के लिए नहीं है)",
                        "description": organ_info["message"],
                        "symptoms": ["पत्ती की जगह कंद/फल की तस्वीर दी गई है।"],
                        "causes": "अंग बेमेल: अपलोड की गई तस्वीर पत्ती की बजाय कंद, फल या जड़ का प्रतिनिधित्व करती है।",
                        "favourable_conditions": "पत्ती मॉडल के लिए पत्ती आवश्यक है।",
                        "disease_spread": "लागू नहीं",
                        "severity": "सूचनात्मक",
                        "prevention": ["पौधे की हरी पत्तियों की फोटो लें।"],
                        "organic_control": ["पत्तियों की जांच करें।"],
                        "chemical_control": ["बिना विशेषज्ञ सलाह के कंद पर दवा न डालें।"],
                        "precautions": ["गलत अंग पर कीटनाशक न छिड़कें।"],
                        "when_to_consult_expert": "कंद या फल के वास्तविक नमूने के साथ कृषि विज्ञान केंद्र से संपर्क करें।"
                    }
                }
            }

        # ---------------------------------------------------------------------
        # 4. HIERARCHICAL PIPELINE STEP D: Foliar Neural Classification
        # ---------------------------------------------------------------------
        tensor = self.transform(image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            outputs = self.model(tensor)
            probabilities = F.softmax(outputs, dim=1)[0]
            confidence, predicted_idx = torch.max(probabilities, 0)
            
            pred_idx = int(predicted_idx.item())
            conf_val = float(confidence.item())
            predicted_class = self.idx_to_class.get(pred_idx, f"Class_{pred_idx}")

            # Top 3 probabilities
            top_probs, top_indices = torch.topk(probabilities, min(3, len(self.class_names)))
            top_predictions = []
            for p, idx in zip(top_probs, top_indices):
                top_predictions.append({
                    "class_name": self.idx_to_class.get(int(idx.item()), f"Class_{idx.item()}"),
                    "confidence_percentage": round(float(p.item()) * 100, 2)
                })

            # Normalized Shannon Entropy: H_norm = -sum(p * log2(p)) / log2(C)
            num_classes = len(self.class_names)
            eps = 1e-12
            entropy = -float(torch.sum(probabilities * torch.log2(probabilities + eps)).item())
            max_entropy = float(torch.log2(torch.tensor(num_classes, dtype=torch.float32)).item())
            normalized_entropy = round(min(max(entropy / max(max_entropy, 1.0), 0.0), 1.0), 4)

        # ---------------------------------------------------------------------
        # 5. HIERARCHICAL PIPELINE STEP E: Crop Family & Calibrated OOD Gating
        # ---------------------------------------------------------------------
        crop_probs = {"Corn": 0.0, "Cotton": 0.0, "Potato": 0.0, "Tomato": 0.0}
        for p, idx in zip(probabilities, range(num_classes)):
            cname = self.idx_to_class.get(idx, "")
            prob_val = float(p.item())
            for crop_key in crop_probs.keys():
                if crop_key.lower() in cname.lower():
                    crop_probs[crop_key] += prob_val
                    break

        best_crop, best_crop_prob = max(crop_probs.items(), key=lambda item: item[1])
        
        CONFIRM_THRESHOLD = 0.55
        OOD_CROP_THRESHOLD = 0.40
        OOD_CONF_THRESHOLD = 0.28
        MAX_ENTROPY_THRESHOLD = 0.88
        
        if best_crop_prob < OOD_CROP_THRESHOLD or conf_val < OOD_CONF_THRESHOLD or normalized_entropy > MAX_ENTROPY_THRESHOLD:
            is_supported_crop = False
            is_uncertain = True
            status = "unsupported_or_unknown"
            display_crop = "Unknown / Unsupported Crop"
            display_condition = "Uncertain or Unsupported Foliage"
            recommended_action = (
                "The uploaded leaf image does not reliably match any of AgriSmart's supported crops "
                "(Cotton, Tomato, Potato, Corn). Please upload a clear photo of a supported crop leaf."
            )
        elif conf_val < CONFIRM_THRESHOLD:
            is_supported_crop = True
            is_uncertain = True
            status = "uncertain"
            display_crop = predicted_class.split("___")[0].replace("_", " ")
            display_condition = predicted_class.split("___")[-1].replace("_", " ")
            recommended_action = (
                f"Crop detected as {best_crop} ({round(best_crop_prob*100, 1)}% crop confidence), but disease condition has moderate confidence. "
                "Physical inspection or confirmation from a certified agricultural officer is recommended before applying chemical sprays."
            )
        else:
            is_supported_crop = True
            is_uncertain = False
            status = "confirmed"
            display_crop = predicted_class.split("___")[0].replace("_", " ")
            display_condition = predicted_class.split("___")[-1].replace("_", " ")
            recommended_action = "Follow the verified integrated pest management practices detailed below."

        # ---------------------------------------------------------------------
        # 6. HIERARCHICAL PIPELINE STEP F: Bilingual Agronomic Advisory Synthesis
        # ---------------------------------------------------------------------
        remedy_info = self.remedies_db.get(predicted_class, {
            "crop": predicted_class.split("___")[0].replace("_", " "),
            "condition": predicted_class.split("___")[-1].replace("_", " "),
            "pathogen": "Consult local agricultural extension office for verification",
            "severity": "Unspecified",
            "symptoms": ["Visible spotting or chlorosis on leaf surface"],
            "organic_controls": ["Isolate affected plant", "Apply broad-spectrum organic copper soap"],
            "chemical_treatment": ["Contact certified agronomist for targeted prescription"],
            "preventative_practices": ["Ensure clean sanitation and avoid wet foliage"],
            "source_reference": "State Agricultural University Advisory"
        })

        bilingual = {
            "en": remedy_info.get("en", {
                "crop_name": remedy_info.get("crop", display_crop),
                "plant_part": "Leaf (Foliage)",
                "disease_name": remedy_info.get("condition", display_condition),
                "causal_organism": remedy_info.get("pathogen", "Identified by field symptoms"),
                "pathogen": remedy_info.get("pathogen", "Identified by field symptoms"),
                "description": f"Foliar condition observed on {display_crop}.",
                "symptoms": remedy_info.get("symptoms", []),
                "causes": "Foliar pathogen infection affecting photosynthetic tissues.",
                "favourable_conditions": "Humid and warm agricultural micro-climate with persistent leaf wetness.",
                "disease_spread": "Spread by wind-borne spores, insects, and irrigation run-off.",
                "severity": remedy_info.get("severity", "Moderate"),
                "prevention": remedy_info.get("preventative_practices", []),
                "organic_control": remedy_info.get("organic_controls", []),
                "chemical_control": remedy_info.get("chemical_treatment", []),
                "precautions": ["Avoid chemical sprays during high winds, hot midday sun, or rain."],
                "when_to_consult_expert": "Consult your local KVK or extension officer if more than 15% of the leaf area shows active lesions."
            }),
            "hi": remedy_info.get("hi", {
                "crop_name": remedy_info.get("crop", display_crop),
                "plant_part": "पत्ती (Foliage)",
                "disease_name": remedy_info.get("condition", display_condition),
                "causal_organism": remedy_info.get("pathogen", "लक्षणों द्वारा पहचाना गया"),
                "pathogen": remedy_info.get("pathogen", "लक्षणों द्वारा पहचाना गया"),
                "description": f"{display_crop} की पत्तियों पर रोग के लक्षण।",
                "symptoms": remedy_info.get("symptoms", []),
                "causes": "पत्ती के ऊतकों को प्रभावित करने वाला रोगजनक संक्रमण।",
                "favourable_conditions": "उमस और वर्षा के अनुकूल मौसम में कवक या जीवाणु की तीव्र वृद्धि।",
                "disease_spread": "हवा, कीटों और बारिश के पानी के छींटों द्वारा।",
                "severity": remedy_info.get("severity", "मध्यम"),
                "prevention": remedy_info.get("preventative_practices", []),
                "organic_control": remedy_info.get("organic_controls", []),
                "chemical_control": remedy_info.get("chemical_treatment", []),
                "precautions": ["हवा, तेज धूप या बारिश के समय कीटनाशक का छिड़काव न करें।"],
                "when_to_consult_expert": "यदि 15% से अधिक पत्तियों पर लक्षण फैल जाएं, तो तुरंत नजदीकी कृषि विज्ञान केंद्र (KVK) से संपर्क करें।"
            })
        }

        is_healthy = "healthy" in predicted_class.lower()

        return {
            "prediction": {
                "class_name": predicted_class if is_supported_crop else "Unknown_or_Unsupported",
                "crop": display_crop if not is_supported_crop else remedy_info.get("crop", display_crop),
                "condition": display_condition if not is_supported_crop else remedy_info.get("condition", display_condition),
                "is_healthy": is_healthy and is_supported_crop,
                "confidence_score": round(conf_val, 4),
                "confidence_percentage": round(conf_val * 100, 2),
                "top_predictions": top_predictions,
                "is_supported_crop": is_supported_crop,
                "is_uncertain": is_uncertain,
                "status": status,
                "normalized_entropy": normalized_entropy,
                "recommended_action": recommended_action,
                "supported_crops": SUPPORTED_CROPS,
                "plant_part": organ_info["part"],
                "is_plant": is_plant,
                "image_quality": quality_report
            },
            "pathology_and_remedies": remedy_info if is_supported_crop else {
                "crop": "Unsupported Crop",
                "condition": "Foliage not matching supported crops (Tomato, Potato, Corn, Cotton)",
                "pathogen": "N/A",
                "severity": "Unknown",
                "symptoms": ["The visual characteristics do not reliably match known classes."],
                "organic_controls": ["Consult a local Krishi Vigyan Kendra (KVK) for specialized crop diagnosis."],
                "chemical_treatment": ["Do not spray broad-spectrum chemicals without expert diagnosis."],
                "preventative_practices": ["Ensure sample images have clear lighting and focus on leaf surface."],
                "source_reference": "AgriSmart Out-of-Distribution Rejection Engine"
            },
            "bilingual_advisory": bilingual
        }

# Singleton instance
disease_service = DiseaseClassifierService()
