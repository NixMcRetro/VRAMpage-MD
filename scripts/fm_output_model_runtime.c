#include "shared.h"
#include "fm_output_model_runtime.h"
#include <emscripten/emscripten.h>

enum { FM_OUTPUT_DISCRETE = 0, FM_OUTPUT_INTEGRATED = 1, FM_BACKEND_MAME = 0, FM_BACKEND_NUKED = 1 };

static int requested_model = FM_OUTPUT_DISCRETE;
static int effective_model = -1;
static int model_loaded;

int set_fm_output_model_request(double model)
{
  if (model != (double)FM_OUTPUT_DISCRETE && model != (double)FM_OUTPUT_INTEGRATED) return 1;
  if (config.ym3438 != 0) return 2;
  requested_model = (int)model;
  return 0;
}

int EMSCRIPTEN_KEEPALIVE set_fm_output_model_request_c(double model)
{
  return set_fm_output_model_request(model);
}

int EMSCRIPTEN_KEEPALIVE get_fm_output_model_requested_c(void) { return fm_output_model_requested(); }
int EMSCRIPTEN_KEEPALIVE get_fm_output_model_effective_c(void) { return fm_output_model_effective(); }
int EMSCRIPTEN_KEEPALIVE get_fm_output_model_loaded_c(void) { return fm_output_model_loaded(); }
int EMSCRIPTEN_KEEPALIVE get_fm_output_model_supported_c(void) { return fm_output_model_supported(); }
int EMSCRIPTEN_KEEPALIVE get_fm_output_model_backend_c(void) { return fm_output_model_backend(); }

void fm_output_model_prepare_start(void)
{
  model_loaded = 0;
  effective_model = -1;
  config.ym2612 = requested_model;
}

void fm_output_model_mark_loaded(void)
{
  model_loaded = 1;
  if (config.ym3438 == 0 &&
      (config.ym2612 == FM_OUTPUT_DISCRETE || config.ym2612 == FM_OUTPUT_INTEGRATED))
    effective_model = config.ym2612;
}

int fm_output_model_requested(void) { return requested_model; }
int fm_output_model_effective(void) { return model_loaded ? effective_model : -1; }
int fm_output_model_loaded(void) { return model_loaded; }
int fm_output_model_supported(void)
{
  return config.ym3438 == 0 && (!model_loaded ||
      effective_model == FM_OUTPUT_DISCRETE || effective_model == FM_OUTPUT_INTEGRATED);
}
int fm_output_model_backend(void) { return config.ym3438 ? FM_BACKEND_NUKED : FM_BACKEND_MAME; }
