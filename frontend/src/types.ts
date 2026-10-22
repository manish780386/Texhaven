export interface AppConfig {
  sms_enabled: boolean;
  demo_mode: boolean;
  price_per_segment_cents: number;
  currency: string;
  max_segments: number;
  ttl_hours: number;
  turnstile_site_key: string;
  footer_template: string;
  blocked_countries: string[];
}

export type MessageStatus =
  | "awaiting_payment" | "paid" | "queued" | "sent" | "delivered" | "undelivered" | "cancelled" | "expired";

export interface TrackedMessage {
  id: string;
  status: MessageStatus;
  to: string;
  country: string;
  segments: number;
  price_cents: number;
  currency: string;
  created_at: string;
  paid_at: string | null;
  sent_at: string | null;
  delivered_at: string | null;
  expires_at: string;
  content_deleted: boolean;
  refunded: boolean;
  checkout_url?: string;
}

export interface ScanResult {
  score: number;
  level: "low" | "medium" | "high";
  categories: string[];
  reasons: { code: string; label: string; category: string }[];
  urls: { url: string; host: string; flags: string[] }[];
  advice: string[];
  hard_block: boolean;
}
