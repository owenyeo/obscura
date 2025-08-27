// App.tsx
import { useState } from "react";
import { Image, View, Text, Pressable, ActivityIndicator, StyleSheet } from "react-native";
import * as ImagePicker from "expo-image-picker";

export default function App() {
  const [img, setImg] = useState<{ uri: string; type?: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function pick() {
    setErr(null);
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== "granted") return setErr("Permission denied");
    const res = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.9,
      allowsMultipleSelection: false,
    });
    if (!res.canceled) {
      const a = res.assets[0];
      setImg({ uri: a.uri, type: a.mimeType ?? "image/jpeg" });
    }
  }

  async function upload() {
    if (!img) return;
    setBusy(true); setErr(null);
    try {
      const fd = new FormData();
      fd.append("file", {
        // @ts-ignore React Native FormData file
        uri: img.uri,
        name: "photo.jpg",
        type: img.type || "image/jpeg",
      });
      const r = await fetch("https://your-api.example.com/upload", {
        method: "POST",
        body: fd,
        headers: { "Content-Type": "multipart/form-data" },
      });
      if (!r.ok) throw new Error(`Upload failed: ${r.status}`);
    } catch (e: any) {
      setErr(String(e.message || e));
    } finally { setBusy(false); }
  }

  return (
    <View style={{ padding: 16, gap: 12, flex: 1, justifyContent: "center"}}>
      <UploadBox
        imageUri={img?.uri || null}
        busy={busy}
        onPress={pick}
      />

      {img && (
        <Pressable
          onPress={upload}
          disabled={busy}
          style={[styles.uploadBtn, busy && { opacity: 0.6 }]}
          accessibilityRole="button"
        >
          <Text style={styles.uploadBtnText}>{busy ? "Uploading…" : "Upload"}</Text>
        </Pressable>
      )}

      {err && <Text style={{ color: "red" }}>{err}</Text>}
    </View>
  );
}

function UploadBox({
  imageUri,
  onPress,
  busy,
}: {
  imageUri: string | null;
  onPress: () => void;
  busy?: boolean;
}) {
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      style={({ pressed }) => [
        styles.box,
        pressed && { opacity: 0.85 },
        imageUri ? styles.boxWithImage : styles.boxEmpty,
      ]}
    >
      {imageUri ? (
        <>
          <Image source={{ uri: imageUri }} style={styles.boxImage} />
          <View style={styles.overlay}>
            <Text style={styles.overlayText}>{busy ? "Busy…" : "Tap to change"}</Text>
          </View>
        </>
      ) : (
        <View style={styles.boxInner}>
          <Text style={styles.icon}>⬆️</Text>
          <Text style={styles.title}>Tap to upload</Text>
          <Text style={styles.subtitle}>PNG or JPG, up to ~10MB</Text>
        </View>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  box: {
    height: 280,
    borderRadius: 12,
    overflow: "hidden",
  },
  boxEmpty: {
    borderWidth: 2,
    borderStyle: "dashed",
    borderColor: "#BDBDBD",
    backgroundColor: "#FAFAFA",
    alignItems: "center",
    justifyContent: "center",
  },
  boxWithImage: {
    borderWidth: 0,
    backgroundColor: "#000",
  },
  boxInner: { alignItems: "center", gap: 6 },
  icon: { fontSize: 28, marginBottom: 4 },
  title: { fontSize: 16, fontWeight: "600" },
  subtitle: { fontSize: 12, color: "#666" },
  boxImage: { width: "100%", height: "100%" },
  overlay: {
    position: "absolute",
    bottom: 0,
    width: "100%",
    paddingVertical: 8,
    backgroundColor: "rgba(0,0,0,0.4)",
    alignItems: "center",
  },
  overlayText: { color: "#fff", fontWeight: "600" },
  uploadBtn: {
    backgroundColor: "#111",
    paddingVertical: 12,
    borderRadius: 10,
    alignItems: "center",
  },
  uploadBtnText: { color: "#fff", fontWeight: "600" },
});
