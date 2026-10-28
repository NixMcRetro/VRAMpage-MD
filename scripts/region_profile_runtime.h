#ifndef VRAMPAGE_REGION_PROFILE_RUNTIME_H
#define VRAMPAGE_REGION_PROFILE_RUNTIME_H

int set_region_request(int id);
int region_profile_set_request(int id);
void region_profile_prepare_start(void);
void region_profile_mark_loaded(void);
int region_profile_requested(void);
int region_profile_loaded(void);
int region_profile_region_code(void);
int region_profile_pal(void);
int region_profile_master_clock(void);
double region_profile_frame_rate(void);
int region_profile_lines_per_frame(void);
int region_profile_width(void);
int region_profile_height(void);
int region_profile_interlaced(void);

#endif
