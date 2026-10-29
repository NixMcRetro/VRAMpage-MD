#ifndef VRAMPAGE_FM_OUTPUT_MODEL_RUNTIME_H
#define VRAMPAGE_FM_OUTPUT_MODEL_RUNTIME_H

int set_fm_output_model_request(double model);
void fm_output_model_prepare_start(void);
void fm_output_model_mark_loaded(void);
int fm_output_model_requested(void);
int fm_output_model_effective(void);
int fm_output_model_loaded(void);
int fm_output_model_supported(void);
int fm_output_model_backend(void);

#endif
