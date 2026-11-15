from contextlib import asynccontextmanager
import os
import secrets
from typing import Optional
from fastapi import Depends,FastAPI,Header,HTTPException
from pydantic import BaseModel
from .lineage import Catalog,asset_id
from .masking import project_record

class Preview(BaseModel):
    namespace: str
    name: str
    record: dict

def create_app(path=None,admin_key=None,reader_key=None,masking_key=None):
    admin=admin_key or os.environ.get('GOVERNANCE_ADMIN_KEY')
    reader=reader_key or os.environ.get('GOVERNANCE_READER_KEY')
    secret=(masking_key or os.environ.get('MASKING_KEY','')).encode()
    if not admin or not reader or admin==reader or len(secret)<16:
        raise ValueError('Distinct admin/reader keys and a >=16-byte MASKING_KEY required')
    @asynccontextmanager
    async def lifespan(app):
        app.state.catalog=Catalog(path or os.environ.get('CATALOG_DB','catalog.sqlite'))
        yield
        app.state.catalog.db.close()
    app=FastAPI(title='Governance control plane',lifespan=lifespan)
    def role(x_api_key:Optional[str]=Header(default=None)):
        if x_api_key and secrets.compare_digest(x_api_key,admin):
            return 'steward'
        if x_api_key and secrets.compare_digest(x_api_key,reader):
            return 'analyst'
        raise HTTPException(401,'Invalid key')
    def steward(current=Depends(role)):
        if current!='steward':
            raise HTTPException(403,'Steward role required')
        return current
    @app.post('/lineage',dependencies=[Depends(steward)])
    def lineage(event:dict):
        try:
            return app.state.catalog.ingest(event)
        except (KeyError,ValueError,TypeError) as error:
            raise HTTPException(422,str(error))
    @app.get('/impact',dependencies=[Depends(role)])
    def impact(namespace:str,name:str):
        return app.state.catalog.impact(asset_id({'namespace':namespace,'name':name}))
    @app.put('/policy',dependencies=[Depends(steward)])
    def policy(namespace:str,name:str,fields:dict):
        try:
            app.state.catalog.set_policy(asset_id({'namespace':namespace,'name':name}),fields)
            return {'stored':True}
        except ValueError as error:
            raise HTTPException(422,str(error))
    @app.post('/preview')
    def preview(body:Preview,current=Depends(role)):
        asset=asset_id(body.model_dump())
        try:
            fields=app.state.catalog.policy(asset)
        except KeyError:
            raise HTTPException(404,'Dataset has no policy')
        result=project_record(body.record,fields,current,secret)
        app.state.catalog.audit(current,asset,'preview')
        return result
    return app
