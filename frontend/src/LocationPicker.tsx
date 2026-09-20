import { KeyboardEvent, lazy, Suspense, useEffect, useRef, useState } from "react";

import {
  getLocationCapabilities, LocationPrecision, LocationSearchResult, LocationSource,
  reverseLocation, searchLocations,
} from "./api/complaints";

const LocationMap = lazy(() => import("./LocationMap"));

export type LocationSelection = {
  latitude: number;
  longitude: number;
  label: string;
  precision: LocationPrecision;
  details: string;
  source: LocationSource;
  accuracyMeters?: number;
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
const AUTOCOMPLETE_DELAY_MS = 350;

export default function LocationPicker({ value, error, disabled, onChange }: Props) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<LocationSearchResult[]>([]);
  const [activeResult, setActiveResult] = useState(-1);
  const [searching, setSearching] = useState(false);
  const [resolvingAddress, setResolvingAddress] = useState(false);
  const [searchMessage, setSearchMessage] = useState("");
  const [locating, setLocating] = useState(false);
  const [autocomplete, setAutocomplete] = useState(false);
  const searchRequest = useRef(0);
  const reverseRequest = useRef(0);
  const locationRequest = useRef(0);

  useEffect(() => {
    let active = true;
    void getLocationCapabilities()
      .then((capabilities) => {
        if (active) setAutocomplete(Boolean(capabilities.autocomplete));
      })
      .catch(() => {
        if (active) setAutocomplete(false);
      });
    return () => { active = false; };
  }, []);

  async function runSearch(searchQuery: string, quiet = false) {
    const normalized = searchQuery.trim();
    if (normalized.length < 3) {
      searchRequest.current += 1;
      setResults([]);
      setActiveResult(-1);
      if (!quiet) setSearchMessage("Enter at least 3 characters, such as a locality, PIN code, street or landmark.");
      return;
    }
    const requestId = ++searchRequest.current;
    setSearching(true);
    if (!quiet) setSearchMessage("Searching for matching places…");
    try {
      const matches = await searchLocations(normalized);
      if (requestId !== searchRequest.current) return;
      setResults(matches);
      setActiveResult(matches.length ? 0 : -1);
      setSearchMessage(matches.length
        ? `${matches.length} suggestion${matches.length === 1 ? "" : "s"} found. Choose the closest match.`
        : "No matching locations found. Try a nearby landmark, street or PIN code.");
    } catch (searchError) {
      if (requestId !== searchRequest.current) return;
      setResults([]);
      setActiveResult(-1);
      setSearchMessage(searchError instanceof Error ? searchError.message : "Location search is temporarily unavailable.");
    } finally {
      if (requestId === searchRequest.current) setSearching(false);
    }
  }

  useEffect(() => {
    if (!autocomplete || query.trim().length < 3) return;
    const timer = window.setTimeout(() => void runSearch(query, true), AUTOCOMPLETE_DELAY_MS);
    return () => window.clearTimeout(timer);
  }, [query, autocomplete]);

  function chooseResult(result: LocationSearchResult) {
    searchRequest.current += 1;
    locationRequest.current += 1;
    reverseRequest.current += 1;
    setSearching(false);
    setLocating(false);
    onChange({
      latitude: result.latitude,
      longitude: result.longitude,
      label: result.label,
      precision: result.precision,
      details: "",
      source: "search",
      confirmed: false,
    });
    setResults([]);
    setActiveResult(-1);
    setSearchMessage("Location selected. Check the pin on the street map, then confirm it.");
  }

  async function updateAddress(selection: LocationSelection) {
    const requestId = ++reverseRequest.current;
    setResolvingAddress(true);
    try {
      const result = await reverseLocation(selection.latitude, selection.longitude);
      if (requestId !== reverseRequest.current) return;
      onChange({ ...selection, label: result?.label || selection.label });
      setSearchMessage(result
        ? "Pin adjusted and address updated. Review the point, then confirm it."
        : "Pin adjusted. No street address was found; review the point, then confirm it.");
    } catch {
      if (requestId !== reverseRequest.current) return;
      onChange(selection);
      setSearchMessage("Pin adjusted, but the address could not be refreshed. The selected point is still available for review.");
    } finally {
      if (requestId === reverseRequest.current) setResolvingAddress(false);
    }
  }

  function captureCurrentLocation() {
    const requestId = ++locationRequest.current;
    searchRequest.current += 1;
    setSearching(false);
    setResults([]);
    setActiveResult(-1);
    if (!navigator.geolocation) {
      setSearchMessage("This browser does not support location. Search for the issue location instead.");
      return;
    }
    reverseRequest.current += 1;
    onChange(undefined);
    setLocating(true);
    setSearchMessage("Finding your current location…");
    navigator.geolocation.getCurrentPosition(
      (position) => {
        if (requestId !== locationRequest.current) return;
        setLocating(false);
        const { latitude, longitude, accuracy } = position.coords;
        if (!Number.isFinite(latitude) || !Number.isFinite(longitude) || Math.abs(latitude) > 90 || Math.abs(longitude) > 180) {
          setSearchMessage("Location could not be determined. Search for the issue location instead.");
          return;
        }
        const selection: LocationSelection = {
          latitude,
          longitude,
          label: "Current device location",
          precision: "exact",
          details: "",
          source: "device",
          accuracyMeters: Number.isFinite(accuracy) && accuracy >= 0 && accuracy <= 100_000 ? accuracy : undefined,
          confirmed: false,
        };
        onChange(selection);
        setSearchMessage("Current location captured. Checking the nearest address…");
        void updateAddress(selection);
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
      { enableHighAccuracy: true, timeout: LOCATION_TIMEOUT_MS, maximumAge: LOCATION_MAX_AGE_MS },
    );
  }

  function updateMap(coordinates: { latitude: number; longitude: number }) {
    if (!value) return;
    const selection: LocationSelection = {
      ...value,
      ...coordinates,
      precision: "exact",
      source: "map",
      accuracyMeters: undefined,
      confirmed: false,
    };
    onChange(selection);
    setSearchMessage("Pin adjusted. Updating the nearest address…");
    void updateAddress(selection);
  }

  function clearSelection() {
    searchRequest.current += 1;
    locationRequest.current += 1;
    reverseRequest.current += 1;
    setSearching(false);
    setLocating(false);
    setResolvingAddress(false);
    onChange(undefined);
    setSearchMessage("Location cleared. Search or use your current location to continue.");
  }

  function handleSearchKey(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "ArrowDown" && results.length) {
      event.preventDefault();
      setActiveResult((current) => (current + 1) % results.length);
    } else if (event.key === "ArrowUp" && results.length) {
      event.preventDefault();
      setActiveResult((current) => (current <= 0 ? results.length - 1 : current - 1));
    } else if (event.key === "Enter") {
      event.preventDefault();
      if (activeResult >= 0 && results[activeResult]) chooseResult(results[activeResult]);
      else void runSearch(query);
    } else if (event.key === "Escape") {
      setResults([]);
      setActiveResult(-1);
    }
  }

  return (
    <div className="location-picker">
      <div className="location-search" role="search" aria-label="Search for issue location">
        <label htmlFor="location-query">Search locality, PIN code, street or landmark</label>
        <div className="search-row">
          <input
            id="location-query"
            role="combobox"
            aria-autocomplete={autocomplete ? "list" : "none"}
            aria-expanded={results.length > 0}
            aria-controls="location-suggestions"
            aria-activedescendant={activeResult >= 0 ? `location-result-${activeResult}` : undefined}
            value={query}
            onChange={(event) => {
              searchRequest.current += 1;
              setSearching(false);
              setQuery(event.target.value);
              setActiveResult(-1);
              setResults([]);
            }}
            placeholder="Example: BT Road, Baranagar or 700036"
            maxLength={200}
            disabled={disabled}
            onKeyDown={handleSearchKey}
          />
          <button type="button" className="secondary-button" disabled={disabled || searching} onClick={() => void runSearch(query)}>
            {searching ? "Searching…" : "Search"}
          </button>
        </div>
        <p className="search-mode">{autocomplete ? "Suggestions update while you type." : "Press Search to look up this place."}</p>
      </div>

      {results.length > 0 && (
        <div className="search-results" id="location-suggestions" role="listbox" aria-label="Location suggestions">
          {results.map((result, index) => (
            <button
              type="button"
              role="option"
              aria-selected={index === activeResult}
              id={`location-result-${index}`}
              key={result.provider_id}
              className={index === activeResult ? "active" : ""}
              onMouseEnter={() => setActiveResult(index)}
              onClick={() => chooseResult(result)}
            >
              <strong>{result.label}</strong>
              <span>{result.precision === "broad" ? "Broad area" : "Address or place"}</span>
            </button>
          ))}
        </div>
      )}

      <div className="location-divider"><span>or</span></div>
      <button className="secondary-button location-action" type="button" onClick={captureCurrentLocation} disabled={disabled || locating}>
        {locating ? "Finding location…" : "Use my current location"}
      </button>

      <p className="field-help location-status" aria-live="polite">{searchMessage || "Search for the issue location or use your current position if you are there now."}</p>

      {value && (
        <div className={`selected-location${value.confirmed ? " confirmed" : ""}`}>
          <div>
            <span className="selection-kicker">{value.confirmed ? "Confirmed issue location" : "Review issue location"}</span>
            <strong>{value.label}</strong>
            <small>
              {resolvingAddress ? "Updating nearest address…" : value.precision === "exact" ? "User-confirmed point" : value.precision === "broad" ? "Broad area—refine the pin" : "Suggested point—check the pin"}
            </small>
          </div>

          <Suspense fallback={<div className="map-loading" role="status">Loading detailed street map…</div>}>
            <LocationMap latitude={value.latitude} longitude={value.longitude} onChange={updateMap} />
          </Suspense>

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
            {!value.confirmed && (
              <button type="button" className="confirm-location" disabled={resolvingAddress} onClick={() => onChange({ ...value, confirmed: true })}>
                {resolvingAddress ? "Checking address…" : "Confirm this location"}
              </button>
            )}
            <button type="button" className="text-button" onClick={clearSelection}>Choose a different location</button>
          </div>
        </div>
      )}

      {error && <p className="field-error" id="location-error" role="alert">{error}</p>}
    </div>
  );
}
