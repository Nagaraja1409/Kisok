export interface CampusBranding {
  instituteName: string;
  shortCode: string;
  logo: string;
  motto: string;
  affiliation: string;
  tickerNotices: string[];
}

export interface HeroConfig {
  videoUrl: string;
  posterUrl: string;
  headline: string;
  subheadline: string;
  ctaText?: string;
  ctaAction?: string;
}

export interface LeadershipMember {
  id: string;
  name: string;
  designation: string;
  image: string;
  quotePreview: string;
  fullQuote: string;
  order?: number;
  active?: boolean;
}

export interface TourFacility {
  id: string;
  title: string;
  category: string;
  image: string;
  description: string;
  highlights?: string[];
  order?: number;
  active?: boolean;
}

export interface GalleryItem {
  id: string;
  title: string;
  shortTitle: string;
  category: string;
  categoryFilter: "academics" | "sports" | "cultural" | "facilities" | "all";
  date: string;
  description: string;
  src: string;
  featured?: boolean;
}

export interface CampusEvent {
  id: string;
  day: string;
  month: string;
  year?: string;
  name: string;
  tag: string;
  tagClass: "academics" | "sports" | "stem" | "fest" | "ptm" | "general";
  venue: string;
  image: string;
  cardClass?: string;
  description?: string;
  time?: string;
}

export interface CampusAchievement {
  id: string;
  title: string;
  badge: string;
  rank: string;
  category: string;
  date: string;
  image: string;
  description?: string;
}

export interface QuickStats {
  studentsCount: string;
  facultyCount: string;
  busCount: string;
  labsCount: string;
  campusArea: string;
}

export interface CampusInfoData {
  branding: CampusBranding;
  hero: HeroConfig;
  quickStats: QuickStats;
  leadership: LeadershipMember[];
  facilities: TourFacility[];
  gallery: GalleryItem[];
  events: CampusEvent[];
  achievements: CampusAchievement[];
  footerMotto?: string;
}
