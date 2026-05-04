// =============================================================================
// TYPE DEFINITIONS - Shared TypeScript Types
// =============================================================================

// -----------------------------------------------------------------------------
// User Types
// -----------------------------------------------------------------------------
export type AccountType = 'admin' | 'special' | 'normal';
export type SubscriptionStatus = 'free' | 'basic' | 'premium' | 'cancelled' | 'expired';

export interface User {
  id: string;
  email: string;
  fullName: string;
  avatarUrl?: string;
  accountType: AccountType;
  subscriptionStatus: SubscriptionStatus;
  subscriptionEndsAt?: string;
  totalPoints: number;
  readingStreak: number;
  createdAt: string;
  updatedAt: string;
}

export interface UserProfile extends User {
  emailVerified: boolean;
  lastLoginAt?: string;
  preferences: UserPreferences;
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'system' | 'amoled' | 'sepia';
  textSize: number;
  emailNotifications: boolean;
  pushNotifications: boolean;
}

// -----------------------------------------------------------------------------
// Book Types
// -----------------------------------------------------------------------------
export type BookStatus = 'draft' | 'published' | 'archived';

export interface Book {
  id: string;
  title: string;
  slug: string;
  description: string;
  authorName: string;
  authorId?: string;
  price: number;
  isFree: boolean;
  totalPages: number;
  previewPages: number;
  coverImageUrl?: string;
  pdfUrl?: string;
  epubUrl?: string;
  language: string;
  status: BookStatus;
  downloadsCount: number;
  viewsCount: number;
  averageRating?: number;
  reviewCount?: number;
  publishedAt?: string;
  createdAt: string;
  updatedAt: string;
}

export interface BookWithTags extends Book {
  tags: Tag[];
}

export interface Tag {
  id: string;
  name: string;
  slug: string;
}

// -----------------------------------------------------------------------------
// Payment Types
// -----------------------------------------------------------------------------
export type PaymentMethod = 'stripe' | 'opay' | 'paypal' | 'flutterwave';
export type PaymentStatus = 'pending' | 'completed' | 'failed' | 'refunded';
export type PaymentItemType = 'book' | 'subscription' | 'custom_booking';

export interface Payment {
  id: string;
  userId: string;
  amount: number;
  currency: string;
  paymentMethod: PaymentMethod;
  itemType: PaymentItemType;
  itemId: string;
  status: PaymentStatus;
  gatewayTransactionId?: string;
  gatewayReference?: string;
  paidAt?: string;
  refundedAt?: string;
  createdAt: string;
}

// -----------------------------------------------------------------------------
// Subscription Types
// -----------------------------------------------------------------------------
export interface SubscriptionPlan {
  id: string;
  name: string;
  slug: string;
  description: string;
  price: number;
  currency: string;
  durationDays: number;
  features: string[];
  booksPerMonth?: number;
  downloadLimit?: number;
  isActive: boolean;
  sortOrder: number;
}

export interface UserSubscription {
  id: string;
  userId: string;
  planId: string;
  plan: SubscriptionPlan;
  startDate: string;
  endDate: string;
  autoRenew: boolean;
  status: 'active' | 'expired' | 'cancelled' | 'pending';
  createdAt: string;
}

// -----------------------------------------------------------------------------
// Booking Types
// -----------------------------------------------------------------------------
export type BookingStatus = 'pending' | 'accepted' | 'in_progress' | 'completed' | 'cancelled' | 'delivered';

export interface Booking {
  id: string;
  userId: string;
  title: string;
  description?: string;
  genre?: string;
  wordCount?: number;
  deadline?: string;
  budget?: number;
  requirements?: Record<string, any>;
  attachments?: string[];
  status: BookingStatus;
  adminNotes?: string;
  userNotes?: string;
  deliveryUrl?: string;
  deliveredAt?: string;
  acceptedAt?: string;
  completedAt?: string;
  paymentId?: string;
  createdAt: string;
  updatedAt: string;
}

// -----------------------------------------------------------------------------
// Gamification Types
// -----------------------------------------------------------------------------
export type BadgeRarity = 'common' | 'rare' | 'epic' | 'legendary';
export type BadgeCriteriaType = 'books_read' | 'reviews_written' | 'purchase_count' | 'streak_days' | 'total_points';

export interface Badge {
  id: string;
  name: string;
  slug: string;
  description: string;
  imageUrl: string;
  criteriaType: BadgeCriteriaType;
  criteriaValue: number;
  points: number;
  rarity: BadgeRarity;
  isActive: boolean;
}

export interface UserBadge {
  userId: string;
  badgeId: string;
  badge: Badge;
  earnedAt: string;
  progress: number;
}

export interface LeaderboardEntry {
  userId: string;
  userName: string;
  userAvatar?: string;
  totalPoints: number;
  rank: number;
  badgesCount: number;
}

// -----------------------------------------------------------------------------
// API Response Types
// -----------------------------------------------------------------------------
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  message?: string;
  errors?: Record<string, string[]>;
  meta?: PaginationMeta;
}

export interface PaginationMeta {
  page: number;
  limit: number;
  total: number;
  totalPages: number;
}

export interface PaginatedResponse<T> extends ApiResponse<T[]> {
  meta: PaginationMeta;
}

// -----------------------------------------------------------------------------
// Analytics Types
// -----------------------------------------------------------------------------
export type EventType = 'page_view' | 'book_view' | 'search' | 'login' | 'purchase';

export interface AnalyticsEvent {
  id: string;
  userId?: string;
  eventType: EventType;
  eventData: Record<string, any>;
  sessionId: string;
  createdAt: string;
}

// -----------------------------------------------------------------------------
// Notification Types
// -----------------------------------------------------------------------------
export type NotificationType = 'welcome' | 'new_book' | 'subscription' | 'payment' | 'booking' | 'system';

export interface Notification {
  id: string;
  userId: string;
  type: NotificationType;
  title: string;
  message: string;
  isRead: boolean;
  metadata?: Record<string, any>;
  createdAt: string;
}

// -----------------------------------------------------------------------------
// Cart Types
// -----------------------------------------------------------------------------
export interface CartItem {
  id: string;
  type: 'book' | 'subscription';
  itemId: string;
  title: string;
  price: number;
  quantity: number;
  coverImage?: string;
}

export interface Cart {
  items: CartItem[];
  subtotal: number;
  total: number;
  itemCount: number;
}
