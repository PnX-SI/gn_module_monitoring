export const leafletDrawOptions: any = {
  position: 'topleft',
  draw: {
    polyline: true,
    circle: false, // Turns off this drawing tool
    circlemarker: false,
    rectangle: false,
    marker: false,
    polygon: true,
  },
  edit: {
    remove: false,
    moveMarker: true
  }
};
