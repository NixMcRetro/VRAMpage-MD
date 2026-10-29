/* Test-only MAME YM2612 model adapter. Never included in shipped builds. */
#include <emscripten/emscripten.h>

static int fm_model_proof_pending;
static int fm_model_proof_active = -1;
static int fm_model_proof_start_count;

int EMSCRIPTEN_KEEPALIVE fm_model_proof_request(double model)
{
  if (model != YM2612_DISCRETE && model != YM2612_INTEGRATED) return 1;
  fm_model_proof_pending = model;
  return 0;
}

int EMSCRIPTEN_KEEPALIVE fm_model_proof_pending_model(void)
{
  return fm_model_proof_pending;
}

int EMSCRIPTEN_KEEPALIVE fm_model_proof_active_model(void)
{
  return fm_model_proof_active;
}

int EMSCRIPTEN_KEEPALIVE fm_model_proof_started(void)
{
  return fm_model_proof_start_count;
}

void fm_model_proof_prepare_start(void)
{
  config.ym2612 = fm_model_proof_pending;
  fm_model_proof_active = fm_model_proof_pending;
  ++fm_model_proof_start_count;
}
