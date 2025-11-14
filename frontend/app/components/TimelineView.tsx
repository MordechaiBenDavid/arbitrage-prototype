"use client";

import useSWR from "swr";
import { fetchTimeline, type TimelineResponse } from "../../lib/api";

export default function TimelineView({ skuId }: { skuId: number }) {
  const { data, error, isLoading } = useSWR<TimelineResponse>(
    skuId ? ["timeline", skuId] : null,
    ([, id]) => fetchTimeline(id)
  );

  if (isLoading) return <p>Loading timeline…</p>;
  if (error || !data) return <p>Timeline unavailable.</p>;

  return (
    <section className="card">
      <h2>{data.sku.name}</h2>
      <p>Canonical SKU: {data.sku.canonical_sku}</p>
      <p>
        Last seen {data.last_known_location ?? "Unknown"} — {data.inferred_status}
      </p>
      <ul className="timeline">
        {data.events.map((event) => (
          <li key={event.id}>
            <strong>{event.event_type}</strong> ({event.provider})
            <div>{new Date(event.observed_at).toLocaleString()}</div>
          </li>
        ))}
      </ul>
    </section>
  );
}
