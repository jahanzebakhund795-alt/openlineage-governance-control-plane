import hashlib
import hmac
import json

def project_record(record,policy,role,secret):
    if len(secret)<16:
        raise ValueError('Masking secret must contain at least 16 bytes')
    result={}
    for field,spec in policy.items():
        if field not in record:
            continue
        value=record[field]
        if role in spec.get('roles',[]):
            result[field]=value
        elif spec['mask']=='hmac':
            canonical=json.dumps([field,value],sort_keys=True,separators=(',',':')).encode()
            result[field]=hmac.new(secret,canonical,hashlib.sha256).hexdigest()
        elif spec['mask']=='last4':
            text=str(value)
            result[field]='*'*max(4,len(text)-4)+text[-4:] if len(text)>4 else '****'
    return result
