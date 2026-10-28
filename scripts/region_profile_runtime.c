#include "shared.h"
#include "region_profile_runtime.h"
#include "io_ctrl.h"
#include "vdp_ctrl.h"
#include <emscripten/emscripten.h>

static int requested_region = 1;
static int region_loaded;

int set_region_request(int id)
{
  if (id < 0 || id > 4) return 1;
  requested_region = id;
  return 0;
}

int region_profile_set_request(int id) { return set_region_request(id); }

int EMSCRIPTEN_KEEPALIVE set_region_request_c(int id) { return set_region_request(id); }
int EMSCRIPTEN_KEEPALIVE get_region_requested_c(void) { return region_profile_requested(); }
int EMSCRIPTEN_KEEPALIVE get_region_loaded_c(void) { return region_profile_loaded(); }
int EMSCRIPTEN_KEEPALIVE get_region_code_c(void) { return region_profile_region_code(); }
int EMSCRIPTEN_KEEPALIVE get_region_pal_c(void) { return region_profile_pal(); }
int EMSCRIPTEN_KEEPALIVE get_region_master_clock_c(void) { return region_profile_master_clock(); }
double EMSCRIPTEN_KEEPALIVE get_region_frame_rate_c(void) { return region_profile_frame_rate(); }
int EMSCRIPTEN_KEEPALIVE get_region_lines_per_frame_c(void) { return region_profile_lines_per_frame(); }
int EMSCRIPTEN_KEEPALIVE get_region_width_c(void) { return region_profile_width(); }
int EMSCRIPTEN_KEEPALIVE get_region_height_c(void) { return region_profile_height(); }
int EMSCRIPTEN_KEEPALIVE get_region_interlaced_c(void) { return region_profile_interlaced(); }

void region_profile_prepare_start(void)
{
  requested_region = (requested_region < 0 || requested_region > 4) ? 1 : requested_region;
  region_loaded = 0;
  config.region_detect = requested_region;
  if (requested_region == 1)
  {
    /* Keep the legacy NTSC-U profile's explicit overrides byte-for-byte. */
    config.vdp_mode = 1;
    config.master_clock = 1;
  }
  else
  {
    config.vdp_mode = 0;
    config.master_clock = 0;
  }
}

void region_profile_mark_loaded(void) { region_loaded = 1; }
int region_profile_requested(void) { return requested_region; }
int region_profile_loaded(void) { return region_loaded; }
int region_profile_region_code(void) { return region_code; }
int region_profile_pal(void) { return vdp_pal; }
int region_profile_master_clock(void) { return (int)system_clock; }
int region_profile_lines_per_frame(void) { return lines_per_frame; }
int region_profile_interlaced(void) { return interlaced; }

double region_profile_frame_rate(void)
{
  return lines_per_frame ? (double)system_clock / (3420.0 * lines_per_frame) : 0.0;
}

int region_profile_width(void)
{
  /* This matches remap_line()'s width expression, including its viewport crop. */
  return bitmap.viewport.w + 2 * bitmap.viewport.x;
}

int region_profile_height(void)
{
  return bitmap.viewport.h * ((interlaced && config.render) ? 2 : 1);
}
