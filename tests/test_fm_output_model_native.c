#include <assert.h>
#include <math.h>
#include "shared.h"
#include "fm_output_model_runtime.h"

struct test_config config;

int main(void)
{
  int invalid[] = {-1, 2, 3};
  unsigned i;
  config.ym2612 = 0;
  config.ym3438 = 0;
  assert(fm_output_model_requested() == 0);
  assert(fm_output_model_effective() == -1);
  assert(fm_output_model_loaded() == 0);
  assert(fm_output_model_supported() == 1);
  assert(fm_output_model_backend() == 0);
  for (i = 0; i < sizeof(invalid) / sizeof(invalid[0]); ++i)
    assert(set_fm_output_model_request(invalid[i]) == 1);
  assert(set_fm_output_model_request(0.5) == 1);
  assert(set_fm_output_model_request(NAN) == 1);
  assert(set_fm_output_model_request(INFINITY) == 1);
  assert(fm_output_model_requested() == 0);
  assert(set_fm_output_model_request(1.0) == 0);
  assert(fm_output_model_requested() == 1);
  assert(fm_output_model_effective() == -1);
  fm_output_model_prepare_start();
  assert(config.ym2612 == 1);
  assert(fm_output_model_loaded() == 0);
  assert(fm_output_model_effective() == -1);
  fm_output_model_mark_loaded();
  assert(fm_output_model_effective() == 1);
  assert(set_fm_output_model_request(0) == 0);
  assert(fm_output_model_requested() == 0);
  assert(fm_output_model_effective() == 1);
  config.ym3438 = 1;
  assert(fm_output_model_supported() == 0);
  assert(fm_output_model_backend() == 1);
  assert(set_fm_output_model_request(1) == 2);
  assert(fm_output_model_requested() == 0);
  config.ym3438 = 0;
  fm_output_model_prepare_start();
  config.ym2612 = 2;
  fm_output_model_mark_loaded();
  assert(fm_output_model_backend() == 0);
  assert(fm_output_model_supported() == 0);
  assert(fm_output_model_effective() == -1);
  config.ym2612 = 0;
  fm_output_model_prepare_start();
  fm_output_model_mark_loaded();
  assert(fm_output_model_effective() == 0);
  return 0;
}
