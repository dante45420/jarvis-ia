import { useState } from "react";
import { Linking, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { palette, radius, spacing } from "@/theme";
import { Screen } from "@/components/ui/Screen";
import { Txt } from "@/components/ui/Txt";
import { Field } from "@/components/ui/Field";
import { Button } from "@/components/ui/Button";
import { Chip } from "@/components/ui/Chip";
import { Card } from "@/components/ui/Card";
import { StateView } from "@/components/ui/StateView";
import { SkeletonList } from "@/components/ui/Skeleton";
import { StagedProgress } from "@/components/ui/StagedProgress";
import { StoryCard } from "@/components/heraldo/StoryCard";
import { heraldoModule } from "@/modules/heraldo/module";
import { useScreenContext } from "@/state/useScreenContext";
import { useAsync, useAction } from "@/api/useAsync";
import { composeEpisode, gatherStories, listVoices } from "@/api/heraldo";
import { toSeed, type Episode, type Story } from "@/api/types";

const MINUTES = [3, 5, 10];
const STAGES = [
  "Reuniendo fuentes reales…",
  "Escribiendo el guion con sustancia…",
  "Grabando la voz…",
  "Puliendo el audio…",
];

export default function Podcasts() {
  useScreenContext(heraldoModule.id, heraldoModule.tabs, "/heraldo/podcasts");
  const router = useRouter();
  const params = useLocalSearchParams<{ topicId?: string; topic?: string }>();
  const topicId = typeof params.topicId === "string" ? params.topicId : undefined;
  const [topic, setTopic] = useState(typeof params.topic === "string" ? params.topic : "");
  const [voice, setVoice] = useState("Charon");
  const [minutes, setMinutes] = useState(5);
  const [stories, setStories] = useState<Story[] | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [episode, setEpisode] = useState<Episode | null>(null);

  const gather = useAction(gatherStories);
  const compose = useAction(composeEpisode);

  async function findSources() {
    const terms = topic.trim();
    if (!terms) {
      return;
    }
    const result = await gather.run({ subtopics: terms.split(/\s+/), recency_hours: 336 });
    setStories(result ?? []);
  }

  function toggle(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  async function generate() {
    const seeds = (stories ?? []).filter((story) => selected.has(story.id)).map(toSeed);
    const result = await compose.run(seeds, "narrator", minutes, voice, topicId);
    setEpisode(result);
  }

  function restart() {
    setEpisode(null);
    setStories(null);
    setSelected(new Set());
  }

  if (compose.loading) {
    return (
      <Screen kicker="Generando" title="Podcast">
        <StagedProgress stages={STAGES} stageSeconds={30} />
      </Screen>
    );
  }

  if (episode) {
    return (
      <Screen kicker="Listo para escuchar" title="Podcast">
        <Player episode={episode} onRestart={restart} />
      </Screen>
    );
  }

  return (
    <Screen
      kicker="Nuevo episodio"
      title="Podcast"
      rightAction={{ icon: "options", onPress: () => router.push("/heraldo/config") }}
    >
      <TopicBanner personalized={Boolean(topicId)} onConfigure={() => router.push("/heraldo/onboarding")} />
      <Setup
        topic={topic}
        onTopic={setTopic}
        voice={voice}
        onVoice={setVoice}
        minutes={minutes}
        onMinutes={setMinutes}
        onFind={findSources}
        finding={gather.loading}
      />
      <StateView
        loading={gather.loading}
        error={gather.error}
        onRetry={findSources}
        skeleton={<SkeletonList count={3} />}
      >
        <Selection
          stories={stories}
          selected={selected}
          onToggle={toggle}
          onGenerate={generate}
        />
      </StateView>
    </Screen>
  );
}

function TopicBanner({ personalized, onConfigure }: { personalized: boolean; onConfigure: () => void }) {
  if (personalized) {
    return (
      <View style={{ flexDirection: "row", alignItems: "center", gap: spacing.sm }}>
        <Chip label="✓ Tema personalizado" selected onPress={onConfigure} />
        <Txt variant="small" dim>
          Jarvis usa tu onboarding y no repite ángulos.
        </Txt>
      </View>
    );
  }
  return (
    <Button label="Configurar un tema (onboarding) →" variant="secondary" onPress={onConfigure} />
  );
}

function Setup({
  topic,
  onTopic,
  voice,
  onVoice,
  minutes,
  onMinutes,
  onFind,
  finding,
}: {
  topic: string;
  onTopic: (t: string) => void;
  voice: string;
  onVoice: (v: string) => void;
  minutes: number;
  onMinutes: (m: number) => void;
  onFind: () => void;
  finding: boolean;
}) {
  return (
    <View style={{ gap: spacing.md }}>
      <Txt variant="label">¿Sobre qué tema?</Txt>
      <Field value={topic} onChangeText={onTopic} onSubmitEditing={onFind} placeholder="Ej: IA para emprender" />

      <Txt variant="label" style={{ marginTop: spacing.sm }}>
        Duración
      </Txt>
      <View style={{ flexDirection: "row", gap: spacing.sm }}>
        {MINUTES.map((m) => (
          <Chip key={m} label={`${m} min`} selected={minutes === m} onPress={() => onMinutes(m)} />
        ))}
      </View>

      <VoicePicker voice={voice} onVoice={onVoice} />

      <Button label="Buscar fuentes" onPress={onFind} loading={finding} disabled={!topic.trim()} />
    </View>
  );
}

function VoicePicker({ voice, onVoice }: { voice: string; onVoice: (v: string) => void }) {
  const voices = useAsync(listVoices, []);
  return (
    <View style={{ gap: spacing.sm }}>
      <Txt variant="label" style={{ marginTop: spacing.sm }}>
        Voz
      </Txt>
      <StateView loading={voices.loading} error={voices.error} onRetry={voices.reload}>
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
          {(voices.data ?? []).map((item) => (
            <Chip
              key={item.name}
              label={`${item.name} · ${item.vibe}`}
              selected={voice === item.name}
              onPress={() => onVoice(item.name)}
            />
          ))}
        </View>
      </StateView>
    </View>
  );
}

function Selection({
  stories,
  selected,
  onToggle,
  onGenerate,
}: {
  stories: Story[] | null;
  selected: Set<string>;
  onToggle: (id: string) => void;
  onGenerate: () => void;
}) {
  if (stories === null) {
    return null;
  }
  if (stories.length === 0) {
    return (
      <Txt dim style={{ textAlign: "center", paddingVertical: spacing.lg }}>
        No encontré fuentes para eso. Prueba con otro tema.
      </Txt>
    );
  }
  return (
    <View style={{ gap: spacing.md }}>
      <Txt variant="mono" dim>
        ELIGE LAS FUENTES DEL EPISODIO
      </Txt>
      {stories.map((story) => (
        <StoryCard
          key={story.id}
          story={story}
          selected={selected.has(story.id)}
          onToggle={() => onToggle(story.id)}
        />
      ))}
      <Button
        label={selected.size ? `Generar episodio (${selected.size})` : "Elige al menos una fuente"}
        onPress={onGenerate}
        disabled={selected.size === 0}
      />
    </View>
  );
}

function Player({ episode, onRestart }: { episode: Episode; onRestart: () => void }) {
  const [showScript, setShowScript] = useState(false);
  return (
    <View style={{ gap: spacing.md }}>
      <Card>
        <Txt variant="title">{episode.title}</Txt>
        <Txt variant="mono" dim style={{ marginTop: spacing.sm }}>
          {episode.duration_minutes} MIN · {episode.sources.length} FUENTES
        </Txt>
      </Card>

      <Button label="▶  Escuchar episodio" onPress={() => Linking.openURL(episode.audio_url)} />

      <Button
        label={showScript ? "Ocultar guion" : "Ver guion"}
        variant="secondary"
        onPress={() => setShowScript((prev) => !prev)}
      />
      {showScript ? (
        <Card>
          <Txt variant="small" style={{ lineHeight: 22 }}>
            {episode.script}
          </Txt>
        </Card>
      ) : null}

      {episode.sources.length ? (
        <View style={styles.sources}>
          {episode.sources.map((source) => (
            <View key={source} style={styles.sourceChip}>
              <Txt variant="mono" dim>
                {source}
              </Txt>
            </View>
          ))}
        </View>
      ) : null}

      <Button label="Crear otro episodio" variant="secondary" onPress={onRestart} />
    </View>
  );
}

const styles = {
  sources: { flexDirection: "row" as const, flexWrap: "wrap" as const, gap: spacing.sm },
  sourceChip: {
    borderWidth: 1,
    borderColor: palette.line,
    borderRadius: radius.pill,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
  },
};
