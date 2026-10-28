/* Public requested/effective region API for the opt-in runtime build. */
(function installRegionProfileApi(Module) {
  var previous = Module["postRun"];
  var callbacks = Array.isArray(previous) ? previous.slice() :
    (typeof previous === "function" ? [previous] : []);

  function install() {
    var setter = Module["_set_region_request_c"];
    if (typeof setter !== "function") throw new Error("Region profile runtime export is missing");
    delete Module["_set_region_request_c"];
    Module["_set_region_request"] = function (id) {
      if (arguments.length !== 1 || typeof id !== "number" || !Number.isInteger(id) || id < 0 || id > 4) return 1;
      return setter(id);
    };
    Module["_get_region_state"] = function () {
      var loaded = Module["_get_region_loaded_c"]() !== 0;
      var nullable = function (name) { return loaded ? Module[name]() : null; };
      return {
        schemaVersion: 1,
        available: true,
        loaded: loaded,
        requestedRegion: Module["_get_region_requested_c"](),
        regionCode: nullable("_get_region_code_c"),
        pal: loaded ? Module["_get_region_pal_c"]() !== 0 : null,
        masterClock: nullable("_get_region_master_clock_c"),
        frameRate: nullable("_get_region_frame_rate_c"),
        linesPerFrame: nullable("_get_region_lines_per_frame_c"),
        width: nullable("_get_region_width_c"),
        height: nullable("_get_region_height_c"),
        interlaced: loaded ? Module["_get_region_interlaced_c"]() !== 0 : null
      };
    };
  }

  Module["postRun"] = [install].concat(callbacks);
})(Module);
