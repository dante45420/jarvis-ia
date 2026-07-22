import { useState } from "react";
import { View } from "react-native";
import { useRouter } from "expo-router";
import { spacing } from "@/theme";
import { Screen } from "@/components/ui/Screen";
import { Txt } from "@/components/ui/Txt";
import { Button } from "@/components/ui/Button";
import { StateView } from "@/components/ui/StateView";
import { SkeletonList } from "@/components/ui/Skeleton";
import { StoryCard } from "@/components/heraldo/StoryCard";
import { NewsCardView } from "@/components/heraldo/NewsCardView";
import { heraldoModule } from "@/modules/heraldo/module";
import { useScreenContext } from "@/state/useScreenContext";
import { useAsync, useAction } from "@/api/useAsync";
import { gatherStories, deepenStories } from "@/api/heraldo";
import { toSeed, type NewsCard, type Story } from "@/api/types";

const DEFAULT_INTEREST = ["inteligencia artificial", "tecnología", "startups"];

export default function Noticias() {
  useScreenContext(heraldoModule.id, heraldoModule.tabs, "/heraldo/noticias");
  const router = useRouter();
  const candidates = useAsync(
    () => gatherStories({ subtopics: DEFAULT_INTEREST, recency_hours: 72 }),
    [],
  );
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [cards, setCards] = useState<NewsCard[] | null>(null);
  const deepen = useAction(deepenStories);

  function toggle(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  async function profundizar(stories: Story[]) {
    const seeds = stories.filter((story) => selected.has(story.id)).map(toSeed);
    const result = await deepen.run(seeds);
    setCards(result ?? []);
  }

  function reset() {
    setCards(null);
    setSelected(new Set());
  }

  if (cards) {
    return (
      <Screen kicker="Tu selección" title="Noticiero">
        {cards.map((card) => (
          <NewsCardView key={card.story_id} card={card} />
        ))}
        <Button label="Ver otras noticias" variant="secondary" onPress={reset} />
      </Screen>
    );
  }

  return (
    <Screen
      kicker="Titulares de hoy"
      title="Noticiero"
      rightAction={{ icon: "options", onPress: () => router.push("/heraldo/config") }}
    >
      <Txt variant="mono" dim style={{ marginTop: -spacing.xs }}>
        ELIGE CUÁLES PROFUNDIZAR · SOLO ESAS GASTAN IA
      </Txt>

      <StateView
        loading={candidates.loading}
        error={candidates.error}
        onRetry={candidates.reload}
        skeleton={<SkeletonList count={4} />}
      >
        <Candidates
          stories={candidates.data ?? []}
          selected={selected}
          onToggle={toggle}
          onDeepen={() => profundizar(candidates.data ?? [])}
          deepening={deepen.loading}
        />
      </StateView>
    </Screen>
  );
}

function Candidates({
  stories,
  selected,
  onToggle,
  onDeepen,
  deepening,
}: {
  stories: Story[];
  selected: Set<string>;
  onToggle: (id: string) => void;
  onDeepen: () => void;
  deepening: boolean;
}) {
  if (stories.length === 0) {
    return (
      <Txt dim style={{ textAlign: "center", paddingVertical: spacing.xl }}>
        No hay titulares frescos por ahora. Vuelve más tarde.
      </Txt>
    );
  }
  return (
    <View style={{ gap: spacing.md }}>
      {stories.map((story) => (
        <StoryCard
          key={story.id}
          story={story}
          selected={selected.has(story.id)}
          onToggle={() => onToggle(story.id)}
        />
      ))}
      <Button
        label={selected.size ? `Profundizar (${selected.size})` : "Elige al menos una"}
        onPress={onDeepen}
        loading={deepening}
        disabled={selected.size === 0}
      />
    </View>
  );
}
