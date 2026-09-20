import { useEffect, useRef, useState } from "react";
import * as maplibregl from "maplibre-gl";
import type { Map, MapMouseEvent, Marker } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

type Coordinates = { latitude: number; longitude: number };

type Props = Coordinates & {
  onChange: (coordinates: Coordinates) => void;
};

const styleUrl = import.meta.env.VITE_MAP_STYLE_URL?.trim() || "https://demotiles.maplibre.org/style.json";
const NUDGE_DEGREES = 0.0001;

export default function LocationMap({ latitude, longitude, onChange }: Props) {
  const container = useRef<HTMLDivElement>(null);
  const mapRef = useRef<Map | null>(null);
  const markerRef = useRef<Marker | null>(null);
  const onChangeRef = useRef(onChange);
  const [mapError, setMapError] = useState("");

  useEffect(() => {
    onChangeRef.current = onChange;
  }, [onChange]);

  useEffect(() => {
    if (!container.current) return;
    const map = new maplibregl.Map({
      container: container.current,
      style: styleUrl,
      center: [longitude, latitude],
      zoom: 16,
    });
    const marker = new maplibregl.Marker({ draggable: true })
      .setLngLat([longitude, latitude])
      .addTo(map);

    marker.on("dragend", () => {
      const point = marker.getLngLat();
      onChangeRef.current({ latitude: point.lat, longitude: point.lng });
    });
    map.on("click", (event: MapMouseEvent) => {
      marker.setLngLat(event.lngLat);
      onChangeRef.current({ latitude: event.lngLat.lat, longitude: event.lngLat.lng });
    });
    map.on("error", () => {
      setMapError("The map could not load completely. Your selected location is still available.");
    });
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
    mapRef.current = map;
    markerRef.current = marker;

    return () => {
      marker.remove();
      map.remove();
      markerRef.current = null;
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    markerRef.current?.setLngLat([longitude, latitude]);
    mapRef.current?.easeTo({ center: [longitude, latitude] });
  }, [latitude, longitude]);

  function nudge(latitudeDelta: number, longitudeDelta: number) {
    onChange({
      latitude: Math.max(-90, Math.min(90, latitude + latitudeDelta)),
      longitude: Math.max(-180, Math.min(180, longitude + longitudeDelta)),
    });
  }

  return (
    <div className="map-adjuster">
      <div ref={container} className="location-map" aria-label="Map showing the selected issue location" />
      <p className="field-help">Click the map or drag the marker. Keyboard users can move it with the controls below.</p>
      <div className="map-nudge-controls" aria-label="Move issue-location pin">
        <button type="button" onClick={() => nudge(NUDGE_DEGREES, 0)}>Move north</button>
        <button type="button" onClick={() => nudge(0, -NUDGE_DEGREES)}>Move west</button>
        <button type="button" onClick={() => nudge(0, NUDGE_DEGREES)}>Move east</button>
        <button type="button" onClick={() => nudge(-NUDGE_DEGREES, 0)}>Move south</button>
      </div>
      {mapError && <p className="field-error" role="status">{mapError}</p>}
      <p className="map-attribution">Map rendered with MapLibre. Map data/style attribution appears inside the map.</p>
    </div>
  );
}
