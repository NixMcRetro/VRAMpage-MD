/* Public guard for the optional Z80 RAM write-address pair. */
(function installZ80RamBridgeApi(Module) {
  var previous = Module["postRun"];
  var callbacks = Array.isArray(previous) ? previous.slice() : (typeof previous === "function" ? [previous] : []);
  function install() {
    var nativeSetter = Module["_set_z80_ram_bridge_c"];
    if (typeof nativeSetter !== "function") throw new Error("Z80 RAM bridge runtime export is missing");
    delete Module["_set_z80_ram_bridge_c"];
    Module["_set_z80_ram_bridge"] = function () {
      if (arguments.length !== 3) return 1;
      for (var i = 0; i < 3; i++) if (typeof arguments[i] !== "number" || !Number.isInteger(arguments[i])) return 1;
      return nativeSetter.apply(Module, arguments);
    };
    function count(name) { var n = Module[name](); return String(typeof n === "bigint" ? BigInt.asUintN(64, n) : n); }
    Module["_get_z80_ram_ref"] = function () { return Module["_get_z80_ram_bridge_ram_ref"](); };
    Module["_get_z80_ram_bridge_state"] = function () {
      var p = Module["_get_z80_ram_bridge_version"](), h = Module["HEAPU8"], v = "";
      while (h[p]) v += String.fromCharCode(h[p++]);
      var supported = !!Module["_get_z80_ram_bridge_supported"](), configured = !!Module["_get_z80_ram_bridge_enabled"]();
      return {modelVersion:v,supported:supported,configured:configured,effective:supported&&configured,
        reason:!supported?"unsupported-system":(configured?"active":"disabled"),
        bridgeA:Module["_get_z80_ram_bridge_a"](),bridgeB:Module["_get_z80_ram_bridge_b"](),
        ramWrites:count("_get_z80_ram_bridge_ram_writes"),changedAddresses:count("_get_z80_ram_bridge_changed_addresses"),
        z80Writes:count("_get_z80_ram_bridge_z80_writes"),m68kWrites:count("_get_z80_ram_bridge_m68k_writes"),
        activationFrame:Module["_get_z80_ram_bridge_activation_frame"]() >>> 0};
    };
  }
  Module["postRun"] = [install].concat(callbacks);
})(Module);
