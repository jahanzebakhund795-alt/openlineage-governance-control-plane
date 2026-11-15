import json
from pathlib import Path
from .lineage import Catalog,asset_id
from .masking import project_record

def main():
    Path('output').mkdir(exist_ok=True)
    catalog=Catalog('output/catalog.sqlite')
    try:
        event=json.loads(Path('fixtures/complete-event.json').read_text())
        catalog.ingest(event)
        impact=catalog.impact(asset_id({'namespace':'demo','name':'raw_claims'}))
        policy={'member':{'roles':['steward'],'mask':'hmac'},'region':{'roles':['steward','analyst'],'mask':'drop'}}
        output=project_record({'member':'SYN001','region':'WEST','private':'not projected'},policy,'analyst',b'demo-only-key-not-for-production')
        print(json.dumps({'impact':impact,'analyst_projection':output},indent=2))
    finally:
        catalog.db.close()
if __name__=='__main__':
    main()
