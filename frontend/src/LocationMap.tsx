import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import type { LeafletMouseEvent, Map as LeafletMap, Marker as LeafletMarker } from "leaflet";
import "leaflet/dist/leaflet.css";

type Coordinates = { latitude: number; longitude: number };

type Props = Coordinates & {
  onChange?: (coordinates: Coordinates) => void;
  readOnly?: boolean;
};

const MAPTILER_ATTRIBUTION = '<a href="https://www.maptiler.com/copyright/" target="_blank" rel="noopener">&copy; MapTiler</a> <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">&copy; OpenStreetMap contributors</a>';

export function mapTilerTileUrl(key: string | undefined): string | null {
  const normalized = key?.trim();
  return normalized
    ? `https://api.maptiler.com/maps/streets-v4/{z}/{x}/{y}.png?key=${encodeURIComponent(normalized)}`
    : null;
}

const issuePin = L.divIcon({
  className: "issue-map-marker",
  html: '<span aria-hidden="true"></span>',
  iconAnchor: [14, 36],
  iconSize: [28, 36],
});

export default function LocationMap({ latitude, longitude, onChange, readOnly = false }: Props) {
  const container = useRef<HTMLDivElement>(null);
  const mapRef = useRef<LeafletMap | null>(null);
  const markerRef = useRef<LeafletMarker | null>(null);
  const onChangeRef = useRef(onChange);
  const [mapError, setMapError] = useState("");
  const tileUrl = mapTilerTileUrl(import.meta.env.VITE_MAPTILER_API_KEY);

  useEffect(() => {
    onChangeRef.current = onChange;
  }, [onChange]);

  useEffect(() => {
    if (!container.current || !tileUrl) return;
    const map = L.map(container.current, {
      center: [latitude, longitude],
      zoom: 17,
      zoomControl: true,
    });
    const tiles = L.tileLayer(tileUrl, {
      attribution: MAPTILER_ATTRIBUTION,
      crossOrigin: true,
      minZoom: 1,
      maxZoom: 20,
      tileSize: 512,
      zoomOffset: -1,
    }).addTo(map);
    const marker = L.marker([latitude, longitude], {
      draggable: !readOnly,
      icon: issuePin,
      keyboard: true,
      title: "Selected issue location",
    }).addTo(map);

    marker.on("dragend", () => {
      const point = marker.getLatLng();
      onChangeRef.current?.({ latitude: point.lat, longitude: point.lng });
    });
    if (!readOnly) {
      map.on("click", (event: LeafletMouseEvent) => {
        marker.setLatLng(event.latlng);
        onChangeRef.current?.({ latitude: event.latlng.lat, longitude: event.latlng.lng });
      });
    }
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
  }, [readOnly, tileUrl]);

  useEffect(() => {
    markerRef.current?.setLatLng([latitude, longitude]);
    mapRef.current?.panTo([latitude, longitude]);
  }, [latitude, longitude]);

  return (
    <div className="map-adjuster">
      {tileUrl ? <div className="map-frame">
        <div ref={container} className="location-map" aria-label="Map showing the selected issue location" />
        <a className="maptiler-logo" href="https://www.maptiler.com/" target="_blank" rel="noopener" aria-label="Map tiles by MapTiler">
          <img src="https://api.maptiler.com/resources/logo.svg" alt="MapTiler" />
        </a>
      </div> : <div className="map-loading" role="status">Map tiles are not configured. The selected location is still available.</div>}
      {!readOnly && <p className="field-help">On a computer, left-click the exact spot or drag the marker. On a phone, drag and zoom the map, then drag the marker to the issue.</p>}
      {readOnly && <p className="field-help">Read-only map of the citizen-submitted issue location.</p>}
      {mapError && <p className="field-error" role="status">{mapError}</p>}
      <p className="map-attribution">Interactive map rendered with Leaflet and MapTiler. MapTiler and OpenStreetMap attribution appears inside the map.</p>
    </div>
  );
}
