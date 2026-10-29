/* Requested/effective MAME FM output model API for the runtime core. */
(function installFmOutputModelApi(Module) {
  var previous = Module["postRun"];
  var callbacks = Array.isArray(previous) ? previous.slice() :
    (typeof previous === "function" ? [previous] : []);

  function install() {
    var setter = Module["_set_fm_output_model_request_c"];
    if (typeof setter !== "function") throw new Error("FM output model runtime export is missing");
    delete Module["_set_fm_output_model_request_c"];
    Module["_set_fm_output_model_request"] = function (id) {
      if (arguments.length !== 1 || typeof id !== "number" || !Number.isInteger(id) || id < 0 || id > 1) return 1;
      return setter(id);
    };
    Module["_get_fm_output_model_state"] = function () {
      var requested = Module["_get_fm_output_model_requested_c"]();
      var loaded = Module["_get_fm_output_model_loaded_c"]() !== 0;
      var supported = Module["_get_fm_output_model_supported_c"]() !== 0;
      var backendId = Module["_get_fm_output_model_backend_c"]();
      var effective = Module["_get_fm_output_model_effective_c"]();
      if ((requested !== 0 && requested !== 1) || (backendId !== 0 && backendId !== 1) ||
          loaded && supported && effective !== 0 && effective !== 1 ||
          (!loaded || !supported) && effective !== -1) return null;
      return {
        schemaVersion: 1,
        available: true,
        supported: supported,
        loaded: loaded,
        requestedModel: requested === 0 ? "discrete" : "integrated",
        effectiveModel: loaded && supported ? (effective === 0 ? "discrete" : "integrated") : null,
        backend: loaded ? (backendId === 0 ? "mame-opn2" : "nuked-opn2") : null,
        reason: !supported ? (backendId === 1 ? "unsupported-backend" : "unsupported-model") : loaded ? "none" : "not-started"
      };
    };
  }

  Module["postRun"] = [install].concat(callbacks);
})(Module);
