export interface MediaSource {
  media_id: number;
  name: string;
  url?: string;
  country?: string;
  language?: string;
}

export interface CollectionSummary {
  tags_id: number;
  label: string;
  description?: string;
}

const API_BASE_URL =
  import.meta.env.VITE_MEDIACLOUD_API_BASE_URL ?? "https://api.mediacloud.org/api/v2";

const API_KEY = import.meta.env.VITE_MEDIACLOUD_API_KEY ?? "";

async function request<T>(path: string, params: Record<string, string | number>): Promise<T> {
  const url = new URL(API_BASE_URL + path);
  Object.entries(params).forEach(([key, value]) => {
    url.searchParams.set(key, String(value));
  });

  if (API_KEY) {
    url.searchParams.set("key", API_KEY);
  }

  const res = await fetch(url.toString());
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${res.statusText}`);
  }
  return (await res.json()) as T;
}

// Fetch a single collection summary (label/description) by ID
export async function fetchCollection(collectionId: number): Promise<CollectionSummary | null> {
  type CollectionResponse = { collections: CollectionSummary[] };

  const data = await request<CollectionResponse>("/collections/list", {
    tags_id: collectionId,
  });

  return data.collections?.[0] ?? null;
}

// Fetch media sources in a collection.
// This uses the Media Cloud media list endpoint filtered by collection id.
export async function fetchCollectionMedia(collectionId: number): Promise<MediaSource[]> {
  type MediaResponse = { media: MediaSource[] };

  const data = await request<MediaResponse>("/media/list", {
    tags_id_media: collectionId,
    rows: 500,
    offset: 0,
  });

  return data.media ?? [];
}

