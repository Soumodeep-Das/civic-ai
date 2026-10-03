import { mapTilerTileUrl } from "./LocationMap";

test("builds a MapTiler Streets raster URL from a browser-public key", () => {
  expect(mapTilerTileUrl(" public/key ")).toBe(
    "https://api.maptiler.com/maps/streets-v4/{z}/{x}/{y}.png?key=public%2Fkey",
  );
});

test("does not fall back to an anonymous tile provider without a public key", () => {
  expect(mapTilerTileUrl(undefined)).toBeNull();
  expect(mapTilerTileUrl("   ")).toBeNull();
});
