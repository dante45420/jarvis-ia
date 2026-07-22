/** Campo de texto temado. */
import { TextInput } from "react-native";
import { fontFamily, fontSize, palette, radius, spacing } from "@/theme";

type Props = {
  value: string;
  onChangeText: (text: string) => void;
  placeholder?: string;
  onSubmitEditing?: () => void;
};

export function Field({ value, onChangeText, placeholder, onSubmitEditing }: Props) {
  return (
    <TextInput
      value={value}
      onChangeText={onChangeText}
      placeholder={placeholder}
      placeholderTextColor={palette.dim}
      onSubmitEditing={onSubmitEditing}
      returnKeyType="search"
      style={{
        backgroundColor: palette.surface,
        borderWidth: 1,
        borderColor: palette.line,
        borderRadius: radius.md,
        paddingHorizontal: spacing.lg,
        paddingVertical: spacing.md + 2,
        color: palette.text,
        fontFamily: fontFamily.bodyRegular,
        fontSize: fontSize.body,
      }}
    />
  );
}
