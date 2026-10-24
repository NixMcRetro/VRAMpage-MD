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
    const recognizable=(key,value)=>key==='rom'&&!!value&&typeof value==='object'&&!Array.isArray(value)&&
        (Object.hasOwn(value,'name')&&(value.name===null||typeof value.name==='string')||Object.hasOwn(value,'sha256')&&(value.sha256===null||typeof value.sha256==='string'))
      ||key==='vramFault'&&!!value&&typeof value==='object'&&!Array.isArray(value)&&
        typeof value.kind==='string'&&['none','address-stuck-low','address-bridge'].includes(value.kind)
      ||key==='logic'&&!!value&&typeof value==='object'&&!Array.isArray(value)&&
        (value.schemaVersion===1||typeof value.active==='boolean'||value.fault===null||!!value.fault&&typeof value.fault==='object')
      ||key==='logicFault'&&!!value&&typeof value==='object'&&!Array.isArray(value)&&typeof value.kind==='string'
      ||['fmInputFault','psgInputFault'].includes(key)&&!!value&&typeof value==='object'&&!Array.isArray(value)&&typeof value.available==='boolean'
      ||key==='corePin'&&typeof value==='string'&&/^[a-f0-9]{40}$/.test(value)
      ||key==='modelVersion'&&typeof value==='string'&&value.length>0;
    if (!Object.keys(data).some(key=>recognizable(key,data[key])))
      throw new Error('JSON does not look like a VRAMpage MD experiment export.');
    let nodes=0;
    function bound(value,depth) {
      if (++nodes>MAX_NODES || depth>MAX_DEPTH) throw new Error('Experiment JSON exceeds supported structure limits.');
      if (!value || typeof value!=='object') return;
      const keys=Object.keys(value);
      if (!Array.isArray(value)&&keys.length>512) throw new Error('Experiment JSON object has too many fields.');
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
  const isInteger=(value,min=0,max=Number.MAX_SAFE_INTEGER)=>Number.isInteger(value)&&value>=min&&value<=max;
  const isPair=value=>value===null||Array.isArray(value)&&value.length===2&&value.every(line=>isInteger(line,0,31));
  const isVramPair=value=>value===null||Array.isArray(value)&&value.length===2&&value.every(line=>isInteger(line,0,7))&&value[0]!==value[1];
  const isLineList=value=>Array.isArray(value)&&value.every(line=>typeof line==='string'&&/^(A(?:[1-9]|1[0-5])|D(?:[0-9]|1[0-5]))$/.test(line));
  const isRecord=value=>!!value&&typeof value==='object'&&!Array.isArray(value);
  const isCount=value=>typeof value==='string'&&/^\d+$/.test(value)||isInteger(value);
  const isString=value=>typeof value==='string';
  const isBoolean=value=>typeof value==='boolean';
  const isObject=value=>isRecord(value)||Array.isArray(value);
  function identity(a,b,label,keys,valid=()=>true) {
    const av=path(a,keys), bv=path(b,keys);
    const usable=(record,v)=>typeof v==='string'&&v.length>0&&valid(v,record);
    if (!usable(a,av)||!usable(b,bv)) return {label,a:usable(a,av)?show(av):'Unknown',b:usable(b,bv)?show(bv):'Unknown',status:'unknown'};
    return {label,a:show(av),b:show(bv),status:av===bv?'match':'mismatch'};
  }
  function compare(a,b) {
    const ramFault=record=>hasPath(record,['logic','fault'])?path(record,['logic','fault']):record.logicFault;
    const logicAvailability=hasPath(a,['logic'])||hasPath(b,['logic'])?['logic','available']:null;
    const rows=[
      identity(a,b,'ROM SHA-256',['rom','sha256'],v=>/^[a-f0-9]{64}$/.test(v)),
      identity(a,b,'Core revision',['corePin'],v=>/^[a-f0-9]{40}$/.test(v)),
      identity(a,b,'Build source commit',['build','sourceCommit'],(v,record)=>/^[a-f0-9]{40}$/.test(v)&&path(record,['build','status'])==='available'),
      identity(a,b,'Application version',['build','applicationVersion'],v=>/^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$/.test(v)),
      identity(a,b,'Model version',['modelVersion']),
      identity(a,b,'RAM model version',['logic','modelVersion']),
      identity(a,b,'ROM title',['rom','name'])
    ];
    const field=(label,keys,availability,valid=()=>true)=> {
      const av=path(a,keys),bv=path(b,keys);
      const aAvailable=!availability||path(a,availability)===true;
      const bAvailable=!availability||path(b,availability)===true;
      if(!aAvailable||!bAvailable) {
        rows.push({label,a:aAvailable?show(av):'Unknown',b:bAvailable?show(bv):'Unknown',status:'unknown'});return;
      }
      if(!hasPath(a,keys)||!hasPath(b,keys)||!valid(av)||!valid(bv)) { rows.push({label,a:valid(av)?show(av):'Unknown',b:valid(bv)?show(bv):'Unknown',status:'unknown'});return; }
      rows.push({label,a:show(av),b:show(bv),status:equal(av,bv)?'match':'mismatch'});
    };
    const audio=(name,key)=>{
      for(const [label,fieldName] of [['configured','configured'],['effective','effective'],['data mask','dataMask'],['bridge A','bridgeA'],['bridge B','bridgeB']]) {
        const valid=fieldName==='configured'||fieldName==='effective'?isBoolean:
          fieldName==='dataMask'?value=>isInteger(value,0,255):value=>isInteger(value,-1,7);
        field(`${name} ${label}`,[key,fieldName],[key,'available'],valid);
      }
    };
    const ramA=ramFault(a),ramB=ramFault(b);
    for(const [label,get,valid] of [
      ['kind',v=>v?.kind,value=>typeof value==='string'&&['address','data','address-stuck-low','address-mask','line-pair'].includes(value)],
      ['access',v=>v?.access,value=>typeof value==='string'&&['read','write','read + write','both'].includes(value)],
      ['address mask',v=>v?.addressMask,value=>isInteger(value,0,32767)],
      ['lines / pair',v=>v?.lines??v?.linesPair,value=>isLineList(value)||isPair(value)],
      ['activation frame',v=>v?.activationFrame,value=>isInteger(value)]
    ]) {
      const av=ramA===null?null:get(ramA),bv=ramB===null?null:get(ramB);
      const aValid=av===null||valid(av),bValid=bv===null||valid(bv);
      rows.push({label:`RAM recorded ${label}`,a:aValid?show(av):'Unknown',b:bValid?show(bv):'Unknown',status:av===undefined||bv===undefined||!aValid||!bValid?'unknown':equal(av,bv)?'match':'mismatch'});
    }
    for(const [label,keys,valid] of [
      ['kind',['vramFault','kind'],value=>typeof value==='string'&&['none','address-stuck-low','address-bridge'].includes(value)],
      ['address mask',['vramFault','addressMask'],value=>isInteger(value,0,255)],['bridge',['vramFault','bridge'],isVramPair],
      ['model id',['vramTransaction','modelId'],value=>isInteger(value,1,255)],['model version',['vramTransaction','modelVersion'],isString],
      ['transaction mask',['vramTransaction','mask'],value=>isInteger(value,0,255)],
      ['transaction bridge A',['vramTransaction','bridgeA'],value=>isInteger(value,-1,7)],
      ['transaction bridge B',['vramTransaction','bridgeB'],value=>isInteger(value,-1,7)]
    ]) field(`VRAM ${label}`,keys,keys[0]==='vramTransaction'?['vramTransaction','available']:null,valid);
    audio('FM','fmInputFault'); audio('PSG','psgInputFault');
    for(const [name,key] of [['FM','fmInputFault'],['PSG','psgInputFault']]) {
      for(const [label,fieldName] of [['model version','modelVersion'],['changed writes','changedWrites']])
        field(`${name} ${label}`,[key,fieldName],[key,'available'],fieldName==='changedWrites'?isCount:isString);
    }
    for(const [label,keys,valid] of [
      ['RAM active',['logic','active'],isBoolean],['RAM affected reads',['logic','readCount'],isInteger],['RAM affected writes',['logic','writeCount'],isInteger],
      ['Current frame',['currentFrame'],isInteger],['CPU flags',['cpuFlags'],value=>isInteger(value,0,65535)],
      ['VRAM transaction counts',['vramTransaction','lastFrameCounts'],isRecord],
      ['PSG recorded writes',['psgInputFault','inputWrites'],isCount],['FM recorded writes',['fmInputFault','inputWrites'],isCount],
      ['Fault disconnect outcomes',['faultDisconnects'],isObject],['CPU interventions',['cpuInterventions'],isObject],['Reset state',['resetState'],isString]
    ]) {
      const legacyKeys={
        'logic.active':'faultActive','logic.readCount':'readCount','logic.writeCount':'writeCount'
      };
      const fallback=legacyKeys[keys.join('.')];
      if(fallback) {
        const av=hasPath(a,keys)?path(a,keys):path(a,[fallback]),bv=hasPath(b,keys)?path(b,keys):path(b,[fallback]);
        const availabilityRequired=logicAvailability&&keys[1]!=='active';
        const aValid=valid(av)&&(!availabilityRequired||!hasPath(a,['logic'])||path(a,logicAvailability)===true),bValid=valid(bv)&&(!availabilityRequired||!hasPath(b,['logic'])||path(b,logicAvailability)===true);
        rows.push({label,a:aValid?show(av):'Unknown',b:bValid?show(bv):'Unknown',status:av===undefined||bv===undefined||!aValid||!bValid?'unknown':equal(av,bv)?'match':'mismatch'});
      } else field(label,keys,keys[0]==='psgInputFault'||keys[0]==='fmInputFault'?[keys[0],'available']:
        keys[0]==='vramTransaction'?['vramTransaction','available']:
        ['Current frame','VRAM transaction counts'].includes(label)?logicAvailability:null,valid);
    }
    return rows;
  }
  root.VRAMpageExperimentComparison={parse,compare,MAX_BYTES};
})(typeof window!=='undefined'?window:globalThis);
