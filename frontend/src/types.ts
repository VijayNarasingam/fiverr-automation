export interface Gig {
  id: number;
  title: string;
  category: string;
  status: string;
  gig_url?: string | null;
}

export interface Order {
  id: number;
  fiverr_order_id: string | null;
  gig_id: number | null;
  buyer_username: string | null;
  amount: number;
  status: string;
}

export interface Message {
  id: number;
  order_id: number | null;
  direction: string;
  content: string;
  is_auto_replied: boolean;
}

export interface AnalyticsOverview {
  gigs: number;
  orders: number;
  revenue_cents: number;
}

export interface GigPerformance {
  gig_id: number;
  title: string;
  order_count: number;
}

export interface AbTestResult {
  gig_id: number;
  winner: string | null;
  confidence: number;
  note: string;
}

export interface SendMessageInput {
  direction: string;
  content: string;
  order_id?: number | null;
}
