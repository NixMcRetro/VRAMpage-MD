/* Public integer-checked API for the optional Work RAM data-line mask. */
(function installWorkRamDataMaskApi(Module) {
  var previous = Module["postRun"];
  var callbacks = Array.isArray(previous) ? previous.slice() :
    (typeof previous === "function" ? [previous] : []);

  function install() {
    var nativeSetter = Module["_set_logic_data_mask_c"];
    var nativeGetter = Module["_get_logic_data_mask_c"];
    if (typeof nativeSetter !== "function" || typeof nativeGetter !== "function") {
      throw new Error("Work RAM data-mask runtime export is missing");
    }
    delete Module["_set_logic_data_mask_c"];
    delete Module["_get_logic_data_mask_c"];
    Module["_set_logic_data_mask"] = function () {
      if (arguments.length !== 2) return 5;
      for (var i = 0; i < 2; ++i) {
        if (typeof arguments[i] !== "number" || !Number.isInteger(arguments[i])) return 5;
      }
      return nativeSetter.apply(Module, arguments);
    };
    Module["_get_logic_data_mask"] = function () {
      return nativeGetter.call(Module) >>> 0;
    };
  }

  Module["postRun"] = [install].concat(callbacks);
})(Module);
