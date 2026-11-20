# Experimental assessment guard

Offline policy `experimental-text-guard-v1` wraps the local model. No application endpoint or UI is connected yet. Empty/oversized descriptions, non-Latin alphabetic content, missing supported-family cues, mixed-family cues and selected resolved/negated phrases return needs_review. Model absence, zero vocabulary, invalid output, exceptions and disagreement with the single family cue also return needs_review. An allowed suggestion still requires staff review, carries no confidence percentage and never changes status, routing or priority.

This is an intentionally conservative heuristic scope filter, not a trained out-of-distribution detector or validated language/negation understanding. Latin-script Hindi/transliteration can pass; paraphrases may be deferred; place names can trigger false family cues; unsupported content containing an accepted cue can still pass. Broad negation/resolution rules may defer valid complaints such as requests to have something fixed. All suggestions require review. Do not claim these rules cover all edge cases or guarantee correctness.

The seven existing authored challenge probes were replayed on the actual local model. Six returned needs_review; the overflowing-drain example returned an experimental drainage suggestion. These are smoke tests designed after observing failures, not independent performance measurements.

Primary reference: https://scikit-learn.org/stable/modules/classification_threshold.html explains the distinction between prediction scores and action thresholds. No calibrated probability or learned rejection threshold is claimed here. No additional dependency, production model loader, API or frontend change.

Next implement durable authorized municipal assessment storage and review, with model artifact identity and failure isolation. Keep the local guard explicitly experimental and disabled by default until integration is verified.
