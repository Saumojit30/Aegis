# Aegis — Attribution and Data Provenance

This document provides complete provenance, licensing, and attribution notices for datasets, synthetic generation models, nutritional databases, and third-party resources used in the Aegis research prototype.

---

## 1. Primary Dataset: CGMacros

* **Dataset Title:** Continuous Glucose Monitoring and Macronutrient Intake in Prediabetes and Type 2 Diabetes (CGMacros)
* **Version:** 1.0.0
* **Repository:** PhysioNet
* **Persistent Identifier / DOI:** [10.13026/3z8q-x658](https://doi.org/10.13026/3z8q-x658)
* **License:** Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International ([CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/))
* **Primary Citation:**
  > Hall, H., Perelman, D., Breschi, A., Limcaoco, P., Kellogg, R., McLaughlin, T., & Snyder, M. (2023). Continuous Glucose Monitoring and Macronutrient Intake in Prediabetes and Type 2 Diabetes (version 1.0.0). *PhysioNet*. https://doi.org/10.13026/3z8q-x658.
  > 
  > Goldberger, A. L., Amaral, L. A., Glass, L., Hausdorff, J. M., Ivanov, P. C., Mark, R. G., Mietus, J. E., Moody, G. B., Peng, C. K., & Stanley, H. E. (2000). PhysioBank, PhysioToolkit, and PhysioNet: Components of a new research resource for complex physiologic signals. *Circulation*, 101(23), e215–e220.

### Modifications and Transformations Notice (CC BY-NC-SA 4.0 §3.a.2)
In accordance with CC BY-NC-SA 4.0, the following transformations have been applied to the CGMacros data within Aegis:
1. **Resampling:** Raw sensor CGM, METs, and heart-rate signals were aligned and resampled onto a continuous 5-minute equidistant temporal grid ($T=36$ points for 180-minute postprandial intervals).
2. **Missingness Imputation & Masking:** CGM dropouts and wearable telemetry gaps are explicitly tracked via binary indicator masks (`cgm_mask`, `hr_mask`, `steps_mask`, `met_mask`).
3. **Meal Parsing:** Food logging records were harmonized into macronutrient vectors (carbohydrates, protein, fat, total calories, fiber) anchored to verified meal onset timestamps.
4. **Attributed Demo Fixture:** A trimmed 2-patient offline demonstration subset is maintained under `data/demo/` strictly for offline reproducibility, code evaluation, and automated testing.

---

## 2. Synthetic Clinical EHR Layer

* **Module:** `aegis.data.ehr_synthetic`
* **Provenance:** Fully synthetic EHR generation module authored by the Aegis team.
* **Clinical Distribution Grounding:**
  - Distribution parameters, lab reference ranges, and medication co-occurrences are modeled after clinical guidelines published by the American Diabetes Association (*ADA Standards of Care in Diabetes — 2024*) and epidemiology statistics from the National Health and Nutrition Examination Survey (NHANES).
* **Synthetic Flags:**
  - Every synthetic EHR record emitted by Aegis is strictly marked with `is_synthetic: true` to prevent any confusion with real clinical electronic health records.
* **License:** Apache-2.0 (code).

---

## 3. Indian Dietary Presets & Nutritional Data

* **Sources:**
  - **IFCT 2017:** Longvah, T., Ananthan, R., Bhaskarachary, K., & Venkaiah, K. (2017). *Indian Food Composition Tables*. National Institute of Nutrition (ICMR-NIN), Hyderabad, India.
  - **USDA FoodData Central:** U.S. Department of Agriculture, Agricultural Research Service. *FoodData Central*, 2024. https://fdc.nal.usda.gov/.
* **Presets Config:** `configs/presets.yaml`
* **Attribution Notice:** Meal compositions for standard regional Indian dishes (e.g., Masala Dosa, Dal Roti, Biryani, Poha) were derived from nutritional reference tables and literature estimates. Aegis enforces out-of-distribution clamping and flags reduced reliability (`LOW` confidence) whenever dietary inputs deviate substantially from the training distribution support.

---

## 4. Software Dependencies and Open-Source Acknowledgments

Aegis builds upon standard scientific Python and web libraries:
* **PyTorch:** BSD-style license ([pytorch.org](https://pytorch.org))
* **LightGBM:** MIT License ([github.com/microsoft/LightGBM](https://github.com/microsoft/LightGBM))
* **Scikit-learn:** BSD 3-Clause License ([scikit-learn.org](https://scikit-learn.org))
* **FastAPI & Starlette:** MIT License ([fastapi.tiangolo.com](https://fastapi.tiangolo.com))
* **Pydantic:** MIT License ([pydantic.dev](https://pydantic.dev))
* **SQLAlchemy:** MIT License ([sqlalchemy.org](https://sqlalchemy.org))
* **Polars & PyArrow:** Apache-2.0 License
* **MLflow:** Apache-2.0 License ([mlflow.org](https://mlflow.org))
