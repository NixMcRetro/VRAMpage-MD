// Read-only comparison helpers for previously exported experiment metadata.
(function(root) {
  'use strict';
  const MAX_BYTES=262144, MAX_DEPTH=16, MAX_NODES=12000;
  function parse(text) {
    if (typeof text!=='string' || new TextEncoder().encode(text).length>MAX_BYTES)
      throw new Error('Experiment export must be at most 256 KB.');
    const data=JSON.parse(text);
    if (!data || typeof data!=='object' || Array.isArray(data)) throw new Error('Expected an experiment JSON object.');
    if (data.schemaVersion!==undefined && (!Number.isInteger(data.schemaVersion)||data.schemaVersion>1||data.schemaVersion<1))
      throw new Error('Unsupported experiment export schema version.');
    if (!['rom','logicFault','logic','corePin','modelVersion','vramFault','fmInputFault','psgInputFault'].some(key=>Object.hasOwn(data,key)))
      throw new Error('JSON does not look like a VRAMpage MD experiment export.');
    let nodes=0;
    function bound(value,depth) {
      if (++nodes>MAX_NODES || depth>MAX_DEPTH) throw new Error('Experiment JSON exceeds supported structure limits.');
      if (!value || typeof value!=='object') return;
      const keys=Object.keys(value);
      if (keys.length>512) throw new Error('Experiment JSON object has too many fields.');
      for (const key of keys) bound(value[key],depth+1);
    }
    bound(data,0);
    return data;
  }
  const path=(object,keys)=>keys.reduce((value,key)=>value&&typeof value==='object'?value[key]:undefined,object);
  const hasPath=(object,keys)=>{
    let parent=object;
    for(const key of keys.slice(0,-1)) {
      if(!parent||typeof parent!=='object'||!Object.hasOwn(parent,key))return false;
      parent=parent[key];
    }
    return !!parent&&typeof parent==='object'&&Object.hasOwn(parent,keys.at(-1));
  };
  const show=value=>{
    if(value===undefined)return 'Unknown';
    if(value===null)return 'None';
    const text=typeof value==='object'?JSON.stringify(value):String(value);
    return text.length>240?`${text.slice(0,237)}…`:text;
  };
  const equal=(a,b)=>{
    if(a===b)return true;
    if(!a||!b||typeof a!=='object'||typeof b!=='object')return false;
    if(Array.isArray(a)||Array.isArray(b))return Array.isArray(a)&&Array.isArray(b)&&a.length===b.length&&a.every((value,index)=>equal(value,b[index]));
    const ak=Object.keys(a).sort(),bk=Object.keys(b).sort();
    return ak.length===bk.length&&ak.every((key,index)=>key===bk[index]&&equal(a[key],b[key]));
  };
  function identity(a,b,label,keys,valid=()=>true) {
    const av=path(a,keys), bv=path(b,keys);
    const usable=v=>typeof v==='string'&&v.length>0&&valid(v);
    if (!usable(av)||!usable(bv)) return {label,a:usable(av)?show(av):'Unknown',b:usable(bv)?show(bv):'Unknown',status:'unknown'};
    return {label,a:show(av),b:show(bv),status:av===bv?'match':'mismatch'};
  }
  function compare(a,b) {
    const ramFault=record=>hasPath(record,['logic','fault'])?path(record,['logic','fault']):record.logicFault;
    const rows=[
      identity(a,b,'ROM SHA-256',['rom','sha256'],v=>/^[a-f0-9]{64}$/.test(v)),
      identity(a,b,'Core revision',['corePin'],v=>/^[a-f0-9]{40}$/.test(v)),
      identity(a,b,'Build source commit',['build','sourceCommit'],v=>/^[a-f0-9]{40}$/.test(v)&&path(a,['build','status'])==='available'&&path(b,['build','status'])==='available'),
      identity(a,b,'Application version',['build','applicationVersion']),
      identity(a,b,'Model version',['modelVersion']),
      identity(a,b,'ROM title',['rom','name'])
    ];
    const field=(label,keys,availability)=> {
      const av=path(a,keys),bv=path(b,keys);
      if(availability && (path(a,availability)!==true||path(b,availability)!==true)) {
        rows.push({label,a:show(av),b:show(bv),status:'unknown'});return;
      }
      if(!hasPath(a,keys)||!hasPath(b,keys)) { rows.push({label,a:show(av),b:show(bv),status:'unknown'});return; }
      rows.push({label,a:show(av),b:show(bv),status:equal(av,bv)?'match':'mismatch'});
    };
    const audio=(name,key)=>{
      for(const [label,fieldName] of [['configured','configured'],['effective','effective'],['data mask','dataMask'],['bridge A','bridgeA'],['bridge B','bridgeB']])
        field(`${name} ${label}`,[key,fieldName],[key,'available']);
    };
    const ramA=ramFault(a),ramB=ramFault(b);
    for(const [label,get] of [['kind',v=>v?.kind],['access',v=>v?.access],['address mask',v=>v?.addressMask],['lines / pair',v=>v?.lines],['activation frame',v=>v?.activationFrame]]) {
      const av=ramA===null?null:get(ramA),bv=ramB===null?null:get(ramB);
      rows.push({label:`RAM recorded ${label}`,a:show(av),b:show(bv),status:av===undefined||bv===undefined?'unknown':equal(av,bv)?'match':'mismatch'});
    }
    for(const [label,keys] of [['kind',['vramFault','kind']],['address mask',['vramFault','addressMask']],['bridge',['vramFault','bridge']],['model id',['vramTransaction','modelId']],['model version',['vramTransaction','modelVersion']],['transaction mask',['vramTransaction','mask']],['transaction bridge A',['vramTransaction','bridgeA']],['transaction bridge B',['vramTransaction','bridgeB']]])
      field(`VRAM ${label}`,keys,keys[0]==='vramTransaction'?['vramTransaction','available']:null);
    audio('FM','fmInputFault'); audio('PSG','psgInputFault');
    for(const [name,key] of [['FM','fmInputFault'],['PSG','psgInputFault']]) {
      for(const [label,fieldName] of [['model version','modelVersion'],['changed writes','changedWrites']])
        field(`${name} ${label}`,[key,fieldName],[key,'available']);
    }
    for(const [label,keys] of [
      ['RAM active',['logic','active']],['RAM affected reads',['logic','readCount']],['RAM affected writes',['logic','writeCount']],
      ['Current frame',['currentFrame']],['CPU flags',['cpuFlags']],['VRAM transaction counts',['vramTransaction','lastFrameCounts']],
      ['PSG recorded writes',['psgInputFault','inputWrites']],['FM recorded writes',['fmInputFault','inputWrites']],
      ['Fault disconnect outcomes',['faultDisconnects']],['CPU interventions',['cpuInterventions']],['Reset state',['resetState']]
    ]) {
      const legacyKeys={
        'logic.active':'faultActive','logic.readCount':'readCount','logic.writeCount':'writeCount'
      };
      const fallback=legacyKeys[keys.join('.')];
      if(fallback) {
        const av=path(a,keys)??path(a,[fallback]),bv=path(b,keys)??path(b,[fallback]);
        rows.push({label,a:show(av),b:show(bv),status:av===undefined||bv===undefined?'unknown':equal(av,bv)?'match':'mismatch'});
      } else field(label,keys);
    }
    return rows;
  }
  root.VRAMpageExperimentComparison={parse,compare,MAX_BYTES};
})(typeof window!=='undefined'?window:globalThis);
