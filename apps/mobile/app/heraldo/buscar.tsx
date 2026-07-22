import { useState } from "react";
import { Linking, View } from "react-native";
import { useRouter } from "expo-router";
import { spacing } from "@/theme";
import { Screen } from "@/components/ui/Screen";
import { Txt } from "@/components/ui/Txt";
import { Field } from "@/components/ui/Field";
import { Button } from "@/components/ui/Button";
import { StateView } from "@/components/ui/StateView";
import { SkeletonList } from "@/components/ui/Skeleton";
import { StoryCard } from "@/components/heraldo/StoryCard";
import { heraldoModule } from "@/modules/heraldo/module";
import { useScreenContext } from "@/state/useScreenContext";
import { useAction } from "@/api/useAsync";
import { gatherStories } from "@/api/heraldo";
import type { Story } from "@/api/types";

export default function Buscar() {
  useScreenContext(heraldoModule.id, heraldoModule.tabs, "/heraldo/buscar");
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [stories, setStories] = useState<Story[] | null>(null);
  const { run, loading, error } = useAction(gatherStories);

  async function search() {
    const terms = query.trim();
    if (!terms) {
      return;
    }
    const result = await run({ subtopics: terms.split(/\s+/), recency_hours: 336 });
    setStories(result ?? []);
  }

  return (
    <Screen
      kicker="Buscador · en vivo"
      title="Buscar"
      rightAction={{ icon: "options", onPress: () => router.push("/heraldo/config") }}
    >
      <Txt dim style={{ marginTop: -spacing.xs }}>
        Jarvis busca en la web real y junta las mejores fuentes sobre lo que preguntes.
      </Txt>
      <Field
        value={query}
        onChangeText={setQuery}
        onSubmitEditing={search}
        placeholder="Ej: agentes de IA en producción"
      />
      <Button label="Buscar en vivo" onPress={search} loading={loading} disabled={!query.trim()} />

      <StateView
        loading={loading}
        error={error}
        onRetry={search}
        skeleton={<SkeletonList count={4} />}
      >
        <Results stories={stories} />
      </StateView>
    </Screen>
  );
}

function Results({ stories }: { stories: Story[] | null }) {
  if (stories === null) {
    return null;
  }
  if (stories.length === 0) {
    return (
      <Txt dim style={{ textAlign: "center", paddingVertical: spacing.xl }}>
        No encontré nada fresco para eso. Prueba con otras palabras.
      </Txt>
    );
  }
  return (
    <View style={{ gap: spacing.md }}>
      <Txt variant="mono" dim>
        {stories.length} FUENTES
      </Txt>
      {stories.map((story) => (
        <StoryCard key={story.id} story={story} onOpen={() => Linking.openURL(story.url)} />
      ))}
    </View>
  );
}
