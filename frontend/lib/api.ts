const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export type Sku = {
  id: number;
  canonical_sku: string;
  name: string;
  brand?: string;
};

export type TimelineEvent = {
  id: number;
  event_type: string;
  provider: string;
  location?: string;
  observed_at: string;
  payload: Record<string, unknown>;
};

export type TimelineResponse = {
  sku: Sku;
  events: TimelineEvent[];
  inferred_status: string;
  last_known_location?: string;
};

export async function searchSkus(query: string): Promise<Sku[]> {
  const res = await fetch(`${API_BASE}/skus/search?q=${encodeURIComponent(query)}`);
  if (!res.ok) throw new Error("Search failed");
  return res.json();
}

export async function fetchTimeline(id: number): Promise<TimelineResponse> {
  const res = await fetch(`${API_BASE}/skus/${id}/timeline`);
  if (!res.ok) throw new Error("Timeline not found");
  return res.json();
}
