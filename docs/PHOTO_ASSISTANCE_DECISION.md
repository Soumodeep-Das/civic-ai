# Photo-assistance decision for the minor demonstration

Date: 2026-11-21. Status: assessed and deliberately deferred; no photo-analysis provider or model is enabled.

## Decision

CivicAI will keep the submitted photograph as protected evidence for authorized municipal staff during the November 27 minor-project demonstration. It will **not** add an external vision API, generic zero-shot image classifier, automatic caption, image-derived category, or image-derived severity before that demonstration.

This is a scope and safety decision, not a claim that image assistance is impossible. The implemented minor workflow already demonstrates real experimental text classification, separate reported-context priority logic, protected photo/location evidence and human review. A rushed generic image result would not satisfy the project's intended image-only or multimodal research comparison.

## Evidence considered

### Generic cloud vision

Google Cloud Vision label detection returns broad English labels for objects, places and activities. Those labels are not CivicAI's civic taxonomy and do not establish a defect, cause, duration, danger or operational urgency. Google documents that synchronous image content is processed in memory rather than persisted to disk and is not used to train its Vision models, but using it would still transmit protected citizen evidence to a new processor. It also requires a Cloud project with billing enabled; the first 1,000 units per feature per month are currently free and later calls are billed.

Sources:

- [Google Cloud Vision label detection](https://cloud.google.com/vision/docs/labels)
- [Google Cloud Vision data usage](https://cloud.google.com/vision/docs/data-usage)
- [Google Cloud Vision pricing](https://cloud.google.com/vision/pricing)

No Vision API credential, billing authorization, citizen disclosure/consent wording, request budget, timeout policy or provider-specific operational verification currently exists in CivicAI. The existing Google sign-in OAuth client is not a Vision API authorization.

### Local generic zero-shot vision

Hugging Face documents zero-shot image classification as matching an image against caller-supplied candidate labels without task-specific labeled examples. That flexibility does not make the scores calibrated CivicAI probabilities or severity evidence. The `openai/clip-vit-base-patch32` model card states that CLIP was not developed for general deployment and recommends thorough in-domain testing with a fixed taxonomy; it also records fine-grained, counting and bias limitations. CivicAI has no approved representative Indian paired photo release or independent photo labels with which to perform that testing.

Sources:

- [Hugging Face zero-shot image classification](https://huggingface.co/docs/transformers/tasks/zero_shot_image_classification)
- [CLIP ViT-B/32 model card](https://huggingface.co/openai/clip-vit-base-patch32)

Adding PyTorch/Transformers plus a large downloaded model immediately before the presentation would also increase build size, startup time and offline-demo risk. No such dependency or model artifact is added.

### General multimodal APIs

An API capable of describing images would still need credentials, cost limits, failure handling, output constraints, privacy notice and task-specific evaluation. For example, OpenAI documents that API inputs are not used for training by default, while abuse-monitoring logs may retain customer content for up to 30 days unless an eligible retention control applies. CivicAI has no selected or authorized multimodal API account for this feature.

Source: [OpenAI API data controls](https://developers.openai.com/api/docs/guides/your-data)

### Comparable civic reporting workflow

FixMyStreet treats a photograph as report evidence and supports category-specific follow-up questions; its staff tooling also provides photograph moderation/redaction. This supports CivicAI's current evidence-plus-human-review boundary, not automatic visual severity.

Sources:

- [FixMyStreet citizen reporting](https://fixmystreet.org/training/citizens/)
- [FixMyStreet Pro citizen experience](https://fixmystreet.org/pro-manual/citizens-experience/)
- [FixMyStreet staff moderation](https://fixmystreet.org/running/staff/)

These foreign product references inform workflow design only. They are not training or evaluation data.

## What remains implemented

- The citizen uploads one validated JPEG or PNG in the frontend.
- CivicAI decodes and re-encodes it, strips metadata, enforces size/pixel limits and stores it through the configured private evidence adapter.
- Only authorized municipal staff retrieve the image through the protected evidence route.
- Staff inspect the photo alongside the original description, confirmed issue location, citizen-reported context, experimental text suggestion and separate priority suggestion.
- Photo failure or absence in legacy API records never causes the classifier or priority policy to invent visible facts.

No current model consumes the photograph. No output is described as image classification, visual defect detection, severity, authenticity, capture-time verification or multimodal prediction.

## Re-entry requirements for the major project

Reconsider photo assistance only after all of the following are explicit:

1. a fixed, versioned image task and taxonomy distinct from severity and priority;
2. a rights-reviewed Indian image source or consented CivicAI collection with representative category/city coverage;
3. independent labels, grouped leakage-safe splits and an unchanged held-out comparison for image-only and genuinely paired text-plus-image inputs;
4. privacy disclosure/consent and retention rules for any external processor, or measured local inference resources;
5. credentials, quota/budget caps, timeouts, retry/idempotency, disable/rollback behavior and no-secret logging;
6. explicit abstention/unsupported states, protected provenance and authorized human review;
7. evaluation of per-class performance, poor-quality/irrelevant images, Indian scenes, conflicts with text and serious under-triage risk.

Until those gates are met, the honest presentation statement is: **CivicAI stores and displays photo evidence securely, but the current experimental model is text-only and the transparent priority policy uses reported context—not image-derived severity.**
