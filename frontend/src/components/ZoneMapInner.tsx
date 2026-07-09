// frontend/src/components/ZoneMapInner.tsx
// Actual Leaflet map. Only ever loaded client-side via next/dynamic in
// ZoneMap.tsx (ssr: false) — Leaflet touches `window` at import time.

"use client";

import { useMemo } from "react";
import { CircleMarker, MapContainer, Popup, TileLayer } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import type { AnalysisResult, Zone } from "@/lib/api";

interface Props {
  analysis: AnalysisResult;
}

type GeoZone = Zone & { centroid_lat: number; centroid_lng: number };

function rankColor(rank: number) {
  if (rank === 1) return "#ef4444";
  if (rank === 2) return "#f97316";
  if (rank === 3) return "#eab308";
  return "#22c55e";
}

export default function ZoneMapInner({ analysis }: Props) {
  const geoZones = useMemo(
    () =>
      analysis.zones.filter(
        (zone): zone is GeoZone =>
          typeof zone.centroid_lat === "number" &&
          typeof zone.centroid_lng === "number"
      ),
    [analysis.zones]
  );

  if (geoZones.length === 0) return null;

  const center: [number, number] = [
    geoZones.reduce((sum, z) => sum + z.centroid_lat, 0) / geoZones.length,
    geoZones.reduce((sum, z) => sum + z.centroid_lng, 0) / geoZones.length,
  ];

  return (
    <MapContainer
      center={center}
      zoom={16}
      scrollWheelZoom={false}
      className="h-full w-full"
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      {geoZones.map((zone) => (
        <CircleMarker
          key={zone.rank}
          center={[zone.centroid_lat, zone.centroid_lng]}
          radius={zone.rank <= 3 ? 12 : 8}
          pathOptions={{
            color: rankColor(zone.rank),
            fillColor: rankColor(zone.rank),
            fillOpacity: 0.55,
            weight: 2,
          }}
        >
          <Popup>
            <div className="text-xs">
              <p className="font-bold">Zone {zone.rank}</p>
              <p>
                Destroyed: {zone.building_counts.destroyed} · Major:{" "}
                {zone.building_counts.major} buildings
              </p>
              <p>Priority score: {zone.priority_score}</p>
            </div>
          </Popup>
        </CircleMarker>
      ))}
    </MapContainer>
  );
}
