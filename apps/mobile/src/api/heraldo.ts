/** Llamadas tipadas a las capacidades del módulo Heraldo (id "herald"). */
import { invokeCapability } from "@/api/client";
import type {
  Episode,
  GatherParams,
  NewsCard,
  OnboardingSubmission,
  PodcastStyle,
  Story,
  StorySeed,
  Topic,
  Voice,
} from "@/api/types";

const MODULE = "herald";

export async function gatherStories(params: GatherParams): Promise<Story[]> {
  const input = { reach_threshold: 1, recency_hours: 48, include_keywords: [], exclude_keywords: [], ...params };
  const out = (await invokeCapability(MODULE, "gather_stories", input)) as { stories: Story[] };
  return out.stories;
}

export async function deepenStories(seeds: StorySeed[], topicId?: string): Promise<NewsCard[]> {
  const input = { stories: seeds, topic_id: topicId ?? null };
  const out = (await invokeCapability(MODULE, "deepen_stories", input)) as { cards: NewsCard[] };
  return out.cards;
}

export async function composeEpisode(
  seeds: StorySeed[],
  style: PodcastStyle,
  minutes: number,
  voice: string,
  topicId?: string,
): Promise<Episode> {
  const input = { stories: seeds, style, minutes, voice, topic_id: topicId ?? null };
  const out = (await invokeCapability(MODULE, "compose_episode", input)) as { episode: Episode };
  return out.episode;
}

export async function compileTopic(submission: OnboardingSubmission): Promise<Topic> {
  const out = (await invokeCapability(MODULE, "compile_topic_profile", submission)) as { topic: Topic };
  return out.topic;
}

export async function listTopics(ownerId: string): Promise<Topic[]> {
  const out = (await invokeCapability(MODULE, "list_topics", { owner_id: ownerId })) as { topics: Topic[] };
  return out.topics;
}

export async function listVoices(): Promise<Voice[]> {
  const out = (await invokeCapability(MODULE, "list_voices", {})) as { voices: Voice[] };
  return out.voices;
}

export async function proposeQuestions(name: string): Promise<string[]> {
  const out = (await invokeCapability(MODULE, "propose_topic_questions", { name })) as { questions: string[] };
  return out.questions;
}
