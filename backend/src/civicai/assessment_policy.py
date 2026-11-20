"""Conservative offline demonstration guard; heuristics are not an OOD guarantee."""
import re
import unicodedata

POLICY_VERSION = 'experimental-text-guard-v1'
CUES = {
 'roads_and_pedestrian_access': r'\b(road|roads|footpath|footpaths|pothole|potholes|pavement)\b',
 'solid_waste': r'\b(garbage|rubbish|waste|dustbin|dustbins|debris)\b',
 'drainage_and_sewerage': r'\b(drain|drains|drainage|sewage|sewer|manhole|manholes)\b',
 'public_lighting': r'\b(streetlight|streetlights|street light|street lights|lamp post)\b',
}


def assess(text, model=None):
    result={'state':'needs_review','suggested_family':None,'reasons':[],
            'experimental':True,'human_review_required':True,'policy_version':POLICY_VERSION}
    def stop(reason):
        result['reasons']=[reason]; return result
    if not isinstance(text,str) or not text.strip(): return stop('empty_description')
    if len(text)>10000: return stop('description_too_long')
    normalized=unicodedata.normalize('NFKC',text).casefold()
    if any(c.isalpha() and 'LATIN' not in unicodedata.name(c,'') for c in normalized): return stop('unsupported_script')
    if re.search(r"\b(repaired|resolved|fixed|no problem|no longer|not broken|not blocked)\b",normalized): return stop('possible_resolved_or_negated_issue')
    cues=[family for family,pattern in CUES.items() if re.search(pattern,normalized)]
    if not cues: return stop('outside_supported_vocabulary')
    if len(cues)>1: return stop('multiple_family_cues')
    if model is None: return stop('model_unavailable')
    try:
        vector=model.named_steps['tfidf'].transform([normalized])
        if vector.nnz==0: return stop('no_known_model_features')
        prediction=str(model.predict([normalized])[0])
        if prediction not in CUES: return stop('invalid_model_output')
        if prediction!=cues[0]: return stop('model_cue_disagreement')
    except Exception:
        return stop('assessment_failed')
    result.update(state='suggested',suggested_family=prediction,reasons=['experimental_model_and_scope_cue_agree'])
    return result
