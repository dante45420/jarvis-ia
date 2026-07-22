/** Tipos que espejan los DTOs de Heraldo en el backend (una sola fuente de verdad). */

export type Story = {
  id: string;
  title: string;
  snippet: string;
  url: string;
  reach: number;
  sources: string[];
  latest: string;
};

export type StorySeed = {
  id: string;
  title: string;
  snippet?: string;
  url: string;
  sources: string[];
};

export type NewsCard = {
  story_id: string;
  hook: string;
  one_line: string;
  key_points: string[];
  detail: string;
  why_it_matters: string;
  sources: string[];
};

export type Voice = {
  name: string;
  vibe: string;
};

export type Episode = {
  id: string;
  title: string;
  script: string;
  audio_url: string;
  duration_minutes: number;
  sources: string[];
};

export type GatherParams = {
  subtopics: string[];
  include_keywords?: string[];
  exclude_keywords?: string[];
  reach_threshold?: number;
  recency_hours?: number;
};

export type PodcastStyle = "narrator" | "dialogue";

export type Objective = "learn_skill" | "mental_health" | "stay_informed" | "other";

export type StyleFlags = {
  chilean_casual: boolean;
  backed_with_data: boolean;
  direct: boolean;
  with_examples: boolean;
};

export type Frequency = "daily" | "every_n_days" | "weekly";

export type Cadence = {
  frequency: Frequency;
  every_days: number;
  hour: number;
};

export type Answer = {
  question: string;
  answer: string;
};

/** Lo que el formulario de onboarding envía para compilar y crear un tema. */
export type OnboardingSubmission = {
  owner_id: string;
  name: string;
  podcast_style: PodcastStyle;
  answers: Answer[];
  objective: Objective;
  objective_note: string;
  style: StyleFlags;
  cadence: Cadence;
};

export type Topic = {
  id: string;
  name: string;
  state: string;
  podcast_style: string;
  subtopics: string[];
  include_keywords: string[];
  exclude_keywords: string[];
  reach_threshold: number;
  recency_hours: number;
  cadence: Cadence;
  onboarding: {
    objective: Objective;
    objective_note: string;
    style: StyleFlags;
    questions: Answer[];
  } | null;
};

/** Convierte una historia del menú en la semilla que reenvían deepen/compose. */
export function toSeed(story: Story): StorySeed {
  return { id: story.id, title: story.title, snippet: story.snippet, url: story.url, sources: story.sources };
}
