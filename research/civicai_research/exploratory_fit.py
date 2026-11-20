"""Fixed local AI-label pilot experiment; never an independent evaluation."""
import json
from pathlib import Path
import hashlib
import unicodedata
from datetime import datetime, timezone
import time
import joblib
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.dummy import DummyClassifier
from threadpoolctl import threadpool_limits
from .text_baseline import fit_pipeline, measure, select_best, validate_folds, git_state, PACKAGES
from .manifest import _file_hash
from .text_proposal import write_json
from importlib.metadata import version
import platform


def checked_rows(packet, decisions, families):
    records={r['task_id']:r for r in packet['records']}
    if len(records)!=len(packet['records']): raise ValueError('Duplicate packet identity')
    expected={k for k,r in records.items() if r['candidate_family'] in families and r['disposition']=='annotation_candidate'}
    if len(decisions)!=len(expected) or {d['task_id'] for d in decisions}!=expected: raise ValueError('Decision coverage differs')
    rows=[]; duplicates={}
    for d in decisions:
        r=records[d['task_id']]
        actual=hashlib.sha256(r['text'].encode('utf-8')).hexdigest()
        if actual!=r['text_sha256'] or actual!=d['text_sha256'] or d['family_proposal']!=r['candidate_family'] or d['group_id']!=r['group_id']: raise ValueError('Decision binding differs')
        if d['author_kind']!='ai_assistant' or d['training_approved'] is not False or d['decision'] not in {'defer','candidate_local_exploration'}: raise ValueError('Invalid screening provenance')
        if d['decision']=='candidate_local_exploration':
            if not r['text'].strip() or r['proposed_spans'] or 'context_hold' in r['privacy_flags']: raise ValueError('Unresolved screening hold')
            norm=' '.join(unicodedata.normalize('NFKC',r['text']).casefold().split())
            if norm in duplicates and duplicates[norm]!=r['group_id']: raise ValueError('Duplicate crosses groups')
            duplicates[norm]=r['group_id']
            rows.append({'record_id':r['task_id'],'group_id':r['group_id'],'text':r['text'],'label':r['candidate_family']})
    return rows


def run():
    protocol_path=Path('research/protocols/exploratory_ai_labels_v1.json')
    packet_path=Path('data/review/development-release-review-v1/packet.json')
    decisions_path=Path('data/review/exploratory-privacy-pass-v1/decisions.json')
    summary_path=decisions_path.with_name('summary.json')
    output=Path('research/results/exploratory-ai-labels-v1')
    if output.exists(): raise ValueError('Output exists')
    protocol=json.loads(protocol_path.read_text())
    summary=json.loads(summary_path.read_text())
    if _file_hash(packet_path)!=summary['packet_sha256']: raise ValueError('Stale packet')
    packet=json.loads(packet_path.read_text()); decisions=json.loads(decisions_path.read_text())
    rows=checked_rows(packet, decisions, protocol['real_data_scope']['families'])
    if len(rows)!=97: raise ValueError('Fixed pilot coverage differs')
    labels=sorted({r['label'] for r in rows})
    folds=list(StratifiedGroupKFold(n_splits=3,shuffle=True,random_state=42).split([r['text'] for r in rows],[r['label'] for r in rows],[r['group_id'] for r in rows]))
    validate_folds(rows,folds,labels,3)
    output.mkdir(parents=True); (output/'INCOMPLETE').touch()
    started=datetime.now(timezone.utc).isoformat(); tick=time.perf_counter()
    results=[]; predictions=[]
    configurations=[None]+[{'C':c,'class_weight':w} for c in protocol['logistic_regression']['C'] for w in protocol['logistic_regression']['class_weight']]
    with threadpool_limits(limits=1):
        for number,params in enumerate(configurations):
            metrics=[]
            for fold,(tr,va) in enumerate(folds):
                truth=[rows[int(i)]['label'] for i in va]
                if params is None:
                    model=DummyClassifier(strategy='most_frequent').fit([[0] for i in tr],[rows[int(i)]['label'] for i in tr]); pred=model.predict([[0] for i in va])
                else:
                    model,warnings=fit_pipeline([rows[int(i)]['text'] for i in tr],[rows[int(i)]['label'] for i in tr],protocol,params)
                    if warnings: raise ValueError('Investigate fitting warnings')
                    pred=model.predict([rows[int(i)]['text'] for i in va])
                metrics.append(measure(truth,list(pred),labels))
                predictions.extend({'record_id':rows[int(i)]['record_id'],'fold':fold,'configuration':number,'ai_proposed_label':t,'prediction':str(p)} for i,t,p in zip(va,truth,pred,strict=True))
            results.append({'configuration':number,'parameters':params,'folds':metrics,'mean_macro_f1':sum(m['macro_f1'] for m in metrics)/3})
        winner=select_best(results[1:])
        final,warnings=fit_pipeline([r['text'] for r in rows],[r['label'] for r in rows],protocol,winner['parameters'])
        if warnings: raise ValueError('Investigate refit warnings')
    joblib.dump({'pipeline':final,'label_origin':'AI_proposals','operational_release_approved':False,'protocol_sha256':_file_hash(protocol_path)},output/'experimental-model.joblib')
    report={'status':'local_exploratory_fit_complete','records':97,'groups':97,'deferred':37,'selected':winner,'dummy':results[0],'independent_accuracy_measured':False,'operational_release_approved':False,'git':git_state(),'packages':{p:version(p) for p in PACKAGES},'python':platform.python_version(),'platform':platform.platform(),'started_at':started,'elapsed_seconds':time.perf_counter()-tick,'input_sha256':{str(p):_file_hash(p) for p in [protocol_path,packet_path,decisions_path,Path(__file__)]}}
    for name,value in [('summary.json',report),('results.json',results),('predictions.json',predictions),('protocol.json',protocol),('split.json',[{'train':[rows[int(i)]['record_id'] for i in a],'validation':[rows[int(i)]['record_id'] for i in b]} for a,b in folds])]: write_json(output/name,value)
    write_json(output/'artifacts.json',{p.name:_file_hash(p) for p in output.iterdir() if p.name!='INCOMPLETE'})
    (output/'COMPLETE').touch(); (output/'INCOMPLETE').unlink()
    print(json.dumps({'records':97,'selected_parameters':winner['parameters'],'development_macro_f1':winner['mean_macro_f1'],'dummy_macro_f1':results[0]['mean_macro_f1'],'independent_accuracy_measured':False}))

if __name__=='__main__': run()
