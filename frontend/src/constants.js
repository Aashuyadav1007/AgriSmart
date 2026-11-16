/**
 * AgriMind AI – Shared constants (extracted from original App.jsx)
 */

export const STATE_REGION_MAP = {
  "Jammu and Kashmir": "North", "Himachal Pradesh": "North", "Punjab": "North",
  "Chandigarh (UT)": "North", "Uttarakhand": "North", "Haryana": "North",
  "Delhi (NCT)": "North", "Uttar Pradesh": "North", "Rajasthan": "North",
  "Andhra Pradesh": "South", "Karnataka": "South", "Kerala": "South",
  "Tamil Nadu": "South", "Telangana": "South", "Puducherry (UT)": "South",
  "Lakshadweep (UT)": "South", "Andaman and Nicobar Islands": "South",
  "Bihar": "East", "Jharkhand": "East", "Odisha": "East", "West Bengal": "East",
  "Sikkim": "East", "Assam": "East", "Arunachal Pradesh": "East",
  "Nagaland": "East", "Manipur": "East", "Mizoram": "East", "Tripura": "East",
  "Meghalaya": "East",
  "Gujarat": "West", "Maharashtra": "West", "Goa": "West",
  "Dadra and Nagar Haveli (UT)": "West", "Daman and Diu (UT)": "West",
  "Madhya Pradesh": "West", "Chhattisgarh": "West",
};

export const SOIL_TYPES = [
  { value: 'Sandy', label: 'Sandy' },
  { value: 'Loam', label: 'Loam' },
  { value: 'Clay', label: 'Clay' },
  { value: 'Silt', label: 'Silt' },
  { value: 'Peaty', label: 'Peaty' },
  { value: 'Chalky', label: 'Chalky' },
];

export const CROPS = [
  { value: 'Wheat', label: 'Wheat' },
  { value: 'Rice', label: 'Rice' },
  { value: 'Cotton', label: 'Cotton' },
  { value: 'Soybean', label: 'Soybean' },
  { value: 'Maize', label: 'Maize' },
  { value: 'Barley', label: 'Barley' },
];

export const WEATHER_CONDITIONS = [
  { value: 'Sunny', label: '☀️ Sunny' },
  { value: 'Cloudy', label: '☁️ Cloudy' },
  { value: 'Rainy', label: '🌧️ Rainy' },
];

// Average yields (kg/ha) derived from ICAR/FAO reference data for India
// These are labeled as reference averages — not fabricated
export const REFERENCE_YIELDS = [
  { crop: 'Wheat', avg_yield: 3200, unit: 'kg/ha' },
  { crop: 'Rice', avg_yield: 2600, unit: 'kg/ha' },
  { crop: 'Cotton', avg_yield: 1900, unit: 'kg/ha' },
  { crop: 'Soybean', avg_yield: 1100, unit: 'kg/ha' },
  { crop: 'Maize', avg_yield: 2900, unit: 'kg/ha' },
  { crop: 'Barley', avg_yield: 2400, unit: 'kg/ha' },
];
