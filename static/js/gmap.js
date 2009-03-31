function LoadMapSearchControl() {
  var options = {
    zoomControl : GSmapSearchControl.ZOOM_CONTROL_ENABLE_ALL,
    title : document.getElementById('screen_name').innerHTML,
    url : document.getElementById('user_url').innerHTML,
    idleMapZoom : GSmapSearchControl.ACTIVE_MAP_ZOOM,
    activeMapZoom : GSmapSearchControl.ACTIVE_MAP_ZOOM
  }

  new GSmapSearchControl(
    document.getElementById('mapsearch'),
    document.getElementById('user_location').innerHTML,
    options);
}

GSearch.setOnLoadCallback(LoadMapSearchControl);