/* Build-owned public guard for the optional PSG input bridge. */
(function installPsgDataBridgeApi(Module) {
  var previous = Module["postRun"];
  var callbacks = Array.isArray(previous) ? previous.slice() :
    (typeof previous === "function" ? [previous] : []);

  function install() {
    var nativeSetter = Module["_set_psg_data_bridge_c"];
    var nativeMaskSetter = Module["_set_psg_data_mask_c"];
    if (typeof nativeSetter !== "function" || typeof nativeMaskSetter !== "function") {
      throw new Error("PSG data bridge runtime export is missing");
    }
    delete Module["_set_psg_data_bridge_c"];
    delete Module["_set_psg_data_mask_c"];
    Module["_set_psg_data_bridge"] = function () {
      if (arguments.length !== 3) return 1;
      for (var i = 0; i < 3; ++i) {
        if (typeof arguments[i] !== "number" || !Number.isInteger(arguments[i])) {
          return 1;
        }
      }
      return nativeSetter.apply(Module, arguments);
    };
    Module["_set_psg_data_mask"] = function () {
      if (arguments.length !== 1 || typeof arguments[0] !== "number" ||
          !Number.isInteger(arguments[0])) return 1;
      return nativeMaskSetter.call(Module, arguments[0]);
    };
    function unsignedCounterString(value) {
      return String(typeof value === "bigint" ? BigInt.asUintN(64, value) : value);
    }
    Module["_get_psg_data_bridge_state"] = function () {
      var versionPointer = Module["_get_psg_data_bridge_version"]();
      var heap = Module["HEAPU8"];
      var version = "";
      while (heap[versionPointer]) version += String.fromCharCode(heap[versionPointer++]);
      var supported = Module["_get_psg_data_bridge_supported"]() !== 0;
      var enabled = Module["_get_psg_data_bridge_enabled"]() !== 0;
      return {
        modelVersion: version,
        supported: supported,
        configured: enabled,
        effective: supported && enabled,
        reason: !supported ? "unsupported-system" : (enabled ? "active" : "disabled"),
        bridgeA: Module["_get_psg_data_bridge_a"](),
        bridgeB: Module["_get_psg_data_bridge_b"](),
        dataMask: Module["_get_psg_data_mask"](),
        inputWrites: unsignedCounterString(Module["_get_psg_data_bridge_input_writes"]()),
        changedWrites: unsignedCounterString(Module["_get_psg_data_bridge_changed_writes"]())
      };
    };
  }

  Module["postRun"] = [install].concat(callbacks);
})(Module);
