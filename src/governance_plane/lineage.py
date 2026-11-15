from collections import deque
import json
import sqlite3
from threading import RLock

def asset_id(dataset):
    if not dataset.get('namespace') or not dataset.get('name'):
        raise ValueError('Dataset namespace and name required')
    return json.dumps([dataset['namespace'],dataset['name']],separators=(',',':'))

class Catalog:
    def __init__(self,path):
        self.lock=RLock()
        self.db=sqlite3.connect(path,check_same_thread=False)
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS runs(run_id TEXT PRIMARY KEY,state TEXT,job TEXT);
            CREATE TABLE IF NOT EXISTS events(run_id TEXT,event_type TEXT,payload TEXT,PRIMARY KEY(run_id,event_type));
            CREATE TABLE IF NOT EXISTS edges(source TEXT,target TEXT,run_id TEXT,PRIMARY KEY(source,target,run_id));
            CREATE TABLE IF NOT EXISTS column_edges(source TEXT,source_field TEXT,target TEXT,target_field TEXT,run_id TEXT,PRIMARY KEY(source,source_field,target,target_field,run_id));
            CREATE TABLE IF NOT EXISTS policies(asset TEXT PRIMARY KEY,payload TEXT);
            CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY,role TEXT,asset TEXT,action TEXT);
        """)

    def ingest(self,event):
        kind=event['eventType']
        if kind not in ('START','COMPLETE','FAIL','ABORT'):
            raise ValueError('Unsupported event type')
        run=event['run']['runId']
        job=asset_id(event['job'])
        if not run:
            raise ValueError('runId required')
        serialized=json.dumps(event,sort_keys=True,separators=(',',':'))
        inputs=[asset_id(d) for d in event.get('inputs',[])]
        outputs=event.get('outputs',[])
        for output in outputs:
            asset_id(output)
        with self.lock,self.db:
            old=self.db.execute('SELECT payload FROM events WHERE run_id=? AND event_type=?',(run,kind)).fetchone()
            if old:
                if old[0]!=serialized:
                    raise ValueError('Conflicting lineage event replay')
                return {'replayed':True}
            previous=self.db.execute('SELECT state,job FROM runs WHERE run_id=?',(run,)).fetchone()
            if previous and previous[1]!=job:
                raise ValueError('Run ID belongs to another job')
            terminal=('COMPLETE','FAIL','ABORT')
            if previous and previous[0] in terminal and kind in terminal and previous[0]!=kind:
                raise ValueError('Conflicting terminal run states')
            state=previous[0] if previous and kind=='START' else kind
            self.db.execute('INSERT INTO runs VALUES(?,?,?) ON CONFLICT(run_id) DO UPDATE SET state=excluded.state',(run,state,job))
            self.db.execute('INSERT INTO events VALUES(?,?,?)',(run,kind,serialized))
            if kind=='COMPLETE':
                for output in outputs:
                    target=asset_id(output)
                    for source in inputs:
                        self.db.execute('INSERT OR IGNORE INTO edges VALUES(?,?,?)',(source,target,run))
                    fields=output.get('facets',{}).get('columnLineage',{}).get('fields',{})
                    for target_field,spec in fields.items():
                        for source_field in spec.get('inputFields',[]):
                            source=asset_id(source_field)
                            self.db.execute('INSERT OR IGNORE INTO column_edges VALUES(?,?,?,?,?)',(
                                source,source_field['field'],target,target_field,run))
        return {'replayed':False,'state':state}

    def impact(self,asset,max_nodes=10000):
        with self.lock:
            edges=self.db.execute('SELECT DISTINCT source,target FROM edges').fetchall()
        graph={}
        for source,target in edges:
            graph.setdefault(source,set()).add(target)
        found={asset:0}
        queue=deque([asset])
        while queue:
            current=queue.popleft()
            for target in graph.get(current,()):
                if target not in found:
                    if len(found)>=max_nodes:
                        raise ValueError('Impact traversal exceeded node limit')
                    found[target]=found[current]+1
                    queue.append(target)
        return [{'dataset':json.loads(k),'distance':v} for k,v in sorted(found.items()) if k!=asset]

    def set_policy(self,asset,policy):
        for spec in policy.values():
            if set(spec)-{'roles','mask'} or spec.get('mask') not in ('drop','hmac','last4'):
                raise ValueError('Invalid field policy')
            if not set(spec.get('roles',[]))<={'steward','analyst'}:
                raise ValueError('Unknown role')
        with self.lock,self.db:
            self.db.execute('INSERT INTO policies VALUES(?,?) ON CONFLICT(asset) DO UPDATE SET payload=excluded.payload',(asset,json.dumps(policy)))

    def policy(self,asset):
        with self.lock:
            row=self.db.execute('SELECT payload FROM policies WHERE asset=?',(asset,)).fetchone()
        if not row:
            raise KeyError(asset)
        return json.loads(row[0])

    def audit(self,role,asset,action):
        with self.lock,self.db:
            self.db.execute('INSERT INTO audit(role,asset,action) VALUES(?,?,?)',(role,asset,action))
