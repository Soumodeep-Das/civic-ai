import { KeyboardEvent, lazy, Suspense, useRef, useState } from "react";

import { LocationPrecision, LocationSearchResult, searchLocations } from "./api/complaints";

const LocationMap = lazy(() => import("./LocationMap"));

export type LocationSelection = {
  latitude: number;
  longitude: number;
  label: string;
  precision: LocationPrecision;
  details: string;
  confirmed: boolean;
};

type Props = {
  value?: LocationSelection;
  error?: string;
  disabled?: boolean;
  onChange: (selection?: LocationSelection) => void;
};

const LOCATION_TIMEOUT_MS = 30_000;
const LOCATION_MAX_AGE_MS = 5 * 60_000;

export default function LocationPicker({ value, error, disabled, onChange }: Props) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<LocationSearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [searchMessage, setSearchMessage] = useState("");
  const [locating, setLocating] = useState(false);
  const [showMap, setShowMap] = useState(false);
  const searchRequest = useRef(0);
  const locationRequest = useRef(0);

  async function handleSearch() {
    const normalized = query.trim();
    if (normalized.length < 3) {
      setResults([]);
      setSearchMessage("Enter at least 3 characters, such as a locality, PIN code, street or landmark.");
      return;
    }
    const requestId = ++searchRequest.current;
    setSearching(true);
    setSearchMessage("Searching for matching places…");
    try {
      const matches = await searchLocations(normalized);
      if (requestId !== searchRequest.current) return;
      setResults(matches);
      setSearchMessage(matches.length ? `${matches.length} location ${matches.length === 1 ? "match" : "matches"} found.` : "No matching locations found. Try a nearby landmark, street or PIN code.");
    } catch (searchError) {
      if (requestId !== searchRequest.current) return;
      setResults([]);
      setSearchMessage(searchError instanceof Error ? searchError.message : "Location search is temporarily unavailable.");
    } finally {
      if (requestId === searchRequest.current) setSearching(false);
    }
  }

  function chooseResult(result: LocationSearchResult) {
    locationRequest.current += 1;
    setLocating(false);
    onChange({
      latitude: result.latitude,
      longitude: result.longitude,
      label: result.label,
      precision: result.precision,
      details: "",
      confirmed: false,
    });
    setResults([]);
    setSearchMessage("Location selected. Review and confirm it below; map adjustment is optional.");
    setShowMap(false);
  }

  function captureCurrentLocation() {
    const requestId = ++locationRequest.current;
    if (!navigator.geolocation) {
      setSearchMessage("This browser does not support location. Search for the issue location instead.");
      return;
    }
    onChange(undefined);
    setShowMap(false);
    setLocating(true);
    setSearchMessage("Finding your current location…");
    navigator.geolocation.getCurrentPosition(
      (position) => {
        if (requestId !== locationRequest.current) return;
        setLocating(false);
        const { latitude, longitude } = position.coords;
        if (!Number.isFinite(latitude) || !Number.isFinite(longitude) || Math.abs(latitude) > 90 || Math.abs(longitude) > 180) {
          setSearchMessage("Location could not be determined. Search for the issue location instead.");
          return;
        }
        onChange({ latitude, longitude, label: "Current device location", precision: "exact", details: "", confirmed: false });
        setSearchMessage("Current location captured. Review and confirm it below.");
        setShowMap(false);
      },
      (positionError) => {
        if (requestId !== locationRequest.current) return;
        setLocating(false);
        setSearchMessage(positionError.code === 1
          ? "Location access is blocked. Allow it in browser and device settings, or search for the issue location."
          : positionError.code === 3
            ? "Location was not available within 30 seconds. Search for the issue location instead."
            : "Current location could not be determined. Search for the issue location instead.");
      },
      { enableHighAccuracy: false, timeout: LOCATION_TIMEOUT_MS, maximumAge: LOCATION_MAX_AGE_MS },
    );
  }

  function updateMap(coordinates: { latitude: number; longitude: number }) {
    if (!value) return;
    onChange({ ...value, ...coordinates, precision: "exact", confirmed: false });
    setSearchMessage("Pin adjusted. Confirm the revised issue location.");
  }

  function clearSelection() {
    locationRequest.current += 1;
    setLocating(false);
    setShowMap(false);
    onChange(undefined);
    setSearchMessage("Location cleared. Search or use your current location to continue.");
  }

  return (
    <div className="location-picker">
      <div className="location-search" role="search" aria-label="Search for issue location">
        <label htmlFor="location-query">Search locality, PIN code, street or landmark</label>
        <div className="search-row">
          <input
            id="location-query"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Example: Baranagar Municipality or 700036"
            maxLength={200}
            disabled={disabled || searching}
            onKeyDown={(event: KeyboardEvent<HTMLInputElement>) => {
              if (event.key === "Enter") {
                event.preventDefault();
                void handleSearch();
              }
            }}
          />
          <button type="button" className="secondary-button" disabled={disabled || searching} onClick={() => void handleSearch()}>
            {searching ? "Searching…" : "Search"}
          </button>
        </div>
      </div>

      <div className="location-divider"><span>or</span></div>
      <button className="secondary-button location-action" type="button" onClick={captureCurrentLocation} disabled={disabled || locating}>
        {locating ? "Finding location…" : "Use my current location"}
      </button>

      <p className="field-help location-status" aria-live="polite">{searchMessage || "Search for the issue location or use your current position if you are there now."}</p>

      {results.length > 0 && (
        <div className="search-results" aria-label="Location search results">
          {results.map((result) => (
            <button type="button" key={result.provider_id} onClick={() => chooseResult(result)}>
              <strong>{result.label}</strong>
              <span>{result.precision === "broad" ? "Broad area" : "Approximate place"}</span>
            </button>
          ))}
        </div>
      )}

      {value && (
        <div className={`selected-location${value.confirmed ? " confirmed" : ""}`}>
          <div>
            <span className="selection-kicker">{value.confirmed ? "Confirmed issue location" : "Review issue location"}</span>
            <strong>{value.label}</strong>
            <small>{value.precision === "exact" ? "Pin/device point" : value.precision === "broad" ? "Broad area" : "Approximate place"}</small>
          </div>
          <label htmlFor="location-details">Nearby details <span>Optional</span></label>
          <input
            id="location-details"
            value={value.details}
            onChange={(event) => onChange({ ...value, details: event.target.value.slice(0, 500) })}
            placeholder="Example: Opposite the main gate, beside the bus stop"
            maxLength={500}
            disabled={disabled}
          />
          <div className="selection-actions">
            {!value.confirmed && <button type="button" className="confirm-location" onClick={() => onChange({ ...value, confirmed: true })}>Confirm this location</button>}
            <button type="button" className="secondary-button" onClick={() => setShowMap((current) => !current)}>
              {showMap ? "Hide map" : "Adjust precisely on map"}
            </button>
            <button type="button" className="text-button" onClick={clearSelection}>Choose a different location</button>
          </div>
          {showMap && (
            <Suspense fallback={<div className="map-loading" role="status">Loading interactive map…</div>}>
              <LocationMap latitude={value.latitude} longitude={value.longitude} onChange={updateMap} />
            </Suspense>
          )}
        </div>
      )}

      {error && <p className="field-error" id="location-error" role="alert">{error}</p>}
    </div>
  );
}
