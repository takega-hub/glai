// User types
export interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
}

export interface UserProfile {
  name: string;
  email: string;
  birthDate: string;
  avatar: string;
  about: string;
  joinedDate: string;
  totalChatTime: string;
  unlockedContent: {
    photos: number;
    videos: number;
  };
  activeCharacters: number;
}

// Character types
export interface Character {
  id: string;
  name: string;
  display_name: string;
  avatar_url: string;
  avatar?: string;
  image?: string;
  profile_image?: string;
  photo?: string;
  personality_type: string;
  archetype?: string;
  biography?: string;
  age?: number;
  status: string;
  last_interaction?: string;
  trust_score: number;
  current_layer: number;
  content_preview: {
    id: string;
    thumbnail_url?: string;
    is_locked: boolean;
  }[];
  is_hot: boolean;
}

// Chat types
export interface Message {
  id: string;
  text: string;
  sender: 'user' | 'character' | 'system' | 'assistant';
  timestamp: Date;
  imageUrl?: string;
  action?: 'awaiting_gift_for_generation';
  photo_proposal_details?: any;
  giftProposal?: any;
}

// Content types
export interface ContentItem {
  id: string;
  type: 'photo' | 'video';
  url: string;
  media_url: string;
  thumbnail_url?: string;
  title: string;
  description: string;
  is_locked: boolean;
  unlock_requirement?: string;
  trust_level_required: number;
}