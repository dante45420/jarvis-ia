import { useMemo, useState } from "react";
import { View } from "react-native";
import { useRouter } from "expo-router";
import { palette, spacing } from "@/theme";
import { Screen } from "@/components/ui/Screen";
import { Txt } from "@/components/ui/Txt";
import { Field } from "@/components/ui/Field";
import { Button } from "@/components/ui/Button";
import { Chip } from "@/components/ui/Chip";
import { Card } from "@/components/ui/Card";
import { Toggle } from "@/components/ui/Toggle";
import { heraldoModule } from "@/modules/heraldo/module";
import { useScreenContext } from "@/state/useScreenContext";
import { useAction } from "@/api/useAsync";
import { ownerId } from "@/api/config";
import { compileTopic, proposeQuestions } from "@/api/heraldo";
import type { Frequency, Objective, OnboardingSubmission, StyleFlags } from "@/api/types";

const OBJECTIVES: { key: Objective; label: string }[] = [
  { key: "learn_skill", label: "Aprender una habilidad" },
  { key: "mental_health", label: "Bienestar mental" },
  { key: "stay_informed", label: "Mantenerme al día" },
  { key: "other", label: "Otro" },
];

const SWITCHES: { key: keyof StyleFlags; label: string }[] = [
  { key: "chilean_casual", label: "Chileno cercano" },
  { key: "backed_with_data", label: "Con datos y fuentes" },
  { key: "direct", label: "Directo, sin relleno" },
  { key: "with_examples", label: "Con ejemplos concretos" },
];

const FREQUENCIES: { key: Frequency; label: string }[] = [
  { key: "daily", label: "Diario" },
  { key: "every_n_days", label: "Cada 3 días" },
  { key: "weekly", label: "Semanal" },
];

const HOURS = [6, 8, 12, 18, 21];
const DEFAULT_STYLE: StyleFlags = {
  chilean_casual: true,
  backed_with_data: true,
  direct: true,
  with_examples: false,
};

export default function Onboarding() {
  useScreenContext(heraldoModule.id, heraldoModule.tabs, "/heraldo/onboarding");
  const router = useRouter();
  const form = useOnboardingForm();
  const propose = useAction(proposeQuestions);
  const compile = useAction(compileTopic);

  async function generateQuestions() {
    const questions = await propose.run(form.name.trim());
    form.setQuestions(questions ?? []);
  }

  async function submit() {
    const topic = await compile.run(form.toSubmission());
    if (topic) {
      router.replace(`/heraldo/podcasts?topicId=${topic.id}&topic=${encodeURIComponent(topic.name)}`);
    }
  }

  return (
    <Screen kicker="Configura un tema" title="Onboarding">
      <TopicStep
        name={form.name}
        onName={form.setName}
        onGenerate={generateQuestions}
        generating={propose.loading}
      />
      <ObjectivePicker objective={form.objective} onPick={form.setObjective} />
      {form.objective === "other" ? (
        <Field value={form.note} onChangeText={form.setNote} placeholder="¿Qué buscas en este tema?" />
      ) : null}
      <StyleSwitches style={form.style} onToggle={form.toggleStyle} />
      <CadencePicker
        frequency={form.frequency}
        onFrequency={form.setFrequency}
        hour={form.hour}
        onHour={form.setHour}
      />
      <QuestionsForm
        questions={form.questions}
        answers={form.answers}
        onAnswer={form.setAnswer}
      />
      <Submit ready={form.ready} loading={compile.loading} error={compile.error} onSubmit={submit} />
    </Screen>
  );
}

function useOnboardingForm() {
  const [name, setName] = useState("");
  const [objective, setObjective] = useState<Objective>("learn_skill");
  const [note, setNote] = useState("");
  const [style, setStyle] = useState<StyleFlags>(DEFAULT_STYLE);
  const [frequency, setFrequency] = useState<Frequency>("daily");
  const [hour, setHour] = useState(8);
  const [questions, setQuestions] = useState<string[] | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});

  const toggleStyle = (key: keyof StyleFlags) =>
    setStyle((prev) => ({ ...prev, [key]: !prev[key] }));
  const setAnswer = (question: string, value: string) =>
    setAnswers((prev) => ({ ...prev, [question]: value }));

  const ready = name.trim().length > 0;
  const toSubmission = (): OnboardingSubmission => ({
    owner_id: ownerId,
    name: name.trim(),
    podcast_style: "narrator",
    answers: (questions ?? []).map((question) => ({ question, answer: answers[question] ?? "" })),
    objective,
    objective_note: note.trim(),
    style,
    cadence: { frequency, every_days: frequency === "every_n_days" ? 3 : 1, hour },
  });

  return {
    name, setName, objective, setObjective, note, setNote, style, toggleStyle,
    frequency, setFrequency, hour, setHour, questions, setQuestions, answers, setAnswer,
    ready, toSubmission,
  };
}

function TopicStep({
  name,
  onName,
  onGenerate,
  generating,
}: {
  name: string;
  onName: (t: string) => void;
  onGenerate: () => void;
  generating: boolean;
}) {
  return (
    <View style={{ gap: spacing.sm }}>
      <Txt variant="label">¿Sobre qué tema quieres que Jarvis te hable?</Txt>
      <Field value={name} onChangeText={onName} placeholder="Ej: IA para emprender" />
      <Button
        label="Generar preguntas del tema"
        variant="secondary"
        onPress={onGenerate}
        loading={generating}
        disabled={!name.trim()}
      />
    </View>
  );
}

function ObjectivePicker({
  objective,
  onPick,
}: {
  objective: Objective;
  onPick: (o: Objective) => void;
}) {
  return (
    <View style={{ gap: spacing.sm }}>
      <SectionLabel text="¿Para qué sigues este tema?" />
      <View style={styles.wrap}>
        {OBJECTIVES.map((item) => (
          <Chip
            key={item.key}
            label={item.label}
            selected={objective === item.key}
            onPress={() => onPick(item.key)}
          />
        ))}
      </View>
    </View>
  );
}

function StyleSwitches({
  style,
  onToggle,
}: {
  style: StyleFlags;
  onToggle: (key: keyof StyleFlags) => void;
}) {
  return (
    <View style={{ gap: spacing.sm }}>
      <SectionLabel text="Tono y estilo" />
      <Card style={{ gap: spacing.md }}>
        {SWITCHES.map((item) => (
          <View key={item.key} style={styles.switchRow}>
            <Txt variant="label">{item.label}</Txt>
            <Toggle value={style[item.key]} onChange={() => onToggle(item.key)} />
          </View>
        ))}
      </Card>
    </View>
  );
}

function CadencePicker({
  frequency,
  onFrequency,
  hour,
  onHour,
}: {
  frequency: Frequency;
  onFrequency: (f: Frequency) => void;
  hour: number;
  onHour: (h: number) => void;
}) {
  return (
    <View style={{ gap: spacing.sm }}>
      <SectionLabel text="¿Cada cuánto y a qué hora?" />
      <View style={styles.wrap}>
        {FREQUENCIES.map((item) => (
          <Chip
            key={item.key}
            label={item.label}
            selected={frequency === item.key}
            onPress={() => onFrequency(item.key)}
          />
        ))}
      </View>
      <View style={styles.wrap}>
        {HOURS.map((value) => (
          <Chip
            key={value}
            label={`${value}:00`}
            selected={hour === value}
            onPress={() => onHour(value)}
          />
        ))}
      </View>
    </View>
  );
}

function QuestionsForm({
  questions,
  answers,
  onAnswer,
}: {
  questions: string[] | null;
  answers: Record<string, string>;
  onAnswer: (question: string, value: string) => void;
}) {
  if (questions === null) {
    return (
      <Txt variant="small" dim>
        Escribe el tema y toca "Generar preguntas" para que Jarvis afine lo que te interesa.
      </Txt>
    );
  }
  if (questions.length === 0) {
    return <Txt variant="small" dim>No hubo preguntas para este tema. Puedes crearlo igual.</Txt>;
  }
  return (
    <View style={{ gap: spacing.md }}>
      <SectionLabel text="Lo que Jarvis quiere saber" />
      {questions.map((question) => (
        <View key={question} style={{ gap: spacing.xs }}>
          <Txt variant="label">{question}</Txt>
          <Field
            value={answers[question] ?? ""}
            onChangeText={(value) => onAnswer(question, value)}
            placeholder="Tu respuesta"
          />
        </View>
      ))}
    </View>
  );
}

function Submit({
  ready,
  loading,
  error,
  onSubmit,
}: {
  ready: boolean;
  loading: boolean;
  error: string | null;
  onSubmit: () => void;
}) {
  return (
    <View style={{ gap: spacing.sm, marginTop: spacing.sm }}>
      {error ? <Txt variant="small" color={palette.coral}>{error}</Txt> : null}
      <Button label="Crear tema" onPress={onSubmit} loading={loading} disabled={!ready} />
    </View>
  );
}

function SectionLabel({ text }: { text: string }) {
  return (
    <Txt variant="mono" dim>
      {text.toUpperCase()}
    </Txt>
  );
}

const styles = {
  wrap: { flexDirection: "row" as const, flexWrap: "wrap" as const, gap: spacing.sm },
  switchRow: {
    flexDirection: "row" as const,
    alignItems: "center" as const,
    justifyContent: "space-between" as const,
  },
};
