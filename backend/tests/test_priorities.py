def test_priority_persistence_and_review(client):
    created = client.post('/api/v1/complaints', files={'description': (None, 'Blocked public access')}).json()
    base = f"/api/v1/admin/complaints/{created['complaint_id']}/priority"
    request = {'context': {'source': 'municipal_report', 'immediate_danger': 'no', 'access_blocked': 'yes'}, 'note': 'Reported blocked access, service impact unknown'}
    response = client.post(base + '/context', json=request)
    assert response.status_code == 201
    snapshot = response.json()
    assert snapshot['suggestion']['band'] == 'High'
    review = {'snapshot_id': snapshot['event_id'], 'decision': 'accepted', 'note': 'Reviewed context'}
    assert client.post(base + '/reviews', json=review).status_code == 201
    history = client.get(base).json()
    assert len(history) == 2 and history[0]['actor_id'] == history[1]['actor_id']
    detail = client.get(base.removesuffix('/priority')).json()
    assert detail['status'] == created['status'] and detail['updated_at'] == created['updated_at']
    second = client.post(base + '/context', json={'context': {'source': 'citizen_report'}, 'note': 'Unknown facts'}).json()
    assert client.post(base + '/reviews', json=review).status_code == 409
    review['snapshot_id'] = second['event_id']
    assert client.post(base + '/reviews', json=review).status_code == 422
    review['decision'] = 'corrected'
    review['corrected_band'] = 'Medium'
    assert client.post(base + '/reviews', json=review).status_code == 201
    review.pop('corrected_band')
    review['decision'] = 'deferred'
    assert client.post(base + '/reviews', json=review).status_code == 201
    other = client.post('/api/v1/complaints', files={'description': (None, 'Another complaint')}).json()['complaint_id']
    assert client.post(f'/api/v1/admin/complaints/{other}/priority/reviews', json=review).status_code == 404
    client.headers.pop('X-CSRF-Token')
    assert client.post(base + '/context', json=request).status_code == 403

def test_priority_requires_auth(anonymous_client):
    assert anonymous_client.get('/api/v1/admin/complaints/00000000-0000-0000-0000-000000000001/priority').status_code == 401

def test_priority_operator_scope(operator_client):
    from uuid import uuid4
    c = operator_client
    identity = c.post('/api/v1/complaints', files={'description': (None, 'Blocked access')}).json()['complaint_id']
    base = f'/api/v1/admin/complaints/{identity}/priority'
    assert c.get(base).status_code == 403
    assert c.post(base + '/context', json={'context': {'source': 'municipal_report'}, 'note': 'Test'}).status_code == 403
    assert c.post(base + '/reviews', json={'snapshot_id': str(uuid4()), 'decision': 'deferred', 'note': 'Test'}).status_code == 403
