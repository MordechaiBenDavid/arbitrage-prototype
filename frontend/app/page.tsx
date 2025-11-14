"use client";

import { useState } from "react";
import useSWR from "swr";
import { fetchTimeline, searchSkus, type Sku, type TimelineResponse } from "../lib/api";

export default function HomePage() {
  const [query, setQuery] = useState("");
  const [selectedSku, setSelectedSku] = useState<Sku | null>(null);

  const { data: results, isLoading, error } = useSWR(
    query.length >= 3 ? ["search", query] : null,
    ([, q]) => searchSkus(q)
  );

  const { data: timeline } = useSWR<TimelineResponse>(
    selectedSku ? ["timeline", selectedSku.id] : null,
    ([, id]) => fetchTimeline(id)
  );

  return (
    <section>
      <header>
        <h1>SKU Lifecycle Tracker</h1>
        <p>Search a product identifier and view its latest status across providers.</p>
      </header>

      <div style={{ display: "flex", gap: "1rem", marginTop: "1rem" }}>
        <input
          placeholder="Search by canonical SKU / name"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
        <button disabled>Advanced filters</button>
      </div>

      {error && <p style={{ color: "#ff8080" }}>Search failed. Try again.</p>}

      {query.length >= 3 && (
        <div className="card">
          <h2>Matches</h2>
          {isLoading && <p>Loading…</p>}
          {!isLoading && results && results.length === 0 && <p>No SKUs found.</p>}
          <ul>
            {results?.map((sku) => (
              <li key={sku.id} style={{ marginBottom: "0.75rem" }}>
                <button
                  style={{ width: "100%" }}
                  onClick={() => setSelectedSku(sku)}
                >
                  <strong>{sku.canonical_sku}</strong> — {sku.name}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {timeline && selectedSku && (
        <div className="card">
          <h2>{selectedSku.name}</h2>
          <p>
            Latest status: <strong>{timeline.inferred_status}</strong>
          </p>
          <p>Last known location: {timeline.last_known_location ?? "Unknown"}</p>
          <h3>Timeline</h3>
          <ul className="timeline">
            {timeline.events.map((event) => (
              <li key={event.id}>
                <strong>{event.event_type}</strong> via {event.provider}
                <div>{new Date(event.observed_at).toLocaleString()}</div>
                {event.location && <div>Location: {event.location}</div>}
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
