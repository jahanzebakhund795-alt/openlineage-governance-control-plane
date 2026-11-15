import copy
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from governance_plane.lineage import Catalog,asset_id
from governance_plane.masking import project_record
from governance_plane.api import create_app

def event():
    return json.loads(Path('fixtures/complete-event.json').read_text())

def test_run_state_lineage_and_replay(tmp_path):
    catalog=Catalog(str(tmp_path/'catalog.sqlite'))
    assert catalog.ingest(event())['state']=='COMPLETE'
    assert catalog.ingest(event())['replayed']
    start=event();start['eventType']='START'
    assert catalog.ingest(start)['state']=='COMPLETE'
    failed=event();failed['eventType']='FAIL'
    with pytest.raises(ValueError):
        catalog.ingest(failed)
    assert len(catalog.impact(asset_id({'namespace':'demo','name':'raw_claims'})))==1
    assert catalog.db.execute('SELECT COUNT(*) FROM column_edges').fetchone()[0]==1
    catalog.db.close()

def test_allowlist_masking_and_role_derived_from_key(tmp_path):
    policy={'patient':{'roles':['steward'],'mask':'hmac'},'region':{'roles':['steward','analyst'],'mask':'drop'}}
    record={'patient':'SYN001','region':'WEST','undeclared_secret':'must disappear'}
    output=project_record(record,policy,'analyst',b'x'*32)
    assert output['patient']!='SYN001' and output['region']=='WEST'
    assert 'undeclared_secret' not in output
    app=create_app(str(tmp_path/'api.sqlite'),'admin','reader','x'*32)
    with TestClient(app) as client:
        assert client.put('/policy?namespace=demo&name=claims',headers={'x-api-key':'reader'},json=policy).status_code==403
        assert client.put('/policy?namespace=demo&name=claims',headers={'x-api-key':'admin'},json=policy).status_code==200
        response=client.post('/preview',headers={'x-api-key':'reader'},json={'namespace':'demo','name':'claims','record':record})
        assert response.json()==output
