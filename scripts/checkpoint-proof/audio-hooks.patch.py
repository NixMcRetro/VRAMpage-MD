from pathlib import Path
import sys
root = Path(sys.argv[1]) / 'src/main/c'
def append(rel, marker, text):
    p=root/rel; s=p.read_text()
    if marker not in s: p.write_text(s+'\n'+text+'\n')

blip_header = root/'core/sound/blip_buf.h'
s=blip_header.read_text()
if 'blip_proof_size' not in s:
    s=s.replace('void blip_delete( blip_t* );','void blip_delete( blip_t* );\nunsigned blip_proof_size(const blip_t*);\nint blip_proof_save(blip_t*, unsigned char*, unsigned);\nint blip_proof_load(blip_t*, const unsigned char*, unsigned);')
    blip_header.write_text(s)
append('core/sound/blip_buf.c','unsigned blip_proof_size(',r'''typedef struct { fixed_t factor, offset; int size, integrator[2]; } blip_proof_header;
unsigned blip_proof_size(const blip_t *m) {
  return m ? (unsigned)(sizeof(blip_proof_header) + 2u * (unsigned)(m->size + buf_extra) * sizeof(buf_t)) : 0;
}
int blip_proof_save(blip_t *m, unsigned char *out, unsigned cap) {
  blip_proof_header h;
  unsigned need=blip_proof_size(m), p=0, bytes;
  if (!m || !out || cap<need) return -1;
  h.factor=m->factor; h.offset=m->offset; h.size=m->size;
  h.integrator[0]=m->integrator[0]; h.integrator[1]=m->integrator[1];
  memcpy(out+p,&h,sizeof(h)); p+=(unsigned)sizeof(h);
  bytes=(unsigned)(m->size+buf_extra)*sizeof(buf_t);
  memcpy(out+p,m->buffer[0],bytes); p+=bytes;
  memcpy(out+p,m->buffer[1],bytes); p+=bytes;
  return (int)p;
}
int blip_proof_load(blip_t *m, const unsigned char *in, unsigned len) {
  blip_proof_header h; unsigned p=0, bytes, need=blip_proof_size(m);
  if (!m || !in || len!=need) return -1;
  memcpy(&h,in,sizeof(h)); p+=(unsigned)sizeof(h);
  if (h.size!=m->size) return -1;
  bytes=(unsigned)(m->size+buf_extra)*sizeof(buf_t);
  m->factor=h.factor; m->offset=h.offset;
  m->integrator[0]=h.integrator[0]; m->integrator[1]=h.integrator[1];
  memcpy(m->buffer[0],in+p,bytes); p+=bytes;
  memcpy(m->buffer[1],in+p,bytes); p+=bytes;
  return (int)p;
}
uintptr_t blip_proof_pointer_fingerprint(const blip_t *m) {
  return m ? (uintptr_t)m ^ (uintptr_t)m->buffer[0] ^ (uintptr_t)m->buffer[1] : 0;
}''')
append('core/sound/psg.c','unsigned psg_proof_size(',r'''unsigned psg_proof_size(void) { return (unsigned)sizeof(psg); }
int psg_proof_save(unsigned char *out, unsigned cap) {
  if (!out || cap<sizeof(psg)) return -1;
  memcpy(out,&psg,sizeof(psg)); return (int)sizeof(psg);
}
int psg_proof_load(const unsigned char *in, unsigned len) {
  if (!in || len!=sizeof(psg)) return -1;
  memcpy(&psg,in,sizeof(psg)); return (int)sizeof(psg);
}''')
append('core/sound/sound.c','unsigned sound_proof_size(',r'''extern unsigned psg_proof_size(void);
extern int psg_proof_save(unsigned char*, unsigned);
extern int psg_proof_load(const unsigned char*, unsigned);
unsigned sound_proof_size(void) {
  return (unsigned)(sizeof(fm_last)+sizeof(fm_cycles_ratio)+sizeof(fm_cycles_start)+sizeof(fm_cycles_count)+sizeof(fm_cycles_busy)+sizeof(ym3438_cycles))+psg_proof_size();
}
int sound_proof_save(unsigned char *out, unsigned cap) {
  unsigned p=0, n=sound_proof_size();
  if (!out || cap<n) return -1;
#define SOUND_PROOF_SAVE(x) do { memcpy(out+p,&(x),sizeof(x)); p+=(unsigned)sizeof(x); } while (0)
  SOUND_PROOF_SAVE(fm_last); SOUND_PROOF_SAVE(fm_cycles_ratio); SOUND_PROOF_SAVE(fm_cycles_start); SOUND_PROOF_SAVE(fm_cycles_count); SOUND_PROOF_SAVE(fm_cycles_busy); SOUND_PROOF_SAVE(ym3438_cycles);
#undef SOUND_PROOF_SAVE
  int m=psg_proof_save(out+p,cap-p); if (m<0) return -1; p+=(unsigned)m;
  return (int)p;
}
int sound_proof_load(const unsigned char *in, unsigned len) {
  unsigned p=0, n=sound_proof_size();
  if (!in || len<n) return -1;
#define SOUND_PROOF_LOAD(x) do { memcpy(&(x),in+p,sizeof(x)); p+=(unsigned)sizeof(x); } while (0)
  SOUND_PROOF_LOAD(fm_last); SOUND_PROOF_LOAD(fm_cycles_ratio); SOUND_PROOF_LOAD(fm_cycles_start); SOUND_PROOF_LOAD(fm_cycles_count); SOUND_PROOF_LOAD(fm_cycles_busy); SOUND_PROOF_LOAD(ym3438_cycles);
#undef SOUND_PROOF_LOAD
  int m=psg_proof_load(in+p,psg_proof_size()); if (m<0) return -1; p+=(unsigned)m;
  fm_ptr=fm_buffer;
  return (int)p;
}''')
append('core/system.c','unsigned system_audio_proof_size(',r'''extern unsigned sound_proof_size(void);
extern int sound_proof_save(unsigned char*, unsigned);
extern int sound_proof_load(const unsigned char*, unsigned);
extern unsigned blip_proof_size(const blip_t*);
extern int blip_proof_save(blip_t*, unsigned char*, unsigned);
extern int blip_proof_load(blip_t*, const unsigned char*, unsigned);
unsigned system_audio_proof_size(void) {
  return (unsigned)(sizeof(mcycles_vdp)+sizeof(eq)+sizeof(llp)+sizeof(rrp)+sizeof(snd.sample_rate)+sizeof(snd.frame_rate)) + sound_proof_size() + blip_proof_size(snd.blips[0]);
}
int system_audio_proof_save(unsigned char *out, unsigned cap) {
  unsigned p=0,n=system_audio_proof_size();
  if (!out || !snd.blips[0] || cap<n) return -1;
#define SYSTEM_PROOF_SAVE(x) do { memcpy(out+p,&(x),sizeof(x)); p+=(unsigned)sizeof(x); } while (0)
  SYSTEM_PROOF_SAVE(mcycles_vdp); SYSTEM_PROOF_SAVE(eq); SYSTEM_PROOF_SAVE(llp); SYSTEM_PROOF_SAVE(rrp); SYSTEM_PROOF_SAVE(snd.sample_rate); SYSTEM_PROOF_SAVE(snd.frame_rate);
#undef SYSTEM_PROOF_SAVE
  int m=sound_proof_save(out+p,cap-p); if(m<0)return -1; p+=(unsigned)m;
  m=blip_proof_save(snd.blips[0],out+p,cap-p); if(m<0)return -1; p+=(unsigned)m;
  return (int)p;
}
int system_audio_proof_load(const unsigned char *in, unsigned len) {
  unsigned p=0,n=system_audio_proof_size(); int sample_rate; double frame_rate;
  if (!in || !snd.blips[0] || len!=n) return -1;
  unsigned profile_offset=(unsigned)(sizeof(mcycles_vdp)+sizeof(eq)+sizeof(llp)+sizeof(rrp));
  memcpy(&sample_rate,in+profile_offset,sizeof(sample_rate));
  memcpy(&frame_rate,in+profile_offset+sizeof(sample_rate),sizeof(frame_rate));
  if (sample_rate!=snd.sample_rate || frame_rate!=snd.frame_rate) return -1;
#define SYSTEM_PROOF_LOAD(x) do { memcpy(&(x),in+p,sizeof(x)); p+=(unsigned)sizeof(x); } while (0)
  SYSTEM_PROOF_LOAD(mcycles_vdp); SYSTEM_PROOF_LOAD(eq); SYSTEM_PROOF_LOAD(llp); SYSTEM_PROOF_LOAD(rrp); SYSTEM_PROOF_LOAD(snd.sample_rate); SYSTEM_PROOF_LOAD(snd.frame_rate);
#undef SYSTEM_PROOF_LOAD
  int m=sound_proof_load(in+p,len-p); if(m<0)return -1; p+=(unsigned)m;
  m=blip_proof_load(snd.blips[0],in+p,len-p); if(m<0)return -1; p+=(unsigned)m;
  return (int)p;
}
int system_audio_proof_reject_profile(const unsigned char *in, unsigned len) {
  int old=snd.sample_rate; snd.sample_rate=old+1; int result=system_audio_proof_load(in,len); snd.sample_rate=old; return result == -1;
}
extern uintptr_t blip_proof_pointer_fingerprint(const blip_t*);
uintptr_t system_audio_proof_pointer_fingerprint(void) { return blip_proof_pointer_fingerprint(snd.blips[0]); }''')
