/* Build-owned public API guard, linked only by the opt-in runtime build. */
(function installVramModelApi(Module) {
  var previous = Module["postRun"];
  var callbacks = Array.isArray(previous) ? previous.slice() :
    (typeof previous === "function" ? [previous] : []);

  function install() {
    var nativeSetter = Module["_set_vram_fault_model_c"];
    if (typeof nativeSetter !== "function") {
      throw new Error("VRAM model runtime export is missing");
    }
    delete Module["_set_vram_fault_model_c"];
    Module["_set_vram_fault_model"] = function () {
      if (arguments.length !== 4) return 1;
      for (var i = 0; i < 4; ++i) {
        if (typeof arguments[i] !== "number" || !Number.isInteger(arguments[i])) {
          return 1;
        }
      }
      return nativeSetter.apply(Module, arguments);
    };
    Module["_get_vram_fault_model_state"] = function () {
      var id = Module["_get_vram_fault_model_id"]();
      var versionPointer = Module["_get_vram_fault_model_version"]();
      var bytes = Module["HEAPU8"];
      var version = "";
      while (bytes[versionPointer]) version += String.fromCharCode(bytes[versionPointer++]);
      var reasonCode = Module["_get_vram_fault_model_reason"]();
      var counterNames = [
        ["logicalByteReads", "logical_byte_reads"],
        ["logicalByteWrites", "logical_byte_writes"],
        ["redirectedByteReads", "redirected_byte_reads"],
        ["redirectedByteWrites", "redirected_byte_writes"],
        ["changedPhysicalByteWrites", "changed_physical_byte_writes"]
      ];
      var counters = counterNames.map(function (entry) {
        return Number(Module["_get_vram_fault_" + entry[1]]());
      });
      return {
        modelId: id,
        modelVersion: version,
        supportedModelsMask: Module["_get_vram_supported_model_mask"](),
        effective: Module["_get_vram_fault_model_effective"]() !== 0,
        reason: ["none", "no-fault", "unsupported-mode", "off"][reasonCode] || "none",
        mask: Module["_get_vram_fault_model_mask"](),
        bridgeA: Module["_get_vram_fault_model_bridge_a"](),
        bridgeB: Module["_get_vram_fault_model_bridge_b"](),
        lastFrameCounts: {
          logicalByteReads: counters[0],
          logicalByteWrites: counters[1],
          redirectedByteReads: counters[2],
          redirectedByteWrites: counters[3],
          changedPhysicalByteWrites: counters[4]
        }
      };
    };
  }

  Module["postRun"] = [install].concat(callbacks);
})(Module);
