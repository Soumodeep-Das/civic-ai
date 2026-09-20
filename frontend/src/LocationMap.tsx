import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import type { LeafletMouseEvent, Map as LeafletMap, Marker as LeafletMarker } from "leaflet";
import "leaflet/dist/leaflet.css";

type Coordinates = { latitude: number; longitude: number };

type Props = Coordinates & {
  onChange: (coordinates: Coordinates) => void;
};

const tileUrl = import.meta.env.VITE_MAP_TILE_URL?.trim() || "https://tile.openstreetmap.org/{z}/{x}/{y}.png";

const issuePin = L.divIcon({
  className: "issue-map-marker",
  html: '<span aria-hidden="true"></span>',
  iconAnchor: [14, 36],
  iconSize: [28, 36],
});

export default function LocationMap({ latitude, longitude, onChange }: Props) {
  const container = useRef<HTMLDivElement>(null);
  const mapRef = useRef<LeafletMap | null>(null);
  const markerRef = useRef<LeafletMarker | null>(null);
  const onChangeRef = useRef(onChange);
  const [mapError, setMapError] = useState("");

  useEffect(() => {
    onChangeRef.current = onChange;
  }, [onChange]);

  useEffect(() => {
    if (!container.current) return;
    const map = L.map(container.current, {
      center: [latitude, longitude],
      zoom: 17,
      zoomControl: true,
    });
    const tiles = L.tileLayer(tileUrl, {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 19,
    }).addTo(map);
    const marker = L.marker([latitude, longitude], {
      draggable: true,
      icon: issuePin,
      keyboard: true,
      title: "Selected issue location",
    }).addTo(map);

    marker.on("dragend", () => {
      const point = marker.getLatLng();
      onChangeRef.current({ latitude: point.lat, longitude: point.lng });
    });
    map.on("click", (event: LeafletMouseEvent) => {
      marker.setLatLng(event.latlng);
      onChangeRef.current({ latitude: event.latlng.lat, longitude: event.latlng.lng });
    });
    tiles.on("tileerror", () => {
      setMapError("The map could not load completely. Your selected location is still available.");
    });
    map.whenReady(() => map.invalidateSize());
    mapRef.current = map;
    markerRef.current = marker;

    return () => {
      map.remove();
      markerRef.current = null;
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    markerRef.current?.setLatLng([latitude, longitude]);
    mapRef.current?.panTo([latitude, longitude]);
  }, [latitude, longitude]);

  return (
    <div className="map-adjuster">
      <div ref={container} className="location-map" aria-label="Map showing the selected issue location" />
      <p className="field-help">On a computer, left-click the exact spot or drag the marker. On a phone, drag and zoom the map, then drag the marker to the issue.</p>
      {mapError && <p className="field-error" role="status">{mapError}</p>}
      <p className="map-attribution">Interactive map rendered with Leaflet. OpenStreetMap attribution appears inside the map.</p>
    </div>
  );
}
